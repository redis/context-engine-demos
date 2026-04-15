from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from backend.app.core.domain_contract import DomainPack
from backend.app.redis_connection import create_async_redis_client, create_redis_client
from backend.app.settings import Settings

DOMAIN_EVENT_STREAM_SUFFIX = "stream:events"


def domain_event_stream_key(domain: DomainPack) -> str:
    return f"{domain.manifest.namespace.redis_prefix}:{DOMAIN_EVENT_STREAM_SUFFIX}"


def _stringify_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def build_domain_event(
    *,
    event_family: str,
    event_type: str,
    headline: str,
    message: str = "",
    source: str = "",
    company_id: str = "",
    ticker: str = "",
    document_id: str = "",
    importance_score: float | int | None = None,
    published_at: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_payload = payload or {}
    published_value = published_at or datetime.now(timezone.utc).isoformat()
    return {
        "event_family": event_family,
        "event_type": event_type,
        "headline": headline,
        "message": message,
        "source": source,
        "company_id": company_id,
        "ticker": ticker,
        "document_id": document_id,
        "importance_score": importance_score,
        "published_at": published_value,
        "payload": event_payload,
    }


def _encode_domain_event(event: dict[str, Any]) -> dict[str, str]:
    encoded = {
        "event_family": _stringify_field(event.get("event_family")),
        "event_type": _stringify_field(event.get("event_type")),
        "headline": _stringify_field(event.get("headline")),
        "message": _stringify_field(event.get("message")),
        "source": _stringify_field(event.get("source")),
        "company_id": _stringify_field(event.get("company_id")),
        "ticker": _stringify_field(event.get("ticker")),
        "document_id": _stringify_field(event.get("document_id")),
        "importance_score": _stringify_field(event.get("importance_score")),
        "published_at": _stringify_field(event.get("published_at")),
        "payload": _stringify_field(event.get("payload", {})),
    }
    return {key: value for key, value in encoded.items() if value != ""}


def publish_domain_event(settings: Settings, domain: DomainPack, event: dict[str, Any]) -> str:
    client = create_redis_client(settings)
    return str(client.xadd(domain_event_stream_key(domain), _encode_domain_event(event)))


def _decode_domain_event(event_id: str, raw_fields: dict[str, Any]) -> dict[str, Any]:
    event = dict(raw_fields)
    payload_raw = event.get("payload")
    if isinstance(payload_raw, str) and payload_raw:
        try:
            event["payload"] = json.loads(payload_raw)
        except json.JSONDecodeError:
            event["payload"] = {"raw": payload_raw}
    elif payload_raw is None:
        event["payload"] = {}
    event["stream_id"] = event_id
    event["importance_score"] = event.get("importance_score")
    return event


def _format_sse(*, event_type: str, event_id: str | None, data: dict[str, Any]) -> str:
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event_type}")
    lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
    return "\n".join(lines) + "\n\n"


def _redis_stream_id_is_older_or_equal(left: str, right: str) -> bool:
    if left == right:
        return True

    try:
        left_ms, left_seq = (int(part) for part in left.split("-", 1))
        right_ms, right_seq = (int(part) for part in right.split("-", 1))
    except ValueError:
        return False

    return (left_ms, left_seq) <= (right_ms, right_seq)


async def stream_domain_events(
    settings: Settings,
    domain: DomainPack,
    *,
    cursor: str = "$",
    history_limit: int = 12,
) -> AsyncIterator[str]:
    client = create_async_redis_client(settings)
    stream_key = domain_event_stream_key(domain)
    last_id = cursor or "$"

    try:
        if history_limit > 0:
            history = await client.xrevrange(stream_key, max="+", min="-", count=history_limit)
            if history:
                for event_id, fields in reversed(history):
                    yield _format_sse(
                        event_type="domain-event",
                        event_id=event_id,
                        data=_decode_domain_event(event_id, fields),
                    )
                newest_history_id = history[0][0]
                if last_id == "$" or _redis_stream_id_is_older_or_equal(last_id, newest_history_id):
                    last_id = newest_history_id

        while True:
            messages = await client.xread({stream_key: last_id}, block=15000, count=50)
            if not messages:
                yield ": keepalive\n\n"
                continue

            for _stream_name, entries in messages:
                for event_id, fields in entries:
                    if event_id == last_id:
                        continue
                    last_id = event_id
                    yield _format_sse(
                        event_type="domain-event",
                        event_id=event_id,
                        data=_decode_domain_event(event_id, fields),
                    )
    finally:
        await client.aclose()
