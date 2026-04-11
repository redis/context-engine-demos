from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_hint: str
    description: str
    index: str | None = None
    weight: float | None = None
    no_stem: bool = False
    sortable: bool = False
    is_key_component: bool = False
    default_factory: str | None = None
    vector_dim: int | None = None
    distance_metric: str | None = None


@dataclass(frozen=True)
class RelationshipSpec:
    name: str
    description: str
    source_field: str


@dataclass(frozen=True)
class EntitySpec:
    class_name: str
    redis_key_template: str
    file_name: str
    id_field: str
    fields: tuple[FieldSpec, ...]
    relationships: tuple[RelationshipSpec, ...] = field(default_factory=tuple)


def entity_by_file(entity_specs: tuple[EntitySpec, ...]) -> dict[str, EntitySpec]:
    return {spec.file_name: spec for spec in entity_specs}


def entity_by_class(entity_specs: tuple[EntitySpec, ...]) -> dict[str, EntitySpec]:
    return {spec.class_name: spec for spec in entity_specs}


def _base_type_name(type_hint: str) -> str:
    cleaned = type_hint.strip()
    if "|" in cleaned:
        cleaned = cleaned.split("|", 1)[0].strip()
    return cleaned.removeprefix("Optional[").removesuffix("]")


def _is_numeric_type(type_hint: str) -> bool:
    return _base_type_name(type_hint) in {"int", "float"}


def validate_entity_specs(entity_specs: tuple[EntitySpec, ...]) -> list[str]:
    errors: list[str] = []
    seen_classes: set[str] = set()
    seen_files: set[str] = set()

    for spec in entity_specs:
        if spec.class_name in seen_classes:
            errors.append(f"Duplicate entity class name: {spec.class_name}")
        if spec.file_name in seen_files:
            errors.append(f"Duplicate entity file name: {spec.file_name}")
        seen_classes.add(spec.class_name)
        seen_files.add(spec.file_name)

        for field_spec in spec.fields:
            if field_spec.index == "tag" and _is_numeric_type(field_spec.type_hint):
                errors.append(
                    "Invalid RediSearch mapping: "
                    f"{spec.class_name}.{field_spec.name} uses type '{field_spec.type_hint}' "
                    "with index='tag'. Numeric JSON values are not indexed by TAG fields; "
                    "use type 'str' for identifiers or index='numeric'."
                )

    return errors


def validate_exported_data_model(data_model: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    entities = data_model.get("entities", [])
    if not isinstance(entities, list):
        return ["Exported data model must contain an 'entities' list."]

    for entity in entities:
        if not isinstance(entity, dict):
            continue
        entity_name = str(entity.get("name", "<unknown entity>"))
        fields = entity.get("fields", [])
        if not isinstance(fields, list):
            continue

        for field in fields:
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "<unknown field>"))
            field_type = str(field.get("type", ""))
            redis_indices = field.get("redis_indices", [])
            if not isinstance(redis_indices, list):
                continue

            for index in redis_indices:
                if not isinstance(index, dict):
                    continue
                if index.get("type") == "tag" and _is_numeric_type(field_type):
                    errors.append(
                        "Invalid exported data model: "
                        f"{entity_name}.{field_name} uses type '{field_type}' with TAG index. "
                        "Redis JSON TAG fields cannot index numeric values; use a string field "
                        "or a NUMERIC index instead."
                    )

    return errors
