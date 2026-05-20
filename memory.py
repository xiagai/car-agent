from mem0 import AsyncMemory
from dotenv import load_dotenv
import os

load_dotenv()

_memory: AsyncMemory = None


def get_memory() -> AsyncMemory:
    global _memory
    if _memory is None:
        _memory = AsyncMemory()
    return _memory


async def remember(user_id: str, messages: list):
    """对话结束后提取并存储记忆"""
    m = get_memory()
    await m.add(messages, user_id=user_id)


async def recall(user_id: str, query: str) -> str:
    """检索与当前场景相关的记忆"""
    m = get_memory()
    results = await m.search(query, user_id=user_id, limit=5)
    if not results:
        return ""
    return "\n".join(r["memory"] for r in results)
