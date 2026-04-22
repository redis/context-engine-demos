# Finance Price CSV Cache

These CSV files are the checked-in canonical price history cache for the `finance-researcher` demo.

The generator prefers these files before attempting any live price API calls.

Populate or refresh them with:

```bash
export FMP_API_KEY=...
uv run python domains/finance-researcher/fetch_price_csvs.py --years 5 --overwrite
```

Expected columns:

- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `adj_close`
- `volume`
