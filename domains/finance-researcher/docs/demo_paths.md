# Finance Researcher Domain Spec

## Persona

The flagship user is **Morgan Lee**, a buy-side analyst who uses the demo to compare a curated 14-company watchlist across filings, earnings materials, structured metrics, price history, and normalized update events.

## Watchlist

The v1 watchlist is intentionally concentrated in large-cap and AI-adjacent names so the demo can support cross-company comparisons:

- `NVDA` NVIDIA
- `AMD` Advanced Micro Devices
- `AVGO` Broadcom
- `MU` Micron Technology
- `INTC` Intel
- `QCOM` Qualcomm
- `AAPL` Apple
- `AMZN` Amazon
- `MSFT` Microsoft
- `GOOGL` Alphabet
- `META` Meta Platforms
- `TSLA` Tesla
- `ORCL` Oracle
- `MDB` MongoDB

All flagship paths below stay inside that 14-company watchlist.

## Source Inventory

The dataset should prioritize official and reproducible sources:

1. SEC filings: 10-K, 10-Q, 8-K, and other publicly filed disclosures.
2. Earnings releases: official investor-relations press releases.
3. Investor presentations: company-hosted PDF slide decks.
4. Prepared remarks: official earnings call remarks or transcript-like documents when the company publishes them directly.

## Source Priority Rules

- Use SEC filings first when a question asks for facts, period comparisons, or the authoritative version of a statement.
- Use earnings releases next when the user asks what changed in the latest quarter or wants management's summary.
- Use investor presentations for strategy, segment, and outlook framing.
- Use prepared remarks only when the company publishes them directly and they add useful color.
- Do not lean on unofficial transcripts, broker research, or paywalled material in v1.

## Schema Expectations

The planned dataset supports these record types:

- `AnalystProfile`
- `Company`
- `ResearchDocument`
- `ResearchChunk`
- `FinancialMetricPoint`
- `PriceBar`
- `CoverageEvent`

## Flagship Demo Paths

### 1. Cross-company narrative comparison

Ask: "Compare the latest NVIDIA, AMD, and Broadcom filings and tell me what changed across the three companies."

What the dataset must support:

- Recent documents for `NVDA`, `AMD`, and `AVGO`
- Chunks from the most recent filing or earnings materials
- A way to compare how each company describes demand, guidance, or capital intensity

### 2. Metric-plus-document reasoning

Ask: "Walk me through Oracle's latest quarter using both the filing and the structured metrics."

What the dataset must support:

- Oracle documents with a clear period label
- Quarterly metric points for revenue, gross profit, operating income, net income, and cash flow proxies
- Enough document chunks to explain the narrative behind the numbers

### 3. Peer price and fundamentals trend comparison

Ask: "Compare stock price and fundamentals trends for NVIDIA, AMD, and MongoDB."

What the dataset must support:

- Daily `PriceBar` rows for `NVDA`, `AMD`, and `MDB`
- Comparable metric points across the same companies
- A consistent benchmark group so the peer set is obvious

### 4. What is new in my watchlist

Ask: "What's new in my watchlist this week?"

What the dataset must support:

- Normalized `CoverageEvent` rows for new filings, releases, presentations, or notable price moves
- A way to trace each event back to a `ResearchDocument`
- Recent timestamps so the agent can answer using the current market or filing window

## Non-Goals For v1

- Premium or paywalled research
- Expert-network content
- Intraday market data
- Backtesting, valuation engines, or portfolio math
- Dashboard-style analytics outside the existing app shell
- Coverage outside the 14-company watchlist
