# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

Copy `.env.example` to `.env` and fill in at minimum one LLM provider key:

```bash
cp .env.example .env
pip install -r requirements.txt
```

## Running

CLI mode (for local testing):
```bash
python3 main.py
```

WebSocket server:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

This is a **car companion AI agent** designed for in-vehicle use. It converses with users, remembers preferences across sessions, and can invoke tools (currently: podcast search).

**Data flow per turn:**
1. `main.py` — creates a hardcoded `Context` (speed, time of day, duration) and runs the REPL
2. `agent.py:CarAgent.chat()` — orchestrates each turn:
   - Calls `memory.recall()` to prepend relevant past memories to the system prompt
   - Sends conversation history + tools to the LLM
   - If the LLM returns tool calls, executes them via `TOOL_HANDLERS` and re-queries the LLM for a final reply
   - Every 5 user turns, calls `memory.remember()` to persist the conversation to mem0
3. `llm.py:LLMClient` — thin wrapper around the OpenAI-compatible SDK; supports DeepSeek, Qwen (Dashscope), and Kimi (Moonshot) via `LLM_PROVIDER` env var
4. `memory.py` — uses `mem0ai` (`AsyncMemory`) for semantic memory storage/retrieval per `user_id`
5. `tools/` — each tool module exposes a `TOOL_SPEC` (OpenAI function-calling schema) and an async handler; `tools/__init__.py` aggregates into `ALL_TOOLS` and `TOOL_HANDLERS`

**Adding a new tool:** create `tools/my_tool.py` with an async function and a `TOOL_SPEC` dict, then register both in `tools/__init__.py`.

**LLM provider selection:** set `LLM_PROVIDER=deepseek|qwen|kimi` in `.env`. The client uses the OpenAI SDK with provider-specific `base_url` and `api_key_env`.

**Memory backend:** mem0 requires `MEM0_API_KEY` (cloud) or can run locally — see mem0 docs. Memory is keyed by `user_id` set in `Context`.

## Planned but not yet implemented

`requirements.txt` includes `fastapi`, `uvicorn`, `websockets`, `sounddevice`, and `numpy` — these suggest a future voice/WebSocket interface. The current code only has the CLI mode.
