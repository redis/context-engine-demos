from __future__ import annotations

import json
from typing import Any

from context_surfaces import UnifiedClient

from backend.app.settings import Settings


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
        self._tool_cache = [t if isinstance(t, dict) else t.model_dump() for t in tools]
        return self._tool_cache or []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with UnifiedClient() as client:
            result = await client.query_tool(
                agent_key=self.settings.mcp_agent_key,
                tool_name=tool_name,
                arguments=arguments,
            )
        if isinstance(result, dict):
            content = result.get("content", [])
            if content and isinstance(content, list) and content[0].get("type") == "text":
                text = content[0].get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw_text": text}
        return result if isinstance(result, dict) else {"result": result}

