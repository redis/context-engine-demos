"""Reddish data-model definitions – single source of truth.

Each EntitySpec drives:
  • ContextModel code generation  (scripts/generate_reddash_models.py)
  • Redis Search index creation   (scripts/load_reddash_data.py)
  • Sample-data generation        (scripts/generate_demo_data.py)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_hint: str
    description: str
    index: str | None = None
    weight: float | None = None
    no_stem: bool = False
    sortable: bool = False
    is_key_component: bool = False
    default_factory: str | None = None
    # vector-specific
    vector_dim: int | None = None
    distance_metric: str | None = None


@dataclass(frozen=True)
class RelationshipSpec:
    name: str
    description: str
    source_field: str


@dataclass(frozen=True)
class EntitySpec:
    class_name: str
    redis_key_template: str
    file_name: str
    id_field: str
    fields: tuple[FieldSpec, ...]
    relationships: tuple[RelationshipSpec, ...] = field(default_factory=tuple)


ENTITY_SPECS: tuple[EntitySpec, ...] = (
    # ── Customer ────────────────────────────────────────
    EntitySpec(
        class_name="Customer",
        redis_key_template="reddash_customer:{customer_id}",
        file_name="customers.jsonl",
        id_field="customer_id",
        fields=(
            FieldSpec("customer_id", "str", "Unique customer identifier", is_key_component=True),
            FieldSpec("name", "str", "Customer full name", index="text", weight=2.0),
            FieldSpec("email", "str", "Customer email", index="text", weight=1.5, no_stem=True),
            FieldSpec("phone", "str | None", "Phone number"),
            FieldSpec("account_status", "str", "Account status: active, suspended, deactivated", index="tag"),
            FieldSpec("membership_tier", "str", "Subscription tier: none, plus, premium", index="tag"),
            FieldSpec("city", "str", "Primary city", index="tag"),
            FieldSpec("default_address", "str | None", "Default delivery address"),
            FieldSpec("lifetime_orders", "int", "Total orders placed", index="numeric", sortable=True),
            FieldSpec("account_created_at", "str", "ISO timestamp of account creation"),
        ),
        relationships=(
            RelationshipSpec("orders", "Orders placed by this customer", "customer_id"),
        ),
    ),
    # ── Restaurant ──────────────────────────────────────
    EntitySpec(
        class_name="Restaurant",
        redis_key_template="reddash_restaurant:{restaurant_id}",
        file_name="restaurants.jsonl",
        id_field="restaurant_id",
        fields=(
            FieldSpec("restaurant_id", "str", "Unique restaurant identifier", is_key_component=True),
            FieldSpec("name", "str", "Restaurant name", index="text", weight=2.0),
            FieldSpec("cuisine_type", "str", "Cuisine category", index="tag"),
            FieldSpec("city", "str", "Restaurant city", index="tag"),
            FieldSpec("address", "str | None", "Street address"),
            FieldSpec("rating", "float", "Average rating 1-5", index="numeric", sortable=True),
            FieldSpec("avg_prep_time_mins", "int", "Average food preparation time in minutes", index="numeric"),
            FieldSpec("status", "str", "Operating status: open, closed, temporarily_closed", index="tag"),
        ),
        relationships=(
            RelationshipSpec("orders", "Orders from this restaurant", "restaurant_id"),
        ),
    ),
    # ── Driver ──────────────────────────────────────────
    EntitySpec(
        class_name="Driver",
        redis_key_template="reddash_driver:{driver_id}",
        file_name="drivers.jsonl",
        id_field="driver_id",
        fields=(
            FieldSpec("driver_id", "str", "Unique driver identifier", is_key_component=True),
            FieldSpec("name", "str", "Driver full name", index="text", weight=2.0),
            FieldSpec("phone", "str | None", "Driver phone number"),
            FieldSpec("vehicle_type", "str", "Vehicle type: car, bike, scooter", index="tag"),
            FieldSpec("current_status", "str", "Status: available, en_route, at_restaurant, delivering, offline", index="tag"),
            FieldSpec("rating", "float", "Average driver rating 1-5", index="numeric", sortable=True),
            FieldSpec("city", "str", "Operating city", index="tag"),
            FieldSpec("active_order_id", "str | None", "Currently assigned order ID", index="tag"),
            FieldSpec("status_update", "str | None", "Driver's latest status message about current delivery", index="text"),
            FieldSpec("status_updated_at", "str | None", "ISO timestamp of last status update"),
        ),
    ),
    # ── Order ───────────────────────────────────────────
    EntitySpec(
        class_name="Order",
        redis_key_template="reddash_order:{order_id}",
        file_name="orders.jsonl",
        id_field="order_id",
        fields=(
            FieldSpec("order_id", "str", "Unique order identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer who placed the order", index="tag"),
            FieldSpec("restaurant_id", "str", "Fulfilling restaurant", index="tag"),
            FieldSpec("driver_id", "str | None", "Assigned delivery driver", index="tag"),
            FieldSpec("status", "str", "Order status: placed, confirmed, preparing, ready, picked_up, in_transit, delivered, cancelled", index="tag"),
            FieldSpec("order_total", "float", "Total amount charged", index="numeric", sortable=True),
            FieldSpec("items_summary", "str", "Readable summary of items ordered", index="text"),
            FieldSpec("placed_at", "str", "ISO timestamp when order was placed"),
            FieldSpec("estimated_delivery", "str | None", "ISO timestamp of estimated delivery"),
            FieldSpec("delivered_at", "str | None", "ISO timestamp of actual delivery"),
            FieldSpec("delivery_address", "str | None", "Delivery address for this order"),
            FieldSpec("city", "str", "Delivery city", index="tag"),
            FieldSpec("restaurant_name", "str | None", "Denormalized restaurant name", index="text", weight=1.2),
            FieldSpec("driver_name", "str | None", "Denormalized driver name"),
            FieldSpec("cancelled_at", "str | None", "ISO timestamp if cancelled"),
            FieldSpec("cancellation_reason", "str | None", "Reason for cancellation"),
        ),
        relationships=(
            RelationshipSpec("customer", "Customer who placed the order", "customer_id"),
            RelationshipSpec("restaurant", "Restaurant fulfilling the order", "restaurant_id"),
            RelationshipSpec("driver", "Driver delivering the order", "driver_id"),
        ),
    ),
    # ── OrderItem ───────────────────────────────────────
    EntitySpec(
        class_name="OrderItem",
        redis_key_template="reddash_order_item:{item_id}",
        file_name="order_items.jsonl",
        id_field="item_id",
        fields=(
            FieldSpec("item_id", "str", "Unique item identifier", is_key_component=True),
            FieldSpec("order_id", "str", "Parent order", index="tag"),
            FieldSpec("item_name", "str", "Name of the menu item", index="text"),
            FieldSpec("quantity", "int", "Quantity ordered", index="numeric"),
            FieldSpec("unit_price", "float", "Price per unit", index="numeric"),
            FieldSpec("modifications", "str | None", "Modifications: extra spicy, no onions, etc."),
            FieldSpec("special_instructions", "str | None", "Special delivery instructions"),
        ),
        relationships=(
            RelationshipSpec("order", "Parent order", "order_id"),
        ),
    ),
    # ── DeliveryEvent ───────────────────────────────────
    EntitySpec(
        class_name="DeliveryEvent",
        redis_key_template="reddash_delivery_event:{event_id}",
        file_name="delivery_events.jsonl",
        id_field="event_id",
        fields=(
            FieldSpec("event_id", "str", "Unique event identifier", is_key_component=True),
            FieldSpec("order_id", "str", "Associated order", index="tag"),
            FieldSpec("event_type", "str", "Event type: placed, confirmed, preparing, ready, driver_assigned, picked_up, en_route, delivered, cancelled", index="tag"),
            FieldSpec("timestamp", "str", "ISO timestamp of event"),
            FieldSpec("description", "str", "Human-readable event description", index="text"),
            FieldSpec("actor", "str", "Who triggered it: customer, restaurant, driver, system", index="tag"),
        ),
        relationships=(
            RelationshipSpec("order", "Associated order", "order_id"),
        ),
    ),
    # ── Payment ─────────────────────────────────────────
    EntitySpec(
        class_name="Payment",
        redis_key_template="reddash_payment:{payment_id}",
        file_name="payments.jsonl",
        id_field="payment_id",
        fields=(
            FieldSpec("payment_id", "str", "Unique payment identifier", is_key_component=True),
            FieldSpec("order_id", "str", "Associated order", index="tag"),
            FieldSpec("customer_id", "str", "Customer who paid", index="tag"),
            FieldSpec("subtotal", "float", "Food subtotal", index="numeric"),
            FieldSpec("delivery_fee", "float", "Delivery fee", index="numeric"),
            FieldSpec("service_fee", "float", "Service fee", index="numeric"),
            FieldSpec("tax", "float", "Tax amount", index="numeric"),
            FieldSpec("tip", "float", "Driver tip", index="numeric"),
            FieldSpec("discount", "float", "Applied discount", index="numeric"),
            FieldSpec("total_charged", "float", "Final amount charged", index="numeric", sortable=True),
            FieldSpec("payment_method", "str", "Payment method: visa_4242, mastercard_8888, apple_pay", index="tag"),
            FieldSpec("promo_code", "str | None", "Applied promo code", index="tag"),
            FieldSpec("refund_amount", "float", "Refund amount (0 if none)", index="numeric"),
            FieldSpec("refund_status", "str", "Refund status: none, pending, completed", index="tag"),
            FieldSpec("refund_reason", "str | None", "Reason for refund"),
        ),
        relationships=(
            RelationshipSpec("order", "Associated order", "order_id"),
            RelationshipSpec("customer", "Customer who paid", "customer_id"),
        ),
    ),
    # ── SupportTicket ───────────────────────────────────
    EntitySpec(
        class_name="SupportTicket",
        redis_key_template="reddash_support_ticket:{ticket_id}",
        file_name="support_tickets.jsonl",
        id_field="ticket_id",
        fields=(
            FieldSpec("ticket_id", "str", "Unique ticket identifier", is_key_component=True),
            FieldSpec("customer_id", "str", "Customer who filed the ticket", index="tag"),
            FieldSpec("order_id", "str | None", "Related order", index="tag"),
            FieldSpec("category", "str", "Category: late_delivery, wrong_item, missing_item, billing, account, other", index="tag"),
            FieldSpec("status", "str", "Status: open, in_progress, resolved, closed", index="tag"),
            FieldSpec("created_at", "str", "ISO timestamp when ticket was created"),
            FieldSpec("resolved_at", "str | None", "ISO timestamp when resolved"),
            FieldSpec("summary", "str", "Ticket summary", index="text"),
            FieldSpec("resolution", "str | None", "How it was resolved"),
        ),
        relationships=(
            RelationshipSpec("customer", "Customer who filed the ticket", "customer_id"),
            RelationshipSpec("order", "Related order", "order_id"),
        ),
    ),
    # ── Policy ──────────────────────────────────────────
    EntitySpec(
        class_name="Policy",
        redis_key_template="reddash_policy:{policy_id}",
        file_name="policies.jsonl",
        id_field="policy_id",
        fields=(
            FieldSpec("policy_id", "str", "Unique policy identifier", is_key_component=True),
            FieldSpec("title", "str", "Policy title", index="text", weight=2.0),
            FieldSpec("category", "str", "Policy category", index="tag"),
            FieldSpec("content", "str", "Full policy text", index="text"),
            FieldSpec(
                "content_embedding", "list[float]", "Vector embedding of policy content",
                index="vector", vector_dim=1536, distance_metric="COSINE",
            ),
        ),
    ),
)

ENTITY_BY_FILE = {spec.file_name: spec for spec in ENTITY_SPECS}
ENTITY_BY_CLASS = {spec.class_name: spec for spec in ENTITY_SPECS}

