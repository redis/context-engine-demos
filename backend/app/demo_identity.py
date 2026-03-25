from __future__ import annotations

import os
from typing import Final

DEFAULT_USER: Final[dict[str, str]] = {
    "user_id": "CUST_DEMO_001",
    "name": "Alex Rivera",
    "email": "alex.rivera@example.com",
}


def get_current_user() -> dict[str, str]:
    return {
        "user_id": os.getenv("DEMO_USER_ID", DEFAULT_USER["user_id"]),
        "name": os.getenv("DEMO_USER_NAME", DEFAULT_USER["name"]),
        "email": os.getenv("DEMO_USER_EMAIL", DEFAULT_USER["email"]),
    }

