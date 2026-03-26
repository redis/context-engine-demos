"""Validate a domain pack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import load_domain
from backend.app.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=None)
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain or settings.demo_domain)
    errors = domain.validate()
    if errors:
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print(f"Domain '{domain.manifest.id}' is valid.")


if __name__ == "__main__":
    main()
