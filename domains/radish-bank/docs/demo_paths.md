# Radish Bank — demo paths

Single customer **Merv Kwok** (`CUST001`). Use **Context Surfaces** mode for structured + doc retrieval; compare with **Simple RAG** on policy-style questions.

## 1. Product discovery (FD + insurance)

- "What fixed deposit plans do you offer?"
- "What accident insurance plans do you offer and what are the premiums?"

Expect: structured **FixedDepositPlan** / **InsurancePlan** data; optional doc augmentation from FAQs.

## 2. Branch + hours

- "Is the Bishan location a full branch?"
- "What are the operating hours for Tampines?"

Expect: **Branch** + **BranchHours** (or branch guide doc for narrative).

## 3. Place fixed deposit (approve)

- "Place 8000 SGD into the 6-month fixed deposit from my savings account."

Expect: `place_fixed_deposit` **approved**; new **ProductHolding**; optional balance deduction on **ACC001**.

## 4. Place fixed deposit (reject — over cap)

- "Put 12000 SGD into the 12-month fixed deposit."

Expect: **rejected** (amount must be **< 10000** SGD).

## 5. Buy insurance (approve)

- "Buy the Plus Accident Cover plan for me."

Expect: `buy_accident_insurance` **approved** if not already held.

## 6. Annual fee waiver

- "Can you waive my annual card fee?"

Expect: `request_annual_card_fee_waiver` **approved** when no **approved** waiver in the **last 12 months** (historical demo waiver is older).

## 7. Retrieval-only

- "What happens if I withdraw my fixed deposit early?"

Expect: **BankDocument** / vector search on FD FAQ; no state change.

> **Tip:** After a path, switch to **Simple RAG** and ask the same policy question to contrast grounded retrieval vs structured tool chains.
