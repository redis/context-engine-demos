"""Create or reuse the Context Surface for the active domain."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import load_domain
from backend.app.settings import ENV_PATH, get_settings


def run_ctxctl(args: list[str]) -> dict[str, str]:
    proc = subprocess.run(
        ["uv", "run", "ctxctl", "-o", "json", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def upsert_env_values(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text().splitlines() if path.exists() else []
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        if "=" not in line or line.strip().startswith("#"):
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
    path.write_text("\n".join(output) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=None)
    parser.add_argument("--force-create", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain or settings.demo_domain)
    env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}

    if not settings.ctx_admin_key:
        print("CTX_ADMIN_KEY is not set in .env")
        sys.exit(1)

    generated_models_path = ROOT / domain.manifest.generated_models_path
    if not generated_models_path.exists():
        print(f"Generated model file is missing: {generated_models_path}")
        print("Run model generation first.")
        sys.exit(1)

    tls_args = ["--tls"] if settings.redis_ssl else []

    redis_instance_id = env.get("CTX_REDIS_INSTANCE_ID", "") if not args.force_create else ""
    if redis_instance_id:
        print(f"Reusing Redis instance registration: {redis_instance_id}")
    else:
        print("Creating Redis instance registration...")
        payload = run_ctxctl([
            "redis", "create",
            "--name", env.get("REDIS_INSTANCE_NAME", domain.manifest.namespace.redis_instance_name),
            "--addr", f"{settings.redis_host}:{settings.redis_port}",
            "--username", settings.redis_username or "default",
            "--password", settings.redis_password,
            *tls_args,
            "--admin-key", settings.ctx_admin_key,
        ])
        redis_instance_id = payload.get("id", "")

    surface_id = env.get("CTX_SURFACE_ID", "") if not args.force_create else ""
    if surface_id:
        print(f"Reusing context surface: {surface_id}")
    else:
        print("Creating context surface...")
        payload = run_ctxctl([
            "surface", "create",
            "--name", env.get("CTX_SURFACE_NAME", domain.manifest.namespace.surface_name),
            "--models", str(generated_models_path),
            "--redis-instance-id", redis_instance_id,
            "--admin-key", settings.ctx_admin_key,
        ])
        surface_id = payload.get("id", "")

    agent_key = env.get("MCP_AGENT_KEY", "") if not args.force_create else ""
    if agent_key:
        print("Reusing agent key from .env")
    else:
        print("Creating agent key...")
        payload = run_ctxctl([
            "agent", "create",
            "--surface-id", surface_id,
            "--name", env.get("CTX_AGENT_NAME", domain.manifest.namespace.agent_name),
            "--admin-key", settings.ctx_admin_key,
        ])
        agent_key = payload.get("key", "")

    updates = {
        "CTX_REDIS_INSTANCE_ID": redis_instance_id,
        "CTX_SURFACE_ID": surface_id,
        "MCP_AGENT_KEY": agent_key,
    }
    upsert_env_values(ENV_PATH, updates)

    print("")
    print("Context surface ready.")
    print(f"  Redis instance ID: {redis_instance_id}")
    print(f"  Surface ID:        {surface_id}")
    print("  Agent key saved to .env as MCP_AGENT_KEY")


if __name__ == "__main__":
    main()
