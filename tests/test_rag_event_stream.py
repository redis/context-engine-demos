"""RAG SSE stream contract (terminal ``done`` after success or error)."""

from __future__ import annotations

import asyncio
import json


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
