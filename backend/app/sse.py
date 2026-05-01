from __future__ import annotations

import json
from typing import Any


def format_sse_event(event_type: str, **fields: Any) -> str:
    """Return one SSE ``data:`` line (JSON payload).

    Common ``event_type`` values:

    - ``text-delta``, ``status``, ``tool-call``, ``tool-result``, ``thinking-step``, …
    - ``error`` — structured failure. Prefer fields ``errorCode`` (e.g.
      ``\"budget_exceeded\"``, ``\"openai_error\"``) and ``message`` (human-readable).
      Clients should still wait for a terminal ``done`` event after ``error``.
    - ``done`` — stream finished; includes ``totalElapsedMs`` when emitted from the backend.
    """
    return f"data: {json.dumps({'type': event_type, **fields})}\n\n"
