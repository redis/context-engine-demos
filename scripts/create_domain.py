"""Scaffold a new domain pack."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("Domain name must contain letters or digits")
    return slug


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    args = parser.parse_args()

    domain_id = slugify(args.domain)
    domain_dir = ROOT / "domains" / domain_id
    if domain_dir.exists():
        print(f"Domain already exists: {domain_dir}")
        sys.exit(1)

    title = domain_id.replace("-", " ").title()

    write(domain_dir / "__init__.py", f'"""{title} domain."""\n')
    write(domain_dir / "schema.py", """from __future__ import annotations

from backend.app.core.domain_schema import EntitySpec

ENTITY_SPECS: tuple[EntitySpec, ...] = ()
""")
    write(domain_dir / "prompt.py", """from __future__ import annotations

from typing import Any, Sequence


def build_system_prompt(*, mcp_tools: Sequence[dict[str, Any]]) -> str:
    del mcp_tools
    return "You are a domain assistant."
""")
    write(domain_dir / "data_generator.py", f"""from __future__ import annotations

from pathlib import Path

from backend.app.core.domain_contract import GeneratedDataset


def generate_demo_data(*, output_dir: Path, seed: int | None = None, update_env_file: bool = True) -> GeneratedDataset:
    del seed, update_env_file
    output_dir.mkdir(parents=True, exist_ok=True)
    return GeneratedDataset(output_dir=str(output_dir), env_updates={{}}, summary={{}})
""")
    write(domain_dir / "domain.py", f"""from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from backend.app.core.domain_contract import (
    BrandingConfig,
    DomainManifest,
    GeneratedDataset,
    IdentityConfig,
    InternalToolDefinition,
    NamespaceConfig,
    RagConfig,
    ThemeConfig,
)
from backend.app.core.domain_schema import EntitySpec
from {f"domains.{domain_id}.data_generator"} import generate_demo_data
from {f"domains.{domain_id}.prompt"} import build_system_prompt
from {f"domains.{domain_id}.schema"} import ENTITY_SPECS


class {title.replace(" ", "")}Domain:
    manifest = DomainManifest(
        id="{domain_id}",
        description="{title} demo domain.",
        generated_models_module="domains.{domain_id}.generated_models",
        generated_models_path="domains/{domain_id}/generated_models.py",
        output_dir="output/{domain_id}",
        branding=BrandingConfig(
            app_name="{title}",
            subtitle="Demo",
            hero_title="How can we help?",
            placeholder_text="Ask a question...",
            logo_path="domains/{domain_id}/assets/logo.svg",
            starter_prompts=[],
            theme=ThemeConfig(
                bg="#0d0f14",
                bg_accent_a="rgba(255,255,255,0.08)",
                bg_accent_b="rgba(255,255,255,0.04)",
                panel="rgba(20, 23, 32, 0.88)",
                panel_strong="rgba(24, 28, 40, 0.96)",
                panel_elevated="rgba(30, 35, 50, 0.92)",
                line="rgba(255,255,255,0.1)",
                line_strong="rgba(255,255,255,0.18)",
                text="#f2f0ed",
                muted="#9a9490",
                soft="#d4cfc8",
                accent="#4cc2ff",
                user="#1f2833",
            ),
        ),
        namespace=NamespaceConfig(
            redis_prefix="{domain_id}",
            dataset_meta_key="{domain_id}:meta:dataset",
            checkpoint_prefix="{domain_id}:checkpoint",
            checkpoint_write_prefix="{domain_id}:checkpoint_write",
            redis_instance_name="{title} Redis Cloud",
            surface_name="{title} Surface",
            agent_name="{title} Agent",
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
            default_id="DEMO_USER_001",
            default_name="Demo User",
            default_email="demo@example.com",
            description="Returns the signed-in demo user profile.",
        ),
    )

    def get_entity_specs(self) -> tuple[EntitySpec, ...]:
        return ENTITY_SPECS

    def build_system_prompt(self, *, mcp_tools: Sequence[dict[str, Any]]) -> str:
        return build_system_prompt(mcp_tools=mcp_tools)

    def get_internal_tool_definitions(self) -> Sequence[InternalToolDefinition]:
        return ()

    def execute_internal_tool(self, tool_name: str, arguments: dict[str, Any], settings: Any) -> dict[str, Any]:
        del tool_name, arguments, settings
        return {{}}

    def write_dataset_meta(self, *, settings: Any, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        del settings, records
        return {{}}

    def generate_demo_data(
        self,
        *,
        output_dir: Path,
        seed: int | None = None,
        update_env_file: bool = True,
    ) -> GeneratedDataset:
        return generate_demo_data(output_dir=output_dir, seed=seed, update_env_file=update_env_file)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not Path(self.manifest.branding.logo_path).exists():
            errors.append(f"Logo file not found: {{self.manifest.branding.logo_path}}")
        return errors


DOMAIN = {title.replace(" ", "")}Domain()
""")
    write(domain_dir / "assets" / "logo.svg", """<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="40" height="40" rx="12" fill="#4cc2ff" />
  <path d="M11 20h18" stroke="#08111a" stroke-width="3" stroke-linecap="round" />
</svg>
""")
    write(domain_dir / "docs" / "demo_paths.md", f"# {title}\n\nAdd scripted demo paths here.\n")
    write(ROOT / "tests" / f"test_{domain_id.replace('-', '_')}_domain.py", f"""from backend.app.core.domain_loader import load_domain


def test_{domain_id.replace('-', '_')}_domain_loads() -> None:
    domain = load_domain("{domain_id}")
    assert domain.manifest.id == "{domain_id}"
""")

    print(f"Created domain scaffold at {domain_dir}")
    print("Next steps:")
    print(f"  1. Fill in domains/{domain_id}/schema.py")
    print(f"  2. Customize domains/{domain_id}/domain.py")
    print(f"  3. Run: uv run python scripts/validate_domain.py --domain {domain_id}")
    print(f"  4. Run: uv run python scripts/generate_models.py --domain {domain_id}")


if __name__ == "__main__":
    main()
