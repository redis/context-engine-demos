# Domain Checklist

Use this checklist after scaffolding a domain.

## `domain.py`

- `manifest.id` matches the folder name
- `generated_models_module` and `generated_models_path` match the folder
- `output_dir` is `output/<domain-id>`
- namespace keys are unique
- `logo_path` points to a real asset under `domains/<domain-id>/assets/`
- branding includes at least one starter prompt
- identity defaults line up with the generated demo user

## `schema.py`

- every entity has a unique `class_name`
- every entity has a unique `file_name`
- Redis key templates use the domain namespace
- vector fields declare `vector_dim` and `distance_metric`

## `data_generator.py`

- writes all files declared by the schema
- returns `GeneratedDataset`
- updates demo identity env vars when the demo uses a signed-in user
- creates records that support the documented flagship demo paths

## `docs/demo_paths.md`

- includes at least two realistic conversation paths
- references real products, stores, orders, or policies from the generated data

## `presentations/` (optional)

- any domain-specific deck lives under `domains/<domain-id>/presentations/`
- deck assets are copied into the domain folder instead of referencing files from `~/Desktop`, `~/Downloads`, or another repo
- a short local run note exists if the presentation needs a static server

## Validation Commands

```bash
uv run python scripts/validate_domain.py --domain <domain-id>
uv run python scripts/generate_models.py --domain <domain-id>
uv run python scripts/smoke_domain.py --domain <domain-id>
pytest
```
