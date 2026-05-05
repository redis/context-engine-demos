"""Classify OpenAI / LiteLLM errors for user-facing SSE messages."""

from __future__ import annotations

import json
from typing import Any

_BUDGET_MESSAGE = (
    "Session LLM budget is exhausted. Ask your facilitator to regenerate the LiteLLM key or raise the budget."
)


def _truncate_detail(text: str, *, max_len: int = 280) -> str:
    normalized = text.strip()
    if len(normalized) <= max_len:
        return normalized or "An OpenAI request failed."
    return normalized[: max_len - 1] + "…"


def _coerce_body(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _error_type_from_body(body: dict[str, Any]) -> str | None:
    err = body.get("error")
    if isinstance(err, dict):
        t = err.get("type")
        if isinstance(t, str):
            return t
    return None


def classify_openai_exception(exc: BaseException) -> tuple[str | None, str]:
    """Return ``(error_code, user_message)`` for SSE ``error`` events.

    Prefer parsing ``openai.BadRequestError.body`` (dict or JSON string):
    ``body["error"]["type"] == "budget_exceeded"``.

    Fallback: substring ``budget_exceeded`` or ``Budget has been exceeded`` on
    ``str(exc)``.

    Returns ``(\"budget_exceeded\", ...)`` or ``(\"openai_error\", ...)``. The
    first element is never ``None`` for OpenAI-shaped failures; callers may
    treat a hypothetical ``None`` as ``openai_error``.
    """
    try:
        from openai import BadRequestError
    except ImportError:
        BadRequestError = None  # type: ignore[misc, assignment]

    if BadRequestError is not None and isinstance(exc, BadRequestError):
        body = _coerce_body(getattr(exc, "body", None))
        if _error_type_from_body(body) == "budget_exceeded":
            return ("budget_exceeded", _BUDGET_MESSAGE)

    text = str(exc)
    lower = text.lower()
    if "budget_exceeded" in lower or "budget has been exceeded" in lower:
        return ("budget_exceeded", _BUDGET_MESSAGE)

    return ("openai_error", _truncate_detail(text))
