from __future__ import annotations

import importlib
from functools import lru_cache

from backend.app.core.domain_contract import DomainPack
from backend.app.settings import Settings


def _module_name(domain_id: str) -> str:
    return f"domains.{domain_id}.domain"


@lru_cache(maxsize=16)
def load_domain(domain_id: str) -> DomainPack:
    module = importlib.import_module(_module_name(domain_id))
    domain = getattr(module, "DOMAIN", None)
    if domain is None:
        raise RuntimeError(f"Domain module '{_module_name(domain_id)}' must export DOMAIN")
    errors = domain.validate()
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(f"Domain '{domain_id}' failed validation:\n{joined}")
    return domain


def get_active_domain(settings: Settings) -> DomainPack:
    return load_domain(settings.demo_domain)
