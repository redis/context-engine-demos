from __future__ import annotations

from dataclasses import dataclass, field


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

