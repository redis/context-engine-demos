"""Fetch finance-researcher price history from FMP and cache it as local CSV files."""

from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULE_PATH = Path(__file__).with_name("data_generator.py")
SPEC = importlib.util.spec_from_file_location("finance_researcher_data_generator", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load finance-researcher data generator from {MODULE_PATH}")
DATA_GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DATA_GENERATOR
SPEC.loader.exec_module(DATA_GENERATOR)

WATCHLIST = getattr(DATA_GENERATOR, "WATCHLIST")
PRICE_DIR = Path(__file__).resolve().parent / "data" / "prices"
MANIFEST_PATH = PRICE_DIR / "manifest.json"
FMP_BASE_URL = "https://financialmodelingprep.com/stable/historical-price-eod/full"
CSV_FIELDNAMES = ["trade_date", "open", "high", "low", "close", "adj_close", "volume"]


def _build_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("historical"), list):
        records = payload["historical"]
    elif isinstance(payload, list):
        records = payload
    else:
        raise RuntimeError("Unexpected FMP response shape for historical price data")

    rows: list[dict[str, Any]] = []
    for item in records:
        trade_date = str(item.get("date") or item.get("trade_date") or "").strip()
        close_value = item.get("close")
        if not trade_date or close_value in {None, ""}:
            continue
        rows.append(
            {
                "trade_date": trade_date,
                "open": float(item.get("open") or close_value),
                "high": float(item.get("high") or close_value),
                "low": float(item.get("low") or close_value),
                "close": float(close_value),
                "adj_close": float(item.get("adjClose") or item.get("adj_close") or close_value),
                "volume": int(float(item.get("volume") or 0)),
            }
        )
    rows.sort(key=lambda row: row["trade_date"])
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=5, help="Number of trailing years to fetch into checked-in CSV caches.")
    parser.add_argument("--tickers", nargs="*", default=None, help="Optional ticker subset. Defaults to the full finance watchlist.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing CSV files.")
    args = parser.parse_args()

    api_key = os.getenv("FMP_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("FMP_API_KEY is not set. Add it to your shell or .env before running this fetcher.")

    known = {entry["ticker"].upper(): entry for entry in WATCHLIST}
    tickers = [ticker.upper() for ticker in (args.tickers or sorted(known))]
    invalid = [ticker for ticker in tickers if ticker not in known]
    if invalid:
        raise SystemExit(f"Unknown watchlist tickers: {', '.join(invalid)}")

    today = date.today()
    start = today - timedelta(days=max(args.years, 1) * 366)
    manifest: dict[str, Any] = {
        "source": "Financial Modeling Prep",
        "generated_at": DATA_GENERATOR.ts(DATA_GENERATOR.now_utc()),
        "from": start.isoformat(),
        "to": today.isoformat(),
        "tickers": {},
    }

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        written_count = 0
        for ticker in tickers:
            csv_path = PRICE_DIR / f"{ticker}.csv"
            if csv_path.exists() and not args.overwrite:
                manifest["tickers"][ticker] = {
                    "status": "skipped_existing",
                    "path": str(csv_path.relative_to(Path(__file__).resolve().parent)),
                }
                print(f"{ticker}: skipped existing CSV")
                continue

            try:
                response = client.get(
                    FMP_BASE_URL,
                    params={
                        "symbol": ticker,
                        "from": start.isoformat(),
                        "to": today.isoformat(),
                        "apikey": api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                rows = _build_rows(payload)
                if not rows:
                    raise RuntimeError(f"No price rows returned by FMP for {ticker}")
                _write_csv(csv_path, rows)
                manifest["tickers"][ticker] = {
                    "status": "written",
                    "row_count": len(rows),
                    "path": str(csv_path.relative_to(Path(__file__).resolve().parent)),
                    "first_date": rows[0]["trade_date"],
                    "last_date": rows[-1]["trade_date"],
                    "endpoint": FMP_BASE_URL,
                }
                written_count += 1
                print(f"{ticker}: wrote {len(rows)} rows -> {csv_path}")
            except Exception as exc:
                manifest["tickers"][ticker] = {
                    "status": "error",
                    "error": str(exc),
                    "endpoint": FMP_BASE_URL,
                }
                print(f"{ticker}: error -> {exc}")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written -> {MANIFEST_PATH}")
    if written_count == 0:
        raise SystemExit("No CSV files were written. Check your FMP plan coverage and API key.")


if __name__ == "__main__":
    main()
