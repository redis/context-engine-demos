from __future__ import annotations

import json
from typing import Any

from context_surfaces import UnifiedClient

from backend.app.settings import Settings


def _default_array_items_schema(*, field_name: str | None = None, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    description = ""
    if isinstance(schema, dict):
        description = str(schema.get("description", ""))
    hint = " ".join(part for part in (field_name or "", description) if part).lower()
    if any(token in hint for token in ("embedding", "vector")):
        return {"type": "number"}
    return {}


def _sanitize_property_schema(name: str, schema: Any) -> Any:
    if isinstance(schema, list):
        return [_sanitize_property_schema(name, item) for item in schema]
    if not isinstance(schema, dict):
        return schema

    sanitized = dict(schema)
    schema_type = sanitized.get("type")

    if schema_type == "array":
        items = sanitized.get("items")
        if isinstance(items, dict):
            sanitized["items"] = _sanitize_property_schema(f"{name}_item", items)
        elif items is None:
            sanitized["items"] = _default_array_items_schema(field_name=name, schema=sanitized)

    properties = sanitized.get("properties")
    if isinstance(properties, dict):
        sanitized["properties"] = {
            prop_name: _sanitize_property_schema(prop_name, prop_schema)
            for prop_name, prop_schema in properties.items()
        }

    additional_properties = sanitized.get("additionalProperties")
    if isinstance(additional_properties, (dict, list)):
        sanitized["additionalProperties"] = _sanitize_property_schema(
            f"{name}_value",
            additional_properties,
        )

    for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
        value = sanitized.get(key)
        if isinstance(value, list):
            sanitized[key] = [_sanitize_property_schema(name, item) for item in value]

    negated = sanitized.get("not")
    if isinstance(negated, dict):
        sanitized["not"] = _sanitize_property_schema(name, negated)

    return sanitized


def _sanitize_tool_definition(tool_def: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(tool_def)
    input_schema = sanitized.get("inputSchema")
    if isinstance(input_schema, dict):
        sanitized["inputSchema"] = _sanitize_property_schema("input", input_schema)
    return sanitized


def _extract_wrapped_content_text(raw: str) -> str | None:
    start_marker = "content='"
    start = raw.find(start_marker)
    if start < 0:
        return None

    content_start = start + len(start_marker)
    value = ""

    for index in range(content_start, len(raw)):
        char = raw[index]
        previous = raw[index - 1] if index > content_start else ""

        if char == "'" and previous != "\\":
            return value

        value += char

    return None


def _parse_wrapped_content_json(raw: str) -> Any | None:
    wrapped = _extract_wrapped_content_text(raw)
    if wrapped is None:
        return None
    try:
        return json.loads(wrapped.replace("\\'", "'"))
    except json.JSONDecodeError:
        return None


def _normalize_tool_result_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        content = result.get("content", [])
        if content and isinstance(content, list) and content[0].get("type") == "text":
            text = content[0].get("text", "")
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = _parse_wrapped_content_json(text)
            if isinstance(parsed, dict):
                return parsed
            return {"raw_text": text}
        raw_text = result.get("raw_text")
        if isinstance(raw_text, str):
            parsed = _parse_wrapped_content_json(raw_text)
            if isinstance(parsed, dict):
                return parsed
        nested_result = result.get("result")
        if isinstance(nested_result, str):
            parsed = _parse_wrapped_content_json(nested_result)
            if isinstance(parsed, dict):
                return parsed
        return result

    if isinstance(result, str):
        parsed = _parse_wrapped_content_json(result)
        if isinstance(parsed, dict):
            return parsed
        try:
            loaded = json.loads(result)
        except json.JSONDecodeError:
            return {"result": result}
        return loaded if isinstance(loaded, dict) else {"result": loaded}

    parsed = _parse_wrapped_content_json(str(result))
    if isinstance(parsed, dict):
        return parsed
    return {"result": result}


class ContextSurfaceService:
    """Wraps the context-surfaces SDK to list and call MCP tools.

    Uses UnifiedClient which auto-resolves API/MCP URLs from built-in defaults
    (or CTX_API_URL / CTX_MCP_URL env vars if set).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._tool_cache: list[dict[str, Any]] | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.mcp_agent_key)

    async def list_tools(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        if self._tool_cache is not None:
            return self._tool_cache
        async with UnifiedClient() as client:
            tools = await client.list_tools(self.settings.mcp_agent_key)
        self._tool_cache = [
            _sanitize_tool_definition(t if isinstance(t, dict) else t.model_dump())
            for t in tools
        ]
        return self._tool_cache or []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with UnifiedClient() as client:
            result = await client.query_tool(
                agent_key=self.settings.mcp_agent_key,
                tool_name=tool_name,
                arguments=arguments,
            )
        return _normalize_tool_result_payload(result)
