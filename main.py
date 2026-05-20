"""
命令行模式 — 先跑通 Agent 对话和记忆，不涉及语音
用法：python main.py
"""
import asyncio
from datetime import datetime
from agent import CarAgent, Context


async def main():
    agent = CarAgent()
    ctx = Context(
        speed_kmh=80,
        duration_min=30,
        hour=datetime.now().hour,
        user_id="test_user",
    )

    print(f"场景：{ctx.to_str()}")
    print("输入 quit 退出\n")

    while True:
        user_input = input("你：").strip()
        if not user_input or user_input == "quit":
            break

        reply = await agent.chat(user_input, ctx)
        print(f"助手：{reply}\n")


if __name__ == "__main__":
    asyncio.run(main())
