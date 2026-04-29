"""Generated Context Surface models for the Reddash domain."""

from __future__ import annotations

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the Reddash domain."""

    __redis_key_template__ = "reddash_customer:{customer_id}"

    customer_id: str = ContextField(
        description="Unique customer identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Customer full name",
        index="text",
        weight=2.0,
    )

    email: str = ContextField(
        description="Customer email",
        index="text",
        weight=1.5,
        no_stem=True,
    )

    phone: str | None = ContextField(
        description="Phone number",
    )

    account_status: str = ContextField(
        description="Account status: active, suspended, deactivated",
        index="tag",
    )

    membership_tier: str = ContextField(
        description="Subscription tier: none, plus, premium",
        index="tag",
    )

    city: str = ContextField(
        description="Primary city",
        index="tag",
    )

    default_address: str | None = ContextField(
        description="Default delivery address",
    )

    lifetime_orders: int = ContextField(
        description="Total orders placed",
        index="numeric",
        sortable=True,
    )

    account_created_at: str = ContextField(
        description="ISO timestamp of account creation",
    )

    orders: Order = ContextRelationship(
        description="Orders placed by this customer",
        source_field="customer_id",
    )


class Restaurant(ContextModel):
    """Restaurant entity for the Reddash domain."""

    __redis_key_template__ = "reddash_restaurant:{restaurant_id}"

    restaurant_id: str = ContextField(
        description="Unique restaurant identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Restaurant name",
        index="text",
        weight=2.0,
    )

    cuisine_type: str = ContextField(
        description="Cuisine category",
        index="tag",
    )

    city: str = ContextField(
        description="Restaurant city",
        index="tag",
    )

    address: str | None = ContextField(
        description="Street address",
    )

    rating: float = ContextField(
        description="Average rating 1-5",
        index="numeric",
        sortable=True,
    )

    avg_prep_time_mins: int = ContextField(
        description="Average food preparation time in minutes",
        index="numeric",
    )

    status: str = ContextField(
        description="Operating status: open, closed, temporarily_closed",
        index="tag",
    )

    orders: Order = ContextRelationship(
        description="Orders from this restaurant",
        source_field="restaurant_id",
    )


class Driver(ContextModel):
    """Driver entity for the Reddash domain."""

    __redis_key_template__ = "reddash_driver:{driver_id}"

    driver_id: str = ContextField(
        description="Unique driver identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Driver full name",
        index="text",
        weight=2.0,
    )

    phone: str | None = ContextField(
        description="Driver phone number",
    )

    vehicle_type: str = ContextField(
        description="Vehicle type: car, bike, scooter",
        index="tag",
    )

    current_status: str = ContextField(
        description="Status: available, en_route, at_restaurant, delivering, offline",
        index="tag",
    )

    rating: float = ContextField(
        description="Average driver rating 1-5",
        index="numeric",
        sortable=True,
    )

    city: str = ContextField(
        description="Operating city",
        index="tag",
    )

    active_order_id: str | None = ContextField(
        description="Currently assigned order ID",
        index="tag",
    )

    status_update: str | None = ContextField(
        description="Driver's latest status message about current delivery",
        index="text",
    )

    status_updated_at: str | None = ContextField(
        description="ISO timestamp of last status update",
    )


class Order(ContextModel):
    """Order entity for the Reddash domain."""

    __redis_key_template__ = "reddash_order:{order_id}"

    order_id: str = ContextField(
        description="Unique order identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer who placed the order",
        index="tag",
    )

    restaurant_id: str = ContextField(
        description="Fulfilling restaurant",
        index="tag",
    )

    driver_id: str | None = ContextField(
        description="Assigned delivery driver",
        index="tag",
    )

    status: str = ContextField(
        description="Order status: placed, confirmed, preparing, ready, picked_up, in_transit, delivered, cancelled",
        index="tag",
    )

    order_total: float = ContextField(
        description="Total amount charged",
        index="numeric",
        sortable=True,
    )

    items_summary: str = ContextField(
        description="Readable summary of items ordered",
        index="text",
    )

    placed_at: str = ContextField(
        description="ISO timestamp when order was placed",
    )

    estimated_delivery: str | None = ContextField(
        description="ISO timestamp of estimated delivery",
    )

    delivered_at: str | None = ContextField(
        description="ISO timestamp of actual delivery",
    )

    delivery_address: str | None = ContextField(
        description="Delivery address for this order",
    )

    city: str = ContextField(
        description="Delivery city",
        index="tag",
    )

    restaurant_name: str | None = ContextField(
        description="Denormalized restaurant name",
        index="text",
        weight=1.2,
    )

    driver_name: str | None = ContextField(
        description="Denormalized driver name",
    )

    cancelled_at: str | None = ContextField(
        description="ISO timestamp if cancelled",
    )

    cancellation_reason: str | None = ContextField(
        description="Reason for cancellation",
    )

    customer: Customer = ContextRelationship(
        description="Customer who placed the order",
        source_field="customer_id",
    )

    restaurant: Restaurant = ContextRelationship(
        description="Restaurant fulfilling the order",
        source_field="restaurant_id",
    )

    driver: Driver = ContextRelationship(
        description="Driver delivering the order",
        source_field="driver_id",
    )


class OrderItem(ContextModel):
    """OrderItem entity for the Reddash domain."""

    __redis_key_template__ = "reddash_order_item:{item_id}"

    item_id: str = ContextField(
        description="Unique item identifier",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Parent order",
        index="tag",
    )

    item_name: str = ContextField(
        description="Name of the menu item",
        index="text",
    )

    quantity: int = ContextField(
        description="Quantity ordered",
        index="numeric",
    )

    unit_price: float = ContextField(
        description="Price per unit",
        index="numeric",
    )

    modifications: str | None = ContextField(
        description="Modifications: extra spicy, no onions, etc.",
    )

    special_instructions: str | None = ContextField(
        description="Special delivery instructions",
    )

    order: Order = ContextRelationship(
        description="Parent order",
        source_field="order_id",
    )


class DeliveryEvent(ContextModel):
    """DeliveryEvent entity for the Reddash domain."""

    __redis_key_template__ = "reddash_delivery_event:{event_id}"

    event_id: str = ContextField(
        description="Unique event identifier",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Associated order",
        index="tag",
    )

    event_type: str = ContextField(
        description="Event type: placed, confirmed, preparing, ready, driver_assigned, picked_up, en_route, delivered, cancelled",
        index="tag",
    )

    timestamp: str = ContextField(
        description="ISO timestamp of event",
    )

    description: str = ContextField(
        description="Human-readable event description",
        index="text",
    )

    actor: str = ContextField(
        description="Who triggered it: customer, restaurant, driver, system",
        index="tag",
    )

    order: Order = ContextRelationship(
        description="Associated order",
        source_field="order_id",
    )


class Payment(ContextModel):
    """Payment entity for the Reddash domain."""

    __redis_key_template__ = "reddash_payment:{payment_id}"

    payment_id: str = ContextField(
        description="Unique payment identifier",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Associated order",
        index="tag",
    )

    customer_id: str = ContextField(
        description="Customer who paid",
        index="tag",
    )

    subtotal: float = ContextField(
        description="Food subtotal",
        index="numeric",
    )

    delivery_fee: float = ContextField(
        description="Delivery fee",
        index="numeric",
    )

    service_fee: float = ContextField(
        description="Service fee",
        index="numeric",
    )

    tax: float = ContextField(
        description="Tax amount",
        index="numeric",
    )

    tip: float = ContextField(
        description="Driver tip",
        index="numeric",
    )

    discount: float = ContextField(
        description="Applied discount",
        index="numeric",
    )

    total_charged: float = ContextField(
        description="Final amount charged",
        index="numeric",
        sortable=True,
    )

    payment_method: str = ContextField(
        description="Payment method: visa_4242, mastercard_8888, apple_pay",
        index="tag",
    )

    promo_code: str | None = ContextField(
        description="Applied promo code",
        index="tag",
    )

    refund_amount: float = ContextField(
        description="Refund amount (0 if none)",
        index="numeric",
    )

    refund_status: str = ContextField(
        description="Refund status: none, pending, completed",
        index="tag",
    )

    refund_reason: str | None = ContextField(
        description="Reason for refund",
    )

    order: Order = ContextRelationship(
        description="Associated order",
        source_field="order_id",
    )

    customer: Customer = ContextRelationship(
        description="Customer who paid",
        source_field="customer_id",
    )


class SupportTicket(ContextModel):
    """SupportTicket entity for the Reddash domain."""

    __redis_key_template__ = "reddash_support_ticket:{ticket_id}"

    ticket_id: str = ContextField(
        description="Unique ticket identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer who filed the ticket",
        index="tag",
    )

    order_id: str | None = ContextField(
        description="Related order",
        index="tag",
    )

    category: str = ContextField(
        description="Category: late_delivery, wrong_item, missing_item, billing, account, other",
        index="tag",
    )

    status: str = ContextField(
        description="Status: open, in_progress, resolved, closed",
        index="tag",
    )

    created_at: str = ContextField(
        description="ISO timestamp when ticket was created",
    )

    resolved_at: str | None = ContextField(
        description="ISO timestamp when resolved",
    )

    summary: str = ContextField(
        description="Ticket summary",
        index="text",
    )

    resolution: str | None = ContextField(
        description="How it was resolved",
    )

    customer: Customer = ContextRelationship(
        description="Customer who filed the ticket",
        source_field="customer_id",
    )

    order: Order = ContextRelationship(
        description="Related order",
        source_field="order_id",
    )


class Policy(ContextModel):
    """Policy entity for the Reddash domain."""

    __redis_key_template__ = "reddash_policy:{policy_id}"

    policy_id: str = ContextField(
        description="Unique policy identifier",
        is_key_component=True,
    )

    title: str = ContextField(
        description="Policy title",
        index="text",
        weight=2.0,
    )

    category: str = ContextField(
        description="Policy category",
        index="tag",
    )

    content: str = ContextField(
        description="Full policy text",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Vector embedding of policy content",
        index="vector",
        vector_dim=1536,
        distance_metric="COSINE",
    )
