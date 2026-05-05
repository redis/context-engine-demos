from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Literal

from redisvl.extensions.router.schema import DistanceAggregationMethod, Route, RoutingConfig
from redisvl.extensions.router.semantic import SemanticRouter
from redisvl.utils.vectorize.text.huggingface import HFTextVectorizer

from backend.app.redis_connection import build_redis_url
from backend.app.settings import Settings
from backend.app.sse import format_sse_event

logger = logging.getLogger(__name__)

RouterLabel = Literal["relevant", "off_topic", "malicious"]

ROUTER_INDEX_NAME = "rb_sem_router"

OFF_TOPIC_REPLY = (
    "Invalid input. Radish Bank digital banking can only help with accounts, cards, deposits, "
    "insurance, branches, and related policies. Please ask a banking-related question."
)
MALICIOUS_REPLY = (
    "This session has been ended for security reasons."
)

_MALICIOUS_PATTERNS = re.compile(
    r"(?is)"
    r"\b(ignore|disregard)\b.{0,40}\b(instructions|rules|guidelines|policy|system)\b|"
    r"\b(system|developer)\s*message\b|"
    r"\b(show|reveal|print|leak)\b.{0,20}\b(prompt|system\s*prompt|hidden)\b|"
    r"\bjailbreak\b|"
    r"\bDAN\b|"
    r"<\s*/?\s*system\s*>|"
    r"\boverride\b.{0,20}\b(safety|guardrails)\b"
)

# _OFF_TOPIC_HINTS = re.compile(
#     r"(?is)\b(sky blue|president|recipe|roman empire|capital of mongolia|capital of france|"
#     r"weather tomorrow|tell me a joke|sorting algorithm|python code|who won the super bowl)\b"
# )

# _BANKING_HINTS = re.compile(
#     r"(?is)"
#     r"\b(accounts?|balances?|banking|savings|current|checking|deposit|deposits|"
#     r"fixed\s*deposit|fd\b|FD6|FD12|cards?|cardholder|fee|fees|waiver|waive|"
#     r"branch(es)?|insurance|premiums?|CUST001|jamie|transfer|withdraw|withdrawal|"
#     r"interest|rates?|tampines|bishan|raffles|overdraft|statement|loan|mortgage)\b"
# )

_RELEVANT_REFERENCES = [
    "check my savings balance",
    "fixed deposit rate FD6",
    "waive annual card fee",
    "branch hours Tampines",
    "auto lobby and branch services",
    "accident insurance premium",
    "transfer between my accounts",
    "hello I need help with my account",
    "what accounts do I have",
    "early withdrawal penalty fixed deposit",
    "merv kwok customer profile",
    "fd products available",
    "what is the interest rate",
    "invest in a fixed deposit"
]

_OFF_TOPIC_REFERENCES = [
    "why is the sky blue",
    "who is the current US president",
    "recipe for chocolate cake",
    "capital of Mongolia",
    "write me a python sorting algorithm",
    "what is the weather tomorrow",
    "tell me a joke",
    "history of the roman empire",
    "who is rowan trollope"
]


class RadishRouterUnavailableError(RuntimeError):
    """RedisVL SemanticRouter could not be initialized or could not classify the statement."""


def _default_routes() -> list[Route]:
    rel_th, off_th = 0.85, 0.15
    return [
        Route(
            name="relevant",
            references=list(_RELEVANT_REFERENCES),
            distance_threshold=rel_th,
        ),
        Route(
            name="off_topic",
            references=list(_OFF_TOPIC_REFERENCES),
            distance_threshold=off_th,
        ),
    ]


class RadishInputRouter:
    """Malicious regex gate, then lazy RedisVL SemanticRouter for relevant vs off-topic."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._semantic: SemanticRouter | None = None

    def _ensure_semantic(self) -> SemanticRouter:
        if self._semantic is not None:
            return self._semantic
        try:
            model = self._settings.radish_hf_embedding_model
            token = (self._settings.hf_token or "").strip()
            if token:
                vectorizer = HFTextVectorizer(model=model, token=token)
            else:
                vectorizer = HFTextVectorizer(model=model)
            self._semantic = SemanticRouter(
                name=ROUTER_INDEX_NAME,
                routes=_default_routes(),
                vectorizer=vectorizer,
                routing_config=RoutingConfig(
                    aggregation_method=DistanceAggregationMethod.min,
                ),
                redis_url=build_redis_url(self._settings),
                overwrite=True,
            )
            logger.info("Radish semantic router index ready (%s)", ROUTER_INDEX_NAME)
        except Exception as exc:
            raise RadishRouterUnavailableError(
                "Could not initialize Radish semantic router (Redis or embedding model)."
            ) from exc
        return self._semantic

    def classify(self, text: str) -> tuple[RouterLabel, str | None]:
        """Return (label, debug_distance_or_reason). Raises RadishRouterUnavailableError on router failure."""
        statement = (text or "").strip()
        if not statement:
            return "off_topic", None

        if _MALICIOUS_PATTERNS.search(statement):
            return "malicious", "regex"

        # if _OFF_TOPIC_HINTS.search(statement):
        #     return "off_topic", "keyword"

        # if _BANKING_HINTS.search(statement):
        #     return "relevant", "keyword"

        router = self._ensure_semantic()
        try:
            match = router(statement)
        except Exception as exc:
            raise RadishRouterUnavailableError(
                "Semantic router classification failed; check Redis and index health."
            ) from exc

        if match.name in ("relevant", "off_topic"):
            dist = str(match.distance) if match.distance is not None else None
            return match.name, dist

        # No route within distance threshold — RedisVL returned an empty match.
        return "off_topic", "below_threshold"


_router: RadishInputRouter | None = None


def get_radish_router(settings: Settings) -> RadishInputRouter:
    global _router
    if _router is None:
        _router = RadishInputRouter(settings)
    return _router


def warm_radish_input_router(settings: Settings) -> None:
    """Eagerly load ``HFTextVectorizer`` / SentenceTransformer and ensure the Redis ``SemanticRouter``.

    No-op unless ``demo_domain`` is ``radish-bank``. Raises :class:`RadishRouterUnavailableError`
    on the same failures as lazy init (missing Redis, schema mismatch, etc.).
    """
    if settings.demo_domain != "radish-bank":
        return
    get_radish_router(settings)._ensure_semantic()


ROUTER_UNAVAILABLE_USER_MESSAGE = (
    "Input routing is temporarily unavailable. Check that Redis is reachable and the "
    "semantic router index can be created, then try again."
)


def _sse_elapsed_ms(start: float) -> int:
    return round((perf_counter() - start) * 1000)


async def radish_blocked_sse(*, malicious: bool) -> AsyncIterator[str]:
    """SSE stream for Radish input gate: malicious or off-topic (no full agent run)."""
    t0 = perf_counter()
    if malicious:
        yield format_sse_event(
            "thinking-step",
            step="Input routing: session terminated (security).",
            ts=_sse_elapsed_ms(t0),
        )
        yield format_sse_event("text-delta", delta=MALICIOUS_REPLY, ts=_sse_elapsed_ms(t0))
        yield format_sse_event("session-terminated", reason="malicious_input", ts=_sse_elapsed_ms(t0))
    else:
        yield format_sse_event(
            "thinking-step",
            step="Input routing: off-topic (no LLM).",
            ts=_sse_elapsed_ms(t0),
        )
        yield format_sse_event("text-delta", delta=OFF_TOPIC_REPLY, ts=_sse_elapsed_ms(t0))
    yield format_sse_event("done", totalElapsedMs=_sse_elapsed_ms(t0))


async def radish_router_unavailable_sse() -> AsyncIterator[str]:
    """SSE stream when the semantic router cannot be used (503 body)."""
    t0 = perf_counter()
    yield format_sse_event(
        "thinking-step",
        step="Input routing: semantic router unavailable.",
        ts=_sse_elapsed_ms(t0),
    )
    yield format_sse_event("text-delta", delta=ROUTER_UNAVAILABLE_USER_MESSAGE, ts=_sse_elapsed_ms(t0))
    yield format_sse_event("done", totalElapsedMs=_sse_elapsed_ms(t0))


def make_radish_bank_lifespan(settings: Settings):
    """Build a FastAPI lifespan that warms the HF + Redis semantic router when Radish is active."""

    @asynccontextmanager
    async def lifespan(_app: object):
        if settings.demo_domain == "radish-bank":
            try:
                await asyncio.to_thread(warm_radish_input_router, settings)
                logger.info("Radish input router warmed at startup (HF model + Redis semantic index).")
            except RadishRouterUnavailableError:
                logger.warning(
                    "Radish semantic router warm-up failed; first routed chat may return 503 until "
                    "Redis and the embedding model succeed.",
                    exc_info=True,
                )
        yield

    return lifespan
