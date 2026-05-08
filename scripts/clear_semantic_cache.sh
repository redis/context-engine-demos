#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
TARGET_DOMAIN="${1:-}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "error: ${VENV_PYTHON} not found or not executable" >&2
  exit 1
fi

if [[ -z "${TARGET_DOMAIN}" ]]; then
  echo "usage: $(basename "$0") <domain-id>" >&2
  echo "example: $(basename "$0") northbridge-banking" >&2
  exit 2
fi

"${VENV_PYTHON}" - "${TARGET_DOMAIN}" <<'PY'
from __future__ import annotations

import sys

from backend.app.core.domain_loader import load_domain
from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings
from redis.exceptions import RedisError
from redisvl.index import SearchIndex

settings = get_settings()
domain_id = (sys.argv[1] or "").strip()
domain = load_domain(domain_id)
config = domain.manifest.semantic_cache

if not config.enabled or not config.cache_name:
    print(f"{domain_id}: semantic cache is not enabled")
    raise SystemExit(0)

expected_prefix = domain.manifest.namespace.redis_prefix.replace(":", "_")
expected_cache_name = f"{expected_prefix}_semantic_cache"
if config.cache_name != expected_cache_name:
    print(
        f"{domain_id}: refusing to clear cache index '{config.cache_name}' because it does not exactly match '{expected_cache_name}'",
        file=sys.stderr,
    )
    raise SystemExit(2)

client = create_redis_client(settings)

try:
    try:
        index = SearchIndex.from_existing(config.cache_name, redis_client=client)
        index.delete(drop=True)
    except RedisError as exc:
        message = str(exc)
        if "unknown index name" in message.lower() or "no such index" in message.lower():
            print(f"{domain_id}: semantic cache '{config.cache_name}' is already clear")
            raise SystemExit(0) from exc
        print(f"{domain_id}: unable to clear semantic cache '{config.cache_name}': {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
finally:
    client.close()

print(f"{domain_id}: cleared semantic cache '{config.cache_name}'")
PY
