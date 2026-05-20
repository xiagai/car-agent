import json
from dataclasses import dataclass
from llm import LLMClient
from memory import recall, remember
from tools import ALL_TOOLS, TOOL_HANDLERS

SYSTEM_PROMPT = """你是一个车载陪伴助手，陪伴用户度过驾驶时光。

当前场景：
{context}

关于这个用户你记得：
{memories}

行为准则：
- 用自然口语回答，不要用列表或标题格式
- 回答简短，适合语音播报
- 用户沉默时可以主动找话题
- 根据场景推荐合适的内容（播客/新闻/闲聊）
- 记住用户说过的偏好
"""


@dataclass
class Context:
    speed_kmh: float = 0
    duration_min: float = 0
    hour: int = 12
    user_id: str = "default"

    def to_str(self) -> str:
        scene = "停车" if self.speed_kmh < 5 else ("市区行驶" if self.speed_kmh < 80 else "高速行驶")
        period = "凌晨" if self.hour < 6 else ("早高峰" if self.hour < 9 else ("白天" if self.hour < 18 else "夜间"))
        return f"{period}，{scene}，已行驶 {self.duration_min:.0f} 分钟"


class CarAgent:
    def __init__(self, provider: str = None):
        self.llm = LLMClient(provider)
        self.history: list = []

    async def _inject_context(self, user_input: str, ctx: Context):
        """首轮时注入系统提示，追加用户消息。"""
        if not self.history:
            memories = await recall(ctx.user_id, user_input)
            self.history.append({
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    context=ctx.to_str(),
                    memories=memories or "暂无记录",
                ),
            })
        self.history.append({"role": "user", "content": user_input})

    async def _run_tools(self, response) -> bool:
        """如果 response 含 tool call，执行并追加结果。返回是否有 tool call。"""
        if not response.tool_calls:
            return False
        self.history.append({"role": "assistant", "content": None, "tool_calls": [
            tc.model_dump() for tc in response.tool_calls
        ]})
        for tc in response.tool_calls:
            fn = TOOL_HANDLERS.get(tc.function.name)
            if fn:
                args = json.loads(tc.function.arguments)
                result = await fn(**args)
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        return True

    async def _persist(self, user_id: str, reply: str):
        self.history.append({"role": "assistant", "content": reply})
        user_turns = sum(1 for m in self.history if m["role"] == "user")
        if user_turns % 5 == 0:
            await remember(user_id, self.history)

    async def chat(self, user_input: str, ctx: Context) -> str:
        await self._inject_context(user_input, ctx)
        response = await self.llm.chat(self.history, tools=ALL_TOOLS, stream=False)
        if await self._run_tools(response):
            response = await self.llm.chat(self.history, stream=False)
        reply = response.content
        await self._persist(ctx.user_id, reply)
        return reply

    async def chat_stream(self, user_input: str, ctx: Context):
        """流式输出，返回 async generator of str tokens。
        先非流式检测 tool call（开销低），之后最终回复走流式。
        """
        await self._inject_context(user_input, ctx)
        probe = await self.llm.chat(self.history, tools=ALL_TOOLS, stream=False)
        await self._run_tools(probe)  # 有 tool call 则执行并追加；无则无操作
        stream = await self.llm.chat(self.history, stream=True)

        collected = []

        async def _streamed():
            async for token in stream:
                collected.append(token)
                yield token
            await self._persist(ctx.user_id, "".join(collected))

        return _streamed()
