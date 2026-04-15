from pathlib import Path

from backend.app.core.domain_loader import load_domain


def test_reddash_domain_loads() -> None:
    domain = load_domain("reddash")
    assert domain.manifest.id == "reddash"
    assert Path(domain.manifest.branding.logo_path).exists()
    assert domain.manifest.branding.starter_prompts
    assert domain.manifest.branding.ui.show_platform_surface is False
    assert domain.manifest.branding.ui.show_live_updates is False


def test_reddash_data_generator_writes_expected_files(tmp_path: Path) -> None:
    domain = load_domain("reddash")
    result = domain.generate_demo_data(output_dir=tmp_path, update_env_file=False)
    assert result.env_updates["DEMO_USER_ID"] == "CUST_DEMO_001"
    for spec in domain.get_entity_specs():
        assert (tmp_path / spec.file_name).exists()
