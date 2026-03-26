<div align="center">

# 🍕 Reddash

**Food-delivery support intelligence powered by Redis Context Surfaces**

Ask about order status, late deliveries, refund policies, and more —
with full tool-call visibility in a dark-mode chat UI.

[Getting Started](#getting-started) · [Architecture](#architecture) · [Demo Paths](#demo-paths)

</div>

---

## What is this?

Reddash is now the first built-in **domain pack** in a reusable multi-domain demo framework. The shared runtime shows how **Redis Context Surfaces** turns your Redis data into auto-generated [MCP](https://modelcontextprotocol.io/) tools that any AI agent can call. Instead of stuffing documents into a vector store and hoping the LLM figures it out, Context Surfaces gives agents **structured, scoped, real-time access** to your operational data.

The active built-in domain is a food-delivery support agent that can chain 7+ tool calls across customers, orders, drivers, delivery events, payments, and policies — all backed by Redis Cloud.

**Two modes, same UI:**

| Mode | How it works | Best for |
|------|-------------|----------|
| **Context Surfaces** | LangGraph ReAct agent with 60+ auto-generated MCP tools | Multi-entity reasoning, real-time data |
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
- **Context Surfaces admin key** (`CTX_ADMIN_KEY`) — from the Context Surfaces console

> The `context-surfaces` SDK ships with sensible defaults for API and MCP URLs. No extra URLs to configure.

---

## Getting Started

### 1. Clone and configure

```bash
git clone https://github.com/<your-org>/reddash.git
cd reddash
cp .env.example .env
```

Edit `.env` and fill in three values:

```env
OPENAI_API_KEY=sk-...
REDIS_HOST=redis-xxxxx.c1.us-east-1-2.ec2.redns.redis-cloud.com
REDIS_PORT=12345
REDIS_PASSWORD=your-redis-password
CTX_ADMIN_KEY=your-admin-key
```

Everything else is auto-populated by later steps or has sensible defaults. The active domain defaults to `reddash`; you can override it with `DEMO_DOMAIN=<domain-id>` or `make ... DOMAIN=<domain-id>`.

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

### 4. Set up the Context Surface

```bash
make setup-surface
```

This registers your Redis instance, creates a Context Surface with the active domain's generated models, generates an agent key, and writes `CTX_SURFACE_ID`, `CTX_REDIS_INSTANCE_ID`, and `MCP_AGENT_KEY` back into `.env`.

> Already have a Redis instance registered? Set `CTX_REDIS_INSTANCE_ID` in `.env` first to reuse it.

### 5. Load data

```bash
make load-data
```

Pushes all records for the active domain through the Context Surfaces API, which handles Redis JSON storage and index creation.

### 6. Run

```bash
make dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3040 |
| Backend | http://localhost:8040 |

Open http://localhost:3040 and try:

- *"Why is my order running late?"*
- *"How much was I charged for my last order?"*
- *"What's your refund policy for late deliveries?"*

---

## Architecture

```
┌─────────────┐     SSE      ┌──────────────┐   JSON-RPC   ┌──────────────────┐
│  React Chat │◄────────────►│   FastAPI     │◄────────────►│  Context Surfaces│
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

**Backend** — FastAPI app with a LangGraph ReAct agent. The shared runtime loads an active `DomainPack`, exposes domain UI config to the frontend, mounts domain-defined internal tools, and fetches MCP tools from Context Surfaces at startup. Conversations are persisted via a Redis-backed LangGraph checkpointer. Responses stream to the frontend over SSE.

**Frontend** — React + TypeScript + Vite. The UI shell is shared, while branding, starter prompts, placeholder text, and theme tokens are loaded from `/api/domain-config`. The chat view shows every tool call, payload, result, and duration.

---

## Data Model

Nine entity types model a food-delivery platform:

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

Reddash schema definitions live in [`domains/reddash/schema.py`](domains/reddash/schema.py). A backward-compatible re-export still exists at `schemas/reddash_schema.py`.

---

## Demo Paths

See [`domains/reddash/docs/demo_paths.md`](domains/reddash/docs/demo_paths.md) for four scripted conversation flows:

1. **Late Order Investigation** ⭐ — 7-tool chain across orders, drivers, delivery events, and policies
2. **Payment & Membership** — itemized charges, membership tier awareness
3. **Support History** — ticket lookup, order drill-down, policy citation
4. **Multi-Entity Awareness** — cross-entity aggregation (restaurants, spend, promo codes)

> **Tip:** After each path, toggle to Simple RAG mode and ask the same question to see the contrast.

---

## Makefile Reference

| Target | Description |
|--------|-------------|
| `make install` | Install backend + frontend dependencies |
| `make validate-domain DOMAIN=reddash` | Validate the chosen domain pack |
| `make generate-models DOMAIN=reddash` | Regenerate ContextModel classes for the chosen domain |
| `make generate-data DOMAIN=reddash` | Generate sample JSONL data in `output/<domain>` |
| `make setup-surface DOMAIN=reddash` | Register Redis, create surface + agent key via ctxctl |
| `make load-data DOMAIN=reddash` | Import JSONL data via Context Surfaces API |
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
reddash/
├── backend/app/             # Shared FastAPI + LangGraph runtime
│   ├── core/                # Domain contract, schema types, loader
│   ├── main.py              # App entry, SSE endpoints, /api/domain-config
│   ├── langgraph_agent.py   # Shared ReAct agent runtime
│   ├── context_surface_service.py  # MCP tool integration
│   ├── rag_service.py       # Shared simple-RAG comparison mode
│   └── settings.py          # Pydantic settings (.env loader)
├── domains/
│   └── reddash/             # First built-in domain pack
│       ├── domain.py        # DOMAIN export implementing the contract
│       ├── schema.py        # Entity definitions
│       ├── prompt.py        # Domain prompt/playbooks
│       ├── data_generator.py
│       ├── generated_models.py
│       ├── assets/logo.svg
│       └── docs/demo_paths.md
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

---

## License

MIT
