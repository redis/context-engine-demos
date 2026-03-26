"""Simple RAG service for the active domain."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

from backend.app.core.domain_loader import get_active_domain
from backend.app.redis_connection import build_redis_url, create_redis_client
from backend.app.settings import Settings


def _discover_index(settings: Settings, *, name_contains: str) -> str:
    """Find the domain-configured vector index name dynamically via FT._LIST."""
    client = create_redis_client(settings)
    indexes = client.execute_command("FT._LIST")
    for idx in indexes:
        name = idx if isinstance(idx, str) else idx.decode()
        if name_contains.lower() in name.lower():
            return name
    raise RuntimeError(
        f"No matching search index found for '{name_contains}'. Run setup/load first."
    )


class SimpleRAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.domain = get_active_domain(settings)
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._index: SearchIndex | None = None
        self._index_name: str | None = None

    def _get_index(self) -> SearchIndex:
        if self._index is None:
            rag = self.domain.manifest.rag
            self._index_name = _discover_index(self.settings, name_contains=rag.index_name_contains)
            self._index = SearchIndex.from_existing(
                self._index_name,
                redis_url=build_redis_url(self.settings),
            )
        return self._index

    async def _embed(self, text: str) -> list[float]:
        resp = await self.openai.embeddings.create(
            input=[text],
            model=self.settings.openai_embedding_model,
        )
        return resp.data[0].embedding

    def _search_policies(self, embedding: list[float]) -> list[dict[str, Any]]:
        index = self._get_index()
        rag = self.domain.manifest.rag
        query = VectorQuery(
            vector=embedding,
            vector_field_name=rag.vector_field,
            return_fields=rag.return_fields,
            num_results=rag.num_results,
        )
        return index.query(query)

    async def stream_answer(self, question: str, timer: Any) -> AsyncIterator[str]:
        """Embed the question, search policies, stream a one-shot LLM answer."""
        rag = self.domain.manifest.rag
        yield _sse("status", text="Embedding query…", ts=timer.elapsed_ms())
        embedding = await self._embed(question)

        yield _sse("status", text=rag.status_text, ts=timer.elapsed_ms())
        yield _sse("tool-call", toolName=rag.tool_name, toolKind="internal_function",
                    payload={"query": question, "num_results": rag.num_results}, ts=timer.elapsed_ms())

        timer.lap_ms()
        results = self._search_policies(embedding)
        search_duration = timer.lap_ms()

        search_payload = [
            {k: v for k, v in r.items() if k != rag.vector_field} for r in results
        ]
        yield _sse("tool-result", toolName=rag.tool_name, toolKind="internal_function",
                    payload={"results": search_payload}, durationMs=search_duration, ts=timer.elapsed_ms())

        yield _sse("status", text=f"Found {len(results)} matching documents. {rag.generating_text}", ts=timer.elapsed_ms())

        context_text = "\n\n".join(
            f"**{r.get('title', 'Document')}** ({r.get('category', '')}):\n{r.get('content', '')}"
            for r in results
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
