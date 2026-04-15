"""Simple RAG service for the active domain."""

from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator
from uuid import uuid4

from openai import AsyncOpenAI

from backend.app.context_surface_service import ContextSurfaceService
from backend.app.core.domain_loader import get_active_domain
from backend.app.settings import Settings


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _first_present_field(result: dict[str, Any], fields: list[str]) -> str | None:
    for field in fields:
        value = result.get(field)
        if value:
            return str(value)
    return None


def _result_title(result: dict[str, Any], fields: list[str]) -> str:
    title = _first_present_field(result, fields)
    if title:
        return title
    return "Document"


def _result_label(result: dict[str, Any], fields: list[str]) -> str:
    labels: list[str] = []
    for field in fields:
        value = result.get(field)
        if value:
            labels.append(str(value))
    return ", ".join(labels)


def _result_body(result: dict[str, Any], fields: list[str]) -> str:
    body = _first_present_field(result, fields)
    if body:
        return body
    return json.dumps(result, ensure_ascii=False)


class SimpleRAGService:
    def __init__(self, settings: Settings, cs_service: ContextSurfaceService):
        self.settings = settings
        self.cs_service = cs_service
        self.domain = get_active_domain(settings)
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._vector_tool_name: str | None = None
        self._text_tool_name: str | None = None

    async def _get_search_tool_name(self, *, kind: str) -> str:
        cache_name = "_vector_tool_name" if kind == "vector" else "_text_tool_name"
        cached = getattr(self, cache_name)
        if cached is not None:
            return cached

        rag = self.domain.manifest.rag
        tools = await self.cs_service.list_tools()
        if kind == "vector":
            candidates = [
                tool.get("name", "")
                for tool in tools
                if "content_embedding_similarity" in tool.get("name", "")
            ]
        else:
            candidates = [
                tool.get("name", "")
                for tool in tools
                if tool.get("name", "").startswith("search_") and tool.get("name", "").endswith("_by_text")
            ]
        if not candidates:
            raise RuntimeError(f"No {kind} search tool is available on the active Context Surface.")

        target = _normalize_name(rag.index_name_contains)
        for tool_name in candidates:
            if target and target in _normalize_name(tool_name):
                setattr(self, cache_name, tool_name)
                return tool_name

        if len(candidates) == 1:
            setattr(self, cache_name, candidates[0])
            return candidates[0]

        raise RuntimeError(
            f"No matching {kind} search tool found for '{rag.index_name_contains}'. "
            f"Available tools: {', '.join(candidates)}"
        )

    async def _get_vector_tool_name(self) -> str:
        return await self._get_search_tool_name(kind="vector")

    async def _get_text_tool_name(self) -> str:
        return await self._get_search_tool_name(kind="text")

    async def _search_documents(self, question: str, embedding: list[float]) -> list[dict[str, Any]]:
        rag = self.domain.manifest.rag
        vector_tool_name = await self._get_vector_tool_name()
        payload = await self.cs_service.call_tool(
            vector_tool_name,
            {"vector": embedding, "k": rag.num_results},
        )
        vector_error = str(payload.get("error") or payload.get("raw_text") or "").lower()
        results = payload.get("results", [])
        if isinstance(results, list) and results and "unsupported query type" not in vector_error:
            return results

        text_tool_name = await self._get_text_tool_name()
        payload = await self.cs_service.call_tool(
            text_tool_name,
            {"query": question, "limit": rag.num_results},
        )
        results = payload.get("results", [])
        return results if isinstance(results, list) else []

    async def _embed(self, text: str) -> list[float]:
        resp = await self.openai.embeddings.create(
            input=[text],
            model=self.settings.openai_embedding_model,
        )
        return resp.data[0].embedding

    async def stream_answer(self, question: str, timer: Any) -> AsyncIterator[str]:
        """Embed the question, search domain documents, stream a one-shot LLM answer."""
        rag = self.domain.manifest.rag
        tool_run_id = str(uuid4())
        yield _sse("status", text="Embedding query…", ts=timer.elapsed_ms())
        embedding = await self._embed(question)

        yield _sse("status", text=rag.status_text, ts=timer.elapsed_ms())
        yield _sse(
            "tool-call",
            runId=tool_run_id,
            toolName=rag.tool_name,
            toolKind="internal_function",
            payload={"query": question, "num_results": rag.num_results},
            ts=timer.elapsed_ms(),
        )

        timer.lap_ms()
        try:
            results = await self._search_documents(question, embedding)
            search_duration = timer.lap_ms()
        except Exception as exc:
            search_duration = timer.lap_ms()
            yield _sse(
                "tool-result",
                runId=tool_run_id,
                toolName=rag.tool_name,
                toolKind="internal_function",
                payload={"error": str(exc), "results": []},
                durationMs=search_duration,
                ts=timer.elapsed_ms(),
            )
            yield _sse(
                "text-delta",
                delta="Simple RAG is not available for this domain right now because the vector search index is not ready.",
            )
            return

        yield _sse(
            "tool-result",
            runId=tool_run_id,
            toolName=rag.tool_name,
            toolKind="internal_function",
            payload={"results": results},
            durationMs=search_duration,
            ts=timer.elapsed_ms(),
        )

        yield _sse("status", text=f"Found {len(results)} matching documents. {rag.generating_text}", ts=timer.elapsed_ms())

        context_text = "\n\n".join(
            (
                f"**{_result_title(result, rag.title_fields)}**"
                + (f" ({_result_label(result, rag.label_fields)})" if _result_label(result, rag.label_fields) else "")
                + f":\n{_result_body(result, rag.body_fields)}"
            )
            for result in results
        )
        system_prompt = f"{rag.answer_system_prompt}\n\n--- DOMAIN DOCUMENTS ---\n{context_text}\n--- END ---"
        try:
            stream = await self.openai.chat.completions.create(
                model=self.settings.openai_chat_model,
                temperature=0.2,
                stream=True,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield _sse("text-delta", delta=delta)
        except Exception:
            yield _sse("text-delta", delta="Sorry, I wasn't able to generate a response. Please try again.")


def _sse(event_type: str, **fields: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **fields})}\n\n"
