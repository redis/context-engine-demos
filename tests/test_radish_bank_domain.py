from backend.app.core.domain_loader import load_domain


def test_radish_bank_domain_loads() -> None:
    domain = load_domain("radish-bank")
    assert domain.manifest.id == "radish-bank"
