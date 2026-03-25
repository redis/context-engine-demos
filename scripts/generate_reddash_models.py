"""Generate ContextModel classes from the Reddish EntitySpec definitions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schemas.reddash_schema import ENTITY_SPECS, FieldSpec  # noqa: E402

OUTPUT_PATH = ROOT / "backend/app/context_surfaces/reddash_models.py"


def render_field(field: FieldSpec) -> str:
    lines = [
        f"    {field.name}: {field.type_hint} = ContextField(",
        f'        description="{field.description}",',
    ]
    if field.is_key_component:
        lines.append("        is_key_component=True,")
    if field.index:
        lines.append(f'        index="{field.index}",')
    if field.weight is not None:
        lines.append(f"        weight={field.weight},")
    if field.no_stem:
        lines.append("        no_stem=True,")
    if field.sortable:
        lines.append("        sortable=True,")
    if field.default_factory:
        lines.append(f"        default_factory={field.default_factory},")
    if field.vector_dim is not None:
        lines.append(f"        vector_dim={field.vector_dim},")
    if field.distance_metric is not None:
        lines.append(f'        distance_metric="{field.distance_metric}",')
    lines.append("    )")
    return "\n".join(lines)


def render() -> str:
    chunks = [
        '"""Generated Reddish data models for the food-delivery demo."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship",
        "",
        "",
    ]

    for entity in ENTITY_SPECS:
        chunks.append(f"class {entity.class_name}(ContextModel):")
        chunks.append(f'    """{entity.class_name} entity for the Reddish delivery demo."""')
        chunks.append("")
        chunks.append(f'    __redis_key_template__ = "{entity.redis_key_template}"')
        chunks.append("")
        for field in entity.fields:
            chunks.append(render_field(field))
            chunks.append("")
        for rel in entity.relationships:
            chunks.append(
                "\n".join([
                    f"    {rel.name}: Any = ContextRelationship(",
                    f'        description="{rel.description}",',
                    f'        source_field="{rel.source_field}",',
                    "    )",
                ])
            )
            chunks.append("")
        chunks.append("")

    return "\n".join(chunks).rstrip() + "\n"


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render())
    print(f"Generated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

