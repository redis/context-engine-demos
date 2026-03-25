"""Internal tools that run locally (not via MCP)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.app.demo_identity import get_current_user
from backend.app.redis_connection import create_redis_client
from backend.app.settings import Settings


@dataclass(frozen=True)
class InternalToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


INTERNAL_TOOL_DEFINITIONS: tuple[InternalToolDefinition, ...] = (
    InternalToolDefinition(
        name="get_current_user_id",
        description=(
            "Returns the customer_id, name, and email of the currently signed-in demo user. "
            "Call this whenever the user says 'my orders', 'my account', etc."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
    ),
    InternalToolDefinition(
        name="get_current_time",
        description=(
            "Returns the current date and time in UTC (ISO 8601). "
            "All order timestamps (placed_at, estimated_delivery, delivered_at) are in UTC. "
            "Use this to compare against order times and determine if a delivery is late."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
    ),
    InternalToolDefinition(
        name="dataset_overview",
        description="Returns a summary of the Reddish dataset: counts of customers, restaurants, orders, and policies.",
        input_schema={"type": "object", "properties": {}, "required": []},
    ),
)


def internal_tool_names() -> list[str]:
    return [t.name for t in INTERNAL_TOOL_DEFINITIONS]


class InternalToolService:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def definitions(self) -> tuple[InternalToolDefinition, ...]:
        return INTERNAL_TOOL_DEFINITIONS

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "get_current_user_id":
            return get_current_user()
        if tool_name == "get_current_time":
            now = datetime.now(timezone.utc)
            return {"current_time": now.isoformat(), "timezone": "UTC"}
        if tool_name == "dataset_overview":
            return self._dataset_overview()
        return {"error": f"Unknown tool: {tool_name}"}

    def _dataset_overview(self) -> dict[str, Any]:
        try:
            client = create_redis_client(self.settings)
            raw = client.execute_command("JSON.GET", "reddash:meta:dataset", "$")
            if raw:
                data = json.loads(raw)
                return data[0] if isinstance(data, list) else data
        except Exception:
            pass
        return {"error": "Dataset metadata not found. Run 'make load-data' first."}

