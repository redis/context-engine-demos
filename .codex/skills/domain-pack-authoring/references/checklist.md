# Domain Checklist

Use this checklist after scaffolding a domain.

## `domain.py`

- `manifest.id` matches the folder name
- `generated_models_module` and `generated_models_path` match the folder
- `output_dir` is `output/<domain-id>`
- namespace keys are unique
- branding includes at least one starter prompt

## `schema.py`

- every entity has a unique `class_name`
- every entity has a unique `file_name`
- Redis key templates use the domain namespace
- vector fields declare `vector_dim` and `distance_metric`

## `data_generator.py`

- writes all files declared by the schema
- returns `GeneratedDataset`
- updates demo identity env vars when the demo uses a signed-in user

## Validation Commands

```bash
uv run python scripts/validate_domain.py --domain <domain-id>
uv run python scripts/generate_models.py --domain <domain-id>
uv run python scripts/smoke_domain.py --domain <domain-id>
pytest
```
