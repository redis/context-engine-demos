"""Load generated JSONL data into the active domain's Context Surface."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from context_surfaces import UnifiedClient  # noqa: E402

from backend.app.core.domain_loader import load_domain  # noqa: E402
from backend.app.redis_connection import create_redis_client  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402

DEFAULT_MAX_BATCH_RECORDS = 500
DEFAULT_MAX_BATCH_BYTES = 750_000


def load_records(*, output_dir: Path, entity_by_file: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    payloads: dict[str, list[dict[str, Any]]] = {}
    for file_name, entity in entity_by_file.items():
        path = output_dir / file_name
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        payloads[entity.class_name] = rows
    return payloads


def load_generated_models(module_name: str, module_path: str, class_names: list[str]) -> dict[str, type]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        resolved = ROOT / module_path
        spec = importlib.util.spec_from_file_location(
            module_name.replace(".", "_").replace("-", "_"),
            resolved,
        )
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    return {class_name: getattr(module, class_name) for class_name in class_names}


def _record_payload_size(record: Any) -> int:
    payload = record.model_dump() if hasattr(record, "model_dump") else record
    return len(json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8"))


def iter_import_batches(
    records: list[Any],
    *,
    max_records: int,
    max_bytes: int,
) -> list[list[Any]]:
    if max_records <= 0:
        raise ValueError("--max-batch-records must be greater than zero")
    if max_bytes <= 0:
        raise ValueError("--max-batch-bytes must be greater than zero")

    batches: list[list[Any]] = []
    current: list[Any] = []
    current_bytes = 0

    for record in records:
        record_bytes = _record_payload_size(record)
        if current and (len(current) >= max_records or current_bytes + record_bytes > max_bytes):
            batches.append(current)
            current = []
            current_bytes = 0
        current.append(record)
        current_bytes += record_bytes

    if current:
        batches.append(current)
    return batches


def _delete_matching_keys(client: Any, pattern: str) -> int:
    deleted = 0
    batch: list[str] = []
    for key in client.scan_iter(match=pattern, count=1000):
        batch.append(key)
        if len(batch) >= 500:
            deleted += client.delete(*batch)
            batch = []
    if batch:
        deleted += client.delete(*batch)
    return deleted


def clear_existing_domain_data(settings: Any, domain: Any) -> int:
    """Delete Redis records owned by this domain's generated entity key templates."""
    client = create_redis_client(settings)
    try:
        deleted = 0
        patterns: set[str] = set()
        for spec in domain.get_entity_specs():
            prefix = spec.redis_key_template.split("{", 1)[0]
            patterns.add(f"{prefix}*")
        patterns.add(f"{domain.manifest.namespace.redis_prefix}:ts:*")

        for pattern in sorted(patterns):
            deleted += _delete_matching_keys(client, pattern)
        deleted += client.delete(domain.manifest.namespace.dataset_meta_key)
        return deleted
    finally:
        client.close()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=None)
    parser.add_argument("--max-batch-records", type=int, default=DEFAULT_MAX_BATCH_RECORDS)
    parser.add_argument("--max-batch-bytes", type=int, default=DEFAULT_MAX_BATCH_BYTES)
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Delete existing Redis records for the selected domain before importing.",
    )
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain or settings.demo_domain)
    admin_key = settings.ctx_admin_key
    surface_id = settings.ctx_surface_id

    if not admin_key:
        print("CTX_ADMIN_KEY is not set in .env")
        sys.exit(1)
    if not surface_id:
        print("CTX_SURFACE_ID is not set in .env. Run setup first.")
        sys.exit(1)

    entity_specs = domain.get_entity_specs()
    entity_by_file = {spec.file_name: spec for spec in entity_specs}
    class_names = [spec.class_name for spec in entity_specs]
    generated_models = load_generated_models(
        domain.manifest.generated_models_module,
        domain.manifest.generated_models_path,
        class_names,
    )
    output_dir = ROOT / domain.manifest.output_dir
    raw_records = load_records(output_dir=output_dir, entity_by_file=entity_by_file)

    if args.clear_existing:
        deleted = clear_existing_domain_data(settings, domain)
        print(f"  Cleared {deleted} existing Redis keys for domain '{domain.manifest.id}'.")

    async with UnifiedClient() as client:
        for class_name, rows in raw_records.items():
            model_cls = generated_models[class_name]
            model_instances = [model_cls(**row) for row in rows]
            batches = iter_import_batches(
                model_instances,
                max_records=args.max_batch_records,
                max_bytes=args.max_batch_bytes,
            )
            imported = 0
            failed = 0
            errors: list[Any] = []
            for index, batch in enumerate(batches, start=1):
                try:
                    result = await client.import_data(
                        admin_key=admin_key,
                        context_surface_id=surface_id,
                        records=batch,
                        on_conflict="overwrite",
                        on_error="fail_fast",
                    )
                except Exception as exc:
                    print(
                        f"  {class_name}: failed while importing batch "
                        f"{index}/{len(batches)} ({len(batch)} records).",
                        file=sys.stderr,
                    )
                    print(
                        "  Try rerunning with a smaller batch, for example: "
                        f"uv run python scripts/load_data.py --domain {domain.manifest.id} "
                        "--max-batch-records 25 --max-batch-bytes 250000",
                        file=sys.stderr,
                    )
                    raise RuntimeError(
                        f"Context Surface import failed for {class_name} batch "
                        f"{index}/{len(batches)}"
                    ) from exc
                imported += result.imported
                failed += result.failed
                errors.extend(result.errors or [])
            suffix = f" in {len(batches)} batches" if len(batches) > 1 else ""
            print(f"  {class_name}: imported={imported}, failed={failed}{suffix}")
            for err in errors:
                print(f"    Error: {err}")

    summary = domain.write_dataset_meta(settings=settings, records=raw_records)
    print(f"  Wrote dataset summary → {domain.manifest.namespace.dataset_meta_key}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
