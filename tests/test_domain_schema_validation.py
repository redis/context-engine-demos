from backend.app.core.domain_schema import (
    EntitySpec,
    FieldSpec,
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
