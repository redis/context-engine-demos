"""Create or reuse the Context Surface for the active domain.

This script targets the current admin API contract, which expects
embedded Redis connection settings under ``data_source.connection_config``
when creating a surface.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import redis
from dotenv import dotenv_values
from context_surfaces import config as cs_config
from context_surfaces.cli.main import _parse_data_model_from_python

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_loader import load_domain
from backend.app.redis_connection import create_redis_client
from backend.app.settings import ENV_PATH, get_settings


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


def _admin_headers(admin_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-API-Key": admin_key,
    }


def _safe_response_text(response: httpx.Response) -> str:
    try:
        payload = response.json()
        return json.dumps(payload, indent=2, ensure_ascii=False)
    except Exception:
        return response.text


def _parse_data_model(models_path: Path, *, surface_name: str) -> dict[str, Any]:
    return _parse_data_model_from_python(models_path, surface_name, None, None)


def _create_surface(
    *,
    api_url: str,
    admin_key: str,
    surface_name: str,
    description: str,
    data_model: dict[str, Any],
    redis_addr: str,
    redis_username: str,
    redis_password: str,
    redis_db: int,
    redis_ssl: bool,
) -> dict[str, Any]:
    body = {
        "name": surface_name,
        "description": description,
        "data_model": data_model,
        "data_source": {
            "type": "redis",
            "name": "redis",
            "connection_config": {
                "addr": redis_addr,
                "username": redis_username,
                "password": redis_password,
                "db": redis_db,
                "tls_enabled": redis_ssl,
                "pool_size": 10,
                "min_idle_conns": 2,
            },
        },
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{api_url}/api/v1/context-surfaces",
            headers=_admin_headers(admin_key),
            json=body,
        )
    if response.status_code != 201:
        raise RuntimeError(
            "Failed to create context surface "
            f"(status {response.status_code}): {_safe_response_text(response)}"
        )
    return response.json()


def _create_agent_key(
    *,
    api_url: str,
    admin_key: str,
    surface_id: str,
    agent_name: str,
) -> dict[str, Any]:
    body = {"name": agent_name}
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{api_url}/api/v1/context-surfaces/{surface_id}/agent-keys",
            headers=_admin_headers(admin_key),
            json=body,
        )
    if response.status_code != 201:
        raise RuntimeError(
            "Failed to create agent key "
            f"(status {response.status_code}): {_safe_response_text(response)}"
        )
    return response.json()


def _describe_surface(*, api_url: str, admin_key: str, surface_id: str) -> dict[str, Any]:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{api_url}/api/v1/context-surfaces/{surface_id}",
            headers=_admin_headers(admin_key),
        )
    if response.status_code != 200:
        raise RuntimeError(
            "Failed to describe context surface "
            f"(status {response.status_code}): {_safe_response_text(response)}"
        )
    return response.json()


def _probe_redis_connection(
    *,
    redis_host: str,
    redis_port: int,
    redis_username: str,
    redis_password: str,
    redis_db: int,
    redis_ssl: bool,
) -> tuple[bool, str]:
    try:
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            username=redis_username or "default",
            password=redis_password or None,
            db=redis_db,
            ssl=redis_ssl,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        client.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def _preflight_redis_connection() -> None:
    settings = get_settings()
    # Reuse the app's configured client first so setup and runtime validate the same settings.
    try:
        create_redis_client(settings).ping()
        return
    except Exception as exc:
        current_error = str(exc)

    alternate_ssl = not settings.redis_ssl
    alt_ok, _ = _probe_redis_connection(
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
        redis_username=settings.redis_username or "default",
        redis_password=settings.redis_password,
        redis_db=settings.redis_db,
        redis_ssl=alternate_ssl,
    )
    if alt_ok:
        raise RuntimeError(
            "Redis preflight failed with the current TLS setting. "
            f"REDIS_SSL={str(settings.redis_ssl).lower()} does not work for "
            f"{settings.redis_host}:{settings.redis_port}, but "
            f"REDIS_SSL={str(alternate_ssl).lower()} does. "
            "Update .env and rerun setup."
        )

    raise RuntimeError(
        "Redis preflight failed with the configured connection settings. "
        f"Tried {settings.redis_host}:{settings.redis_port}/{settings.redis_db} "
        f"with REDIS_SSL={str(settings.redis_ssl).lower()}. "
        f"Original error: {current_error}"
    )


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

    api_url = str(cs_config.api_url).rstrip("/")
    surface_name = env.get("CTX_SURFACE_NAME", domain.manifest.namespace.surface_name)
    agent_name = env.get("CTX_AGENT_NAME", domain.manifest.namespace.agent_name)
    surface_id = env.get("CTX_SURFACE_ID", "") if not args.force_create else ""
    agent_key = env.get("MCP_AGENT_KEY", "") if not args.force_create else ""

    if surface_id:
        print(f"Reusing context surface: {surface_id}")
        try:
            _describe_surface(api_url=api_url, admin_key=settings.ctx_admin_key, surface_id=surface_id)
        except Exception as exc:
            print(f"Existing surface is not usable: {exc}")
            print("Run again with --force-create to create a fresh surface.")
            sys.exit(1)
    else:
        print("Validating Redis connection settings...")
        _preflight_redis_connection()
        print("Creating context surface with embedded Redis data source...")
        data_model = _parse_data_model(generated_models_path, surface_name=surface_name)
        payload = _create_surface(
            api_url=api_url,
            admin_key=settings.ctx_admin_key,
            surface_name=surface_name,
            description=domain.manifest.description,
            data_model=data_model,
            redis_addr=f"{settings.redis_host}:{settings.redis_port}",
            redis_username=settings.redis_username or "default",
            redis_password=settings.redis_password,
            redis_db=settings.redis_db,
            redis_ssl=settings.redis_ssl,
        )
        surface_id = str(payload["id"])

    if agent_key:
        print("Reusing agent key from .env")
    else:
        print("Creating agent key...")
        payload = _create_agent_key(
            api_url=api_url,
            admin_key=settings.ctx_admin_key,
            surface_id=surface_id,
            agent_name=agent_name,
        )
        agent_key = str(payload["key"])

    updates = {
        "CTX_SURFACE_ID": surface_id,
        "MCP_AGENT_KEY": agent_key,
    }
    upsert_env_values(ENV_PATH, updates)

    print("")
    print("Context surface ready.")
    print(f"  Surface ID:        {surface_id}")
    print("  Redis source:      embedded connection_config")
    print("  Agent key saved to .env as MCP_AGENT_KEY")


if __name__ == "__main__":
    main()
