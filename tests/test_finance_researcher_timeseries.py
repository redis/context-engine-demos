import importlib
import json

from backend.app.core.domain_loader import load_domain


class FakePipeline:
    def __init__(self, client: "FakeRedis") -> None:
        self.client = client
        self.commands: list[tuple] = []

    def execute_command(self, *args):
        self.commands.append(args)
        return self

    def execute(self):
        for args in self.commands:
            self.client.execute_command(*args)
        self.commands.clear()
        return []


class FakeRedis:
    def __init__(self) -> None:
        self.json_values: dict[str, object] = {}
        self.ts_values: dict[str, list[tuple[int, float]]] = {}

    def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if key in self.ts_values:
                removed += 1
                self.ts_values.pop(key, None)
        return removed

    def pipeline(self, transaction: bool = False) -> FakePipeline:
        del transaction
        return FakePipeline(self)

    def execute_command(self, *args):
        command = args[0]
        if command == "JSON.SET":
            _, key, _path, raw = args
            self.json_values[key] = json.loads(raw)
            return "OK"
        if command == "JSON.GET":
            _, key, _path = args
            value = self.json_values.get(key)
            if value is None:
                return None
            return json.dumps(value)
        if command == "TS.CREATE":
            key = args[1]
            self.ts_values[key] = []
            return "OK"
        if command == "TS.ADD":
            _, key, timestamp, value = args
            self.ts_values.setdefault(key, []).append((int(timestamp), float(value)))
            self.ts_values[key].sort(key=lambda entry: entry[0])
            return timestamp
        if command == "TS.RANGE":
            _, key, start, end = args
            values = self.ts_values.get(key, [])
            start_value = float("-inf") if start == "-" else int(start)
            end_value = float("inf") if end == "+" else int(end)
            return [[timestamp, value] for timestamp, value in values if start_value <= timestamp <= end_value]
        raise AssertionError(f"Unexpected Redis command: {args}")


def test_finance_researcher_writes_and_queries_redis_timeseries(monkeypatch) -> None:
    fake_redis = FakeRedis()
    domain_module = importlib.import_module("domains.finance-researcher.domain")
    monkeypatch.setattr(domain_module, "create_redis_client", lambda settings: fake_redis)

    domain = load_domain("finance-researcher")
    records = {
        "AnalystProfile": [{"user_id": "ANALYST_DEMO_001"}],
        "Company": [{"company_id": "company_nvda", "ticker": "NVDA", "company_name": "NVIDIA"}],
        "ResearchDocument": [],
        "ResearchChunk": [],
        "CoverageEvent": [],
        "PriceBar": [
            {
                "bar_id": "NVDA_2025-01-01",
                "company_id": "company_nvda",
                "ticker": "NVDA",
                "trade_date": "2025-01-01",
                "open": 140.0,
                "high": 145.0,
                "low": 138.0,
                "close": 144.5,
                "adj_close": 144.5,
                "volume": 1_200_000,
            },
            {
                "bar_id": "NVDA_2025-01-02",
                "company_id": "company_nvda",
                "ticker": "NVDA",
                "trade_date": "2025-01-02",
                "open": 144.5,
                "high": 147.0,
                "low": 143.0,
                "close": 146.0,
                "adj_close": 146.0,
                "volume": 1_260_000,
            },
        ],
        "FinancialMetricPoint": [
            {
                "point_id": "company_nvda_revenue_2025_Q4_2025-01-31",
                "company_id": "company_nvda",
                "ticker": "NVDA",
                "metric_name": "revenue",
                "period_type": "quarter",
                "fiscal_year": 2025,
                "fiscal_period": "Q4",
                "period_end": "2025-01-31",
                "value": 60_900_000_000.0,
                "unit": "USD",
                "currency": "USD",
            }
        ],
    }

    summary = domain.write_dataset_meta(settings=object(), records=records)
    assert summary["timeseries_enabled"] is True
    assert summary["timeseries_series_count"] == 3
    assert summary["timeseries_point_count"] == 5
    assert "revenue" in summary["timeseries_available_metric_series"]

    result = domain.execute_internal_tool(
        "query_finance_timeseries",
        {"tickers": "NVDA", "series_name": "close", "window": "max", "limit": 12},
        object(),
    )
    assert result["timeseries_used"] is True
    assert result["series_family"] == "price"
    assert result["redis_commands"] == [
        "TS.RANGE finance-researcher:ts:price:nvda:close - +"
    ]
    assert result["chart"]["type"] == "timeseries"
    assert result["chart"]["series"][0]["label"] == "NVDA close"
    assert len(result["chart"]["series"][0]["points"]) == 2
