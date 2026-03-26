#!/usr/bin/env bash
set -eo pipefail

DOMAIN="${DOMAIN:-${DEMO_DOMAIN:-reddash}}"
uv run python scripts/setup_surface.py --domain "$DOMAIN" "$@"
