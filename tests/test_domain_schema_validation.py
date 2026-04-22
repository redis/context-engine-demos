from backend.app.core.domain_schema import (
    EntitySpec,
    FieldSpec,
    RelationshipSpec,
    validate_entity_specs,
    validate_exported_data_model,
)


def test_validate_entity_specs_rejects_numeric_tag_fields() -> None:
    entity_specs = (
        EntitySpec(
            class_name="Order",
            redis_key_template="order:{id}",
            file_name="orders.jsonl",
            id_field="id",
            fields=(
                FieldSpec("id", "int", "Order ID", is_key_component=True),
                FieldSpec("customer_id", "int", "Customer identifier", index="tag"),
            ),
        ),
    )

    errors = validate_entity_specs(entity_specs)

    assert len(errors) == 1
    assert "Order.customer_id" in errors[0]
    assert "index='tag'" in errors[0]


def test_validate_exported_data_model_rejects_numeric_tag_fields() -> None:
    data_model = {
        "title": "Broken model",
        "description": "Reproduces a TAG vs numeric mismatch",
        "entities": [
            {
                "name": "Order",
                "fields": [
                    {
                        "name": "customer_id",
                        "type": "int",
                        "redis_indices": [{"type": "tag"}],
                    },
                ],
                "relationships": [],
            },
        ],
    }

    errors = validate_exported_data_model(data_model)

    assert len(errors) == 1
    assert "Order.customer_id" in errors[0]
    assert "TAG index" in errors[0]


def test_validate_entity_specs_rejects_unknown_relationship_targets() -> None:
    entity_specs = (
        EntitySpec(
            class_name="Order",
            redis_key_template="order:{id}",
            file_name="orders.jsonl",
            id_field="id",
            fields=(
                FieldSpec("id", "str", "Order ID", is_key_component=True),
                FieldSpec("customer_id", "str", "Customer identifier", index="tag"),
            ),
            relationships=(
                RelationshipSpec("customer", "Customer on the order", "customer_id", "UnknownEntity"),
            ),
        ),
    )

    errors = validate_entity_specs(entity_specs)

    assert len(errors) == 1
    assert "Order.customer" in errors[0]
    assert "UnknownEntity" in errors[0]


def test_validate_entity_specs_rejects_invalid_vector_distance_metrics() -> None:
    entity_specs = (
        EntitySpec(
            class_name="Guide",
            redis_key_template="guide:{id}",
            file_name="guides.jsonl",
            id_field="id",
            fields=(
                FieldSpec("id", "str", "Guide ID", is_key_component=True),
                FieldSpec(
                    "content_embedding",
                    "list[float]",
                    "Embedding vector",
                    index="vector",
                    vector_dim=1536,
                    distance_metric="COSINE",
                ),
            ),
        ),
    )

    errors = validate_entity_specs(entity_specs)

    assert len(errors) == 1
    assert "Guide.content_embedding" in errors[0]
    assert "cosine" in errors[0]
