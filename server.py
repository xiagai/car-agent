"""
FastAPI + WebSocket 后端服务
用法：uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agent import CarAgent, Context

app = FastAPI(title="Car Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")

# 每个 user_id 维护一个 agent 实例（保留对话历史）
_agents: dict[str, CarAgent] = {}


def get_agent(user_id: str) -> CarAgent:
    if user_id not in _agents:
        _agents[user_id] = CarAgent()
    return _agents[user_id]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    agent = get_agent(user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "invalid json"})
                continue

            # 构建 Context，客户端可传入实际数据，缺省用合理默认值
            ctx = Context(
                speed_kmh=data.get("speed_kmh", 0),
                duration_min=data.get("duration_min", 0),
                hour=data.get("hour", datetime.now().hour),
                user_id=user_id,
            )

            user_input = data.get("text", "").strip()
            if not user_input:
                await websocket.send_json({"type": "error", "message": "empty input"})
                continue

            # 流式输出：逐 token 推送
            await websocket.send_json({"type": "start"})
            full_reply = ""
            async for token in await agent.chat_stream(user_input, ctx):
                full_reply += token
                await websocket.send_json({"type": "token", "text": token})
            await websocket.send_json({"type": "done", "text": full_reply})

    except WebSocketDisconnect:
        pass
