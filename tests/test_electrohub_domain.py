import json
from pathlib import Path

from backend.app.core.domain_loader import load_domain


def test_electrohub_domain_loads() -> None:
    domain = load_domain("electrohub")
    assert domain.manifest.id == "electrohub"
    assert Path(domain.manifest.branding.logo_path).exists()
    assert domain.manifest.branding.starter_prompts
    assert domain.manifest.branding.ui.show_platform_surface is False
    assert domain.manifest.branding.ui.show_live_updates is False

    default_runtime_config = domain.get_runtime_config(settings=None)
    tool_names = {tool.name for tool in domain.get_internal_tool_definitions(runtime_config=default_runtime_config)}
    assert "analyze_shopping_request" not in tool_names

    enabled_runtime_config = {
        **default_runtime_config,
        "enable_shopping_analyzer": True,
        "enable_post_model_verifier": True,
        "show_search_translation_trace_step": True,
    }
    tool_names = {tool.name for tool in domain.get_internal_tool_definitions(runtime_config=enabled_runtime_config)}
    assert "analyze_shopping_request" in tool_names

    prompt = domain.build_system_prompt(mcp_tools=[], runtime_config=enabled_runtime_config)
    assert "analyze_shopping_request" in prompt
    assert "before catalog search" in prompt.lower()

    trace_label = domain.describe_tool_trace_step(
        tool_name="analyze_shopping_request",
        payload={"request": "Run some niche app"},
        runtime_config=enabled_runtime_config,
    )
    assert trace_label is not None
    assert "search angles" in trace_label.lower()

    hidden_trace = domain.describe_tool_trace_step(
        tool_name="search_product_by_text",
        payload={"query": "mac mini"},
        runtime_config=default_runtime_config,
    )
    assert hidden_trace == ""


def test_electrohub_data_generator_writes_expected_files(tmp_path: Path) -> None:
    domain = load_domain("electrohub")
    result = domain.generate_demo_data(output_dir=tmp_path, update_env_file=False)
    assert result.env_updates["DEMO_USER_ID"] == "CUST_EH_001"
    assert result.env_updates["DEMO_USER_HOME_STORE_ID"] == "STORE_001"
    assert result.summary["products"] >= 20
    for spec in domain.get_entity_specs():
        assert (tmp_path / spec.file_name).exists()

    product_rows = [
        json.loads(line)
        for line in (tmp_path / "products.jsonl").read_text().splitlines()
        if line.strip()
    ]
    guide_rows = [
        json.loads(line)
        for line in (tmp_path / "guides.jsonl").read_text().splitlines()
        if line.strip()
    ]
    product_text = json.dumps(product_rows).lower()
    guide_text = json.dumps(guide_rows).lower()
    assert "openclaw" not in product_text
    assert "openclaw" not in guide_text
