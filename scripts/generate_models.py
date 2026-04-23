"""Generate ContextModel classes for a domain pack."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import load_domain
from backend.app.core.domain_schema import FieldSpec


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


def _build_target_resolver(domain: object) -> dict[str, str]:
    """Build a mapping from lowercase name -> class_name for relationship target resolution.

    Maps both singular and plural forms of entity class names so that
    relationship names like "orders", "customer", "primary_provider",
    or "referring_provider" can be resolved to entity class names.
    """
    mapping: dict[str, str] = {}
    for entity in domain.get_entity_specs():
        lower = entity.class_name.lower()
        mapping[lower] = entity.class_name
        # Simple plural: "order" -> "orders"
        mapping[lower + "s"] = entity.class_name
        mapping[lower + "es"] = entity.class_name
        # Handle "ies" plural (e.g. "inventory" -> "inventories")
        if lower.endswith("y"):
            mapping[lower[:-1] + "ies"] = entity.class_name
    return mapping


def _resolve_target(rel_name: str, resolver: dict[str, str], fallback: str) -> str:
    """Resolve a relationship name to a target entity class name.

    Tries the full name first (with and without underscores), then
    progressively strips leading underscore-delimited prefixes
    (e.g. "referring_provider" -> "provider").
    """
    lower = rel_name.lower()
    # Try with underscores removed (e.g. "support_cases" -> "supportcases")
    collapsed = lower.replace("_", "")
    for candidate in (lower, collapsed):
        if candidate in resolver:
            return resolver[candidate]
    # Strip leading prefixes
    parts = lower.split("_")
    for i in range(1, len(parts)):
        candidate = "_".join(parts[i:])
        collapsed = candidate.replace("_", "")
        for c in (candidate, collapsed):
            if c in resolver:
                return resolver[c]
    return fallback


def render(domain_id: str) -> str:
    domain = load_domain(domain_id)
    resolver = _build_target_resolver(domain)

    chunks = [
        f'"""Generated Context Surface models for the {domain.manifest.branding.app_name} domain."""',
        "",
        "from __future__ import annotations",
        "",
        "from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship",
        "",
        "",
    ]

    for entity in domain.get_entity_specs():
        chunks.append(f"class {entity.class_name}(ContextModel):")
        chunks.append(f'    """{entity.class_name} entity for the {domain.manifest.branding.app_name} domain."""')
        chunks.append("")
        chunks.append(f'    __redis_key_template__ = "{entity.redis_key_template}"')
        chunks.append("")
        for field in entity.fields:
            chunks.append(render_field(field))
            chunks.append("")
        for rel in entity.relationships:
            target_class = _resolve_target(rel.name, resolver, entity.class_name)
            chunks.append(
                "\n".join([
                    f"    {rel.name}: {target_class} = ContextRelationship(",
                    f'        description="{rel.description}",',
                    f'        source_field="{rel.source_field}",',
                    "    )",
                ])
            )
            chunks.append("")
        chunks.append("")

    return "\n".join(chunks).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="reddash")
    args = parser.parse_args()

    domain = load_domain(args.domain)
    output_path = ROOT / domain.manifest.generated_models_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(args.domain))
    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
