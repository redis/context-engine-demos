# Finance Researcher Demo Paths

## Persona

The flagship user is **Morgan Lee**, a buy-side analyst who uses the demo to compare a curated 14-company watchlist across filings, earnings materials, structured metrics, price history, and normalized update events.

## Demo Positioning

ShiftIQ is not a full portfolio, CRM, trading, or research-management system. It is a focused context-engine demo showing how an agent can use Redis-backed context across structured company records, filings, metrics, price time series, and live update events.

Use **Context Surfaces** mode for the primary flow.

The unique value of the agent flow is coordination:

- It starts from the signed-in analyst context and watchlist instead of a generic prompt.
- It coordinates structured records, document chunks, RedisTimeSeries, and Redis Streams in one conversation.
- It makes the tool path inspectable, so the audience can see when the answer came from records, time-series data, source documents, or live stream events.
- It gives a clean bridge to the broader Redis message: context first, orchestration across data planes second, and optimization next through semantic caching and routing.

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

### 1. Establish analyst and data context

Ask:

```text
What is my active research context, what companies are in scope, and what data is loaded?
```

What this shows:

- The agent identifies the current analyst before answering.
- It inspects dataset coverage instead of relying on prompt memory.
- It frames the 14-company watchlist as the working context for the rest of the demo.

### 2. Cross-company narrative comparison

Ask:

```text
Compare the latest NVIDIA, AMD, and Broadcom filings and tell me what changed across the three companies.
```

What the dataset must support:

- Recent documents for `NVDA`, `AMD`, and `AVGO`
- Chunks from the most recent filing or earnings materials
- A way to compare how each company describes demand, guidance, or capital intensity

What this shows:

- Source-grounded research across multiple companies.
- Coordination between company records, source documents, and document chunks.
- A research workflow that summarizes what changed before a client or stakeholder conversation.

### 3. Metric-plus-document reasoning

Ask:

```text
Walk me through Oracle's latest quarter using both the filing and the structured metrics. Keep it to three bullets.
```

What the dataset must support:

- Oracle documents with a clear period label
- Quarterly metric points for revenue, gross profit, operating income, net income, and cash flow proxies
- Enough document chunks to explain the narrative behind the numbers

What this shows:

- The agent combines narrative evidence with structured metrics.
- The response separates "what the numbers say" from "what the filing says."
- The path is useful as a concise pre-meeting brief.

### 4. Peer price and fundamentals trend comparison

Ask:

```text
Compare the one-year close price trend for Apple, Microsoft, and Amazon. Keep it simple for an advisor.
```

What the dataset must support:

- Daily `PriceBar` rows for `AAPL`, `MSFT`, and `AMZN`
- Comparable metric points across the same companies
- A consistent benchmark group so the peer set is obvious

What this shows:

- RedisTimeSeries as a first-class agent tool.
- Chart-ready time-series output from queried data, not invented by the model.
- Inspectable Redis commands in the trace.

### 5. Live watchlist update context

In another terminal:

```bash
make publish-domain-event DOMAIN=finance-researcher
```

Then ask:

```text
A live watchlist update just came in. Read the latest live events and tell me what changed, which ticker it affects, and what an advisor should pay attention to next.
```

What the dataset must support:

- Normalized `CoverageEvent` rows for new filings, releases, presentations, or notable price moves
- A way to trace each event back to a `ResearchDocument`
- Recent timestamps so the agent can answer using the current market or filing window
- A running backend that exposes `recent_watchlist_events` in `/api/health`

What this shows:

- Redis Streams as live context, not just a UI notification.
- The application and the agent can read from the same stream-backed event feed.
- The model can react to something that arrived after page load.

Before using this step, confirm `/api/health` lists `recent_watchlist_events` under `internal_tools`. If it does not, restart the backend so the current finance-researcher domain code is loaded.

## Additional Softball Prompts

Use these when you want a lower-risk path that still exercises useful tools.

### Company record lookup

Ask:

```text
For Apple, give me the company snapshot from the loaded records and one advisor-facing takeaway.
```

Shows:

- Direct structured lookup against the company record.
- Translation from raw company context into a concise advisory takeaway.

### Watchlist segmentation

Ask:

```text
List the mega-cap technology names in my watchlist and show each ticker with sector and subsector.
```

Shows:

- The agent starts with the analyst watchlist, then resolves company records.
- A raw coverage universe becomes a set of client-discussion buckets.

### Fundamentals trend

Ask:

```text
Compare revenue trends for NVIDIA, AMD, and Broadcom over the max available period. Keep it to three advisor-ready bullets.
```

Shows:

- RedisTimeSeries on fundamentals, not just prices.
- A bridge from market context to operating performance.

## Optional RAG Contrast

Switch to **Simple RAG** and ask:

```text
Compare the one-year close price trend for NVIDIA, AMD, and Microsoft.
```

Point out:

Simple RAG can retrieve text. It cannot coordinate structured records, time-series data, live events, and durable agent state the same way.

## Prompts To Avoid In Executive Demos

Avoid broad keyword prompts like:

```text
Search the research corpus for margin pressure commentary across the watchlist.
```

The current generated corpus is small and can return no matches for generic phrases. Prefer company-specific filing prompts or time-series prompts when you need a reliable demo path.

## Non-Goals For v1

- Premium or paywalled research
- Expert-network content
- Intraday market data
- Backtesting, valuation engines, or portfolio math
- Dashboard-style analytics outside the existing app shell
- Coverage outside the 14-company watchlist
