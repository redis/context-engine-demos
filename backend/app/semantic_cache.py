from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage
from redisvl.extensions.cache.llm import SemanticCache
from redisvl.query.filter import Tag
from redisvl.utils.vectorize import OpenAITextVectorizer

from backend.app.redis_connection import build_redis_url
from backend.app.settings import Settings

log = logging.getLogger(__name__)

LookupClass = Literal["public", "group", "skip"]
StoreClass = Literal["public", "group", "non-cacheable", "ignored"]


@dataclass(frozen=True)
class SemanticCacheHit:
    response: str
    metadata: dict[str, Any]
    filters: dict[str, Any]


class SemanticCacheService:
    def __init__(self, settings: Settings, domain: Any):
        self.settings = settings
        self.domain = domain
        self.config = getattr(domain.manifest, "semantic_cache", None)
        self._cache: SemanticCache | None = None

    @property
    def enabled(self) -> bool:
        return bool(
            self.config
            and getattr(self.config, "enabled", False)
            and self.settings.openai_api_key
        )

    def classify_lookup(self, question: str, user_profile: dict[str, Any] | None) -> LookupClass:
        if not self.enabled:
            return "skip"
        classifier = getattr(self.domain, "classify_semantic_cache_lookup", None)
        if not callable(classifier):
            return "skip"
        result = classifier(question=question, user_profile=user_profile)
        return result if result in {"public", "group"} else "skip"

    def classify_mcp_tool(self, tool_name: str) -> StoreClass:
        classifier = getattr(self.domain, "classify_mcp_semantic_cache_access", None)
        if not callable(classifier):
            return "ignored"
        result = classifier(tool_name=tool_name)
        return result if result in {"public", "group", "non-cacheable"} else "ignored"

    def build_filter_expression(self, *, lookup_class: LookupClass, group_id: str | None) -> Any | None:
        domain_expr = (Tag("domain_id") == self.domain.manifest.id) & (Tag("mode") == "context_surfaces") & (
            Tag("model_name") == self.settings.openai_chat_model
        )
        if lookup_class == "public":
            return domain_expr & (Tag("access_class") == "public")
        if lookup_class == "group" and group_id:
            return domain_expr & (
                ((Tag("access_class") == "public") | ((Tag("access_class") == "group") & (Tag("group_id") == group_id)))
            )
        return None

    async def check(
        self,
        *,
        prompt: str,
        lookup_class: LookupClass,
        group_id: str | None,
    ) -> SemanticCacheHit | None:
        if not self.enabled or lookup_class == "skip":
            return None
        filter_expression = self.build_filter_expression(lookup_class=lookup_class, group_id=group_id)
        if filter_expression is None:
            return None
        hits = await self._get_cache().acheck(
            prompt=prompt,
            num_results=1,
            return_fields=["response", "metadata", "access_class", "group_id", "domain_id", "mode", "model_name"],
            filter_expression=filter_expression,
        )
        if not hits:
            return None
        hit = hits[0]
        response = str(hit.get("response") or "").strip()
        if not response:
            return None
        metadata = hit.get("metadata")
        return SemanticCacheHit(
            response=response,
            metadata=metadata if isinstance(metadata, dict) else {},
            filters={
                "access_class": str(hit.get("access_class") or ""),
                "group_id": str(hit.get("group_id") or ""),
                "domain_id": str(hit.get("domain_id") or ""),
                "mode": str(hit.get("mode") or ""),
                "model_name": str(hit.get("model_name") or ""),
            },
        )

    async def store(
        self,
        *,
        prompt: str,
        response: str,
        access_class: Literal["public", "group"],
        group_id: str | None,
        metadata: dict[str, Any],
    ) -> str | None:
        if not self.enabled:
            return None
        filters = {
            "domain_id": self.domain.manifest.id,
            "mode": "context_surfaces",
            "model_name": self.settings.openai_chat_model,
            "access_class": access_class,
            "group_id": group_id or "__none__",
        }
        return await self._get_cache().astore(
            prompt=prompt,
            response=response,
            metadata=metadata,
            filters=filters,
            ttl=getattr(self.config, "ttl_seconds", None),
        )

    async def thread_is_fresh(self, agent: Any, config: dict[str, Any]) -> bool:
        if not hasattr(agent, "aget_state"):
            return False
        try:
            snapshot = await agent.aget_state(config)
        except Exception:
            log.exception("Unable to read agent state for semantic-cache freshness check")
            return False
        values = snapshot.values if snapshot and snapshot.values else {}
        messages = values.get("messages", [])
        return not messages

    async def persist_cached_turn(
        self,
        *,
        agent: Any,
        config: dict[str, Any],
        question: str,
        answer: str,
    ) -> bool:
        if not hasattr(agent, "aupdate_state"):
            return False
        try:
            await agent.aupdate_state(
                config,
                {"messages": [HumanMessage(content=question), AIMessage(content=answer)]},
            )
        except Exception:
            log.exception("Unable to persist cached turn into LangGraph state")
            return False
        return True

    def _get_cache(self) -> SemanticCache:
        if self._cache is not None:
            return self._cache
        self._cache = SemanticCache(
            name=self.config.cache_name,
            distance_threshold=self.config.distance_threshold,
            ttl=self.config.ttl_seconds,
            vectorizer=OpenAITextVectorizer(
                model=self.settings.openai_embedding_model,
                api_config={"api_key": self.settings.openai_api_key},
            ),
            filterable_fields=[
                {"name": "domain_id", "type": "tag"},
                {"name": "mode", "type": "tag"},
                {"name": "model_name", "type": "tag"},
                {"name": "access_class", "type": "tag"},
                {"name": "group_id", "type": "tag"},
            ],
            redis_url=build_redis_url(self.settings),
        )
        return self._cache
