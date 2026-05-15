"""RAG SSE stream contract (terminal ``done`` after success or error)."""

from __future__ import annotations

import asyncio
import json

from backend.app.contracts import ChatRequest


def test_rag_event_stream_emits_done_after_stream_answer_raises(monkeypatch):
    """Unhandled exceptions during ``stream_answer`` must still emit ``done`` (matches chat stream)."""

    async def failing_stream(question, timer):
        del question, timer
        yield 'data: {"type":"status","text":"starting","ts":0}\n\n'
        raise RuntimeError("simulated failure between embedding and LLM")

    import backend.app.main as main_mod

    monkeypatch.setattr(main_mod.rag_service, "stream_answer", failing_stream)

    async def collect():
        out = []
        async for chunk in main_mod.rag_event_stream("hello"):
            payload = chunk.removeprefix("data: ").split("\n\n", 1)[0].strip()
            out.append(json.loads(payload))
        return out

    events = asyncio.run(collect())

    assert events[-2]["type"] == "error"
    assert events[-2]["errorCode"] == "openai_error"
    assert events[-1]["type"] == "done"
    assert "totalElapsedMs" in events[-1]


def _decode_sse_payload(chunk: str) -> dict:
    payload = chunk.removeprefix("data: ").split("\n\n", 1)[0].strip()
    return json.loads(payload)


async def _collect_chat_events(request: ChatRequest) -> list[dict]:
    import backend.app.main as main_mod

    out = []
    async for chunk in main_mod.cs_event_stream(request):
        out.append(_decode_sse_payload(chunk))
    return out


def _chat_request() -> ChatRequest:
    return ChatRequest(messages=[{"role": "user", "content": "hello"}], thread_id="test-thread")


def test_cs_event_stream_emits_terminal_tool_result_on_tool_error(monkeypatch):
    import backend.app.main as main_mod

    class FakeAgent:
        async def astream_events(self, *_args, **_kwargs):
            yield {
                "event": "on_tool_start",
                "name": "filter_order_by_customer_id",
                "run_id": "tool-1",
                "data": {"input": {"customer_id": "CUST_DEMO_001"}},
            }
            yield {
                "event": "on_tool_error",
                "name": "filter_order_by_customer_id",
                "run_id": "tool-1",
                "data": {"error": ValueError("missing required field: value")},
            }

    async def fake_get_agent():
        return FakeAgent()

    monkeypatch.setattr(main_mod, "get_agent", fake_get_agent)
    monkeypatch.setitem(main_mod.runtime_config, "enable_post_model_verifier", False)

    events = asyncio.run(_collect_chat_events(_chat_request()))
    tool_results = [event for event in events if event["type"] == "tool-result"]

    assert len(tool_results) == 1
    assert tool_results[0]["runId"] == "tool-1"
    assert tool_results[0]["payload"]["error"] == "missing required field: value"
    assert tool_results[0]["durationMs"] >= 1
    assert events[-1]["type"] == "done"


def test_cs_event_stream_flushes_pending_tool_result_before_stream_error(monkeypatch):
    import backend.app.main as main_mod

    class FakeAgent:
        async def astream_events(self, *_args, **_kwargs):
            yield {
                "event": "on_tool_start",
                "name": "filter_order_by_customer_id",
                "run_id": "tool-1",
                "data": {"input": {"value": "CUST_DEMO_001"}},
            }
            raise RuntimeError("stream failed after tool call")

    async def fake_get_agent():
        return FakeAgent()

    monkeypatch.setattr(main_mod, "get_agent", fake_get_agent)
    monkeypatch.setitem(main_mod.runtime_config, "enable_post_model_verifier", False)

    events = asyncio.run(_collect_chat_events(_chat_request()))
    event_types = [event["type"] for event in events]
    tool_result_index = event_types.index("tool-result")
    error_index = event_types.index("error")

    assert tool_result_index < error_index
    assert events[tool_result_index]["runId"] == "tool-1"
    assert events[tool_result_index]["payload"]["error"] == "stream failed after tool call"
    assert events[error_index]["errorCode"] == "openai_error"
    assert events[-1]["type"] == "done"
