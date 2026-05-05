"""Generate sample data for the Reddash delivery demo."""

from __future__ import annotations

import json
import os
import sys
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "reddash"


def ts(dt: datetime) -> str:
    return dt.isoformat()


now = datetime.now(timezone.utc)


def embed(texts: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    resp = client.embeddings.create(
        input=texts, model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    return [item.embedding for item in resp.data]


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMERS (5)
# ═══════════════════════════════════════════════════════════════════════════

DEMO_USER_ID = "CUST_DEMO_001"

CUSTOMERS = [
    {"customer_id": DEMO_USER_ID, "name": "Alex Rivera", "email": "alex.rivera@example.com",
     "phone": "+1-555-0142", "account_status": "active", "membership_tier": "plus",
     "city": "San Francisco", "default_address": "742 Evergreen Terrace, SF, CA 94110",
     "lifetime_orders": 47, "account_created_at": ts(now - timedelta(days=390))},
    {"customer_id": "CUST_002", "name": "Jordan Lee", "email": "jordan.lee@example.com",
     "phone": "+1-555-0201", "account_status": "active", "membership_tier": "premium",
     "city": "San Francisco", "default_address": "88 Mission St, SF, CA 94105",
     "lifetime_orders": 112, "account_created_at": ts(now - timedelta(days=820))},
    {"customer_id": "CUST_003", "name": "Sam Patel", "email": "sam.patel@example.com",
     "phone": "+1-555-0302", "account_status": "active", "membership_tier": "none",
     "city": "New York", "default_address": "350 5th Ave, NY, NY 10118",
     "lifetime_orders": 23, "account_created_at": ts(now - timedelta(days=180))},
    {"customer_id": "CUST_004", "name": "Morgan Chen", "email": "morgan.chen@example.com",
     "phone": "+1-555-0403", "account_status": "suspended", "membership_tier": "none",
     "city": "Austin", "default_address": "1600 Congress Ave, Austin, TX 78701",
     "lifetime_orders": 8, "account_created_at": ts(now - timedelta(days=95))},
    {"customer_id": "CUST_005", "name": "Taylor Kim", "email": "taylor.kim@example.com",
     "phone": "+1-555-0504", "account_status": "active", "membership_tier": "plus",
     "city": "New York", "default_address": "200 Park Ave, NY, NY 10166",
     "lifetime_orders": 61, "account_created_at": ts(now - timedelta(days=540))},
]


# ═══════════════════════════════════════════════════════════════════════════
#  RESTAURANTS (8)
# ═══════════════════════════════════════════════════════════════════════════

RESTAURANTS = [
    {"restaurant_id": "REST_001", "name": "Sakura Sushi", "cuisine_type": "Japanese",
     "city": "San Francisco", "address": "1234 Geary Blvd, SF, CA 94115",
     "rating": 4.7, "avg_prep_time_mins": 22, "status": "open"},
    {"restaurant_id": "REST_002", "name": "Bella Napoli", "cuisine_type": "Italian",
     "city": "San Francisco", "address": "567 Columbus Ave, SF, CA 94133",
     "rating": 4.5, "avg_prep_time_mins": 28, "status": "open"},
    {"restaurant_id": "REST_003", "name": "Taco Loco", "cuisine_type": "Mexican",
     "city": "Austin", "address": "801 S Congress Ave, Austin, TX 78704",
     "rating": 4.3, "avg_prep_time_mins": 15, "status": "open"},
    {"restaurant_id": "REST_004", "name": "Golden Dragon", "cuisine_type": "Chinese",
     "city": "New York", "address": "42 Mott St, NY, NY 10013",
     "rating": 4.4, "avg_prep_time_mins": 20, "status": "open"},
    {"restaurant_id": "REST_005", "name": "Burger Barn", "cuisine_type": "American",
     "city": "San Francisco", "address": "3200 24th St, SF, CA 94110",
     "rating": 4.1, "avg_prep_time_mins": 12, "status": "open"},
    {"restaurant_id": "REST_006", "name": "Spice Route", "cuisine_type": "Indian",
     "city": "New York", "address": "101 Lexington Ave, NY, NY 10016",
     "rating": 4.6, "avg_prep_time_mins": 30, "status": "open"},
    {"restaurant_id": "REST_007", "name": "Le Petit Bistro", "cuisine_type": "French",
     "city": "San Francisco", "address": "2100 Union St, SF, CA 94123",
     "rating": 4.8, "avg_prep_time_mins": 35, "status": "temporarily_closed"},
    {"restaurant_id": "REST_008", "name": "Seoul Kitchen", "cuisine_type": "Korean",
     "city": "Austin", "address": "4500 Guadalupe St, Austin, TX 78751",
     "rating": 4.2, "avg_prep_time_mins": 18, "status": "open"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  DRIVERS (4)
# ═══════════════════════════════════════════════════════════════════════════

DRIVERS = [
    {"driver_id": "DRV_001", "name": "Marcus Johnson", "phone": "+1-555-7001",
     "vehicle_type": "bike", "current_status": "delivering", "rating": 4.8,
     "city": "San Francisco", "active_order_id": "ORD_001",
     "status_update": "Got a flat tire on Market St, had to walk the bike for a few blocks. Back on the road now, about 10 min out.",
     "status_updated_at": ts(now - timedelta(minutes=8))},
    {"driver_id": "DRV_002", "name": "Priya Sharma", "phone": "+1-555-7002",
     "vehicle_type": "car", "current_status": "delivering", "rating": 4.9,
     "city": "San Francisco", "active_order_id": "ORD_008",
     "status_update": "Picked up and heading to drop-off, traffic is light.",
     "status_updated_at": ts(now - timedelta(minutes=5))},
    {"driver_id": "DRV_003", "name": "Diego Ramirez", "phone": "+1-555-7003",
     "vehicle_type": "scooter", "current_status": "available", "rating": 4.5,
     "city": "New York", "active_order_id": None,
     "status_update": None, "status_updated_at": None},
    {"driver_id": "DRV_004", "name": "Kenji Tanaka", "phone": "+1-555-7004",
     "vehicle_type": "car", "current_status": "offline", "rating": 4.6,
     "city": "Austin", "active_order_id": None,
     "status_update": None, "status_updated_at": None},
]


# ORD_001: demo user's LATE order (placed 70min ago, was due 30min ago, still in transit)
ord1_placed = now - timedelta(minutes=70)
ord1_est    = now - timedelta(minutes=30)

ORDERS = [
    {"order_id": "ORD_001", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_001",
     "driver_id": "DRV_001", "status": "in_transit", "order_total": 42.50,
     "items_summary": "Spicy Tuna Roll x2, Miso Soup, Edamame",
     "placed_at": ts(ord1_placed), "estimated_delivery": ts(ord1_est), "delivered_at": None,
     "delivery_address": "742 Evergreen Terrace, SF, CA 94110",
     "city": "San Francisco", "restaurant_name": "Sakura Sushi", "driver_name": "Marcus Johnson",
     "cancelled_at": None, "cancellation_reason": None},

    {"order_id": "ORD_002", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_002",
     "driver_id": "DRV_002", "status": "delivered", "order_total": 38.00,
     "items_summary": "Margherita Pizza, Caesar Salad",
     "placed_at": ts(now - timedelta(days=2)), "estimated_delivery": ts(now - timedelta(days=2) + timedelta(minutes=35)),
     "delivered_at": ts(now - timedelta(days=2) + timedelta(minutes=32)),
     "delivery_address": "742 Evergreen Terrace, SF, CA 94110",
     "city": "San Francisco", "restaurant_name": "Bella Napoli", "driver_name": "Priya Sharma",
     "cancelled_at": None, "cancellation_reason": None},

    {"order_id": "ORD_003", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_005",
     "driver_id": "DRV_001", "status": "delivered", "order_total": 22.99,
     "items_summary": "Classic Burger, Fries, Milkshake",
     "placed_at": ts(now - timedelta(days=5)), "estimated_delivery": ts(now - timedelta(days=5) + timedelta(minutes=25)),
     "delivered_at": ts(now - timedelta(days=5) + timedelta(minutes=28)),
     "delivery_address": "742 Evergreen Terrace, SF, CA 94110",
     "city": "San Francisco", "restaurant_name": "Burger Barn", "driver_name": "Marcus Johnson",
     "cancelled_at": None, "cancellation_reason": None},

    {"order_id": "ORD_004", "customer_id": DEMO_USER_ID, "restaurant_id": "REST_005",
     "driver_id": "DRV_002", "status": "delivered", "order_total": 15.99,
     "items_summary": "Veggie Burger, Side Salad",
     "placed_at": ts(now - timedelta(days=10)), "estimated_delivery": ts(now - timedelta(days=10) + timedelta(minutes=20)),
     "delivered_at": ts(now - timedelta(days=10) + timedelta(minutes=22)),
     "delivery_address": "742 Evergreen Terrace, SF, CA 94110",
     "city": "San Francisco", "restaurant_name": "Burger Barn", "driver_name": "Priya Sharma",
     "cancelled_at": None, "cancellation_reason": None},

    # Other customers
    {"order_id": "ORD_005", "customer_id": "CUST_002", "restaurant_id": "REST_002",
     "driver_id": "DRV_002", "status": "delivered", "order_total": 55.00,
     "items_summary": "Pasta Carbonara, Tiramisu, Garlic Bread",
     "placed_at": ts(now - timedelta(days=1)), "estimated_delivery": ts(now - timedelta(days=1) + timedelta(minutes=40)),
     "delivered_at": ts(now - timedelta(days=1) + timedelta(minutes=38)),
     "delivery_address": "88 Mission St, SF, CA 94105",
     "city": "San Francisco", "restaurant_name": "Bella Napoli", "driver_name": "Priya Sharma",
     "cancelled_at": None, "cancellation_reason": None},

    {"order_id": "ORD_006", "customer_id": "CUST_003", "restaurant_id": "REST_004",
     "driver_id": "DRV_003", "status": "delivered", "order_total": 28.75,
     "items_summary": "Kung Pao Chicken, Fried Rice, Spring Rolls",
     "placed_at": ts(now - timedelta(days=3)), "estimated_delivery": ts(now - timedelta(days=3) + timedelta(minutes=45)),
     "delivered_at": ts(now - timedelta(days=3) + timedelta(minutes=50)),
     "delivery_address": "350 5th Ave, NY, NY 10118",
     "city": "New York", "restaurant_name": "Golden Dragon", "driver_name": "Diego Ramirez",
     "cancelled_at": None, "cancellation_reason": None},

    {"order_id": "ORD_007", "customer_id": "CUST_004", "restaurant_id": "REST_003",
     "driver_id": None, "status": "cancelled", "order_total": 19.99,
     "items_summary": "Burrito Bowl, Chips & Guac",
     "placed_at": ts(now - timedelta(days=1)), "estimated_delivery": None, "delivered_at": None,
     "delivery_address": "1600 Congress Ave, Austin, TX 78701",
     "city": "Austin", "restaurant_name": "Taco Loco", "driver_name": None,
     "cancelled_at": ts(now - timedelta(days=1) + timedelta(minutes=5)),
     "cancellation_reason": "Customer requested cancellation before preparation"},

    {"order_id": "ORD_008", "customer_id": "CUST_002", "restaurant_id": "REST_005",
     "driver_id": "DRV_001", "status": "in_transit", "order_total": 18.50,
     "items_summary": "Cheeseburger, Onion Rings",
     "placed_at": ts(now - timedelta(minutes=30)), "estimated_delivery": ts(now + timedelta(minutes=10)),
     "delivered_at": None,
     "delivery_address": "88 Mission St, SF, CA 94105",
     "city": "San Francisco", "restaurant_name": "Burger Barn", "driver_name": "Marcus Johnson",
     "cancelled_at": None, "cancellation_reason": None},
]


# ═══════════════════════════════════════════════════════════════════════════
#  ORDER ITEMS — line items for every order
# ═══════════════════════════════════════════════════════════════════════════

ORDER_ITEMS = [
    # ORD_001 (demo user late order)
    {"item_id": "ITEM_001", "order_id": "ORD_001", "item_name": "Spicy Tuna Roll", "quantity": 2,
     "unit_price": 14.00, "modifications": "extra spicy", "special_instructions": None},
    {"item_id": "ITEM_002", "order_id": "ORD_001", "item_name": "Miso Soup", "quantity": 1,
     "unit_price": 5.50, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_003", "order_id": "ORD_001", "item_name": "Edamame", "quantity": 1,
     "unit_price": 4.50, "modifications": "lightly salted", "special_instructions": None},
    # ORD_002
    {"item_id": "ITEM_004", "order_id": "ORD_002", "item_name": "Margherita Pizza", "quantity": 1,
     "unit_price": 18.00, "modifications": "extra basil", "special_instructions": None},
    {"item_id": "ITEM_005", "order_id": "ORD_002", "item_name": "Caesar Salad", "quantity": 1,
     "unit_price": 12.00, "modifications": "dressing on the side", "special_instructions": None},
    # ORD_003
    {"item_id": "ITEM_006", "order_id": "ORD_003", "item_name": "Classic Burger", "quantity": 1,
     "unit_price": 11.99, "modifications": "no pickles", "special_instructions": None},
    {"item_id": "ITEM_007", "order_id": "ORD_003", "item_name": "Fries", "quantity": 1,
     "unit_price": 4.50, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_008", "order_id": "ORD_003", "item_name": "Milkshake", "quantity": 1,
     "unit_price": 6.50, "modifications": "chocolate", "special_instructions": None},
    # ORD_004
    {"item_id": "ITEM_009", "order_id": "ORD_004", "item_name": "Veggie Burger", "quantity": 1,
     "unit_price": 10.99, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_010", "order_id": "ORD_004", "item_name": "Side Salad", "quantity": 1,
     "unit_price": 5.00, "modifications": None, "special_instructions": None},
    # ORD_005
    {"item_id": "ITEM_011", "order_id": "ORD_005", "item_name": "Pasta Carbonara", "quantity": 1,
     "unit_price": 22.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_012", "order_id": "ORD_005", "item_name": "Tiramisu", "quantity": 1,
     "unit_price": 12.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_013", "order_id": "ORD_005", "item_name": "Garlic Bread", "quantity": 1,
     "unit_price": 7.00, "modifications": None, "special_instructions": None},
    # ORD_006
    {"item_id": "ITEM_014", "order_id": "ORD_006", "item_name": "Kung Pao Chicken", "quantity": 1,
     "unit_price": 15.75, "modifications": "mild", "special_instructions": None},
    {"item_id": "ITEM_015", "order_id": "ORD_006", "item_name": "Fried Rice", "quantity": 1,
     "unit_price": 8.00, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_016", "order_id": "ORD_006", "item_name": "Spring Rolls", "quantity": 2,
     "unit_price": 3.50, "modifications": None, "special_instructions": None},
    # ORD_007 (cancelled)
    {"item_id": "ITEM_017", "order_id": "ORD_007", "item_name": "Burrito Bowl", "quantity": 1,
     "unit_price": 13.99, "modifications": "no sour cream", "special_instructions": None},
    {"item_id": "ITEM_018", "order_id": "ORD_007", "item_name": "Chips & Guac", "quantity": 1,
     "unit_price": 6.00, "modifications": None, "special_instructions": None},
    # ORD_008
    {"item_id": "ITEM_019", "order_id": "ORD_008", "item_name": "Cheeseburger", "quantity": 1,
     "unit_price": 12.50, "modifications": None, "special_instructions": None},
    {"item_id": "ITEM_020", "order_id": "ORD_008", "item_name": "Onion Rings", "quantity": 1,
     "unit_price": 6.00, "modifications": None, "special_instructions": None},
]


# ═══════════════════════════════════════════════════════════════════════════
#  DELIVERY EVENTS — timeline for ORD_001 (the late order) and a few others
# ═══════════════════════════════════════════════════════════════════════════

DELIVERY_EVENTS = [
    # ORD_001 timeline — the key story: 16-min gap between food ready and driver assignment
    {"event_id": "EVT_001", "order_id": "ORD_001", "event_type": "placed",
     "timestamp": ts(ord1_placed), "description": "Order placed by Alex Rivera", "actor": "customer"},
    {"event_id": "EVT_002", "order_id": "ORD_001", "event_type": "confirmed",
     "timestamp": ts(ord1_placed + timedelta(minutes=2)), "description": "Restaurant confirmed order", "actor": "restaurant"},
    {"event_id": "EVT_003", "order_id": "ORD_001", "event_type": "preparing",
     "timestamp": ts(ord1_placed + timedelta(minutes=3)), "description": "Restaurant started preparing food", "actor": "restaurant"},
    {"event_id": "EVT_004", "order_id": "ORD_001", "event_type": "ready",
     "timestamp": ts(ord1_placed + timedelta(minutes=22)), "description": "Food ready for pickup", "actor": "restaurant"},
    {"event_id": "EVT_005", "order_id": "ORD_001", "event_type": "driver_assigned",
     "timestamp": ts(ord1_placed + timedelta(minutes=38)), "description": "Driver assigned: Marcus Johnson (bike)", "actor": "system"},
    {"event_id": "EVT_006", "order_id": "ORD_001", "event_type": "picked_up",
     "timestamp": ts(ord1_placed + timedelta(minutes=45)), "description": "Driver picked up order from Sakura Sushi", "actor": "driver"},
    {"event_id": "EVT_007", "order_id": "ORD_001", "event_type": "en_route",
     "timestamp": ts(ord1_placed + timedelta(minutes=46)), "description": "Driver en route to delivery address", "actor": "driver"},
    # ORD_002 (delivered normally)
    {"event_id": "EVT_008", "order_id": "ORD_002", "event_type": "placed",
     "timestamp": ts(now - timedelta(days=2)), "description": "Order placed", "actor": "customer"},
    {"event_id": "EVT_009", "order_id": "ORD_002", "event_type": "delivered",
     "timestamp": ts(now - timedelta(days=2) + timedelta(minutes=32)), "description": "Order delivered", "actor": "driver"},
    # ORD_007 (cancelled)
    {"event_id": "EVT_010", "order_id": "ORD_007", "event_type": "placed",
     "timestamp": ts(now - timedelta(days=1)), "description": "Order placed", "actor": "customer"},
    {"event_id": "EVT_011", "order_id": "ORD_007", "event_type": "cancelled",
     "timestamp": ts(now - timedelta(days=1) + timedelta(minutes=5)),
     "description": "Cancelled by customer before restaurant started preparation", "actor": "customer"},
]


# ═══════════════════════════════════════════════════════════════════════════
#  PAYMENTS — one per order with full fee breakdown
# ═══════════════════════════════════════════════════════════════════════════

PAYMENTS = [
    {"payment_id": "PAY_001", "order_id": "ORD_001", "customer_id": DEMO_USER_ID,
     "subtotal": 38.00, "delivery_fee": 0.00, "service_fee": 2.50, "tax": 2.00, "tip": 5.00,
     "discount": 5.00, "total_charged": 42.50, "payment_method": "visa_4242", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    {"payment_id": "PAY_002", "order_id": "ORD_002", "customer_id": DEMO_USER_ID,
     "subtotal": 30.00, "delivery_fee": 0.00, "service_fee": 2.50, "tax": 2.50, "tip": 3.00,
     "discount": 0.00, "total_charged": 38.00, "payment_method": "visa_4242", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    {"payment_id": "PAY_003", "order_id": "ORD_003", "customer_id": DEMO_USER_ID,
     "subtotal": 22.99, "delivery_fee": 0.00, "service_fee": 1.50, "tax": 1.50, "tip": 2.00,
     "discount": 5.00, "total_charged": 22.99, "payment_method": "apple_pay", "promo_code": "WELCOME5",
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    {"payment_id": "PAY_004", "order_id": "ORD_004", "customer_id": DEMO_USER_ID,
     "subtotal": 15.99, "delivery_fee": 0.00, "service_fee": 1.00, "tax": 1.00, "tip": 2.00,
     "discount": 4.00, "total_charged": 15.99, "payment_method": "visa_4242", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    {"payment_id": "PAY_005", "order_id": "ORD_005", "customer_id": "CUST_002",
     "subtotal": 41.00, "delivery_fee": 0.00, "service_fee": 3.50, "tax": 4.50, "tip": 6.00,
     "discount": 0.00, "total_charged": 55.00, "payment_method": "mastercard_8888", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    {"payment_id": "PAY_006", "order_id": "ORD_006", "customer_id": "CUST_003",
     "subtotal": 30.75, "delivery_fee": 3.99, "service_fee": 2.00, "tax": 2.01, "tip": 0.00,
     "discount": 10.00, "total_charged": 28.75, "payment_method": "visa_1234", "promo_code": "FIRSTORDER",
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},

    {"payment_id": "PAY_007", "order_id": "ORD_007", "customer_id": "CUST_004",
     "subtotal": 19.99, "delivery_fee": 3.99, "service_fee": 1.50, "tax": 1.50, "tip": 0.00,
     "discount": 0.00, "total_charged": 26.98, "payment_method": "visa_5678", "promo_code": None,
     "refund_amount": 26.98, "refund_status": "completed", "refund_reason": "Order cancelled before preparation"},

    {"payment_id": "PAY_008", "order_id": "ORD_008", "customer_id": "CUST_002",
     "subtotal": 18.50, "delivery_fee": 0.00, "service_fee": 1.50, "tax": 1.50, "tip": 3.00,
     "discount": 6.00, "total_charged": 18.50, "payment_method": "mastercard_8888", "promo_code": None,
     "refund_amount": 0.00, "refund_status": "none", "refund_reason": None},
]


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPORT TICKETS — past issues for the demo user
# ═══════════════════════════════════════════════════════════════════════════

SUPPORT_TICKETS = [
    {"ticket_id": "TKT_001", "customer_id": DEMO_USER_ID, "order_id": "ORD_003",
     "category": "missing_item", "status": "resolved",
     "created_at": ts(now - timedelta(days=5, hours=1)),
     "resolved_at": ts(now - timedelta(days=5)),
     "summary": "Milkshake was missing from my order",
     "resolution": "Refund of $6.50 issued to original payment method."},
    {"ticket_id": "TKT_002", "customer_id": "CUST_004", "order_id": "ORD_007",
     "category": "billing", "status": "resolved",
     "created_at": ts(now - timedelta(days=1, hours=2)),
     "resolved_at": ts(now - timedelta(days=1)),
     "summary": "Charged for cancelled order",
     "resolution": "Full refund of $26.98 processed."},
    {"ticket_id": "TKT_003", "customer_id": "CUST_003", "order_id": "ORD_006",
     "category": "late_delivery", "status": "closed",
     "created_at": ts(now - timedelta(days=3)),
     "resolved_at": ts(now - timedelta(days=3, hours=-1)),
     "summary": "Delivery was 5 minutes late",
     "resolution": "Delay under 15 minutes. No credit applied per Late Delivery Policy."},
]


# ═══════════════════════════════════════════════════════════════════════════
#  POLICIES (8) — embedding generated at runtime
# ═══════════════════════════════════════════════════════════════════════════

POLICIES_TEXT = [
    {"policy_id": "POL_001", "title": "Late Delivery Policy", "category": "delivery",
     "content": (
         "If your order is delivered more than 15 minutes past the estimated delivery time, "
         "you are eligible for a 20% credit on your next order. If the delay exceeds 30 minutes, "
         "you may request a full refund of the delivery fee. Delays over 45 minutes qualify for "
         "a full order refund. Contact support with your order ID to initiate the process."
     )},
    {"policy_id": "POL_002", "title": "Refund Policy", "category": "refund",
     "content": (
         "Refunds are available for orders that arrive with missing items, incorrect items, "
         "or quality issues. Refund requests must be submitted within 24 hours of delivery. "
         "Photo evidence may be required for quality-related claims. Refunds are processed "
         "within 3-5 business days to the original payment method."
     )},
    {"policy_id": "POL_003", "title": "Cancellation Policy", "category": "cancellation",
     "content": (
         "Orders may be cancelled free of charge within 2 minutes of placement. After the "
         "restaurant begins preparing your order, a cancellation fee of up to 30% of the order "
         "total may apply. Orders that are already picked up by a driver cannot be cancelled."
     )},
    {"policy_id": "POL_004", "title": "Delivery Tracking & ETA", "category": "delivery",
     "content": (
         "Estimated delivery times are calculated based on restaurant preparation time, driver "
         "availability, and distance. ETAs may shift due to high demand, weather, or traffic. "
         "You can track your order in real time. If your ETA changes by more than 10 minutes, "
         "you will receive a notification."
     )},
    {"policy_id": "POL_005", "title": "Customer Account Suspension", "category": "general",
     "content": (
         "Accounts may be suspended for repeated policy violations, fraudulent refund claims, "
         "or abusive behavior toward drivers or restaurant staff. Suspended accounts cannot "
         "place new orders. To appeal a suspension, contact support with your account details."
     )},
    {"policy_id": "POL_006", "title": "Membership Benefits (Plus & Premium)", "category": "general",
     "content": (
         "Plus members receive free delivery on orders over $15 and 5% cashback credits. "
         "Premium members receive free delivery on all orders, 10% cashback credits, priority "
         "driver assignment, and priority support. Benefits renew monthly."
     )},
    {"policy_id": "POL_007", "title": "Driver Delay Compensation", "category": "delivery",
     "content": (
         "When delivery delays are caused by driver-side issues (vehicle breakdown, navigation "
         "error, multi-order batching), Reddash will automatically apply a credit. Credit amount: "
         "10-20 min delay = 10% credit, 20-30 min = 20% credit, 30+ min = full refund eligibility. "
         "Premium members receive 1.5x the standard credit."
     )},
    {"policy_id": "POL_008", "title": "Food Safety & Quality", "category": "general",
     "content": (
         "All partner restaurants must comply with local health and safety regulations. "
         "If you receive food that appears unsafe or spoiled, do not consume it. Report the "
         "issue immediately for a full refund and investigation."
     )},
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — generate embeddings + write JSONL files
# ═══════════════════════════════════════════════════════════════════════════

def write_jsonl(output_dir: Path, filename: str, rows: list[dict]) -> None:
    path = output_dir / filename
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} records")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n")
        return
    lines = env_path.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={safe_value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n")


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = False,
) -> GeneratedDataset:
    del seed
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating embeddings for policies...")
    contents = [p["content"] for p in POLICIES_TEXT]
    embeddings = embed(contents)
    policies = [{**p, "content_embedding": emb} for p, emb in zip(POLICIES_TEXT, embeddings)]

    print("Writing JSONL files:")
    write_jsonl(resolved_output_dir, "customers.jsonl", CUSTOMERS)
    write_jsonl(resolved_output_dir, "restaurants.jsonl", RESTAURANTS)
    write_jsonl(resolved_output_dir, "drivers.jsonl", DRIVERS)
    write_jsonl(resolved_output_dir, "orders.jsonl", ORDERS)
    write_jsonl(resolved_output_dir, "order_items.jsonl", ORDER_ITEMS)
    write_jsonl(resolved_output_dir, "delivery_events.jsonl", DELIVERY_EVENTS)
    write_jsonl(resolved_output_dir, "payments.jsonl", PAYMENTS)
    write_jsonl(resolved_output_dir, "support_tickets.jsonl", SUPPORT_TICKETS)
    write_jsonl(resolved_output_dir, "policies.jsonl", policies)

    demo = CUSTOMERS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["customer_id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nDemo user: {demo['name']} ({demo['customer_id']})")
    print("Done.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["customer_id"],
            "DEMO_USER_NAME": demo["name"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "customers": len(CUSTOMERS),
            "restaurants": len(RESTAURANTS),
            "drivers": len(DRIVERS),
            "orders": len(ORDERS),
            "order_items": len(ORDER_ITEMS),
            "delivery_events": len(DELIVERY_EVENTS),
            "payments": len(PAYMENTS),
            "support_tickets": len(SUPPORT_TICKETS),
            "policies": len(POLICIES_TEXT),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR, update_env_file=True)


if __name__ == "__main__":
    main()
