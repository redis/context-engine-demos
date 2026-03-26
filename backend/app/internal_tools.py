"""Internal tools that run locally, defined by the active domain."""

from __future__ import annotations

from typing import Any

from backend.app.core.domain_contract import InternalToolDefinition
from backend.app.core.domain_loader import get_active_domain
from backend.app.settings import Settings


def domain_runtime_config(domain: Any, settings: Settings) -> dict[str, Any]:
    getter = getattr(domain, "get_runtime_config", None)
    if callable(getter):
        return dict(getter(settings=settings) or {})
    return {}


def internal_tool_names(settings: Settings) -> list[str]:
    domain = get_active_domain(settings)
    runtime_config = domain_runtime_config(domain, settings)
    return [tool.name for tool in domain.get_internal_tool_definitions(runtime_config=runtime_config)]


class InternalToolService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.domain = get_active_domain(settings)

    @property
    def definitions(self) -> tuple[InternalToolDefinition, ...]:
        runtime_config = domain_runtime_config(self.domain, self.settings)
        return tuple(self.domain.get_internal_tool_definitions(runtime_config=runtime_config))

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.domain.execute_internal_tool(tool_name, arguments, self.settings)
