"""Simple RAG service: embed query → vector search policies → one-shot LLM answer."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

from backend.app.redis_connection import build_redis_url, create_redis_client
from backend.app.settings import Settings

VECTOR_FIELD = "content_embedding"
RETURN_FIELDS = ["title", "category", "content", "policy_id"]
NUM_RESULTS = 3


def _discover_policy_index(settings: Settings) -> str:
    """Find the policy index name dynamically via FT._LIST."""
    client = create_redis_client(settings)
    indexes = client.execute_command("FT._LIST")
    for idx in indexes:
        name = idx if isinstance(idx, str) else idx.decode()
        if "policy" in name.lower():
            return name
    raise RuntimeError(
        "No policy index found. Run 'make setup-surface' and 'make load-data' first."
    )


class SimpleRAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._index: SearchIndex | None = None
        self._index_name: str | None = None

    def _get_index(self) -> SearchIndex:
        if self._index is None:
            self._index_name = _discover_policy_index(self.settings)
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
        query = VectorQuery(
            vector=embedding,
            vector_field_name=VECTOR_FIELD,
            return_fields=RETURN_FIELDS,
            num_results=NUM_RESULTS,
        )
        return index.query(query)

    async def stream_answer(self, question: str, timer: Any) -> AsyncIterator[str]:
        """Embed the question, search policies, stream a one-shot LLM answer."""
        yield _sse("status", text="Embedding query…", ts=timer.elapsed_ms())
        embedding = await self._embed(question)

        yield _sse("status", text="Searching policies via vector similarity…", ts=timer.elapsed_ms())
        yield _sse("tool-call", toolName="vector_search_policies", toolKind="internal_function",
                    payload={"query": question, "num_results": NUM_RESULTS}, ts=timer.elapsed_ms())

        timer.lap_ms()
        results = self._search_policies(embedding)
        search_duration = timer.lap_ms()

        search_payload = [
            {k: v for k, v in r.items() if k != VECTOR_FIELD} for r in results
        ]
        yield _sse("tool-result", toolName="vector_search_policies", toolKind="internal_function",
                    payload={"results": search_payload}, durationMs=search_duration, ts=timer.elapsed_ms())

        yield _sse("status", text=f"Found {len(results)} matching policies. Generating answer…", ts=timer.elapsed_ms())

        context_text = "\n\n".join(
            f"**{r.get('title', 'Policy')}** ({r.get('category', '')}):\n{r.get('content', '')}"
            for r in results
        )
        system_prompt = (
            "You are the Reddish food-delivery support assistant. "
            "Answer the customer's question using ONLY the policy documents provided below. "
            "If the policies don't cover the question, say so. Be concise and helpful.\n\n"
            f"--- POLICY DOCUMENTS ---\n{context_text}\n--- END ---"
        )
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

