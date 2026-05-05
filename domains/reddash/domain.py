from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from backend.app.core.domain_contract import (
    BrandingConfig,
    DomainManifest,
    GeneratedDataset,
    IdentityConfig,
    InternalToolDefinition,
    NamespaceConfig,
    PromptCard,
    RagConfig,
    ThemeConfig,
)
from backend.app.core.domain_schema import EntitySpec, validate_entity_specs
from backend.app.redis_connection import create_redis_client
from domains.reddash.data_generator import generate_demo_data
from domains.reddash.prompt import build_system_prompt
from domains.reddash.schema import ENTITY_SPECS

ROOT = Path(__file__).resolve().parents[2]


class ReddashDomain:
    manifest = DomainManifest(
        id="reddash",
        description="Food-delivery support demo comparing Context Surfaces vs simple RAG.",
        generated_models_module="domains.reddash.generated_models",
        generated_models_path="domains/reddash/generated_models.py",
        output_dir="output/reddash",
        branding=BrandingConfig(
            app_name="Reddash",
            subtitle="Delivery Support",
            hero_title="How can we help?",
            placeholder_text="Ask about your order, delivery status, or policies...",
            logo_path="domains/reddash/assets/logo.svg",
            starter_prompts=[
                PromptCard(eyebrow="Order Status", title="Why is my order running late?", prompt="Why is my order running late?"),
                PromptCard(eyebrow="Order History", title="Show me my recent orders", prompt="Show me my order history"),
                PromptCard(eyebrow="Policy", title="What's your refund policy for late deliveries?", prompt="What is your refund policy for late deliveries?"),
                PromptCard(eyebrow="Search", title="Find me a good sushi restaurant", prompt="Can you find me a good sushi restaurant?"),
            ],
            theme=ThemeConfig(
                bg="#0d0f14",
                bg_accent_a="rgba(255, 68, 56, 0.12)",
                bg_accent_b="rgba(255, 140, 66, 0.1)",
                panel="rgba(20, 23, 32, 0.88)",
                panel_strong="rgba(24, 28, 40, 0.96)",
                panel_elevated="rgba(30, 35, 50, 0.92)",
                line="rgba(255, 120, 90, 0.1)",
                line_strong="rgba(255, 120, 90, 0.18)",
                text="#f2f0ed",
                muted="#9a9490",
                soft="#d4cfc8",
                accent="#ff4438",
                user="#2a2420",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="reddash",
            dataset_meta_key="reddash:meta:dataset",
            checkpoint_prefix="reddash:checkpoint",
            checkpoint_write_prefix="reddash:checkpoint_write",
            redis_instance_name="Reddash Redis Cloud",
            surface_name="Reddash Delivery Surface",
            agent_name="Reddash Delivery Agent",
        ),
        rag=RagConfig(
            tool_name="vector_search_policies",
            status_text="Searching policies via vector similarity…",
            generating_text="Generating answer…",
            index_name_contains="policy",
            vector_field="content_embedding",
            return_fields=["title", "category", "content", "policy_id"],
            num_results=3,
            answer_system_prompt=(
                "You are the Reddash delivery-support assistant. "
                "Answer using only the policy documents below. If the policies do not cover the "
                "question, say so. Be concise and helpful."
            ),
        ),
        identity=IdentityConfig(
            default_id="CUST_DEMO_001",
            default_name="Alex Rivera",
            default_email="alex.rivera@example.com",
            description=(
                "Returns the signed-in customer's ID, name, and email. "
                "Call this whenever the user asks about their orders, account, or history."
            ),
        ),
    )

    def get_entity_specs(self) -> tuple[EntitySpec, ...]:
        return ENTITY_SPECS

    def build_system_prompt(
        self,
        *,
        mcp_tools: Sequence[dict[str, Any]],
        runtime_config: dict[str, Any] | None = None,
    ) -> str:
        del runtime_config
        return build_system_prompt(mcp_tools=mcp_tools)

    def build_answer_verifier_prompt(self, *, runtime_config: dict[str, Any] | None = None) -> str:
        del runtime_config
        return (
            "When the user refers to 'that order', 'that charge', or similar follow-ups, resolve the reference to the exact "
            "order, payment, or ticket from the prior turn. Do not mention refunds, credits, or policy outcomes unless the "
            "tool results or cited policy support them."
        )

    def describe_tool_trace_step(
        self,
        *,
        tool_name: str,
        payload: Any,
        runtime_config: dict[str, Any] | None = None,
    ) -> str | None:
        del runtime_config
        detail = ""
        if isinstance(payload, dict):
            for key in ("query", "text", "order_id", "customer_id", "payment_id", "ticket_id"):
                value = payload.get(key)
                if value:
                    detail = str(value)
                    break

        if tool_name == self.manifest.identity.tool_name:
            return "Identify the signed-in customer before checking account or order data."
        if tool_name == "get_current_time":
            return "Compare the current time against order and delivery timestamps."
        if tool_name.startswith("search_policy_by_text"):
            return f"Search delivery policy guidance: {detail or 'policy search'}."
        if tool_name.startswith("filter_driver_by_"):
            return "Check the live driver assignment and status for the relevant order."
        if tool_name.startswith("filter_payment_by_"):
            return "Inspect the payment record before answering charges, credits, or refunds."
        return None

    def get_internal_tool_definitions(
        self,
        *,
        runtime_config: dict[str, Any] | None = None,
    ) -> Sequence[InternalToolDefinition]:
        del runtime_config
        return (
            InternalToolDefinition(
                name=self.manifest.identity.tool_name,
                description=self.manifest.identity.description,
            ),
            InternalToolDefinition(
                name="get_current_time",
                description=(
                    "Returns the current date and time in UTC (ISO 8601). "
                    "Use this to compare against order timestamps and determine if a delivery is late."
                ),
            ),
            InternalToolDefinition(
                name="dataset_overview",
                description="Returns a summary of the current Reddash dataset: counts of customers, restaurants, orders, and policies.",
            ),
        )

    def execute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        from datetime import datetime, timezone
        import os

        if tool_name == self.manifest.identity.tool_name:
            identity = self.manifest.identity
            return {
                identity.id_field: os.getenv(identity.id_env_var, identity.default_id),
                "name": os.getenv(identity.name_env_var, identity.default_name),
                "email": os.getenv(identity.email_env_var, identity.default_email),
            }
        if tool_name == "get_current_time":
            now = datetime.now(timezone.utc)
            return {"current_time": now.isoformat(), "timezone": "UTC"}
        if tool_name == "dataset_overview":
            client = create_redis_client(settings)
            raw = client.execute_command("JSON.GET", self.manifest.namespace.dataset_meta_key, "$")
            if raw:
                data = json.loads(raw)
                return data[0] if isinstance(data, list) else data
            return {"error": "Dataset metadata not found. Run the data loader first."}
        return {"error": f"Unknown tool: {tool_name}"}

    def write_dataset_meta(self, *, settings: Any, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        summary = {
            "customers": len(records.get("Customer", [])),
            "restaurants": len(records.get("Restaurant", [])),
            "drivers": len(records.get("Driver", [])),
            "orders": len(records.get("Order", [])),
            "order_items": len(records.get("OrderItem", [])),
            "delivery_events": len(records.get("DeliveryEvent", [])),
            "payments": len(records.get("Payment", [])),
            "support_tickets": len(records.get("SupportTicket", [])),
            "policies": len(records.get("Policy", [])),
        }
        client = create_redis_client(settings)
        client.execute_command(
            "JSON.SET",
            self.manifest.namespace.dataset_meta_key,
            "$",
            json.dumps(summary, ensure_ascii=False),
        )
        return summary

    def generate_demo_data(
        self,
        *,
        output_dir: Path,
        seed: int | None = None,
        update_env_file: bool = False,
    ) -> GeneratedDataset:
        return generate_demo_data(output_dir=output_dir, seed=seed, update_env_file=update_env_file)

    def validate(self) -> list[str]:
        errors = validate_entity_specs(self.get_entity_specs())
        if not (ROOT / self.manifest.branding.logo_path).exists():
            errors.append(f"Logo file not found: {self.manifest.branding.logo_path}")
        if not self.manifest.branding.starter_prompts:
            errors.append("Branding must define at least one starter prompt")
        return errors


DOMAIN = ReddashDomain()
