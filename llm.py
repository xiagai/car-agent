from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "QWEN_API_KEY",
        "model": "qwen-max",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "api_key_env": "MOONSHOT_API_KEY",
        "model": "moonshot-v1-128k",
    },
}


class LLMClient:
    def __init__(self, provider: str = None):
        provider = provider or os.getenv("LLM_PROVIDER", "deepseek")
        cfg = PROVIDERS[provider]
        self.model = cfg["model"]
        self.client = AsyncOpenAI(
            api_key=os.getenv(cfg["api_key_env"]),
            base_url=cfg["base_url"],
        )

    async def chat(self, messages: list, tools: list = None, stream: bool = True):
        kwargs = dict(model=self.model, messages=messages, stream=stream)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)

        if not stream:
            return response.choices[0].message

        async def _stream():
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        return _stream()
