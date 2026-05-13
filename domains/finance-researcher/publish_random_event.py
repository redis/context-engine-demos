"""Publish a random finance-researcher domain event and print the raw Redis command."""

from __future__ import annotations

import argparse
import importlib
import json
import random
import shlex
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import load_domain
from backend.app.domain_events import build_domain_event, domain_event_stream_key
from backend.app.settings import get_settings


def _stringify_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _load_watchlist(domain_id: str) -> list[dict[str, Any]]:
    module = importlib.import_module(f"domains.{domain_id}.data_generator")
    watchlist = getattr(module, "WATCHLIST", None)
    if not isinstance(watchlist, list) or not watchlist:
        raise RuntimeError(f"Domain '{domain_id}' does not expose a usable WATCHLIST in data_generator.py")
    return watchlist


def _load_latest_document_ids(domain_id: str) -> dict[str, str]:
    document_path = ROOT / "output" / domain_id / "research_documents.jsonl"
    if not document_path.exists():
        return {}

    latest_by_ticker: dict[str, tuple[str, str]] = {}
    for line in document_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        ticker = str(row.get("ticker", "")).upper()
        document_id = str(row.get("document_id", ""))
        published_at = str(row.get("published_at", ""))
        if not ticker or not document_id:
            continue
        current = latest_by_ticker.get(ticker)
        if current is None or published_at > current[0]:
            latest_by_ticker[ticker] = (published_at, document_id)

    return {ticker: document_id for ticker, (_published_at, document_id) in latest_by_ticker.items()}


def _build_random_event(
    company: dict[str, Any],
    rng: random.Random,
    latest_document_ids: dict[str, str],
) -> dict[str, Any]:
    ticker = company["ticker"]
    company_name = company["company_name"]
    sector = company.get("sector", "Technology")
    benchmark_group = company.get("benchmark_group", "watchlist peers")
    company_id = f"company_{ticker.lower()}"

    event_templates = [
        {
            "event_type": "sec-filing",
            "source": "sec",
            "headline": f"{company_name} posted a fresh filing with updated segment and spending disclosures",
            "message": (
                f"The latest SEC filing adds updated commentary on {sector.lower()} execution, capital allocation, "
                "and near-term operating priorities."
            ),
            "payload": {
                "document_kind": rng.choice(["10-Q", "10-K", "8-K"]),
                "themes": ["segment trends", "capital allocation", "risk factors"],
                "sentiment": rng.choice(["mixed", "constructive"]),
                "analyst_takeaway": f"Review for read-throughs against {benchmark_group}.",
            },
        },
        {
            "event_type": "earnings-call",
            "source": "earnings-call",
            "headline": f"{company_name} management highlighted demand trends and operating discipline on the earnings call",
            "message": (
                "Prepared remarks and Q&A emphasized end-market demand, execution priorities, and how management is "
                "thinking about the next quarter."
            ),
            "payload": {
                "themes": ["demand trends", "margin commentary", "next-quarter setup"],
                "sentiment": rng.choice(["constructive", "cautious"]),
                "analyst_takeaway": f"Cross-check remarks against recent commentary from {benchmark_group}.",
            },
        },
        {
            "event_type": "guidance-update",
            "source": "investor-relations",
            "headline": f"{company_name} updated investor messaging around growth, margin, and spending priorities",
            "message": (
                "Investor materials reframed the near-term outlook with attention on revenue cadence, operating "
                "leverage, and strategic investment pacing."
            ),
            "payload": {
                "themes": ["revenue cadence", "operating leverage", "strategic investment"],
                "sentiment": rng.choice(["constructive", "neutral"]),
                "coverage_action": rng.choice(["reiterate", "monitor", "reassess"]),
                "analyst_takeaway": "Useful input for refreshing assumptions ahead of the next earnings cycle.",
            },
        },
        {
            "event_type": "investor-update",
            "source": "investor-relations",
            "headline": f"{company_name} published an investor update with fresh positioning against key peers",
            "message": (
                f"The update focused on product roadmap, customer demand signals, and differentiation relative to "
                f"{benchmark_group}."
            ),
            "payload": {
                "themes": ["product roadmap", "customer demand", "competitive positioning"],
                "sentiment": rng.choice(["constructive", "mixed"]),
                "analyst_takeaway": "Worth comparing with the latest filing language and current valuation debate.",
            },
        },
    ]

    template = rng.choice(event_templates)
    document_id = latest_document_ids.get(ticker, "") if template["event_type"] == "sec-filing" else ""

    return build_domain_event(
        event_family="coverage",
        event_type=template["event_type"],
        headline=template["headline"],
        message=template["message"],
        source=template["source"],
        company_id=company_id,
        ticker=ticker,
        document_id=document_id,
        importance_score=round(rng.uniform(0.62, 0.96), 2),
        payload={
            "company_name": company_name,
            "sector": sector,
            **template["payload"],
        },
    )


def _redis_cli_command(*, stream_key: str, event: dict[str, Any], redis_ssl: bool) -> str:
    command = [
        'REDISCLI_AUTH="$REDIS_PASSWORD"',
        "redis-cli",
    ]
    if redis_ssl:
        command.append("--tls")
    command.extend(
        [
            '-h "$REDIS_HOST"',
            '-p "$REDIS_PORT"',
            '--user "$REDIS_USERNAME"',
            '-n "$REDIS_DB"',
            "XADD",
            shlex.quote(stream_key),
            "'*'",
        ]
    )
    for field_name, value in event.items():
        rendered = _stringify_field(value)
        if rendered == "":
            continue
        command.append(shlex.quote(field_name))
        command.append(shlex.quote(rendered))
    return " ".join(command)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="finance-researcher")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain)
    watchlist = _load_watchlist(args.domain)
    latest_document_ids = _load_latest_document_ids(args.domain)
    rng = random.Random(args.seed)

    company = rng.choice(watchlist)
    event = _build_random_event(company, rng, latest_document_ids)
    stream_id = domain.publish_coverage_event(
        settings=settings,
        company_id=event["company_id"],
        ticker=event["ticker"],
        headline=event["headline"],
        event_type=event["event_type"],
        message=event["message"],
        source=event["source"],
        document_id=event["document_id"],
        importance_score=event["importance_score"],
        payload=event["payload"],
    )

    stream_key = domain_event_stream_key(domain)
    print(f"Published {args.domain} event")
    print(f"  stream_id: {stream_id}")
    print(f"  stream_key: {stream_key}")
    print(f"  ticker: {event['ticker']}")
    print(f"  event_type: {event['event_type']}")
    print(f"  headline: {event['headline']}")
    print("  payload:", json.dumps(event["payload"], ensure_ascii=False, sort_keys=True))
    print("")
    print("Equivalent redis-cli command:")
    print(_redis_cli_command(stream_key=stream_key, event=event, redis_ssl=settings.redis_ssl))


if __name__ == "__main__":
    main()
