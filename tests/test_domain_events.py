import pytest

from backend.app.core.domain_loader import load_domain
from backend.app.domain_events import (
    _decode_domain_event,
    _redis_stream_id_is_older_or_equal,
    build_domain_event,
    domain_event_stream_key,
    publish_domain_event,
    stream_domain_events,
)
from backend.app.settings import Settings


def test_domain_event_stream_key_uses_domain_prefix() -> None:
    domain = load_domain("finance-researcher")
    assert domain_event_stream_key(domain) == "finance-researcher:stream:events"


def test_domain_event_builder_keeps_payload_generic() -> None:
    event = build_domain_event(
        event_family="coverage",
        event_type="new_filing",
        headline="New 10-Q filed for NVDA",
        source="sec",
        ticker="NVDA",
        payload={"document_id": "doc-123", "importance": "high"},
    )

    assert event["event_family"] == "coverage"
    assert event["event_type"] == "new_filing"
    assert event["ticker"] == "NVDA"
    assert event["payload"] == {"document_id": "doc-123", "importance": "high"}


def test_decode_domain_event_restores_numeric_importance_score() -> None:
    decoded = _decode_domain_event(
        "1-0",
        {"headline": "update", "importance_score": "0.75", "payload": "{}"},
    )

    assert decoded["importance_score"] == pytest.approx(0.75)


def test_redis_stream_id_ordering_accepts_incomplete_ids() -> None:
    assert _redis_stream_id_is_older_or_equal("0", "3-0") is True
    assert _redis_stream_id_is_older_or_equal("3", "3-0") is True
    assert _redis_stream_id_is_older_or_equal("4", "3-0") is False


def test_publish_domain_event_closes_sync_redis_client(monkeypatch: pytest.MonkeyPatch) -> None:
    domain = load_domain("finance-researcher")
    captured: dict[str, object] = {}

    class FakeRedisClient:
        def __init__(self) -> None:
            self.closed = False

        def xadd(self, stream_name: str, event: dict[str, str]) -> str:
            captured["stream_name"] = stream_name
            captured["event"] = event
            return "1-0"

        def close(self) -> None:
            self.closed = True

    fake_client = FakeRedisClient()
    monkeypatch.setattr("backend.app.domain_events.create_redis_client", lambda _settings: fake_client)

    event_id = publish_domain_event(
        Settings(),
        domain,
        build_domain_event(
            event_family="coverage",
            event_type="new_filing",
            headline="New filing",
            ticker="NVDA",
            importance_score=0.9,
            payload={"source": "sec"},
        ),
    )

    assert event_id == "1-0"
    assert captured["stream_name"] == "finance-researcher:stream:events"
    event_payload = captured["event"]
    assert isinstance(event_payload, dict)
    assert event_payload["event_family"] == "coverage"
    assert event_payload["event_type"] == "new_filing"
    assert event_payload["headline"] == "New filing"
    assert event_payload["ticker"] == "NVDA"
    assert event_payload["importance_score"] == "0.9"
    assert isinstance(event_payload["published_at"], str)
    assert event_payload["payload"] == '{"source":"sec"}'
    assert fake_client.closed is True


@pytest.mark.asyncio
async def test_stream_domain_events_advances_cursor_past_replayed_history(monkeypatch: pytest.MonkeyPatch) -> None:
    domain = load_domain("finance-researcher")
    stream_key = domain_event_stream_key(domain)

    class FakeAsyncRedisClient:
        def __init__(self) -> None:
            self.xread_calls: list[dict[str, str]] = []

        async def xrevrange(self, stream_name: str, *, max: str, min: str, count: int):
            assert stream_name == stream_key
            assert max == "+"
            assert min == "-"
            assert count == 2
            return [
                ("3-0", {"headline": "history-3", "payload": "{}"}),
                ("2-0", {"headline": "history-2", "payload": "{}"}),
            ]

        async def xread(self, streams: dict[str, str], *, block: int, count: int):
            self.xread_calls.append(streams)
            assert block == 15000
            assert count == 50
            if len(self.xread_calls) == 1:
                return [
                    (
                        stream_key,
                        [
                            ("4-0", {"headline": "live-4", "payload": "{}"}),
                        ],
                    )
                ]
            return []

        async def aclose(self) -> None:
            return None

    fake_client = FakeAsyncRedisClient()
    monkeypatch.setattr("backend.app.domain_events.create_async_redis_client", lambda _settings: fake_client)

    events = stream_domain_events(Settings(), domain, cursor="1-0", history_limit=2)

    first = await anext(events)
    second = await anext(events)
    third = await anext(events)
    await events.aclose()

    assert "id: 2-0" in first
    assert "id: 3-0" in second
    assert '"headline": "live-4"' in third
    assert fake_client.xread_calls == [{stream_key: "3-0"}]
