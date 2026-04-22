"""Generated Context Surface models for the ElectroHub domain."""

from __future__ import annotations

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Customer(ContextModel):
    """Customer entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_customer:{customer_id}"

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

    city: str = ContextField(
        description="Customer city",
        index="tag",
    )

    state: str = ContextField(
        description="Customer state",
        index="tag",
    )

    member_tier: str = ContextField(
        description="Loyalty membership tier",
        index="tag",
    )

    home_store_id: str = ContextField(
        description="Preferred local store",
        index="tag",
    )

    home_store_name: str = ContextField(
        description="Preferred store name",
        index="text",
    )

    account_created_at: str = ContextField(
        description="ISO timestamp for account creation",
    )

    orders: list[Order] = ContextRelationship(
        description="Orders placed by this customer",
        source_field="customer_id",
    )

    support_cases: list[SupportCase] = ContextRelationship(
        description="Support cases opened by this customer",
        source_field="customer_id",
    )


class Store(ContextModel):
    """Store entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_store:{store_id}"

    store_id: str = ContextField(
        description="Unique store identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Store name",
        index="text",
        weight=2.0,
    )

    city: str = ContextField(
        description="Store city",
        index="tag",
    )

    state: str = ContextField(
        description="Store state",
        index="tag",
    )

    zip_code: str = ContextField(
        description="Store ZIP code",
        index="tag",
    )

    address: str = ContextField(
        description="Street address",
    )

    phone: str = ContextField(
        description="Store phone number",
    )

    pickup_supported: bool = ContextField(
        description="Whether in-store pickup is supported",
    )

    curbside_supported: bool = ContextField(
        description="Whether curbside pickup is supported",
    )

    services: str = ContextField(
        description="Key services available at the store",
        index="text",
    )

    hours_summary: str = ContextField(
        description="Store operating hours",
    )


class Product(ContextModel):
    """Product entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_product:{product_id}"

    product_id: str = ContextField(
        description="Unique product identifier",
        is_key_component=True,
    )

    sku: str = ContextField(
        description="Retail SKU",
        index="tag",
        no_stem=True,
    )

    name: str = ContextField(
        description="Product name",
        index="text",
        weight=2.2,
    )

    brand: str = ContextField(
        description="Product brand",
        index="tag",
    )

    category: str = ContextField(
        description="Top-level category",
        index="tag",
    )

    subcategory: str = ContextField(
        description="Subcategory",
        index="tag",
    )

    form_factor: str = ContextField(
        description="Form factor such as laptop or desktop",
        index="tag",
    )

    price: float = ContextField(
        description="Current selling price",
        index="numeric",
        sortable=True,
    )

    sale_price: float | None = ContextField(
        description="Current promotional price",
        index="numeric",
    )

    rating: float = ContextField(
        description="Average customer rating",
        index="numeric",
        sortable=True,
    )

    availability_status: str = ContextField(
        description="Overall availability status",
        index="tag",
    )

    pickup_eligible: bool = ContextField(
        description="Whether local pickup is available",
    )

    shipping_eligible: bool = ContextField(
        description="Whether shipping is available",
    )

    specs_summary: str = ContextField(
        description="Readable hardware summary",
        index="text",
    )

    use_cases: str = ContextField(
        description="Suggested workloads and use cases",
        index="text",
    )

    ai_fit_summary: str = ContextField(
        description="Short AI-authored fit summary",
        index="text",
        weight=1.4,
    )

    search_text: str = ContextField(
        description="Combined searchable description for product discovery",
        index="text",
        weight=1.8,
    )


class StoreInventory(ContextModel):
    """StoreInventory entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_store_inventory:{inventory_id}"

    inventory_id: str = ContextField(
        description="Unique inventory row identifier",
        is_key_component=True,
    )

    store_id: str = ContextField(
        description="Store identifier",
        index="tag",
    )

    product_id: str = ContextField(
        description="Product identifier",
        index="tag",
    )

    store_name: str = ContextField(
        description="Store name",
        index="text",
    )

    product_name: str = ContextField(
        description="Product name",
        index="text",
    )

    quantity_available: int = ContextField(
        description="Quantity currently available",
        index="numeric",
        sortable=True,
    )

    pickup_status: str = ContextField(
        description="Pickup readiness status",
        index="tag",
    )

    pickup_eta_hours: int = ContextField(
        description="Estimated pickup wait time in hours",
        index="numeric",
    )

    aisle_location: str | None = ContextField(
        description="Approximate floor or aisle location",
    )

    store: Store = ContextRelationship(
        description="Store carrying this item",
        source_field="store_id",
    )

    product: Product = ContextRelationship(
        description="Product stocked at the store",
        source_field="product_id",
    )


class Order(ContextModel):
    """Order entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_order:{order_id}"

    order_id: str = ContextField(
        description="Unique order identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer identifier",
        index="tag",
    )

    status: str = ContextField(
        description="Order status",
        index="tag",
    )

    fulfillment_type: str = ContextField(
        description="shipping or pickup",
        index="tag",
    )

    store_id: str | None = ContextField(
        description="Pickup store identifier",
        index="tag",
    )

    store_name: str | None = ContextField(
        description="Pickup store name",
        index="text",
    )

    order_total: float = ContextField(
        description="Total order amount",
        index="numeric",
        sortable=True,
    )

    order_date: str = ContextField(
        description="ISO timestamp when the order was placed",
    )

    promised_date: str | None = ContextField(
        description="Promised delivery or pickup timestamp",
    )

    delivered_at: str | None = ContextField(
        description="Actual delivery timestamp",
    )

    tracking_number: str | None = ContextField(
        description="Carrier tracking number",
        index="tag",
        no_stem=True,
    )

    shipping_address: str | None = ContextField(
        description="Delivery address",
    )

    summary: str = ContextField(
        description="Short order summary",
        index="text",
    )


class OrderItem(ContextModel):
    """OrderItem entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_order_item:{order_item_id}"

    order_item_id: str = ContextField(
        description="Unique order item identifier",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Parent order identifier",
        index="tag",
    )

    product_id: str = ContextField(
        description="Product identifier",
        index="tag",
    )

    product_name: str = ContextField(
        description="Product name",
        index="text",
    )

    quantity: int = ContextField(
        description="Quantity ordered",
        index="numeric",
    )

    unit_price: float = ContextField(
        description="Unit selling price",
        index="numeric",
    )

    fulfillment_status: str = ContextField(
        description="Line-item fulfillment status",
        index="tag",
    )


class Shipment(ContextModel):
    """Shipment entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_shipment:{shipment_id}"

    shipment_id: str = ContextField(
        description="Unique shipment identifier",
        is_key_component=True,
    )

    order_id: str = ContextField(
        description="Parent order identifier",
        index="tag",
    )

    carrier: str = ContextField(
        description="Shipping carrier",
        index="tag",
    )

    tracking_number: str = ContextField(
        description="Tracking number",
        index="tag",
        no_stem=True,
    )

    shipment_status: str = ContextField(
        description="Shipment status",
        index="tag",
    )

    shipped_at: str = ContextField(
        description="Timestamp when the shipment left the warehouse",
    )

    estimated_delivery: str | None = ContextField(
        description="Current estimated delivery timestamp",
    )

    last_scan_at: str | None = ContextField(
        description="Timestamp of the latest scan",
    )

    current_location: str | None = ContextField(
        description="Latest known shipment location",
        index="text",
    )

    delay_reason: str | None = ContextField(
        description="Reason for any delay",
        index="text",
    )


class ShipmentEvent(ContextModel):
    """ShipmentEvent entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_shipment_event:{event_id}"

    event_id: str = ContextField(
        description="Unique shipment event identifier",
        is_key_component=True,
    )

    shipment_id: str = ContextField(
        description="Shipment identifier",
        index="tag",
    )

    order_id: str = ContextField(
        description="Order identifier",
        index="tag",
    )

    event_type: str = ContextField(
        description="Shipment event type",
        index="tag",
    )

    timestamp: str = ContextField(
        description="Event timestamp",
    )

    location: str | None = ContextField(
        description="Event location",
        index="text",
    )

    description: str = ContextField(
        description="Human-readable event description",
        index="text",
    )


class SupportCase(ContextModel):
    """SupportCase entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_support_case:{case_id}"

    case_id: str = ContextField(
        description="Unique support case identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer identifier",
        index="tag",
    )

    order_id: str | None = ContextField(
        description="Related order identifier",
        index="tag",
    )

    category: str = ContextField(
        description="Support case category",
        index="tag",
    )

    status: str = ContextField(
        description="Support case status",
        index="tag",
    )

    opened_at: str = ContextField(
        description="Case open timestamp",
    )

    summary: str = ContextField(
        description="Short support summary",
        index="text",
    )

    resolution: str | None = ContextField(
        description="Resolution summary",
        index="text",
    )


class Guide(ContextModel):
    """Guide entity for the ElectroHub domain."""

    __redis_key_template__ = "electrohub_guide:{guide_id}"

    guide_id: str = ContextField(
        description="Unique guide identifier",
        is_key_component=True,
    )

    title: str = ContextField(
        description="Guide title",
        index="text",
        weight=2.0,
    )

    category: str = ContextField(
        description="Guide category",
        index="tag",
    )

    content: str = ContextField(
        description="Guide body",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Vector embedding for the guide content",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )
