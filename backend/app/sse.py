from __future__ import annotations

import json
from typing import Any


def format_sse_event(event_type: str, **fields: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **fields})}\n\n"
