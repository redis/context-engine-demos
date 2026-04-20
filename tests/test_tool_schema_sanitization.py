from backend.app.context_surface_service import _sanitize_tool_definition
from backend.app.langgraph_agent import _pydantic_model_from_json_schema


def test_sanitize_tool_definition_adds_array_items_for_vector_search() -> None:
    tool_def = {
        "name": "search_policy_by_content_embedding_similarity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vector": {
                    "type": "array",
                    "description": "The content_embedding vector to search for",
                },
                "k": {
                    "type": "number",
                },
            },
            "required": ["vector"],
        },
    }

    sanitized = _sanitize_tool_definition(tool_def)

    assert sanitized["inputSchema"]["properties"]["vector"]["items"] == {"type": "number"}


def test_pydantic_model_from_json_schema_preserves_array_inputs() -> None:
    schema = {
        "type": "object",
        "properties": {
            "vector": {
                "type": "array",
                "description": "Embedding values",
                "items": {"type": "number"},
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["vector"],
    }

    model = _pydantic_model_from_json_schema("VectorSearch", schema)
    parsed = model(vector=[0.1, 0.2], tags=["a", "b"])

    assert parsed.vector == [0.1, 0.2]
    assert parsed.tags == ["a", "b"]


def test_pydantic_model_from_json_schema_emits_items_for_composed_array_inputs() -> None:
    schema = {
        "type": "object",
        "properties": {
            "vector": {
                "anyOf": [
                    {
                        "type": "array",
                        "description": "The content_embedding vector to search for",
                        "items": {"type": "number"},
                    },
                    {
                        "type": "null",
                    },
                ],
            },
        },
        "required": ["vector"],
    }

    model = _pydantic_model_from_json_schema("VectorSearchComposed", schema)
    emitted = model.model_json_schema()

    assert emitted["properties"]["vector"]["type"] == "array"
    assert emitted["properties"]["vector"]["items"] == {"type": "number"}


def test_sanitize_tool_definition_preserves_field_name_through_composition_keywords() -> None:
    tool_def = {
        "name": "search_policy_by_content_embedding_similarity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vector": {
                    "anyOf": [
                        {
                            "type": "array",
                            "description": "The content_embedding vector to search for",
                        },
                        {
                            "type": "null",
                        },
                    ],
                },
            },
            "required": ["vector"],
        },
    }

    sanitized = _sanitize_tool_definition(tool_def)

    assert sanitized["inputSchema"]["properties"]["vector"]["anyOf"][0]["items"] == {
        "type": "number"
    }
