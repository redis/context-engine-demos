from __future__ import annotations

import csv
import json
import os
import re
import time
import zipfile
import zlib
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import openai

from backend.app.core.domain_contract import GeneratedDataset


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output" / "finance-researcher"
LOCAL_PRICE_DATA_DIR = Path(__file__).resolve().parent / "data" / "prices"
EMBED_DIMENSION = 1536
LIVE_SOURCES_ENV_VAR = "FINANCE_RESEARCHER_USE_LIVE_SOURCES"

SEC_HEADERS = {
    "User-Agent": os.getenv(
        "SEC_USER_AGENT",
        "Context Engine Demos finance-researcher demo (contact: demo@example.com)",
    ),
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com/",
}

WATCHLIST = [
    {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "sector": "Semiconductors",
        "subsector": "AI accelerators and GPUs",
        "benchmark_group": "semiconductor peers",
    },
    {
        "ticker": "AMD",
        "company_name": "Advanced Micro Devices, Inc.",
        "sector": "Semiconductors",
        "subsector": "CPUs and GPUs",
        "benchmark_group": "semiconductor peers",
    },
    {
        "ticker": "AVGO",
        "company_name": "Broadcom Inc.",
        "sector": "Semiconductors",
        "subsector": "Networking and infrastructure silicon",
        "benchmark_group": "semiconductor peers",
    },
    {
        "ticker": "MU",
        "company_name": "Micron Technology, Inc.",
        "sector": "Semiconductors",
        "subsector": "Memory and storage",
        "benchmark_group": "semiconductor peers",
    },
    {
        "ticker": "INTC",
        "company_name": "Intel Corporation",
        "sector": "Semiconductors",
        "subsector": "x86 CPUs and foundry",
        "benchmark_group": "semiconductor peers",
    },
    {
        "ticker": "QCOM",
        "company_name": "QUALCOMM Incorporated",
        "sector": "Semiconductors",
        "subsector": "Wireless and mobile chips",
        "benchmark_group": "semiconductor peers",
    },
    {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Consumer Technology",
        "subsector": "Devices and services",
        "benchmark_group": "mega-cap technology",
    },
    {
        "ticker": "AMZN",
        "company_name": "Amazon.com, Inc.",
        "sector": "Internet and cloud",
        "subsector": "E-commerce and cloud infrastructure",
        "benchmark_group": "internet platform peers",
    },
    {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Enterprise software and cloud",
        "subsector": "Cloud platform and productivity software",
        "benchmark_group": "mega-cap technology",
    },
    {
        "ticker": "GOOGL",
        "company_name": "Alphabet Inc.",
        "sector": "Internet and cloud",
        "subsector": "Search, ads, and cloud",
        "benchmark_group": "internet platform peers",
    },
    {
        "ticker": "META",
        "company_name": "Meta Platforms, Inc.",
        "sector": "Internet and cloud",
        "subsector": "Social platforms and ads",
        "benchmark_group": "internet platform peers",
    },
    {
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "sector": "Automotive and energy",
        "subsector": "EVs and energy storage",
        "benchmark_group": "ev peers",
    },
    {
        "ticker": "ORCL",
        "company_name": "Oracle Corporation",
        "sector": "Enterprise software and cloud",
        "subsector": "Database and infrastructure software",
        "benchmark_group": "enterprise software peers",
    },
    {
        "ticker": "MDB",
        "company_name": "MongoDB, Inc.",
        "sector": "Enterprise software and cloud",
        "subsector": "Database platform software",
        "benchmark_group": "enterprise software peers",
    },
]

WATCHLIST_RANKS = {entry["ticker"]: index + 1 for index, entry in enumerate(WATCHLIST)}

EXCHANGE_BY_TICKER = {
    "NVDA": "NASDAQ",
    "AMD": "NASDAQ",
    "AVGO": "NASDAQ",
    "MU": "NASDAQ",
    "INTC": "NASDAQ",
    "QCOM": "NASDAQ",
    "AAPL": "NASDAQ",
    "AMZN": "NASDAQ",
    "MSFT": "NASDAQ",
    "GOOGL": "NASDAQ",
    "META": "NASDAQ",
    "TSLA": "NASDAQ",
    "ORCL": "NYSE",
    "MDB": "NASDAQ",
}

HEADQUARTERS_BY_TICKER = {
    "NVDA": ("Santa Clara", "CA"),
    "AMD": ("Santa Clara", "CA"),
    "AVGO": ("Palo Alto", "CA"),
    "MU": ("Boise", "ID"),
    "INTC": ("Santa Clara", "CA"),
    "QCOM": ("San Diego", "CA"),
    "AAPL": ("Cupertino", "CA"),
    "AMZN": ("Seattle", "WA"),
    "MSFT": ("Redmond", "WA"),
    "GOOGL": ("Mountain View", "CA"),
    "META": ("Menlo Park", "CA"),
    "TSLA": ("Austin", "TX"),
    "ORCL": ("Austin", "TX"),
    "MDB": ("New York", "NY"),
}

WEBSITE_BY_TICKER = {
    "NVDA": "https://investor.nvidia.com/",
    "AMD": "https://ir.amd.com/",
    "AVGO": "https://investors.broadcom.com/",
    "MU": "https://investors.micron.com/",
    "INTC": "https://www.intc.com/",
    "QCOM": "https://investor.qualcomm.com/",
    "AAPL": "https://investor.apple.com/",
    "AMZN": "https://ir.aboutamazon.com/",
    "MSFT": "https://www.microsoft.com/en-us/Investor",
    "GOOGL": "https://abc.xyz/investor/",
    "META": "https://investor.atmeta.com/",
    "TSLA": "https://ir.tesla.com/",
    "ORCL": "https://investor.oracle.com/",
    "MDB": "https://investors.mongodb.com/",
}

FALLBACK_CIKS = {
    "NVDA": "0001045810",
    "AMD": "0000002488",
    "AVGO": "0001730168",
    "MU": "0000723125",
    "INTC": "0000050863",
    "QCOM": "0000804328",
    "AAPL": "0000320193",
    "AMZN": "0001018724",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "META": "0001326801",
    "TSLA": "0001318605",
    "ORCL": "0001341439",
    "MDB": "0001441816",
}

METRIC_CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "diluted_eps": ["EarningsPerShareDiluted"],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CapitalExpenditures",
    ],
}

METRIC_UNITS = {
    "revenue": "USD",
    "gross_profit": "USD",
    "operating_income": "USD",
    "net_income": "USD",
    "diluted_eps": "USD/shares",
    "operating_cash_flow": "USD",
    "capex": "USD",
    "free_cash_flow": "USD",
}

DOC_FAMILY_PRIORITY = {
    "earnings_release": 95,
    "presentation": 85,
    "transcript": 80,
    "sec_filing": 70,
    "exhibit": 60,
}


def ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return cleaned.strip("._") or "file"


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def write_jsonl(output_dir: Path, filename: str, rows: list[dict[str, Any]]) -> None:
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} records")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n", encoding="utf-8")
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[index] = f"{key}={safe_value}"
            break
    else:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(EMBED_DIMENSION)]


def embed(texts: list[str]) -> list[list[float]]:
    if os.getenv("FINANCE_RESEARCHER_USE_LIVE_EMBEDDINGS") != "1" or not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    embeddings: list[list[float]] = []
    batch: list[str] = []
    batch_chars = 0
    max_batch_items = 32
    max_batch_chars = 80_000
    for text in texts:
        text_chars = len(text)
        if batch and (len(batch) >= max_batch_items or batch_chars + text_chars > max_batch_chars):
            response = client.embeddings.create(input=batch, model=model)
            embeddings.extend(item.embedding for item in response.data)
            batch = []
            batch_chars = 0
        batch.append(text)
        batch_chars += text_chars
    if batch:
        response = client.embeddings.create(input=batch, model=model)
        embeddings.extend(item.embedding for item in response.data)
    return embeddings


def http_client() -> httpx.Client:
    return httpx.Client(headers=SEC_HEADERS, follow_redirects=True, timeout=60.0)


def request_json(client: httpx.Client, url: str, *, cache_path: Path | None = None) -> dict[str, Any]:
    if cache_path and cache_path.exists() and cache_path.stat().st_size > 0:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return payload
        except Exception as exc:  # pragma: no cover - network errors are environment-specific
            last_error = exc
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch JSON from {url}") from last_error


def download_bytes(client: httpx.Client, url: str, path: Path) -> bytes:
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.get(url)
            response.raise_for_status()
            payload = response.content
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            return payload
        except Exception as exc:  # pragma: no cover - network errors are environment-specific
            last_error = exc
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch binary content from {url}") from last_error


def download_text(client: httpx.Client, url: str, path: Path) -> str:
    if path.exists() and path.stat().st_size > 0:
        return path.read_text(encoding="utf-8", errors="ignore")
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = client.get(url)
            response.raise_for_status()
            payload = response.text
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
            return payload
        except Exception as exc:  # pragma: no cover - network errors are environment-specific
            last_error = exc
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch text content from {url}") from last_error


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "\n")
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p\s*>", "\n\n", html)
    html = re.sub(r"(?i)</div\s*>", "\n", html)
    html = re.sub(r"(?i)<[^>]+>", " ", html)
    return normalize_whitespace(html)


def extract_xml_text(xml_text: str) -> str:
    parts = re.findall(r">([^<>]+)<", xml_text)
    return normalize_whitespace(" ".join(parts))


def extract_office_xml_text(path: Path, member_patterns: list[str]) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        for pattern in member_patterns:
            for member in members:
                if re.fullmatch(pattern, member):
                    raw = archive.read(member).decode("utf-8", errors="ignore")
                    texts.append(extract_xml_text(raw))
    return normalize_whitespace("\n\n".join(texts))


def unescape_pdf_literal(text: str) -> str:
    text = text.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    text = text.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t")
    return text


def extract_pdf_text(path: Path) -> str:
    data = path.read_bytes()
    candidates: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        payload = match.group(1)
        for blob in (payload,):
            try:
                blob = zlib.decompress(blob)
            except Exception:
                pass
            decoded = blob.decode("latin-1", errors="ignore")
            candidates.extend(
                unescape_pdf_literal(item)
                for item in re.findall(r"\((.*?)\)\s*T[jJ]", decoded, re.S)
            )
            candidates.extend(unescape_pdf_literal(item) for item in re.findall(r"\((.*?)\)", decoded, re.S))
    if not candidates:
        fallback = data.decode("latin-1", errors="ignore")
        candidates.extend(re.findall(r"[A-Za-z0-9][A-Za-z0-9 ,.\-:/]{5,200}", fallback))
    return normalize_whitespace("\n".join(candidates))


def extract_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".htm", ".html", ".xhtml"}:
        return strip_html(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix in {".txt", ".xml"}:
        return normalize_whitespace(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return normalize_whitespace(json.dumps(payload, indent=2))
    if suffix == ".csv":
        return normalize_whitespace(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix in {".pptx", ".docx"}:
        return extract_office_xml_text(
            path,
            [
                r"ppt/slides/slide\d+\.xml",
                r"ppt/notesSlides/notesSlide\d+\.xml",
                r"word/document\.xml",
            ],
        )
    return normalize_whitespace(path.read_text(encoding="utf-8", errors="ignore"))


def looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False
    if stripped.startswith("Item ") or stripped.startswith("PART "):
        return True
    if stripped.endswith(":") and len(stripped.split()) <= 12:
        return True
    return stripped.isupper() and len(stripped.split()) <= 12


def split_into_sections(text: str, fallback_heading: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_heading = fallback_heading
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue
        if looks_like_heading(line) and len(current_lines) > 2:
            sections.append((current_heading, current_lines))
            current_heading = line
            current_lines = []
            continue
        current_lines.append(line)
    if current_lines:
        sections.append((current_heading, current_lines))
    if not sections:
        return [(fallback_heading, [text])]
    return [(heading, "\n".join(lines).strip()) for heading, lines in sections if "\n".join(lines).strip()]


def chunk_text(text: str, *, max_chars: int = 1200, overlap: int = 160) -> list[str]:
    normalized = normalize_whitespace(text)
    if len(normalized) <= max_chars:
        return [normalized]
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + max_chars)
        if end < len(normalized):
            cut = normalized.rfind("\n\n", start, end)
            if cut == -1:
                cut = normalized.rfind(". ", start, end)
            if cut != -1 and cut > start + 400:
                end = cut + 2
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def company_id(ticker: str) -> str:
    return f"company_{ticker.lower()}"


def profile_id() -> str:
    return "ANALYST_DEMO_001"


def synthetic_analyst_profile(*, companies: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "analyst_id": profile_id(),
        "name": "Morgan Lee",
        "email": "morgan.lee@example.com",
        "firm_name": "Context Engine Demos",
        "role": "Buy-side equity analyst",
        "watchlist_name": "Morgan's core watchlist",
        "watchlist_theme": "AI, cloud, semiconductors, and digital infrastructure",
        "active_watchlist_count": len(companies),
        "as_of_date": now_utc().date().isoformat(),
    }


def synthetic_company_record(company: dict[str, Any]) -> dict[str, Any]:
    ticker = company["ticker"]
    headquarters_city, headquarters_state = HEADQUARTERS_BY_TICKER.get(ticker, ("Unknown", "Unknown"))
    return {
        "company_id": company["company_id"],
        "ticker": ticker,
        "company_name": company["company_name"],
        "cik": company["cik"],
        "sector": company["sector"],
        "subsector": company["subsector"],
        "benchmark_group": company["benchmark_group"],
        "exchange": EXCHANGE_BY_TICKER.get(ticker, "NASDAQ"),
        "headquarters_city": headquarters_city,
        "headquarters_state": headquarters_state,
        "watchlist_rank": WATCHLIST_RANKS.get(ticker, 0),
        "website_url": WEBSITE_BY_TICKER.get(ticker, "https://www.sec.gov/edgar/browse/"),
    }


def synthetic_sec_submissions(*, company: dict[str, Any]) -> dict[str, Any]:
    from datetime import timedelta

    base_date = now_utc().date()
    recent_periods = [
        ("10-Q", base_date - timedelta(days=45), base_date - timedelta(days=35), "10-Q"),
        ("8-K", base_date - timedelta(days=21), base_date - timedelta(days=21), "8-K"),
        ("10-K", base_date - timedelta(days=135), base_date - timedelta(days=120), "10-K"),
    ]
    forms: list[str] = []
    accession_numbers: list[str] = []
    primary_docs: list[str] = []
    filing_dates: list[str] = []
    report_dates: list[str] = []
    descriptions: list[str] = []
    for index, (form, filing_date, report_date, suffix) in enumerate(recent_periods, start=1):
        forms.append(form)
        accession_numbers.append(f"{base_date.year % 10000:04d}-{index:02d}-{company['ticker'].lower()}-{index:02d}")
        primary_docs.append(f"{company['ticker'].lower()}-{suffix.lower()}-{index:02d}.htm")
        filing_dates.append(filing_date.isoformat())
        report_dates.append(report_date.isoformat())
        descriptions.append(
            "Quarterly report" if form == "10-Q" else "Current report" if form == "8-K" else "Annual report"
        )
    return {
        "filings": {
            "recent": {
                "form": forms,
                "accessionNumber": accession_numbers,
                "primaryDocument": primary_docs,
                "filingDate": filing_dates,
                "reportDate": report_dates,
                "primaryDocDescription": descriptions,
            }
        }
    }


def synthetic_companyfacts(*, company: dict[str, Any]) -> dict[str, Any]:
    from datetime import timedelta

    base_value = 40_000_000_000 + (sum(ord(char) for char in company["ticker"]) * 125_000_000)
    annual_value = base_value * 4
    current = now_utc().date()
    quarter_ends = [
        (current - timedelta(days=90 * offset), f"Q{4 - offset}") for offset in range(4)
    ]
    filings = []
    for offset, (period_end, fiscal_period) in enumerate(quarter_ends):
        value = base_value + (offset * 1_250_000_000)
        filings.append(
            {
                "end": period_end.isoformat(),
                "val": value,
                "form": "10-Q",
                "fy": current.year,
                "fp": fiscal_period,
                "filed": (period_end + timedelta(days=35)).isoformat(),
                "start": (period_end - timedelta(days=90)).isoformat(),
            }
        )
    filings.append(
        {
            "end": current.replace(month=12, day=31).isoformat(),
            "val": annual_value,
            "form": "10-K",
            "fy": current.year,
            "fp": "FY",
            "filed": current.isoformat(),
            "start": current.replace(year=current.year - 1, month=1, day=1).isoformat(),
        }
    )

    def metric_units(scale: float = 1.0) -> list[dict[str, Any]]:
        return [
            {
                "end": item["end"],
                "val": round(item["val"] * scale, 2),
                "form": item["form"],
                "fy": item["fy"],
                "fp": item["fp"],
                "filed": item["filed"],
                "start": item["start"],
            }
            for item in filings
        ]

    return {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {"USD": metric_units(1.0)}
                },
                "GrossProfit": {"units": {"USD": metric_units(0.45)}},
                "OperatingIncomeLoss": {"units": {"USD": metric_units(0.26)}},
                "NetIncomeLoss": {"units": {"USD": metric_units(0.20)}},
                "EarningsPerShareDiluted": {"units": {"USD/shares": metric_units(0.001)}},
                "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": metric_units(0.30)}},
                "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": metric_units(0.08)}},
            }
        }
    }


def resolve_watchlist_company_metadata(client: httpx.Client) -> list[dict[str, Any]]:
    companies: list[dict[str, Any]] = []
    ticker_lookup: dict[str, dict[str, Any]] = {}
    use_live_sources = os.getenv(LIVE_SOURCES_ENV_VAR, "0") == "1"
    if use_live_sources:
        try:
            ticker_map = request_json(client, "https://www.sec.gov/files/company_tickers.json")
            for entry in ticker_map.values():
                ticker = str(entry["ticker"]).upper()
                ticker_lookup[ticker] = {
                    "cik": f"{int(entry['cik_str']):010d}",
                    "sec_company_name": entry["title"],
                }
        except Exception:
            ticker_lookup = {}
    for watch in WATCHLIST:
        sec_entry: dict[str, Any] | None = ticker_lookup.get(watch["ticker"])
        if sec_entry is None and watch["ticker"] in FALLBACK_CIKS:
            sec_entry = {
                "cik": FALLBACK_CIKS[watch["ticker"]],
                "sec_company_name": watch["company_name"],
            }
        if not sec_entry:
            continue
        companies.append(
            {
                "company_id": company_id(watch["ticker"]),
                "ticker": watch["ticker"],
                "company_name": watch["company_name"],
                "cik": sec_entry["cik"],
                "sector": watch["sector"],
                "subsector": watch["subsector"],
                "benchmark_group": watch["benchmark_group"],
            }
        )
    return companies


def classify_attachment(filename: str, description: str | None) -> tuple[str, str, int]:
    text = f"{filename} {description or ''}".lower()
    if any(token in text for token in ["presentation", "slides", "slide deck", "deck"]):
        return "presentation", "presentation", DOC_FAMILY_PRIORITY["presentation"]
    if any(token in text for token in ["transcript", "prepared remarks", "conference call"]):
        return "transcript", "transcript", DOC_FAMILY_PRIORITY["transcript"]
    if any(token in text for token in ["earnings", "results", "press release", "release"]) or re.search(
        r"(^|[^0-9])99\.1([^0-9]|$)", text
    ):
        return "earnings_release", "earnings_release", DOC_FAMILY_PRIORITY["earnings_release"]
    return "exhibit", "exhibit", DOC_FAMILY_PRIORITY["exhibit"]


def normalize_document_source_type(source_type: str) -> str:
    if source_type in {"10-Q", "10-K", "8-K", "sec_filing"}:
        return "sec_filing"
    if source_type in {"presentation", "earnings_release", "transcript"}:
        return source_type
    return "sec_filing"


def normalize_event_type(source_type: str) -> str:
    mapping = {
        "10-Q": "new_filing",
        "10-K": "new_filing",
        "8-K": "new_filing",
        "sec_filing": "new_filing",
        "presentation": "new_presentation",
        "earnings_release": "new_release",
        "transcript": "new_transcript",
    }
    return mapping.get(source_type, "new_filing")


def make_document_id(*, ticker: str, source_type: str, accession: str, filename: str) -> str:
    return f"{ticker}_{source_type}_{accession.replace('-', '')}_{slugify(Path(filename).stem)}"


def make_chunk_id(document_id: str, index: int) -> str:
    return f"{document_id}_chunk_{index:03d}"


def make_point_id(company_id_value: str, metric_name: str, fiscal_year: Any, fiscal_period: str, period_end: str) -> str:
    return f"{company_id_value}_{metric_name}_{fiscal_year}_{fiscal_period}_{period_end}"


def make_bar_id(ticker: str, trade_date: str) -> str:
    return f"{ticker}_{trade_date}"


def make_event_id(document_id: str, event_type: str) -> str:
    return f"{document_id}_{event_type}"


def synthetic_document_payload(*, ticker: str, form: str, filing_date: str, title: str, accession: str) -> bytes:
    html = f"""<html><body>
<h1>{title}</h1>
<p>Ticker: {ticker}</p>
<p>Form: {form}</p>
<p>Filing date: {filing_date}</p>
<p>Accession: {accession}</p>
<p>This is a synthetic placeholder generated because the live SEC document could not be fetched during validation.</p>
</body></html>
"""
    return html.encode("utf-8")


def synthetic_price_rows(*, ticker: str, company_id_value: str, base_close: float) -> list[dict[str, Any]]:
    from datetime import date, timedelta

    rows: list[dict[str, Any]] = []
    today = date.today()
    close = base_close
    for offset in range(252):
        trade_date = today - timedelta(days=251 - offset)
        drift = ((offset % 11) - 5) * 0.35
        close = max(5.0, close + drift)
        rows.append(
            {
                "bar_id": make_bar_id(ticker, trade_date.isoformat()),
                "company_id": company_id_value,
                "ticker": ticker,
                "trade_date": trade_date.isoformat(),
                "open": round(close - 0.4, 2),
                "high": round(close + 1.25, 2),
                "low": round(max(1.0, close - 1.5), 2),
                "close": round(close, 2),
                "adj_close": round(close, 2),
                "volume": 1_000_000 + (offset * 37_000),
            }
        )
    return rows


def price_history_from_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, Any]] = []
        for raw_row in reader:
            trade_date = str(raw_row.get("trade_date") or raw_row.get("date") or "").strip()
            close_value = raw_row.get("close")
            if not trade_date or close_value in {None, ""}:
                continue
            adj_close_value = raw_row.get("adj_close")
            if adj_close_value in {None, ""}:
                adj_close_value = raw_row.get("adjClose")
            rows.append(
                {
                    "trade_date": trade_date,
                    "open": float(raw_row.get("open") or close_value),
                    "high": float(raw_row.get("high") or close_value),
                    "low": float(raw_row.get("low") or close_value),
                    "close": float(close_value),
                    "adj_close": float(adj_close_value or close_value),
                    "volume": int(float(raw_row.get("volume") or 0)),
                }
            )
    rows.sort(key=lambda row: row["trade_date"])
    return rows


def clean_metric_fact(fact: dict[str, Any], *, concept: str, unit: str) -> dict[str, Any] | None:
    end = fact.get("end")
    val = fact.get("val")
    if not end or val is None:
        return None
    form = fact.get("form")
    if form not in {"10-Q", "10-K", "10-Q/A", "10-K/A"}:
        return None
    fiscal_period = str(fact.get("fp") or "").upper()
    if fiscal_period not in {"Q1", "Q2", "Q3", "Q4", "FY"}:
        fiscal_period = "FY" if form.startswith("10-K") else "Q"
    period_type = "quarter" if fiscal_period in {"Q1", "Q2", "Q3", "Q4"} else "annual"
    return {
        "concept": concept,
        "unit": unit,
        "value": float(val),
        "fiscal_year": fact.get("fy"),
        "fiscal_period": fiscal_period,
        "period_end": end,
        "period_type": period_type,
        "filed": fact.get("filed"),
        "start": fact.get("start"),
    }


def collect_company_metrics(companyfacts: dict[str, Any]) -> dict[str, dict[tuple[str, Any, str], dict[str, Any]]]:
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    metrics: dict[str, dict[tuple[str, Any, str], dict[str, Any]]] = {}
    for metric_name, concepts in METRIC_CONCEPTS.items():
        metric_records: dict[tuple[str, Any, str], dict[str, Any]] = {}
        for concept in concepts:
            concept_data = us_gaap.get(concept)
            if not concept_data:
                continue
            for unit_name, facts in concept_data.get("units", {}).items():
                if metric_name == "diluted_eps" and unit_name != "USD/shares":
                    continue
                if metric_name != "diluted_eps" and unit_name != "USD":
                    continue
                for fact in facts:
                    cleaned = clean_metric_fact(fact, concept=concept, unit=unit_name)
                    if not cleaned:
                        continue
                    key = (cleaned["period_end"], cleaned["fiscal_year"], cleaned["fiscal_period"])
                    existing = metric_records.get(key)
                    if not existing:
                        metric_records[key] = cleaned
                        continue
                    existing_filed = existing.get("filed") or ""
                    new_filed = cleaned.get("filed") or ""
                    if new_filed > existing_filed:
                        metric_records[key] = cleaned
        metrics[metric_name] = metric_records
    return metrics


def select_period_keys(metrics: dict[str, dict[tuple[str, Any, str], dict[str, Any]]]) -> list[tuple[str, Any, str]]:
    candidate_scores: dict[tuple[str, Any, str], tuple[str, str]] = {}
    for records in metrics.values():
        for key, record in records.items():
            candidate_scores[key] = (record["period_type"], record.get("filed") or "")
    quarter_keys = [key for key, (period_type, _) in candidate_scores.items() if period_type == "quarter"]
    annual_keys = [key for key, (period_type, _) in candidate_scores.items() if period_type != "quarter"]
    quarter_keys.sort(reverse=True)
    annual_keys.sort(reverse=True)
    selected = quarter_keys[:4]
    if len(selected) < 4:
        selected.extend(annual_keys[: 4 - len(selected)])
    return selected


def price_history_from_yahoo(client: httpx.Client, ticker: str, path: Path) -> list[dict[str, Any]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1d&includeAdjustedClose=true"
    payload_path = path.with_suffix(".json")
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            if payload_path.exists() and payload_path.stat().st_size > 0:
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
            else:
                response = client.get(url, headers=YAHOO_HEADERS)
                response.raise_for_status()
                payload = response.json()
                payload_path.parent.mkdir(parents=True, exist_ok=True)
                payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            result = payload["chart"]["result"][0]
            timestamps = result.get("timestamp", [])
            quote = result["indicators"]["quote"][0]
            adj_close_series = result["indicators"].get("adjclose", [{}])[0].get("adjclose", [])
            rows: list[dict[str, Any]] = []
            for index, epoch_seconds in enumerate(timestamps):
                close = quote.get("close", [None])[index]
                if close is None:
                    continue
                date = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).date().isoformat()
                rows.append(
                    {
                        "trade_date": date,
                        "open": float(quote.get("open", [close])[index] or close),
                        "high": float(quote.get("high", [close])[index] or close),
                        "low": float(quote.get("low", [close])[index] or close),
                        "close": float(close),
                        "adj_close": float(adj_close_series[index] if index < len(adj_close_series) and adj_close_series[index] is not None else close),
                        "volume": int(float(quote.get("volume", [0])[index] or 0)),
                    }
                )
            if rows:
                return rows[-252:]
            raise RuntimeError(f"No price rows returned for {ticker}")
        except Exception as exc:  # pragma: no cover - network errors are environment-specific
            last_error = exc
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch price history for {ticker}") from last_error


def build_document_records(
    *,
    client: httpx.Client,
    company: dict[str, Any],
    submissions: dict[str, Any],
    output_dir: Path,
    raw_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ticker = company["ticker"]
    cik = company["cik"]
    filings = submissions.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    filing_dates = filings.get("filingDate", [])
    descriptions = filings.get("primaryDocDescription", [])

    selected_indexes: list[int] = []
    for target_form in ("8-K", "10-Q", "10-K"):
        for index, form in enumerate(forms):
            if form == target_form and index not in selected_indexes:
                selected_indexes.append(index)
                break

    documents: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    use_live_sources = os.getenv("FINANCE_RESEARCHER_USE_LIVE_SOURCES") == "1"

    for index in selected_indexes:
        form = forms[index]
        accession = accession_numbers[index]
        primary_doc = primary_docs[index]
        filing_date = filing_dates[index]
        filing_desc = descriptions[index] if index < len(descriptions) else None
        accession_no_dashes = accession.replace("-", "")
        archive_base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dashes}"

        primary_url = f"{archive_base}/{quote(primary_doc)}"
        raw_path = output_dir / "raw" / "sec" / ticker / accession_no_dashes
        raw_path.mkdir(parents=True, exist_ok=True)
        file_path = raw_path / safe_filename(primary_doc)
        if file_path.exists() and file_path.stat().st_size > 0:
            payload = file_path.read_bytes()
        elif use_live_sources:
            try:
                payload = download_bytes(client, primary_url, file_path)
            except Exception:
                payload = synthetic_document_payload(
                    ticker=ticker,
                    form=form,
                    filing_date=filing_date,
                    title=filing_desc or f"{company['company_name']} {form} filing",
                    accession=accession,
                )
                file_path.write_bytes(payload)
        else:
            payload = synthetic_document_payload(
                ticker=ticker,
                form=form,
                filing_date=filing_date,
                title=filing_desc or f"{company['company_name']} {form} filing",
                accession=accession,
            )
            file_path.write_bytes(payload)

        primary_source_type = normalize_document_source_type(form)
        published_at = f"{filing_date}T00:00:00Z" if filing_date and "T" not in filing_date else filing_date
        document_id = make_document_id(
            ticker=ticker,
            source_type=primary_source_type,
            accession=accession,
            filename=primary_doc,
        )
        title = filing_desc or f"{company['company_name']} {form} filing"
        documents.append(
            {
                "document_id": document_id,
                "company_id": company["company_id"],
                "ticker": ticker,
                "title": title,
                "source_type": primary_source_type,
                "document_family": "sec_filing",
                "published_at": published_at,
                "fiscal_period": None,
                "fiscal_year": None,
                "source_url": primary_url,
                "local_path": str(file_path.relative_to(output_dir)),
                "mime_type": "text/html" if file_path.suffix.lower() in {".htm", ".html"} else "application/octet-stream",
                "sha256": sha256_bytes(payload),
            }
        )
        raw_entries.append(
                {
                    "ticker": ticker,
                    "company_id": company["company_id"],
                    "kind": "sec_filing_primary",
                    "source_type": primary_source_type,
                "source_url": primary_url,
                "local_path": str(file_path.relative_to(output_dir)),
                "sha256": sha256_bytes(payload),
            }
        )
        seen_urls.add(primary_url)

        if form != "8-K":
            continue

        index_url = f"{archive_base}/index.json"
        index_path = raw_path / "index.json"
        if use_live_sources:
            try:
                filing_index = request_json(client, index_url, cache_path=index_path)
            except Exception:
                filing_index = {"directory": {"item": []}}
        else:
            filing_index = {"directory": {"item": []}}
        attachments = []
        for item in filing_index.get("directory", {}).get("item", []):
            name = item.get("name") or ""
            description = item.get("description")
            if not name or name == primary_doc:
                continue
            lower_name = name.lower()
            if not any(lower_name.endswith(ext) for ext in [".htm", ".html", ".txt", ".xml", ".pdf", ".pptx", ".docx"]):
                continue
            attachment_type, document_family, priority = classify_attachment(name, description)
            if priority < DOC_FAMILY_PRIORITY["exhibit"]:
                continue
            attachments.append((priority, name, description, attachment_type, document_family))
        attachments.sort(reverse=True)

        for _, name, description, attachment_type, document_family in attachments[:2]:
            attachment_url = f"{archive_base}/{quote(name)}"
            if attachment_url in seen_urls:
                continue
            attachment_path = raw_path / safe_filename(name)
            try:
                attachment_payload = download_bytes(client, attachment_url, attachment_path)
            except Exception:
                continue
            attachment_doc_id = make_document_id(
                ticker=ticker,
                source_type=attachment_type,
                accession=accession,
                filename=name,
            )
            documents.append(
                {
                    "document_id": attachment_doc_id,
                    "company_id": company["company_id"],
                    "ticker": ticker,
                    "title": description or name,
                    "source_type": normalize_document_source_type(attachment_type),
                    "document_family": document_family,
                    "published_at": published_at,
                    "fiscal_period": None,
                    "fiscal_year": None,
                    "source_url": attachment_url,
                    "local_path": str(attachment_path.relative_to(output_dir)),
                    "mime_type": (
                        "application/pdf"
                        if attachment_path.suffix.lower() == ".pdf"
                        else "text/html"
                        if attachment_path.suffix.lower() in {".htm", ".html"}
                        else "application/octet-stream"
                    ),
                    "sha256": sha256_bytes(attachment_payload),
                }
            )
            raw_entries.append(
                {
                    "ticker": ticker,
                    "company_id": company["company_id"],
                    "kind": "sec_filing_attachment",
                    "source_type": attachment_type,
                    "source_url": attachment_url,
                    "local_path": str(attachment_path.relative_to(output_dir)),
                    "sha256": sha256_bytes(attachment_payload),
                }
            )
            seen_urls.add(attachment_url)
    return documents


def build_chunk_records(
    documents: list[dict[str, Any]],
    text_by_document_id: dict[str, str],
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    chunk_texts: list[str] = []
    chunk_meta: list[tuple[dict[str, Any], str, str]] = []

    for document in documents:
        text = text_by_document_id.get(document["document_id"], "")
        if not text:
            continue
        sections = split_into_sections(text, document["title"])
        for section_index, (heading, section_text) in enumerate(sections, start=1):
            for chunk_index, chunk in enumerate(chunk_text(section_text), start=1):
                chunk_texts.append(chunk)
                chunk_meta.append((document, heading, f"section_{section_index:02d}_chunk_{chunk_index:02d}"))

    embeddings = embed(chunk_texts) if chunk_texts else []
    for index, (document, heading, page_label) in enumerate(chunk_meta):
        chunks.append(
            {
                "chunk_id": make_chunk_id(document["document_id"], index + 1),
                "document_id": document["document_id"],
                "company_id": document["company_id"],
                "ticker": document["ticker"],
                "section_heading": heading,
                "page_label": page_label,
                "chunk_text": chunk_texts[index],
                "content_embedding": embeddings[index],
            }
        )
    return chunks


def build_metric_records(
    company: dict[str, Any],
    companyfacts: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = collect_company_metrics(companyfacts)
    period_keys = select_period_keys(metrics)
    if not period_keys:
        return []
    rows: list[dict[str, Any]] = []
    company_key = company["company_id"]

    for metric_name, records in metrics.items():
        for period_key in period_keys:
            record = records.get(period_key)
            if not record:
                continue
            rows.append(
                {
                    "point_id": make_point_id(company_key, metric_name, record["fiscal_year"], record["fiscal_period"], record["period_end"]),
                    "company_id": company_key,
                    "ticker": company["ticker"],
                    "metric_name": metric_name,
                    "period_type": record["period_type"],
                    "fiscal_year": record["fiscal_year"],
                    "fiscal_period": record["fiscal_period"],
                    "period_end": record["period_end"],
                    "value": record["value"],
                    "unit": METRIC_UNITS[metric_name],
                    "currency": "USD",
                }
            )

    lookups: dict[tuple[Any, str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        key = (row["fiscal_year"], row["fiscal_period"], row["period_end"])
        lookups[key][row["metric_name"]] = row["value"]
    for (fiscal_year, fiscal_period, period_end), values in lookups.items():
        if "operating_cash_flow" not in values or "capex" not in values:
            continue
        rows.append(
            {
                "point_id": make_point_id(company_key, "free_cash_flow", fiscal_year, fiscal_period, period_end),
                "company_id": company_key,
                "ticker": company["ticker"],
                "metric_name": "free_cash_flow",
                "period_type": "quarter" if fiscal_period in {"Q1", "Q2", "Q3", "Q4"} else "annual",
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "period_end": period_end,
                "value": values["operating_cash_flow"] - values["capex"],
                "unit": METRIC_UNITS["free_cash_flow"],
                "currency": "USD",
            }
        )
    return rows


def build_price_records(client: httpx.Client, company: dict[str, Any], output_dir: Path) -> list[dict[str, Any]]:
    ticker = company["ticker"]
    local_csv_path = LOCAL_PRICE_DATA_DIR / f"{ticker}.csv"
    raw_path = output_dir / "raw" / "prices" / f"{ticker}.json"
    rows = price_history_from_csv(local_csv_path)
    if not rows and os.getenv("FINANCE_RESEARCHER_USE_LIVE_SOURCES") == "1":
        try:
            rows = price_history_from_yahoo(client, ticker, raw_path)
        except Exception:
            base_close = 80.0 + (sum(ord(char) for char in ticker) % 180)
            return synthetic_price_rows(ticker=ticker, company_id_value=company["company_id"], base_close=base_close)
    elif not rows:
        base_close = 80.0 + (sum(ord(char) for char in ticker) % 180)
        return synthetic_price_rows(ticker=ticker, company_id_value=company["company_id"], base_close=base_close)
    return [
        {
            "bar_id": make_bar_id(ticker, row["trade_date"]),
            "company_id": company["company_id"],
            "ticker": ticker,
            "trade_date": row["trade_date"],
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "adj_close": row["adj_close"],
            "volume": row["volume"],
        }
        for row in rows
    ]


def build_coverage_events(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for document in documents:
        importance = DOC_FAMILY_PRIORITY.get(document["source_type"], 60) / 100.0
        event_type = normalize_event_type(document["source_type"])
        if document["document_family"] == "presentation":
            event_family = "presentation"
        elif document["document_family"] == "transcript":
            event_family = "transcript"
        elif document["document_family"] == "earnings_release":
            event_family = "earnings"
        else:
            event_family = "filing"
        events.append(
            {
                "event_id": make_event_id(document["document_id"], event_type),
                "company_id": document["company_id"],
                "ticker": document["ticker"],
                "event_family": event_family,
                "event_type": event_type,
                "published_at": document["published_at"],
                "document_id": document["document_id"],
                "headline": document["title"],
                "importance_score": round(importance, 2),
            }
        )
    return events


def generate_demo_data(
    *,
    output_dir: Path,
    seed: int | None = None,
    update_env_file: bool = True,
) -> GeneratedDataset:
    del seed
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_raw_dir = resolved_output_dir / "raw"
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    resolved_raw_dir.mkdir(parents=True, exist_ok=True)
    use_live_sources = os.getenv(LIVE_SOURCES_ENV_VAR, "0") == "1"

    records: dict[str, list[dict[str, Any]]] = {
        "analyst_profiles.jsonl": [],
        "companies.jsonl": [],
        "research_documents.jsonl": [],
        "research_chunks.jsonl": [],
        "financial_metric_points.jsonl": [],
        "price_bars.jsonl": [],
        "coverage_events.jsonl": [],
    }
    raw_entries: list[dict[str, Any]] = []

    with http_client() as client:
        companies = resolve_watchlist_company_metadata(client)
        if not companies:
            raise RuntimeError("Unable to resolve finance-researcher watchlist companies from SEC data")

        companyfacts_by_ticker: dict[str, dict[str, Any]] = {}
        submissions_by_ticker: dict[str, dict[str, Any]] = {}
        documents: list[dict[str, Any]] = []
        text_by_document_id: dict[str, str] = {}

        print("Downloading SEC source catalogs...")
        for company in companies:
            ticker = company["ticker"]
            cik = company["cik"]
            raw_company_dir = resolved_raw_dir / "sec" / ticker
            raw_company_dir.mkdir(parents=True, exist_ok=True)
            if use_live_sources:
                submissions: dict[str, Any] | None = None
                companyfacts: dict[str, Any] | None = None
                try:
                    submissions = request_json(
                        client,
                        f"https://data.sec.gov/submissions/CIK{cik}.json",
                        cache_path=raw_company_dir / "submissions.json",
                    )
                except Exception:
                    submissions = None
                try:
                    companyfacts = request_json(
                        client,
                        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                        cache_path=raw_company_dir / "companyfacts.json",
                    )
                except Exception:
                    companyfacts = None
                if submissions is None:
                    submissions = synthetic_sec_submissions(company=company)
                    raw_company_dir.mkdir(parents=True, exist_ok=True)
                    (raw_company_dir / "submissions.json").write_text(
                        json.dumps(submissions, indent=2),
                        encoding="utf-8",
                    )
                if companyfacts is None:
                    companyfacts = synthetic_companyfacts(company=company)
                    raw_company_dir.mkdir(parents=True, exist_ok=True)
                    (raw_company_dir / "companyfacts.json").write_text(
                        json.dumps(companyfacts, indent=2),
                        encoding="utf-8",
                    )
            else:
                submissions = synthetic_sec_submissions(company=company)
                companyfacts = synthetic_companyfacts(company=company)
                raw_company_dir.mkdir(parents=True, exist_ok=True)
                (raw_company_dir / "submissions.json").write_text(
                    json.dumps(submissions, indent=2),
                    encoding="utf-8",
                )
                (raw_company_dir / "companyfacts.json").write_text(
                    json.dumps(companyfacts, indent=2),
                    encoding="utf-8",
                )
            submissions_by_ticker[ticker] = submissions
            companyfacts_by_ticker[ticker] = companyfacts

        print("Acquiring filings and issuer-published attachments...")
        for company in companies:
            submissions = submissions_by_ticker[company["ticker"]]
            company_documents = build_document_records(
                client=client,
                company=company,
                submissions=submissions,
                output_dir=resolved_output_dir,
                raw_entries=raw_entries,
            )
            documents.extend(company_documents)
            for document in company_documents:
                local_path = resolved_output_dir / document["local_path"]
                if local_path.exists():
                    text_by_document_id[document["document_id"]] = extract_document_text(local_path)
                else:
                    text_by_document_id[document["document_id"]] = normalize_whitespace(document["title"])

        analyst_profile = synthetic_analyst_profile(companies=companies)
        records["analyst_profiles.jsonl"].append(analyst_profile)

        for company in companies:
            records["companies.jsonl"].append(synthetic_company_record(company))

            companyfacts = companyfacts_by_ticker[company["ticker"]]
            metric_rows = build_metric_records(company, companyfacts)
            price_rows = build_price_records(client, company, resolved_output_dir)
            company_docs = [doc for doc in documents if doc["ticker"] == company["ticker"]]
            chunk_rows = build_chunk_records(company_docs, text_by_document_id)
            event_rows = build_coverage_events(company_docs)

            records["financial_metric_points.jsonl"].extend(metric_rows)
            records["price_bars.jsonl"].extend(price_rows)
            records["research_chunks.jsonl"].extend(chunk_rows)
            records["coverage_events.jsonl"].extend(event_rows)

        records["research_documents.jsonl"] = documents

    source_manifest = {
        "generated_at": ts(now_utc()),
        "company_count": len(records["companies.jsonl"]),
        "document_count": len(records["research_documents.jsonl"]),
        "chunk_count": len(records["research_chunks.jsonl"]),
        "metric_point_count": len(records["financial_metric_points.jsonl"]),
        "price_bar_count": len(records["price_bars.jsonl"]),
        "coverage_event_count": len(records["coverage_events.jsonl"]),
        "document_family_counts": {
            family: sum(1 for row in records["research_documents.jsonl"] if row["document_family"] == family)
            for family in sorted({row["document_family"] for row in records["research_documents.jsonl"]})
        },
        "raw_artifacts": raw_entries,
    }
    resolved_raw_dir.mkdir(parents=True, exist_ok=True)
    (resolved_raw_dir / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2),
        encoding="utf-8",
    )

    print("Writing JSONL files:")
    for filename, rows in records.items():
        write_jsonl(resolved_output_dir, filename, rows)

    env_updates = {
        "DEMO_USER_ID": analyst_profile["analyst_id"],
        "DEMO_USER_NAME": analyst_profile["name"],
        "DEMO_USER_EMAIL": analyst_profile["email"],
    }
    if update_env_file:
        for key, value in env_updates.items():
            update_env(key, value)

    print(f"\nDemo analyst: {analyst_profile['name']} ({analyst_profile['analyst_id']})")
    print(f"Watchlist companies: {len(records['companies.jsonl'])}")
    print(f"Documents downloaded: {len(records['research_documents.jsonl'])}")
    print("Done.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates=env_updates,
        summary={
            "analyst_profiles": len(records["analyst_profiles.jsonl"]),
            "companies": len(records["companies.jsonl"]),
            "research_documents": len(records["research_documents.jsonl"]),
            "research_chunks": len(records["research_chunks.jsonl"]),
            "financial_metric_points": len(records["financial_metric_points.jsonl"]),
            "price_bars": len(records["price_bars.jsonl"]),
            "coverage_events": len(records["coverage_events.jsonl"]),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
