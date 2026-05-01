# PR: LiteLLM compatibility + budget errors (SSE + UI)

## Summary

This PR targets [`redis/context-engine-demos`](https://github.com/redis/context-engine-demos) **`main`**.

### Phase A (already on branch `litellm-compatibility`)

- **Optional `OPENAI_BASE_URL`** — Plumb through `Settings`, LangGraph agent, RAG service, ElectroHub domain, and frontend Vite config so demos can use any OpenAI-compatible endpoint (LiteLLM proxy, etc.). Default behavior unchanged when unset.
- **Cross-platform `make reset`** — Replace BSD/GNU-divergent `sed -i` with `perl -i -pe` for `.env` rewrites.

### Phase B — Surface LiteLLM `budget_exceeded` in SSE + UI

When LiteLLM returns HTTP 400 with `error.type == "budget_exceeded"`, the chat stream emits structured SSE and the UI shows a clear facilitator-facing message—not a generic failure or broken stream.

| Area | Change |
|------|--------|
| [`backend/app/openai_errors.py`](backend/app/openai_errors.py) | **`classify_openai_exception(exc)`** — Prefer `BadRequestError.body` (`error.type`), fallback substring `budget_exceeded` / `Budget has been exceeded`. |
| [`backend/app/main.py`](backend/app/main.py) | Wrap **`agent.astream_events`** (and post-loop verifier/final text) in **`try`/`except`**. On failure: **`type: error`** with **`errorCode`** + **`message`**, then always **`type: done`**. |
| [`backend/app/rag_service.py`](backend/app/rag_service.py) | Wrap **`_embed`** and **`chat.completions.create`** streaming path; same **`error`** contract before **`done`** (via outer `rag_event_stream`). |
| [`backend/app/sse.py`](backend/app/sse.py) | Document **`error`** / **`done`** in `format_sse_event` docstring. |
| [`frontend/src/App.tsx`](frontend/src/App.tsx) + [`frontend/src/styles.css`](frontend/src/styles.css) | Handle **`type === "error"`**; banner for **`budget_exceeded`**. Loading clears on **`done`** as before. |

### Model codegen / validation

- Regenerated **`domains/reddash/generated_models.py`** and **`domains/electrohub/generated_models.py`** so vector fields use lowercase **`distance_metric="cosine"`**, matching **`validate_entity_specs`** (`backend/app/core/domain_schema.py`).
- **`scripts/generate_models.py`** always emits **`distance_metric`** in lowercase to avoid manual edits drifting to invalid values (e.g. `COSINE`).

## SSE contract

- **`data: {"type":"error","errorCode":"budget_exceeded"|"openai_error","message":"...","ts":...}`**
- **`data: {"type":"done","totalElapsedMs":...}`** — Always sent after a normal stream **or** after **`error`** so the client always sees a terminal event.

## Test plan

- **Unit:** `uv run pytest tests/test_openai_errors.py`
- **Regression:** `uv run pytest tests/test_rag_service.py`
- **Manual (budget):** Exhausted virtual key or `max_budget: 0` — POST `/api/chat/stream`, confirm SSE sequence **`error`** → **`done`**, UI shows budget banner.
- **Manual (happy path):** Normal **`text-delta`** + **`done`** unchanged.

## Create / update PR (fork → upstream)

```bash
git push --force-with-lease origin litellm-compatibility

gh pr create \
  --repo redis/context-engine-demos \
  --base main \
  --head st8ofreality:litellm-compatibility \
  --title "LiteLLM: optional base URL, make reset portable, budget_exceeded in SSE + UI" \
  --body-file PR_DESCRIPTION.md
```

*(If the PR already exists, edit the description on GitHub or use `gh pr edit`.)*
