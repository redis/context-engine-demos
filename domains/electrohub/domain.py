from __future__ import annotations

import json
import os
from datetime import datetime, timezone
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
from domains.electrohub.data_generator import DEMO_CUSTOMER, generate_demo_data
from domains.electrohub.prompt import build_system_prompt
from domains.electrohub.schema import ENTITY_SPECS

ROOT = Path(__file__).resolve().parents[2]


def _env_bool(*names: str, default: bool = False) -> bool:
    for name in names:
        raw = os.getenv(name)
        if raw is not None:
            return raw.strip().lower() in {"1", "true", "yes", "on"}
    return default


class ElectrohubDomain:
    manifest = DomainManifest(
        id="electrohub",
        description="Electronics retail support demo for product discovery, local pickup, and shipment tracking.",
        generated_models_module="domains.electrohub.generated_models",
        generated_models_path="domains/electrohub/generated_models.py",
        output_dir="output/electrohub",
        branding=BrandingConfig(
            app_name="ElectroHub",
            subtitle="Electronics Concierge",
            hero_title="Shop hardware, pickup, and order support in one place.",
            placeholder_text="Ask about products, store pickup, or your shipment...",
            logo_path="domains/electrohub/assets/logo.png",
            starter_prompts=[
                PromptCard(
                    eyebrow="Product Fit",
                    title="Find me something for OpenClaw",
                    prompt="I am looking for a MacMini to run OpenClaw on, what machines do you have in stock that would help?",
                ),
                PromptCard(
                    eyebrow="Local Pickup",
                    title="Check my local store",
                    prompt="Can I pick that up at my local store?",
                ),
                PromptCard(
                    eyebrow="Shipment Help",
                    title="Track my missing shipment",
                    prompt="I haven't received my shipment yet.",
                ),
                PromptCard(
                    eyebrow="Order History",
                    title="Show my recent orders",
                    prompt="Show me my recent ElectroHub orders.",
                ),
            ],
            theme=ThemeConfig(
                bg="#09111d",
                bg_accent_a="rgba(17, 86, 172, 0.30)",
                bg_accent_b="rgba(0, 188, 255, 0.16)",
                panel="rgba(10, 20, 34, 0.90)",
                panel_strong="rgba(8, 17, 29, 0.97)",
                panel_elevated="rgba(14, 27, 45, 0.96)",
                line="rgba(74, 150, 255, 0.12)",
                line_strong="rgba(74, 150, 255, 0.24)",
                text="#f2f7ff",
                muted="#91a3bd",
                soft="#d5e5fb",
                accent="#31c7ff",
                user="#12345b",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="electrohub",
            dataset_meta_key="electrohub:meta:dataset",
            checkpoint_prefix="electrohub:checkpoint",
            checkpoint_write_prefix="electrohub:checkpoint_write",
            redis_instance_name="ElectroHub Redis Cloud",
            surface_name="ElectroHub Commerce Surface",
            agent_name="ElectroHub Commerce Agent",
        ),
        rag=RagConfig(
            tool_name="vector_search_buying_guides",
            status_text="Searching buying guides and retail policies…",
            generating_text="Generating answer…",
            index_name_contains="guide",
            vector_field="content_embedding",
            return_fields=["title", "category", "content"],
            num_results=3,
            answer_system_prompt=(
                "You are the ElectroHub retail assistant. Answer using only the provided guides and policies. "
                "If the guides do not contain the answer, say so plainly."
            ),
        ),
        identity=IdentityConfig(
            id_field="customer_id",
            default_id=DEMO_CUSTOMER["customer_id"],
            default_name=DEMO_CUSTOMER["name"],
            default_email=DEMO_CUSTOMER["email"],
            description=(
                "Returns the signed-in customer's profile, including loyalty tier and preferred local store. "
                "Call this first for account, pickup, shipment, or order-history questions."
            ),
        ),
    )

    def get_entity_specs(self) -> tuple[EntitySpec, ...]:
        return ENTITY_SPECS

    def get_runtime_config(self, *, settings: Any) -> dict[str, Any]:
        del settings
        return {
            "enable_shopping_analyzer": _env_bool(
                "ELECTROHUB_ENABLE_SHOPPING_ANALYZER",
                "ENABLE_DOMAIN_SHOPPING_ANALYZER",
                default=False,
            ),
            "enable_post_model_verifier": _env_bool(
                "ELECTROHUB_ENABLE_POST_MODEL_VERIFIER",
                "ENABLE_POST_MODEL_VERIFIER",
                default=False,
            ),
            "show_search_translation_trace_step": _env_bool(
                "ELECTROHUB_SHOW_SEARCH_TRANSLATION_TRACE_STEP",
                "SHOW_ELECTROHUB_SEARCH_TRANSLATION_STEP",
                default=False,
            ),
        }

    def build_system_prompt(
        self,
        *,
        mcp_tools: Sequence[dict[str, Any]],
        runtime_config: dict[str, Any] | None = None,
    ) -> str:
        return build_system_prompt(
            mcp_tools=mcp_tools,
            shopping_analyzer_enabled=bool((runtime_config or {}).get("enable_shopping_analyzer", False)),
        )

    def build_answer_verifier_prompt(self, *, runtime_config: dict[str, Any] | None = None) -> str:
        if not (runtime_config or {}).get("enable_post_model_verifier", False):
            return ""
        return (
            "For referential follow-ups like 'what goes well with those', resolve 'those' to the exact products or orders "
            "from the recent turn before approving the answer. Keep only recommendations that are direct complements to those "
            "referenced products. Remove items that are merely useful tech in general. Do not recommend items already present "
            "in the referenced order set unless the user explicitly asks for replacements, duplicates, or bundles. "
            "If the answer claims an item is in stock or pickup-ready, that claim must be supported by live inventory data."
        )

    def describe_tool_trace_step(
        self,
        *,
        tool_name: str,
        payload: Any,
        runtime_config: dict[str, Any] | None = None,
    ) -> str | None:
        detail = ""
        if isinstance(payload, dict):
            for key in ("query", "text", "product_id", "store_id", "order_id", "shipment_id", "tracking_number", "customer_id"):
                value = payload.get(key)
                if value:
                    detail = str(value)
                    break

        if tool_name == self.manifest.identity.tool_name:
            return "Identify the signed-in customer context before using live account or store data."
        if tool_name == "get_current_time":
            return "Compare live timestamps against promise dates and delivery windows."
        if tool_name == "analyze_shopping_request":
            return (
                "Research the shopping intent behind the request and infer likely platforms, device types, "
                "performance needs, and search angles before catalog lookup."
            )
        if tool_name.startswith("search_product_by_text"):
            if not (runtime_config or {}).get("show_search_translation_trace_step", False):
                return ""
            return f"Translate the request into likely hardware terms and search the catalog: {detail or 'generic product search'}."
        if tool_name.startswith("filter_storeinventory_by_product_id"):
            return "Verify live inventory and pickup timing for the shortlisted product."
        if tool_name.startswith("filter_storeinventory_by_store_id"):
            return "Inspect the customer's local store inventory before promising pickup."
        if tool_name.startswith("search_guide_by_text"):
            return f"Pull generic guidance or policy to support the final recommendation: {detail or 'guide search'}."
        return None

    def get_internal_tool_definitions(
        self,
        *,
        runtime_config: dict[str, Any] | None = None,
    ) -> Sequence[InternalToolDefinition]:
        definitions: list[InternalToolDefinition] = [
            InternalToolDefinition(
                name=self.manifest.identity.tool_name,
                description=self.manifest.identity.description,
            ),
            InternalToolDefinition(
                name="get_current_time",
                description=(
                    "Returns the current date and time in UTC (ISO 8601). Use this when comparing order promises, "
                    "shipment scans, and pickup readiness windows."
                ),
            ),
            InternalToolDefinition(
                name="dataset_overview",
                description=(
                    "Returns counts for the current ElectroHub demo dataset, including customers, stores, products, "
                    "inventory rows, orders, shipments, cases, and guides."
                ),
            ),
        ]
        if (runtime_config or {}).get("enable_shopping_analyzer", False):
            definitions.append(InternalToolDefinition(
                name="analyze_shopping_request",
                description=(
                    "Research and interpret an electronics shopping request before catalog search. "
                    "Use this for niche software, unfamiliar app names, unusual compatibility questions, "
                    "or when you need to infer likely platform, device class, and search terms. "
                    "Pass the full user request so the tool can infer shopping intent, not just the niche term."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "The user's shopping request or niche software question.",
                        },
                    },
                    "required": ["request"],
                },
            ))
        return tuple(definitions)

    def execute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        if tool_name == self.manifest.identity.tool_name:
            identity = self.manifest.identity
            return {
                identity.id_field: os.getenv(identity.id_env_var, identity.default_id),
                "name": os.getenv(identity.name_env_var, identity.default_name),
                "email": os.getenv(identity.email_env_var, identity.default_email),
                "member_tier": os.getenv("DEMO_USER_MEMBER_TIER", DEMO_CUSTOMER["member_tier"]),
                "city": os.getenv("DEMO_USER_CITY", DEMO_CUSTOMER["city"]),
                "state": os.getenv("DEMO_USER_STATE", DEMO_CUSTOMER["state"]),
                "home_store_id": os.getenv("DEMO_USER_HOME_STORE_ID", DEMO_CUSTOMER["home_store_id"]),
                "home_store_name": os.getenv("DEMO_USER_HOME_STORE_NAME", DEMO_CUSTOMER["home_store_name"]),
            }
        if tool_name == "get_current_time":
            return {
                "current_time": datetime.now(timezone.utc).isoformat(),
                "timezone": "UTC",
            }
        if tool_name == "dataset_overview":
            client = create_redis_client(settings)
            raw = client.execute_command("JSON.GET", self.manifest.namespace.dataset_meta_key, "$")
            if raw:
                data = json.loads(raw)
                return data[0] if isinstance(data, list) else data
            return {"error": "Dataset metadata not found. Run the data loader first."}
        if tool_name == "analyze_shopping_request":
            request = str(arguments.get("request", "")).strip()
            if not request:
                return {"error": "Missing request"}
            return self._analyze_shopping_request(request=request, settings=settings)
        return {"error": f"Unknown tool: {tool_name}"}

    def _analyze_shopping_request(self, *, request: str, settings: Any) -> dict[str, Any]:
        from openai import OpenAI

        if not settings.openai_api_key:
            return {
                "request": request,
                "summary": "No OpenAI API key configured for shopping intent analysis.",
                "likely_platforms": [],
                "likely_device_types": [],
                "performance_tier": "unknown",
                "suggested_search_terms": [],
                "confidence": "low",
            }

        client_kw: dict[str, Any] = {"api_key": settings.openai_api_key}
        base_url = getattr(settings, "openai_base_url", None)
        if base_url:
            client_kw["base_url"] = base_url
        client = OpenAI(**client_kw)
        response = client.chat.completions.create(
            model=settings.openai_lightweight_model or settings.openai_chat_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an electronics retail shopping-intent analyst. "
                        "Interpret a shopper's request and infer what kinds of devices they likely need. "
                        "For unfamiliar software or game names, use general knowledge to infer likely platform, "
                        "device class, portability needs, and performance level. "
                        "Return only JSON with keys: "
                        "summary, likely_platforms, likely_device_types, performance_tier, "
                        "portability_preference, suggested_search_terms, confidence, cautions. "
                        "Keep suggested_search_terms short and retail-oriented."
                    ),
                },
                {
                    "role": "user",
                    "content": request,
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {
                "summary": content,
                "likely_platforms": [],
                "likely_device_types": [],
                "performance_tier": "unknown",
                "portability_preference": "unknown",
                "suggested_search_terms": [],
                "confidence": "low",
                "cautions": [],
            }
        parsed["request"] = request
        return parsed

    def write_dataset_meta(self, *, settings: Any, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        summary = {
            "customers": len(records.get("Customer", [])),
            "stores": len(records.get("Store", [])),
            "products": len(records.get("Product", [])),
            "store_inventory": len(records.get("StoreInventory", [])),
            "orders": len(records.get("Order", [])),
            "order_items": len(records.get("OrderItem", [])),
            "shipments": len(records.get("Shipment", [])),
            "shipment_events": len(records.get("ShipmentEvent", [])),
            "support_cases": len(records.get("SupportCase", [])),
            "guides": len(records.get("Guide", [])),
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


DOMAIN = ElectrohubDomain()
