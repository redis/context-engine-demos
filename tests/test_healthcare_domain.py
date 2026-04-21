from backend.app.core.domain_loader import load_domain


def test_healthcare_domain_loads() -> None:
    domain = load_domain("healthcare")
    assert domain.manifest.id == "healthcare"
