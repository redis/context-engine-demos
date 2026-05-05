---
name: domain-pack-authoring
description: Use when creating, validating, or extending demo business domains in this repo. Covers the required DomainPack contract, fixed folder layout, scaffold command, validation flow, smoke testing, and the rules for keeping framework code separate from domain-specific code.
---

# Domain Pack Authoring

Use this skill when the task is to add a new business domain, refactor an existing domain pack, or check that a domain follows the repo contract.

## Workflow

1. Run `uv run python scripts/create_domain.py <domain-id>` unless the domain already exists.
2. Edit only files under `domains/<domain-id>/` unless the task explicitly changes shared framework code.
3. Fill in the required domain contract in `domains/<domain-id>/domain.py`.
4. Define entity specs in `domains/<domain-id>/schema.py`.
5. Implement prompt guidance in `domains/<domain-id>/prompt.py`.
6. Implement domain demo-data generation in `domains/<domain-id>/data_generator.py`.
7. Add or update scripted demo paths in `domains/<domain-id>/docs/demo_paths.md`.
8. If the domain includes presentation material, keep it under `domains/<domain-id>/presentations/`.
9. Run validation and smoke tests:
   `uv run python scripts/validate_domain.py --domain <domain-id>`
   `uv run python scripts/generate_models.py --domain <domain-id>`
   `uv run python scripts/smoke_domain.py --domain <domain-id>`
10. If shared framework changes were required, run repo tests before finishing.

## Required Layout

Every domain must use this structure:

```text
domains/<domain-id>/
  __init__.py
  domain.py
  schema.py
  prompt.py
  data_generator.py
  assets/logo.<svg|png|jpg|jpeg|webp>
  docs/demo_paths.md
```

Generated files:

```text
domains/<domain-id>/generated_models.py
output/<domain-id>/
```

Optional docs and collateral:

```text
domains/<domain-id>/presentations/
```

## Contract Rules

- `domains/<domain-id>/domain.py` must export `DOMAIN`.
- `DOMAIN` must satisfy the shared contract in `backend/app/core/domain_contract.py`.
- Keep branding, namespace, RAG config, and identity config declarative in `manifest`.
- `manifest.branding.logo_path` may point to any supported image asset under `domains/<domain-id>/assets/`.
- Keep code hooks limited to:
  - `build_system_prompt`
  - `get_internal_tool_definitions`
  - `execute_internal_tool`
  - `write_dataset_meta`
  - `generate_demo_data`
  - `validate`

## Internal Tools

Every domain **must** register at least these internal tools in `get_internal_tool_definitions`:

1. **`get_current_user_profile`** — returns the signed-in user's identity (ID, name, email). Uses `manifest.identity` for env var names, defaults, and `id_field`. Set `identity.id_field` to the domain-appropriate field name (e.g. `"patient_id"`, `"customer_id"`).
2. **`get_current_time`** — returns the current UTC timestamp in ISO 8601. The agent needs this to compare against dates in the data.
3. **`dataset_overview`** — returns record counts per entity. Useful for the agent to understand the data scope.

`execute_internal_tool` must handle all three tool names and return dicts.

## Prompt Rules

The system prompt built by `prompt.py` must include:

- A hint that all `filter_*` and `search_*` MCP tools take a single **`value`** parameter (a string). Without this, the LLM may pass the field name as the parameter key (e.g. `patient_id="P001"` instead of `value="P001"`), which the MCP server rejects silently.
- Tool discovery hints mapping tool names to descriptions for the tools present in `mcp_tools`.
- Common workflows showing the sequence of tool calls for each demo scenario.
- A rule to call `get_current_user_profile` first for any user-specific question.

## Data Generation Rules

- `generate_demo_data` defaults to `update_env_file=False`. Only the `scripts/generate_data.py` pipeline and direct `main()` invocation should pass `update_env_file=True`.
- If the domain has a `main()` guard at the bottom of `data_generator.py`, it must pass `update_env_file=True` explicitly.

## Quality Bar

- Seed the domain with at least one flagship demo user and enough data to support 2-3 realistic conversation paths.
- Make starter prompts correspond to real records in the generated dataset.
- Keep the prompt focused on tool-use workflows, not generic brand copy.
- Document the flagship paths in `docs/demo_paths.md` so an agent or human can run the demo consistently.
- If you build a deck for the domain, keep links, assets, and README notes inside `domains/<domain-id>/presentations/`.

## Separation Rules

- Do not hard-code domain strings in `backend/app/*` or `frontend/src/*`.
- Do not add domain-specific scripts under `scripts/`; extend the generic scripts instead.
- Do not put generated models under `backend/app/context_surfaces/`; keep them inside the domain package.
- If a new requirement seems domain-specific, prefer adding it to the domain contract before touching shared runtime code.

## Stop Conditions

Do not consider the task complete if any of these remain:

- placeholder prompts
- empty `ENTITY_SPECS`
- missing logo asset
- `validate_domain.py` fails
- `smoke_domain.py` fails
- `get_internal_tool_definitions` returns an empty tuple
- system prompt is missing the `value` parameter hint for MCP tools
- `generate_demo_data` still defaults `update_env_file=True`
- generated models use `Any` as relationship type annotations (run `make generate-models DOMAIN=<id>` to regenerate)

## References

Read [references/checklist.md](references/checklist.md) when you need the exact file-by-file checklist.
