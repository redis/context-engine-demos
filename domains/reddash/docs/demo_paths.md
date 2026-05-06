# Demo Paths

Four scripted conversation paths. Each starts with a natural question and
chains follow-ups that showcase multi-entity reasoning, conversational memory,
and the contrast with Simple RAG.

> **Tip:** After running each path in Context Retriever mode, toggle to
> Simple RAG and ask the same opening question to show the contrast.

---

## Path 1 — Late Order Investigation ⭐ (Flagship)

*Shows: 7-tool chain, delivery timeline, driver status, policy citation*

| # | You say | What the agent does | Key data surfaced |
|---|---------|--------------------|--------------------|
| 1 | **"Why is my order late?"** | get_user → orders → time → delivery events → driver → payment → policy search | ORD_001 is ~40 min late. 16-min gap between food ready and driver assignment. Marcus has a flat tire on Market St. Policy: 30+ min = full delivery fee refund. |
| 2 | **"Can I get a refund for that?"** | Searches refund policy (fresh fetch) | Cites specific policy: 30+ min delay qualifies for full refund. References the $42.50 charge on Visa ending 4242. |
| 3 | **"Has this kind of thing happened to me before?"** | Fetches support tickets for customer | Finds TKT_001: missing milkshake on ORD_003 from Burger Barn, resolved with $6.50 refund. |

**RAG contrast:** Simple RAG answers Q1 with generic policy text — no order ID, no driver name, no timeline, no dollar amounts.

---

## Path 2 — Payment & Membership Deep Dive

*Shows: payment breakdown, order items, membership tier awareness*

| # | You say | What the agent does | Key data surfaced |
|---|---------|--------------------|--------------------|
| 1 | **"How much was I charged for my last delivered order?"** | get_user → orders → finds most recent delivered (ORD_002) → payment | $30.00 subtotal + $0.00 delivery (Plus member) + $2.50 service fee + $2.50 tax + $3.00 tip = $38.00 on Visa 4242. |
| 2 | **"What did I order?"** | Fetches order items for ORD_002 | Margherita Pizza ($18.00, extra basil) + Caesar Salad ($12.00, dressing on side). |
| 3 | **"Do I get free delivery because of my membership?"** | Fetches customer record + searches membership policy | Alex is Plus tier: free delivery on orders over $15, 5% cashback. All 4 orders show $0.00 delivery fee. |

**RAG contrast:** Simple RAG can describe membership tiers generically but doesn't know Alex is a Plus member or that he's been getting free delivery.

---

## Path 3 — Support History & Resolution

*Shows: support ticket lookup, order item drill-down, policy retrieval*

| # | You say | What the agent does | Key data surfaced |
|---|---------|--------------------|--------------------|
| 1 | **"I reported a missing item last week — was that resolved?"** | get_user → support tickets | TKT_001: "Milkshake was missing from my order." Status: resolved. Resolution: $6.50 refund to original payment method. |
| 2 | **"What was in that order?"** | Fetches order items for ORD_003 | Classic Burger ($11.99, no pickles), Fries ($4.50), Milkshake ($6.50, chocolate) — from Burger Barn. |
| 3 | **"What's your policy on missing items?"** | Searches refund policy | "Refund requests must be submitted within 24 hours. Photo evidence may be required for quality-related claims. Refunds processed within 3-5 business days." |

**RAG contrast:** Simple RAG has no access to support tickets. It will say something like "contact support to check your ticket status."

---

## Path 4 — Multi-Entity Awareness

*Shows: the agent connecting data across restaurants, orders, and drivers*

| # | You say | What the agent does | Key data surfaced |
|---|---------|--------------------|--------------------|
| 1 | **"What restaurants have I ordered from?"** | get_user → orders | Sakura Sushi, Bella Napoli, Burger Barn (×2). Four orders total, one currently in transit. |
| 2 | **"How much have I spent in total?"** | Fetches payments for customer | $42.50 + $38.00 + $22.99 + $15.99 = $119.48 across 4 orders. Two payment methods: Visa 4242 and Apple Pay. |
| 3 | **"Which order used a promo code?"** | Already has payment data in context | ORD_003: promo code WELCOME5, $5.00 discount on the Burger Barn order. |

**RAG contrast:** Simple RAG has zero transactional data. It cannot answer any of these three questions.
