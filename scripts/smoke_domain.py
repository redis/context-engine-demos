"""Run a lightweight smoke test for a domain pack."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import load_domain
from scripts.generate_models import render


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="reddash")
    args = parser.parse_args()

    domain = load_domain(args.domain)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "output"
        result = domain.generate_demo_data(output_dir=output_dir, update_env_file=False)
        model_text = render(args.domain)

        assert result.output_dir
        assert model_text
        for spec in domain.get_entity_specs():
            assert (output_dir / spec.file_name).exists(), f"Missing {spec.file_name}"

    print(f"Smoke test passed for domain '{args.domain}'.")


if __name__ == "__main__":
    main()
