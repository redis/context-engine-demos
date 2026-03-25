"""Load Reddish JSONL data via the Context Surfaces import_data API.

Uses UnifiedClient.import_data() as recommended by the SDK docs.
Also writes a dataset metadata key directly to Redis for the internal
dataset_overview tool.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from context_surfaces import UnifiedClient  # noqa: E402

from backend.app.redis_connection import create_redis_client  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402
from schemas.reddash_schema import ENTITY_BY_FILE  # noqa: E402

# Import the generated ContextModel classes
from backend.app.context_surfaces.reddash_models import (  # noqa: E402
    Customer,
    DeliveryEvent,
    Driver,
    Order,
    OrderItem,
    Payment,
    Policy,
    Restaurant,
    SupportTicket,
)

OUTPUT_DIR = ROOT / "output"

MODEL_BY_CLASS_NAME: dict[str, type] = {
    "Customer": Customer,
    "Restaurant": Restaurant,
    "Driver": Driver,
    "Order": Order,
    "OrderItem": OrderItem,
    "DeliveryEvent": DeliveryEvent,
    "Payment": Payment,
    "SupportTicket": SupportTicket,
    "Policy": Policy,
}


def load_records() -> dict[str, list[dict[str, Any]]]:
    payloads: dict[str, list[dict[str, Any]]] = {}
    for file_name, entity in ENTITY_BY_FILE.items():
        path = OUTPUT_DIR / file_name
        rows: list[dict[str, Any]] = []
        with path.open() as handle:
            for line in handle:
                rows.append(json.loads(line))
        payloads[entity.class_name] = rows
    return payloads


def write_dataset_meta(settings: Any, records: dict[str, list[dict[str, Any]]]) -> None:
    """Write a small metadata summary directly to Redis for the dataset_overview tool."""
    summary = {
        "customers": len(records.get("Customer", [])),
        "restaurants": len(records.get("Restaurant", [])),
        "drivers": len(records.get("Driver", [])),
        "orders": len(records.get("Order", [])),
        "order_items": len(records.get("OrderItem", [])),
        "delivery_events": len(records.get("DeliveryEvent", [])),
        "payments": len(records.get("Payment", [])),
        "support_tickets": len(records.get("SupportTicket", [])),
        "policies": len(records.get("Policy", [])),
    }
    client = create_redis_client(settings)
    client.execute_command(
        "JSON.SET", "reddash:meta:dataset", "$", json.dumps(summary, ensure_ascii=False),
    )
    print("  Wrote dataset summary → reddash:meta:dataset")


async def main() -> None:
    settings = get_settings()
    admin_key = settings.ctx_admin_key
    surface_id = settings.ctx_surface_id

    if not admin_key:
        print("CTX_ADMIN_KEY is not set in .env")
        sys.exit(1)
    if not surface_id:
        print("CTX_SURFACE_ID is not set in .env. Run 'make setup-surface' first.")
        sys.exit(1)

    raw_records = load_records()

    async with UnifiedClient() as client:
        for class_name, rows in raw_records.items():
            model_cls = MODEL_BY_CLASS_NAME[class_name]
            # Instantiate ContextModel objects from dicts
            model_instances = [model_cls(**row) for row in rows]

            result = await client.import_data(
                admin_key=admin_key,
                context_surface_id=surface_id,
                records=model_instances,
                on_conflict="overwrite",
                on_error="fail_fast",
            )
            print(f"  {class_name}: imported={result.imported}, failed={result.failed}")
            if result.errors:
                for err in result.errors:
                    print(f"    Error: {err}")

    # Write metadata key for the dataset_overview internal tool
    write_dataset_meta(settings, raw_records)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

