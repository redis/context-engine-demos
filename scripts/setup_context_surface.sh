#!/usr/bin/env bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Use uv run so ctxctl resolves from the project venv
CTXCTL="uv run ctxctl"

if [[ ! -f .env ]]; then
  echo ".env not found. Copy .env.example to .env and fill it in first."
  exit 1
fi

set -a
source .env
set +a

if [[ ! -f backend/app/context_surfaces/reddash_models.py ]]; then
  echo "Generated model file is missing. Run 'make generate-models' first."
  exit 1
fi

if [[ -z "${CTX_ADMIN_KEY:-}" ]]; then
  echo "CTX_ADMIN_KEY is not set in .env. Get an admin key from the Context Surfaces console."
  exit 1
fi

ADMIN_ARGS=(--admin-key "$CTX_ADMIN_KEY")

REDIS_NAME="${REDIS_INSTANCE_NAME:-Reddish Redis Cloud}"
SURFACE_NAME="${CTX_SURFACE_NAME:-Reddish Delivery Surface}"
AGENT_NAME="${CTX_AGENT_NAME:-Reddish Delivery Agent}"
FORCE_CREATE="${CTX_FORCE_CREATE:-false}"

TLS_ARGS=()
if [[ "${REDIS_SSL:-false}" == "true" ]]; then
  TLS_ARGS+=(--tls)
fi

# ── Step 1: Register Redis instance ────────────────────────────────────────
if [[ -n "${CTX_REDIS_INSTANCE_ID:-}" ]]; then
  REDIS_INSTANCE_ID="$CTX_REDIS_INSTANCE_ID"
  echo "Reusing Redis instance registration: $REDIS_INSTANCE_ID"
else
  echo "Creating Redis instance registration..."
  REDIS_JSON="$($CTXCTL -o json redis create \
    --name "$REDIS_NAME" \
    --addr "${REDIS_HOST}:${REDIS_PORT}" \
    --username "${REDIS_USERNAME:-default}" \
    --password "${REDIS_PASSWORD}" \
    "${TLS_ARGS[@]}" \
    "${ADMIN_ARGS[@]}")"

  REDIS_INSTANCE_ID="$(python3 - <<'PY' "$REDIS_JSON"
import json, sys
payload = json.loads(sys.argv[1])
print(payload.get("id", ""))
PY
)"
fi

if [[ -z "$REDIS_INSTANCE_ID" ]]; then
  echo "Failed to parse Redis instance ID from ctxctl output."
  exit 1
fi

# ── Step 2: Create context surface ─────────────────────────────────────────
if [[ "$FORCE_CREATE" != "true" && -n "${CTX_SURFACE_ID:-}" ]]; then
  CTX_SURFACE_ID_NEW="$CTX_SURFACE_ID"
  echo "Reusing context surface: $CTX_SURFACE_ID_NEW"
else
  echo "Creating context surface..."
  SURFACE_JSON="$($CTXCTL -o json surface create \
    --name "$SURFACE_NAME" \
    --models backend/app/context_surfaces/reddash_models.py \
    --redis-instance-id "$REDIS_INSTANCE_ID" \
    "${ADMIN_ARGS[@]}")"

  CTX_SURFACE_ID_NEW="$(python3 - <<'PY' "$SURFACE_JSON"
import json, sys
payload = json.loads(sys.argv[1])
print(payload.get("id", ""))
PY
)"
fi

if [[ -z "$CTX_SURFACE_ID_NEW" ]]; then
  echo "Failed to parse context surface ID from ctxctl output."
  exit 1
fi

# ── Step 3: Create agent key ───────────────────────────────────────────────
if [[ "$FORCE_CREATE" != "true" && -n "${MCP_AGENT_KEY:-}" ]]; then
  MCP_AGENT_KEY_NEW="$MCP_AGENT_KEY"
  echo "Reusing agent key from .env"
else
  echo "Creating agent key..."
  AGENT_JSON="$($CTXCTL -o json agent create \
    --surface-id "$CTX_SURFACE_ID_NEW" \
    --name "$AGENT_NAME" \
    "${ADMIN_ARGS[@]}")"

  MCP_AGENT_KEY_NEW="$(python3 - <<'PY' "$AGENT_JSON"
import json, sys
payload = json.loads(sys.argv[1])
print(payload.get("key", ""))
PY
)"
fi

if [[ -z "$MCP_AGENT_KEY_NEW" ]]; then
  echo "Failed to parse agent key from ctxctl output."
  exit 1
fi

# ── Step 4: Update .env ────────────────────────────────────────────────────
python3 - <<'PY' ".env" "$REDIS_INSTANCE_ID" "$CTX_SURFACE_ID_NEW" "$MCP_AGENT_KEY_NEW"
from pathlib import Path
import sys
env_path = Path(sys.argv[1])
updates = {
    "CTX_REDIS_INSTANCE_ID": sys.argv[2],
    "CTX_SURFACE_ID": sys.argv[3],
    "MCP_AGENT_KEY": sys.argv[4],
}
lines = env_path.read_text().splitlines()
seen = set()
output = []
for line in lines:
    if "=" not in line:
        output.append(line)
        continue
    key, _ = line.split("=", 1)
    if key in updates:
        output.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        output.append(line)
for key, value in updates.items():
    if key not in seen:
        output.append(f"{key}={value}")
env_path.write_text("\n".join(output) + "\n")
PY

echo ""
echo "Context surface ready."
echo "  Redis instance ID: $REDIS_INSTANCE_ID"
echo "  Surface ID:        $CTX_SURFACE_ID_NEW"
echo "  Agent key saved to .env as MCP_AGENT_KEY"
echo ""
echo "Recommended next steps:"
echo "  uv run ctxctl tools list --agent-key \"$MCP_AGENT_KEY_NEW\""
echo "  make load-data"
echo "  make dev"

