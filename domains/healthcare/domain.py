from __future__ import annotations

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
from backend.app.core.domain_schema import EntitySpec
from domains.healthcare.data_generator import generate_demo_data
from domains.healthcare.prompt import build_system_prompt
from domains.healthcare.schema import ENTITY_SPECS


class HealthcareDomain:
    manifest = DomainManifest(
        id="healthcare",
        description="Healthcare patient-success demo with locations, providers, patients, appointments, referrals, and waitlist.",
        generated_models_module="domains.healthcare.generated_models",
        generated_models_path="domains/healthcare/generated_models.py",
        output_dir="output/healthcare",
        branding=BrandingConfig(
            app_name="RedHealthConnect",
            subtitle="Patient Success Portal",
            hero_title="How can we help you today?",
            placeholder_text="Ask about appointments, referrals, providers…",
            logo_path="domains/healthcare/assets/logo.svg",
            starter_prompts=[
                PromptCard(
                    eyebrow="Appointments",
                    title="Do I have any upcoming appointments?",
                    prompt="Do I have any upcoming appointments?",
                ),
                PromptCard(
                    eyebrow="Referrals",
                    title="What's the status of my referrals?",
                    prompt="What's the status of my referrals?",
                ),
                PromptCard(
                    eyebrow="Find a Doctor",
                    title="Find me a cardiologist",
                    prompt="Find me a cardiologist accepting new patients",
                ),
                PromptCard(
                    eyebrow="Waitlist",
                    title="Am I on any waitlists?",
                    prompt="Am I on any waitlists?",
                ),
            ],
            theme=ThemeConfig(
                bg="#0a1628",
                bg_accent_a="rgba(76, 194, 255, 0.08)",
                bg_accent_b="rgba(76, 194, 255, 0.04)",
                panel="rgba(16, 28, 48, 0.88)",
                panel_strong="rgba(20, 32, 56, 0.96)",
                panel_elevated="rgba(24, 40, 64, 0.92)",
                line="rgba(76, 194, 255, 0.12)",
                line_strong="rgba(76, 194, 255, 0.22)",
                text="#e8f4f8",
                muted="#7a9aad",
                soft="#b8d4e0",
                accent="#4cc2ff",
                user="#132840",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="healthcare",
            dataset_meta_key="healthcare:meta:dataset",
            checkpoint_prefix="healthcare:checkpoint",
            checkpoint_write_prefix="healthcare:checkpoint_write",
            redis_instance_name="Healthcare Redis Cloud",
            surface_name="Healthcare Surface",
            agent_name="Healthcare Agent",
        ),
        rag=RagConfig(
            tool_name="vector_search_domain_docs",
            status_text="Searching domain documents…",
            generating_text="Generating answer…",
            index_name_contains="docs",
            vector_field="content_embedding",
            return_fields=["title", "category", "content"],
            num_results=3,
            answer_system_prompt="Answer using only the provided documents.",
        ),
        identity=IdentityConfig(
            id_field="patient_id",
            default_id="P001",
            default_name="John Smith",
            default_email="john.smith@email.com",
            description="Returns the signed-in patient's profile, including ID, name, and email. Call this first for any patient-specific question.",
        ),
    )

    def get_entity_specs(self) -> tuple[EntitySpec, ...]:
        return ENTITY_SPECS

    def get_runtime_config(self, *, settings: Any) -> dict[str, Any]:
        del settings
        return {}

    def build_system_prompt(
        self,
        *,
        mcp_tools: Sequence[dict[str, Any]],
        runtime_config: dict[str, Any] | None = None,
    ) -> str:
        return build_system_prompt(mcp_tools=mcp_tools, runtime_config=runtime_config)

    def build_answer_verifier_prompt(self, *, runtime_config: dict[str, Any] | None = None) -> str:
        del runtime_config
        return ""

    def describe_tool_trace_step(
        self,
        *,
        tool_name: str,
        payload: Any,
        runtime_config: dict[str, Any] | None = None,
    ) -> str | None:
        del tool_name, payload, runtime_config
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
                    "Use this to compare against appointment dates and referral timelines."
                ),
            ),
            InternalToolDefinition(
                name="dataset_overview",
                description=(
                    "Returns counts for the current healthcare demo dataset, including "
                    "locations, providers, patients, appointments, referrals, and waitlist entries."
                ),
            ),
        )

    def execute_internal_tool(
        self, tool_name: str, arguments: dict[str, Any], settings: Any
    ) -> dict[str, Any]:
        import os
        from datetime import datetime, timezone

        if tool_name == self.manifest.identity.tool_name:
            identity = self.manifest.identity
            return {
                identity.id_field: os.getenv(identity.id_env_var, identity.default_id),
                "name": os.getenv(identity.name_env_var, identity.default_name),
                "email": os.getenv(identity.email_env_var, identity.default_email),
            }
        if tool_name == "get_current_time":
            return {"current_time": datetime.now(timezone.utc).isoformat()}
        if tool_name == "dataset_overview":
            return {
                "locations": 2,
                "providers": 5,
                "patients": 8,
                "appointments": 10,
                "referrals": 6,
                "waitlist": 4,
            }
        return {"error": f"Unknown tool: {tool_name}"}

    def write_dataset_meta(
        self, *, settings: Any, records: dict[str, list[dict[str, Any]]]
    ) -> dict[str, Any]:
        del settings, records
        return {}

    def generate_demo_data(
        self,
        *,
        output_dir: Path,
        seed: int | None = None,
        update_env_file: bool = False,
    ) -> GeneratedDataset:
        return generate_demo_data(output_dir=output_dir, seed=seed, update_env_file=update_env_file)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not Path(self.manifest.branding.logo_path).exists():
            errors.append(f"Logo file not found: {self.manifest.branding.logo_path}")
        return errors


DOMAIN = HealthcareDomain()
