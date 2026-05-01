"""Tests for OpenAI / LiteLLM error classification."""

from __future__ import annotations

import httpx
from openai import BadRequestError

from backend.app.openai_errors import classify_openai_exception


def _bad_request(*, body: object) -> BadRequestError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(400, request=req)
    return BadRequestError("Bad Request", response=resp, body=body)


def test_budget_from_bad_request_body_dict() -> None:
    exc = _bad_request(body={"error": {"type": "budget_exceeded", "message": "limit"}})
    code, msg = classify_openai_exception(exc)
    assert code == "budget_exceeded"
    assert "budget is exhausted" in msg.lower()
    assert "facilitator" in msg.lower()


def test_budget_from_bad_request_body_json_string() -> None:
    exc = _bad_request(body='{"error": {"type": "budget_exceeded"}}')
    code, msg = classify_openai_exception(exc)
    assert code == "budget_exceeded"
    assert "budget is exhausted" in msg.lower()


def test_budget_fallback_substring() -> None:
    code, msg = classify_openai_exception(RuntimeError('{"type": "budget_exceeded"}'))
    assert code == "budget_exceeded"

    code2, _msg2 = classify_openai_exception(RuntimeError("Budget has been exceeded for this key"))
    assert code2 == "budget_exceeded"


def test_non_budget_bad_request() -> None:
    exc = _bad_request(body={"error": {"type": "invalid_request_error", "message": "nope"}})
    code, msg = classify_openai_exception(exc)
    assert code == "openai_error"
    assert msg


def test_generic_exception() -> None:
    code, msg = classify_openai_exception(RuntimeError("Something else broke"))
    assert code == "openai_error"
    assert "Something else broke" in msg
