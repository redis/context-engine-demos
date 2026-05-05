from __future__ import annotations

import base64
import json
from pathlib import Path
from time import perf_counter
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage

from backend.app.domain_events import stream_domain_events
from backend.app.context_surface_service import ContextSurfaceService
from backend.app.core.domain_loader import get_active_domain
from backend.app.contracts import ChatRequest
from backend.app.internal_tools import InternalToolService, domain_runtime_config, internal_tool_names
from backend.app.langgraph_agent import create_agent, create_checkpointer
from backend.app.rag_service import SimpleRAGService
from backend.app.radish_input_router import (
    RadishRouterUnavailableError,
    get_radish_router,
    make_radish_bank_lifespan,
    radish_blocked_sse,
    radish_router_unavailable_sse,
)
from backend.app.sse import format_sse_event
from backend.app.settings import get_settings

settings = get_settings()
domain = get_active_domain(settings)
ROOT_DIR = Path(__file__).resolve().parents[2]

app = FastAPI(
    title=f"{domain.manifest.branding.app_name} Demo",
    lifespan=make_radish_bank_lifespan(settings),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin, "http://localhost:3040", "http://127.0.0.1:3040"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

internal_tools = InternalToolService(settings)
cs_service = ContextSurfaceService(settings)
rag_service = SimpleRAGService(settings, cs_service)
runtime_config = domain_runtime_config(domain, settings)

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


def _logo_src(path: Path) -> str:
    suffix = path.suffix.lower()
    mime_type = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


_INTERNAL_NAMES: set[str] | None = None


def _tool_kind(name: str) -> str:
    global _INTERNAL_NAMES
    if _INTERNAL_NAMES is None:
        _INTERNAL_NAMES = {t.name for t in internal_tools.definitions}
    return "internal_function" if name in _INTERNAL_NAMES else "mcp_tool"


def _short_input(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("query", "text", "product_id", "store_id", "order_id", "shipment_id", "tracking_number", "customer_id"):
            value = payload.get(key)
            if value:
                return str(value)
    if payload is None:
        return ""
    return str(payload)


def _thinking_step_for_tool(name: str, payload: Any) -> str | None:
    if hasattr(domain, "describe_tool_trace_step"):
        custom = domain.describe_tool_trace_step(tool_name=name, payload=payload, runtime_config=runtime_config)
        if custom is not None:
            return custom or None

    detail = _short_input(payload)
    if name == domain.manifest.identity.tool_name:
        return "Identify the signed-in user context before using live account data."
    if name == "get_current_time":
        return "Compare live timestamps against relevant dates and status windows."
    if name.startswith("search_"):
        return f"Search domain data using: {detail or 'the current query'}."
    if name.startswith("filter_"):
        return "Filter live domain records to narrow the relevant results."
    if name.startswith("get_"):
        return "Fetch the exact record needed for the current question."
    return None


def _format_elapsed_ms(duration_ms: int) -> str:
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.1f}s"
    return f"{duration_ms}ms"


def _llm_phase_label(*, llm_call_index: int, tool_calls_seen: int) -> str:
    if llm_call_index == 1 and tool_calls_seen == 0:
        return "Plan the next action and decide whether tools are needed."
    if tool_calls_seen > 0:
        return "Review tool results and decide the next step."
    return "Reason about the request and decide the next step."


@app.get("/api/health")
async def health() -> JSONResponse:
    mcp_tool_names = [tool.get("name", "") for tool in await cs_service.list_tools()]
    return JSONResponse({
        "ok": True,
        "domain": domain.manifest.id,
        "mcp_enabled": bool(settings.mcp_agent_key),
        "internal_tools": internal_tool_names(settings),
        "mcp_tools": [name for name in mcp_tool_names if name],
    })


@app.get("/api/domain-config")
async def domain_config() -> JSONResponse:
    branding = domain.manifest.branding
    return JSONResponse({
        "id": domain.manifest.id,
        "app_name": branding.app_name,
        "subtitle": branding.subtitle,
        "hero_title": branding.hero_title,
        "placeholder_text": branding.placeholder_text,
        "starter_prompts": [card.model_dump() for card in branding.starter_prompts],
        "theme": branding.theme.model_dump(),
        "ui": branding.ui.model_dump(),
        "logo_src": _logo_src(ROOT_DIR / branding.logo_path),
    })


async def cs_event_stream(request: ChatRequest) -> AsyncIterator[str]:
    timer = Timer()
    latest_message = request.messages[-1].content if request.messages else ""
    yield format_sse_event("status", text="Initializing agent…", ts=timer.elapsed_ms())

    agent = await get_agent()
    defer_final_answer = runtime_config.get("enable_post_model_verifier", False)

    thread_id = request.thread_id or "default"

    config = {"configurable": {"thread_id": thread_id}}

    tool_start_times: dict[str, float] = {}
    llm_start_times: dict[str, float] = {}
    llm_step_ids: dict[str, str] = {}
    llm_call_counter = 0
    tool_calls_seen = 0
    last_thinking_step: str | None = None

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
            tool_calls_seen += 1
            thinking_step = _thinking_step_for_tool(name, tool_input)
            if thinking_step and thinking_step != last_thinking_step:
                last_thinking_step = thinking_step
                yield format_sse_event("thinking-step", step=thinking_step, ts=timer.elapsed_ms())
            yield format_sse_event(
                "tool-call",
                toolName=name,
                toolKind=_tool_kind(name),
                runId=event["run_id"],
                payload=tool_input if isinstance(tool_input, dict) else {"input": tool_input},
                ts=timer.elapsed_ms(),
            )

        elif kind == "on_tool_end":
            name = event.get("name", "")
            raw_output = event["data"].get("output", "")
            try:
                output = json.loads(str(raw_output)) if raw_output else {}
            except (json.JSONDecodeError, TypeError):
                output = {"result": str(raw_output)}
            start = tool_start_times.pop(event["run_id"], perf_counter())
            duration_ms = max(round((perf_counter() - start) * 1000), 1)
            yield format_sse_event(
                "tool-result",
                toolName=name,
                toolKind=_tool_kind(name),
                runId=event["run_id"],
                payload=output,
                durationMs=duration_ms,
                ts=timer.elapsed_ms(),
            )

        elif kind == "on_chat_model_start":
            if not settings.show_llm_trace_steps:
                continue
            llm_call_counter += 1
            llm_start_times[event["run_id"]] = perf_counter()
            step_id = f"llm-step-{llm_call_counter}"
            llm_step_ids[event["run_id"]] = step_id
            step = _llm_phase_label(llm_call_index=llm_call_counter, tool_calls_seen=tool_calls_seen)
            last_thinking_step = step
            yield format_sse_event(
                "thinking-step",
                step=step,
                stepId=step_id,
                stepKind="llm",
                ts=timer.elapsed_ms(),
            )

        elif kind == "on_chat_model_end":
            if not settings.show_llm_trace_steps:
                continue
            start = llm_start_times.pop(event["run_id"], perf_counter())
            step_id = llm_step_ids.pop(event["run_id"], "")
            duration_ms = max(round((perf_counter() - start) * 1000), 1)
            if step_id:
                yield format_sse_event(
                    "thinking-step-finish",
                    stepId=step_id,
                    durationMs=duration_ms,
                    durationText=_format_elapsed_ms(duration_ms),
                    ts=timer.elapsed_ms(),
                )
            else:
                yield format_sse_event(
                    "status",
                    text=f"LLM step completed in {_format_elapsed_ms(duration_ms)}",
                    ts=timer.elapsed_ms(),
                )

        elif kind == "on_chat_model_stream":
            if defer_final_answer:
                # Defer rendering assistant text until the graph finishes so the
                # verifier hook can rewrite the final answer if needed.
                continue
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                if not (hasattr(chunk, "tool_calls") and chunk.tool_calls):
                    yield format_sse_event("text-delta", delta=chunk.content)

    if defer_final_answer and settings.show_final_verifier_trace_step:
        yield format_sse_event(
            "thinking-step",
            step="Validate the final answer against recent context and tool results.",
            ts=timer.elapsed_ms(),
        )
        yield format_sse_event("status", text="Verifying final answer…", ts=timer.elapsed_ms())

    if defer_final_answer:
        final_text = ""
        if hasattr(agent, "aget_state"):
            snapshot = await agent.aget_state(config)
            messages = snapshot.values.get("messages", []) if snapshot and snapshot.values else []
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                    final_text = msg.content if isinstance(msg.content, str) else str(msg.content)
                    break
        if final_text:
            yield format_sse_event("text-delta", delta=final_text)
    yield format_sse_event("done", totalElapsedMs=timer.elapsed_ms())


async def rag_event_stream(question: str) -> AsyncIterator[str]:
    timer = Timer()
    async for chunk in rag_service.stream_answer(question, timer):
        yield chunk
    yield format_sse_event("done", totalElapsedMs=timer.elapsed_ms())


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    question = request.messages[-1].content if request.messages else ""

    if settings.demo_domain == "radish-bank":
        try:
            label, _ = get_radish_router(settings).classify(question)
        except RadishRouterUnavailableError:
            return StreamingResponse(
                radish_router_unavailable_sse(),
                media_type="text/event-stream",
                status_code=503,
            )
        if label == "malicious":
            return StreamingResponse(
                radish_blocked_sse(malicious=True),
                media_type="text/event-stream",
            )
        if label == "off_topic":
            return StreamingResponse(
                radish_blocked_sse(malicious=False),
                media_type="text/event-stream",
            )

    if request.mode == "simple_rag":
        return StreamingResponse(rag_event_stream(question), media_type="text/event-stream")

    return StreamingResponse(
        cs_event_stream(request),
        media_type="text/event-stream",
    )


@app.get("/api/domain-events/stream")
async def domain_events_stream(request: Request, cursor: str = "$", history: int = 12) -> StreamingResponse:
    del request
    return StreamingResponse(
        stream_domain_events(settings, domain, cursor=cursor, history_limit=history),
        media_type="text/event-stream",
    )
