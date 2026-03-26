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

## References

Read [references/checklist.md](references/checklist.md) when you need the exact file-by-file checklist.
