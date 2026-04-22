import json
from pathlib import Path

from backend.app.core.domain_loader import load_domain
from domains.healthcare.data_generator import (
    APPOINTMENTS,
    LOCATIONS,
    PATIENTS,
    PROVIDERS,
    REFERRALS,
    WAITLIST,
    generate_demo_data,
    write_jsonl,
)


def test_healthcare_domain_loads() -> None:
    domain = load_domain("healthcare")
    assert domain.manifest.id == "healthcare"


def test_write_jsonl(tmp_path: Path) -> None:
    rows = [{"id": "1", "name": "test"}, {"id": "2", "name": "other"}]
    write_jsonl(tmp_path, "test.jsonl", rows)
    path = tmp_path / "test.jsonl"
    assert path.exists()
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "id" in parsed
        assert "name" in parsed


def test_generate_demo_data_creates_all_files(tmp_path: Path) -> None:
    result = generate_demo_data(output_dir=tmp_path, update_env_file=False)

    expected_files = [
        "locations.jsonl",
        "providers.jsonl",
        "patients.jsonl",
        "appointments.jsonl",
        "referrals.jsonl",
        "waitlist.jsonl",
    ]
    for filename in expected_files:
        assert (tmp_path / filename).exists(), f"Missing {filename}"

    # Check record counts match constants
    assert result.summary["locations"] == len(LOCATIONS)
    assert result.summary["providers"] == len(PROVIDERS)
    assert result.summary["patients"] == len(PATIENTS)
    assert result.summary["appointments"] == len(APPOINTMENTS)
    assert result.summary["referrals"] == len(REFERRALS)
    assert result.summary["waitlist"] == len(WAITLIST)


def test_generate_demo_data_jsonl_valid(tmp_path: Path) -> None:
    generate_demo_data(output_dir=tmp_path, update_env_file=False)

    for jsonl_file in tmp_path.glob("*.jsonl"):
        for i, line in enumerate(jsonl_file.read_text().strip().splitlines()):
            parsed = json.loads(line)
            assert isinstance(parsed, dict), f"{jsonl_file.name} line {i} not a dict"
            assert "id" in parsed, f"{jsonl_file.name} line {i} missing 'id'"


def test_generate_demo_data_env_updates(tmp_path: Path) -> None:
    result = generate_demo_data(output_dir=tmp_path, update_env_file=False)

    assert result.env_updates["DEMO_USER_ID"] == "P001"
    assert result.env_updates["DEMO_USER_NAME"] == "John Smith"
    assert result.env_updates["DEMO_USER_EMAIL"] == "john.smith@email.com"


def test_generate_demo_data_no_env_mutation(tmp_path: Path) -> None:
    """Verify that update_env_file=False does not touch the repo .env."""
    from domains.healthcare.data_generator import ROOT

    env_path = ROOT / ".env"
    before = env_path.read_text() if env_path.exists() else None

    generate_demo_data(output_dir=tmp_path, update_env_file=False)

    after = env_path.read_text() if env_path.exists() else None
    assert before == after, ".env was mutated despite update_env_file=False"
