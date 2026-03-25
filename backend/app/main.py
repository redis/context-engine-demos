from __future__ import annotations

import json
from time import perf_counter
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.app.context_surface_service import ContextSurfaceService
from backend.app.contracts import ChatRequest
from backend.app.internal_tools import InternalToolService, internal_tool_names
from backend.app.langgraph_agent import create_agent, create_checkpointer
from backend.app.rag_service import SimpleRAGService
from backend.app.settings import get_settings

settings = get_settings()
app = FastAPI(title="Reddish Delivery Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin, "http://localhost:3040", "http://127.0.0.1:3040"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

internal_tools = InternalToolService(settings)
cs_service = ContextSurfaceService(settings)
rag_service = SimpleRAGService(settings)

_langgraph_agent = None
_checkpointer = None


async def get_agent():
    global _langgraph_agent, _checkpointer
    if _langgraph_agent is None:
        _checkpointer = await create_checkpointer(settings)
        _langgraph_agent = await create_agent(settings, internal_tools, cs_service, _checkpointer)
    return _langgraph_agent


class Timer:
    def __init__(self) -> None:
        self._start = perf_counter()
        self._lap = self._start

    def elapsed_ms(self) -> int:
        return round((perf_counter() - self._start) * 1000)

    def lap_ms(self) -> int:
        now = perf_counter()
        delta = round((now - self._lap) * 1000)
        self._lap = now
        return max(delta, 1)


def sse(event_type: str, **fields: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **fields})}\n\n"


_INTERNAL_NAMES: set[str] | None = None


def _tool_kind(name: str) -> str:
    global _INTERNAL_NAMES
    if _INTERNAL_NAMES is None:
        _INTERNAL_NAMES = {t.name for t in internal_tools.definitions}
    return "internal_function" if name in _INTERNAL_NAMES else "mcp_tool"


@app.get("/api/health")
async def health() -> JSONResponse:
    return JSONResponse({
        "ok": True,
        "mcp_enabled": bool(settings.mcp_agent_key),
        "internal_tools": internal_tool_names(),
    })


async def cs_event_stream(request: ChatRequest) -> AsyncIterator[str]:
    timer = Timer()
    yield sse("status", text="Initializing agent…", ts=timer.elapsed_ms())

    agent = await get_agent()

    thread_id = request.thread_id or "default"
    latest_message = request.messages[-1].content if request.messages else ""

    config = {"configurable": {"thread_id": thread_id}}

    tool_start_times: dict[str, float] = {}

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": latest_message}]},
        config=config,
        version="v2",
    ):
        kind = event["event"]

        if kind == "on_tool_start":
            name = event.get("name", "")
            tool_input = event["data"].get("input", {})
            tool_start_times[event["run_id"]] = perf_counter()
            yield sse("tool-call", toolName=name, toolKind=_tool_kind(name),
                       payload=tool_input if isinstance(tool_input, dict) else {"input": tool_input},
                       ts=timer.elapsed_ms())

        elif kind == "on_tool_end":
            name = event.get("name", "")
            raw_output = event["data"].get("output", "")
            try:
                output = json.loads(str(raw_output)) if raw_output else {}
            except (json.JSONDecodeError, TypeError):
                output = {"result": str(raw_output)}
            start = tool_start_times.pop(event["run_id"], perf_counter())
            duration_ms = max(round((perf_counter() - start) * 1000), 1)
            yield sse("tool-result", toolName=name, toolKind=_tool_kind(name),
                       payload=output, durationMs=duration_ms, ts=timer.elapsed_ms())

        elif kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                if not (hasattr(chunk, "tool_calls") and chunk.tool_calls):
                    yield sse("text-delta", delta=chunk.content)

    yield sse("done", totalElapsedMs=timer.elapsed_ms())


async def rag_event_stream(question: str) -> AsyncIterator[str]:
    timer = Timer()
    async for chunk in rag_service.stream_answer(question, timer):
        yield chunk
    yield sse("done", totalElapsedMs=timer.elapsed_ms())


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    question = request.messages[-1].content if request.messages else ""

    if request.mode == "simple_rag":
        return StreamingResponse(rag_event_stream(question), media_type="text/event-stream")

    return StreamingResponse(
        cs_event_stream(request),
        media_type="text/event-stream",
    )