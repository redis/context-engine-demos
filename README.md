<div align="center">

# Context Engine Demos

**Reusable demo apps powered by Redis Context Retriever**

Domain-specific demo apps for agentic workflows over structured Redis data,
with full tool-call visibility in a dark-mode chat UI.

[Getting Started](#getting-started) · [Architecture](#architecture) · [Demo Paths](#demo-paths)

</div>

---

## What is this?

Context Engine Demos is a multi-domain demo framework built around **Redis Context Retriever**. The shared runtime shows how Context Retriever turns Redis data into auto-generated [MCP](https://modelcontextprotocol.io/) tools that an AI agent can call. Instead of stuffing documents into a vector store and hoping the LLM figures it out, Context Retriever gives agents **structured, scoped, real-time access** to operational data.

The repo currently includes built-in demo domains for:

- `northbridge-banking` — public-safe consumer banking support with semantic caching
- `reddash` — food-delivery support
- `electrohub` — electronics retail and order support
- `finance-researcher` — ShiftIQ watchlist research across filings, metrics, prices, and live updates
- `healthcare` — RedHealthConnect patient success portal (appointments, referrals, providers)

**Two modes, same UI:**

| Mode | How it works | Best for |
|------|-------------|----------|
| **Context Retriever** | LangGraph ReAct agent with 60+ auto-generated MCP tools | Multi-entity reasoning, real-time data |
| **Simple RAG** | Vector search over policy docs → one-shot LLM answer | Showing the contrast |

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Python](https://python.org) | ≥ 3.11 | Backend + scripts |
| [uv](https://docs.astral.sh/uv/) | latest | Python package manager |
| [Node.js](https://nodejs.org) | ≥ 18 | Frontend |
| [npm](https://npmjs.com) | ≥ 9 | Frontend dependencies |

You will also need:

- **OpenAI API key** — for embeddings and chat completions
- **Redis Cloud** instance — host, port, and password
- **Context Retriever admin key** (`CTX_ADMIN_KEY`) — from the Context Retriever console

> The `context-surfaces` SDK ships with sensible defaults for API and MCP URLs. No extra URLs to configure.

---

## Getting Started

### 1. Clone and configure

```bash
git clone https://github.com/redis/context-engine-demos.git
cd context-engine-demos
cp .env.example .env
```

Edit `.env` and fill in three values:

```env
OPENAI_API_KEY=your-openai-api-key
REDIS_HOST=redis-xxxxx.c1.us-east-1-2.ec2.redns.redis-cloud.com
REDIS_PORT=12345
REDIS_PASSWORD=your-redis-password
CTX_ADMIN_KEY=your-admin-key
```

Everything else is auto-populated by later steps or has sensible defaults. The active domain defaults to `reddash`; you can override it with `DEMO_DOMAIN=<domain-id>` or `make ... DOMAIN=<domain-id>`.

To run the checked-in banking demo:

```bash
make validate-domain DOMAIN=northbridge-banking
make generate-models DOMAIN=northbridge-banking
make generate-data DOMAIN=northbridge-banking
make setup-surface DOMAIN=northbridge-banking
make load-data DOMAIN=northbridge-banking
DEMO_DOMAIN=northbridge-banking make dev
```

### 2. Install dependencies

```bash
make install
```

Runs `uv sync` (Python) and `npm install` (frontend).

### 3. Generate models and sample data

```bash
make validate-domain DOMAIN=reddash
make generate-models DOMAIN=reddash
make generate-data DOMAIN=reddash
```

### 4. Set up the Context Retriever

```bash
make setup-surface
```

This creates a Context Retriever with the active domain's generated models, embeds the current Redis connection settings as the surface data source, generates an agent key, and writes `CTX_SURFACE_ID` and `MCP_AGENT_KEY` back into `.env`.

### 5. Load data

```bash
make load-data
```

Pushes all records for the active domain through the Context Retriever API, which handles Redis JSON storage and index creation.

### 6. Run

```bash
make dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3040 |
| Backend | http://localhost:8040 |

Open http://localhost:3040 and try:

- In `reddash`:
  - *"Why is my order running late?"*
  - *"How much was I charged for my last order?"*
- In `electrohub`:
  - *"Show me my recent ElectroHub orders."*
  - *"Can I pick that up at my local store?"*
- In `finance-researcher` / ShiftIQ:
  - *"Walk me through Oracle's latest quarter using both the filing and the structured metrics."*
  - *"What's new in my watchlist this week?"*
- In `healthcare`:
  - *"Do I have any upcoming appointments?"*
  - *"Find me a cardiologist accepting new patients?"*

---

## Architecture

```
┌─────────────┐     SSE      ┌──────────────┐   JSON-RPC   ┌──────────────────┐
│  React Chat │◄────────────►│   FastAPI     │◄────────────►│ Context Retriever│
│  (Vite)     │              │ + LangGraph   │              │  MCP Server      │
│  :3040      │              │   :8040       │              │  (cloud)         │
└─────────────┘              └──────┬────────┘              └───────┬──────────┘
                                    │                               │
                                    │ redis-py                      │
                                    ▼                               ▼
                             ┌──────────────┐               ┌──────────────┐
                             │ Redis Cloud  │◄──────────────│ Auto-created │
                             │ (your data)  │               │ Search indexes│
                             └──────────────┘               └──────────────┘
```

**Backend** — FastAPI app with a LangGraph ReAct agent. The shared runtime loads an active `DomainPack`, exposes domain UI config to the frontend, mounts domain-defined internal tools, and fetches MCP tools from Context Retriever at startup. Conversations are persisted via a Redis-backed LangGraph checkpointer. Responses stream to the frontend over SSE.

**Frontend** — React + TypeScript + Vite. The UI shell is shared, while branding, starter prompts, placeholder text, and theme tokens are loaded from `/api/domain-config`. The chat view shows every tool call, payload, result, and duration.

---

## Example Data Model

The `reddash` domain models a food-delivery platform with nine entity types:

| Entity | Key Pattern | Key Indexed Fields |
|--------|-------------|-------------------|
| **Customer** | `reddash_customer:{id}` | name, email, account_status, city |
| **Restaurant** | `reddash_restaurant:{id}` | name, cuisine_type, city, rating |
| **Order** | `reddash_order:{id}` | customer_id, status, order_total, city |
| **OrderItem** | `reddash_order_item:{id}` | order_id, item_name, quantity |
| **DeliveryEvent** | `reddash_delivery_event:{id}` | order_id, event_type, actor |
| **Driver** | `reddash_driver:{id}` | name, current_status, active_order_id |
| **Payment** | `reddash_payment:{id}` | order_id, customer_id, payment_method |
| **SupportTicket** | `reddash_support_ticket:{id}` | customer_id, order_id, category, status |
| **Policy** | `reddash_policy:{id}` | title, category, content, content_embedding (vector) |

Reddash schema definitions live in [`domains/reddash/schema.py`](domains/reddash/schema.py). ElectroHub schema definitions live in [`domains/electrohub/schema.py`](domains/electrohub/schema.py). ShiftIQ schema definitions live in [`domains/finance-researcher/schema.py`](domains/finance-researcher/schema.py).

The `healthcare` domain models a patient success portal with six entity types:

| Entity | Key Pattern | Key Indexed Fields |
|--------|-------------|-------------------|
| **Location** | `healthcare_location:{id}` | name, city, type |
| **Provider** | `healthcare_provider:{id}` | name, specialty, accepting_new_patients, languages |
| **Patient** | `healthcare_patient:{id}` | name, email, insurance_status, preferred_language |
| **Appointment** | `healthcare_appointment:{id}` | patient_id, provider_id, status, type, datetime |
| **Referral** | `healthcare_referral:{id}` | patient_id, to_specialty, urgency, status |
| **Waitlist** | `healthcare_waitlist:{id}` | patient_id, preferred_provider_id, appointment_type |

Healthcare schema definitions live in [`domains/healthcare/schema.py`](domains/healthcare/schema.py).

---

## Demo Paths

See:

- [`domains/northbridge-banking/docs/demo_paths.md`](domains/northbridge-banking/docs/demo_paths.md)
- [`domains/reddash/docs/demo_paths.md`](domains/reddash/docs/demo_paths.md)
- [`domains/electrohub/docs/demo_paths.md`](domains/electrohub/docs/demo_paths.md)
- [`domains/finance-researcher/docs/demo_paths.md`](domains/finance-researcher/docs/demo_paths.md)
- [`domains/healthcare/docs/demo_paths.md`](domains/healthcare/docs/demo_paths.md)

Northbridge Bank includes three scripted conversation flows:

1. **Shared product guidance** — public semantic-cache reuse for card controls
2. **Segment-scoped support guidance** — cache partitioning within `Plus` / `Standard` cohorts
3. **Flagship card decline recovery** — customer-specific reasoning across accounts, cards, authorisations, risk events, and recovery options

Reddash includes four scripted conversation flows:

1. **Late Order Investigation** ⭐ — 7-tool chain across orders, drivers, delivery events, and policies
2. **Payment & Membership** — itemized charges, membership tier awareness
3. **Support History** — ticket lookup, order drill-down, policy citation
4. **Multi-Entity Awareness** — cross-entity aggregation (restaurants, spend, promo codes)

> **Tip:** After each path, toggle to Simple RAG mode and ask the same question to see the contrast.

ShiftIQ includes flagship paths for:

1. **Cross-company narrative comparison** — compare the latest filings and research chunks across peers
2. **Metric-plus-document reasoning** — explain a quarter using both structured metrics and source documents
3. **Peer trend analysis** — compare price and fundamentals trends, including RedisTimeSeries-backed queries
4. **Live watchlist updates** — explain what changed this week using normalized coverage events and Redis Streams

## Presentations

Keep domain-specific presentations with the domain itself:

- `domains/<domain-id>/presentations/`

Example:

- [`domains/electrohub/presentations/director-demo/index.html`](domains/electrohub/presentations/director-demo/index.html)
- [`domains/electrohub/presentations/director-demo/README.md`](domains/electrohub/presentations/director-demo/README.md)
- [`domains/finance-researcher/presentations/engineering-brief/index.html`](domains/finance-researcher/presentations/engineering-brief/index.html)
- [`domains/finance-researcher/presentations/engineering-brief/README.md`](domains/finance-researcher/presentations/engineering-brief/README.md)
- [`domains/finance-researcher/presentations/model-browser/index.html`](domains/finance-researcher/presentations/model-browser/index.html)

---

## Makefile Reference

| Target | Description |
|--------|-------------|
| `make install` | Install backend + frontend dependencies |
| `make validate-domain DOMAIN=reddash` | Validate the chosen domain pack |
| `make generate-models DOMAIN=reddash` | Regenerate ContextModel classes for the chosen domain |
| `make generate-data DOMAIN=reddash` | Generate sample JSONL data in `output/<domain>` |
| `make setup-surface DOMAIN=reddash` | Create surface + agent key using embedded Redis connection settings |
| `make load-data DOMAIN=reddash` | Import JSONL data via Context Retriever API |
| `make smoke-domain DOMAIN=reddash` | Run a lightweight scaffold/data/model smoke test |
| `make create-domain DOMAIN=electronics-store` | Scaffold a new domain pack |
| `make backend` | Start FastAPI backend only |
| `make frontend` | Start Vite frontend only |
| `make dev` | Run backend + frontend together |
| `make flush-redis` | Flush the Redis database |
| `make reset` | Flush Redis + recreate surface + reload data |

---

## Project Structure

```
context-engine-demos/
├── backend/app/             # Shared FastAPI + LangGraph runtime
│   ├── core/                # Domain contract, schema types, loader
│   ├── main.py              # App entry, SSE endpoints, /api/domain-config
│   ├── langgraph_agent.py   # Shared ReAct agent runtime
│   ├── context_surface_service.py  # MCP tool integration
│   ├── rag_service.py       # Shared simple-RAG comparison mode
│   └── settings.py          # Pydantic settings (.env loader)
├── domains/
│   ├── banking_core/        # Reusable consumer-banking core for branded variants
│   ├── northbridge-banking/ # Public-safe banking demo domain
│   ├── reddash/             # Delivery-support reference domain
│   ├── electrohub/          # Electronics retail reference domain
│   ├── finance-researcher/  # ShiftIQ watchlist research domain
│   └── healthcare/          # Patient success portal domain
│       ├── domain.py        # DOMAIN export implementing the contract
│       ├── schema.py        # Entity definitions
│       ├── prompt.py        # Domain prompt/playbooks
│       ├── data_generator.py
│       ├── generated_models.py
│       ├── assets/logo.(svg|png|jpg|webp)
│       ├── docs/demo_paths.md
│       └── presentations/   # Domain-specific decks and assets
├── frontend/src/            # React + Vite chat UI
│   ├── App.tsx              # Shared chat UI shell
│   └── styles.css           # Theme-driven styles
├── scripts/                 # Generic domain tooling
├── tests/                   # Domain and framework smoke tests
├── .codex/skills/domain-pack-authoring/
│   └── SKILL.md             # Agent workflow for creating new domains
├── Makefile                 # All build/run targets
├── pyproject.toml           # Python dependencies
└── .env.example             # Environment template
```

## Creating a New Domain

```bash
make create-domain DOMAIN=electronics-store
make validate-domain DOMAIN=electronics-store
```

Then fill in `domains/electronics-store/` and follow the repo-local skill at
[`./.codex/skills/domain-pack-authoring/SKILL.md`](.codex/skills/domain-pack-authoring/SKILL.md).
Domain logos can be `svg`, `png`, `jpg`, `jpeg`, or `webp` as long as
`branding.logo_path` matches the asset under `domains/<domain>/assets/`.
If the domain has presentation material, keep it under
`domains/<domain-id>/presentations/`.

---

## License

MIT
