import importlib
from pathlib import Path


def test_finance_researcher_prefers_checked_in_price_csv(monkeypatch, tmp_path: Path) -> None:
    data_generator = importlib.import_module("domains.finance-researcher.data_generator")

    csv_dir = tmp_path / "prices"
    csv_dir.mkdir(parents=True, exist_ok=True)
    (csv_dir / "MDB.csv").write_text(
        "\n".join(
            [
                "trade_date,open,high,low,close,adj_close,volume",
                "2026-01-02,233.1,236.2,231.4,235.8,235.8,1987654",
                "2026-01-05,236.0,238.5,234.7,237.9,237.9,1765432",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(data_generator, "LOCAL_PRICE_DATA_DIR", csv_dir)

    company = {
        "ticker": "MDB",
        "company_id": "company_mdb",
    }
    records = data_generator.build_price_records(client=None, company=company, output_dir=tmp_path)
    assert len(records) == 2
    assert records[0]["ticker"] == "MDB"
    assert records[0]["trade_date"] == "2026-01-02"
    assert records[0]["close"] == 235.8
    assert records[1]["volume"] == 1765432
