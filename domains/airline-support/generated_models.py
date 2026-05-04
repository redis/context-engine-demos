"""Generated Context Surface models for the Airline Support domain."""

from __future__ import annotations

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class CustomerProfile(ContextModel):
    """CustomerProfile entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_customer_profile:{customer_id}"

    customer_id: str = ContextField(
        description="Public-safe demo customer identifier",
        is_key_component=True,
    )

    travel_id: str = ContextField(
        description="Traveller profile identifier",
        index="tag",
        no_stem=True,
    )

    display_name: str = ContextField(
        description="Traveller display name",
        index="text",
        weight=2.0,
    )

    masked_loyalty_number: str = ContextField(
        description="Masked loyalty number",
        index="tag",
        no_stem=True,
    )

    loyalty_tier: str = ContextField(
        description="Current loyalty tier",
        index="tag",
    )

    preferred_language: str = ContextField(
        description="Preferred language for service",
        index="tag",
    )

    email: str = ContextField(
        description="Read-only email on file",
        index="text",
        weight=1.4,
        no_stem=True,
    )

    consents: str = ContextField(
        description="Summary of communication and service consents",
        index="text",
    )

    bookings: list[Booking] = ContextRelationship(
        description="Bookings belonging to this traveller",
        source_field="customer_id",
    )

    support_cases: list[SupportCase] = ContextRelationship(
        description="Support cases opened for this traveller",
        source_field="customer_id",
    )


class Booking(ContextModel):
    """Booking entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_booking:{booking_id}"

    booking_id: str = ContextField(
        description="Unique booking identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer identifier",
        index="tag",
    )

    booking_locator: str = ContextField(
        description="Booking locator / PNR",
        index="tag",
        no_stem=True,
    )

    passenger_display_name: str = ContextField(
        description="Passenger display name",
        index="text",
        weight=1.6,
    )

    trip_status: str = ContextField(
        description="Overall trip status",
        index="tag",
    )

    journey_summary: str = ContextField(
        description="Original trip summary",
        index="text",
        weight=1.8,
    )

    current_itinerary_summary: str = ContextField(
        description="Current itinerary summary after any changes",
        index="text",
    )

    created_at: str = ContextField(
        description="Booking creation timestamp",
    )

    fare_family: str = ContextField(
        description="Fare family name",
        index="tag",
    )

    cabin: str = ContextField(
        description="Cabin class",
        index="tag",
    )

    disruption_state: str = ContextField(
        description="Current disruption state",
        index="tag",
    )

    segments: list[FlightSegment] = ContextRelationship(
        description="Segments belonging to this booking",
        source_field="booking_id",
    )

    operational_disruptions: list[OperationalDisruption] = ContextRelationship(
        description="Operational disruption events tied to this booking",
        source_field="booking_id",
    )

    reaccommodation_records: list[ReaccommodationRecord] = ContextRelationship(
        description="Reaccommodation records tied to this booking",
        source_field="booking_id",
    )

    support_cases: list[SupportCase] = ContextRelationship(
        description="Support cases tied to this booking",
        source_field="booking_id",
    )


class FlightSegment(ContextModel):
    """FlightSegment entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_flight_segment:{segment_id}"

    segment_id: str = ContextField(
        description="Unique flight segment identifier",
        is_key_component=True,
    )

    booking_id: str = ContextField(
        description="Parent booking identifier",
        index="tag",
    )

    flight_number: str = ContextField(
        description="Marketing flight number",
        index="tag",
        no_stem=True,
    )

    segment_role: str = ContextField(
        description="original, updated, or unaffected",
        index="tag",
    )

    origin_airport: str = ContextField(
        description="Origin airport code",
        index="tag",
    )

    origin_city: str = ContextField(
        description="Origin city",
        index="text",
    )

    destination_airport: str = ContextField(
        description="Destination airport code",
        index="tag",
    )

    destination_city: str = ContextField(
        description="Destination city",
        index="text",
    )

    scheduled_departure: str = ContextField(
        description="Scheduled departure timestamp",
    )

    estimated_departure: str = ContextField(
        description="Current estimated departure timestamp",
    )

    scheduled_arrival: str = ContextField(
        description="Scheduled arrival timestamp",
    )

    estimated_arrival: str = ContextField(
        description="Current estimated arrival timestamp",
    )

    operating_status: str = ContextField(
        description="Current segment operating status",
        index="tag",
    )

    terminal: str | None = ContextField(
        description="Departure terminal if known",
    )

    gate: str | None = ContextField(
        description="Departure gate if assigned close to departure",
    )

    cabin: str = ContextField(
        description="Cabin on the segment",
        index="tag",
    )

    status_note: str = ContextField(
        description="Short traveller-facing status note",
        index="text",
    )

    booking: Booking = ContextRelationship(
        description="Booking containing this segment",
        source_field="booking_id",
    )


class OperationalDisruption(ContextModel):
    """OperationalDisruption entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_operational_disruption:{operational_disruption_id}"

    operational_disruption_id: str = ContextField(
        description="Unique operational disruption identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer identifier",
        index="tag",
    )

    booking_id: str = ContextField(
        description="Affected booking identifier",
        index="tag",
    )

    affected_segment_id: str = ContextField(
        description="Cancelled or delayed segment identifier",
        index="tag",
    )

    disruption_type: str = ContextField(
        description="Type of disruption",
        index="tag",
    )

    operational_reason: str = ContextField(
        description="Operational cause summary",
        index="text",
    )

    impact_status: str = ContextField(
        description="Traveller-visible impact status",
        index="tag",
    )

    recorded_at: str = ContextField(
        description="Timestamp when the disruption was recorded",
    )

    source_system: str = ContextField(
        description="Source operational system or feed",
        index="tag",
    )

    booking: Booking = ContextRelationship(
        description="Booking tied to this disruption",
        source_field="booking_id",
    )

    affected_segment: FlightSegment = ContextRelationship(
        description="Affected segment",
        source_field="affected_segment_id",
    )


class ReaccommodationRecord(ContextModel):
    """ReaccommodationRecord entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_reaccommodation_record:{reaccommodation_record_id}"

    reaccommodation_record_id: str = ContextField(
        description="Unique reaccommodation identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer identifier",
        index="tag",
    )

    booking_id: str = ContextField(
        description="Booking identifier",
        index="tag",
    )

    original_segment_id: str = ContextField(
        description="Original affected segment identifier",
        index="tag",
    )

    replacement_segment_id: str = ContextField(
        description="Replacement segment identifier",
        index="tag",
    )

    reaccommodation_status: str = ContextField(
        description="Reaccommodation status",
        index="tag",
    )

    action_source: str = ContextField(
        description="Automatic or agent-driven reassignment source",
        index="tag",
    )

    reaccommodated_at: str = ContextField(
        description="Timestamp when the reassignment was applied",
    )

    protection_reason: str = ContextField(
        description="Why the reassignment was created",
        index="text",
    )

    booking: Booking = ContextRelationship(
        description="Booking tied to this reaccommodation",
        source_field="booking_id",
    )

    original_segment: FlightSegment = ContextRelationship(
        description="Original disrupted segment",
        source_field="original_segment_id",
    )

    replacement_segment: FlightSegment = ContextRelationship(
        description="Replacement segment assigned to the traveller",
        source_field="replacement_segment_id",
    )


class SupportCase(ContextModel):
    """SupportCase entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_support_case:{support_case_id}"

    support_case_id: str = ContextField(
        description="Unique support case identifier",
        is_key_component=True,
    )

    customer_id: str = ContextField(
        description="Customer identifier",
        index="tag",
    )

    booking_id: str = ContextField(
        description="Related booking identifier",
        index="tag",
    )

    case_type: str = ContextField(
        description="Support case type",
        index="tag",
    )

    status: str = ContextField(
        description="Support case status",
        index="tag",
    )

    opened_at: str = ContextField(
        description="Case creation timestamp",
    )

    channel: str = ContextField(
        description="Channel used to open the case",
        index="tag",
    )

    summary: str = ContextField(
        description="Short support summary",
        index="text",
    )

    latest_note: str = ContextField(
        description="Most recent case note",
        index="text",
    )

    booking: Booking = ContextRelationship(
        description="Booking tied to this support case",
        source_field="booking_id",
    )


class TravelPolicyDoc(ContextModel):
    """TravelPolicyDoc entity for the Airline Support domain."""

    __redis_key_template__ = "airline_support_travel_policy_doc:{doc_id}"

    doc_id: str = ContextField(
        description="Unique policy document identifier",
        is_key_component=True,
    )

    category: str = ContextField(
        description="Policy topic category",
        index="tag",
    )

    title: str = ContextField(
        description="Policy document title",
        index="text",
        weight=2.0,
    )

    content: str = ContextField(
        description="Policy document content",
        index="text",
    )

    content_embedding: list[float] = ContextField(
        description="Vector embedding for the document content",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )
