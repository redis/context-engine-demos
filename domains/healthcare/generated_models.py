"""Generated Context Surface models for the HealthConnect domain."""

from __future__ import annotations

from typing import Any

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class Location(ContextModel):
    """Location entity for the HealthConnect domain."""

    __redis_key_template__ = "healthcare_location:{id}"

    id: str = ContextField(
        description="Location ID",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Facility name",
        index="text",
        weight=2.0,
    )

    address: str = ContextField(
        description="Street address",
        index="text",
    )

    city: str = ContextField(
        description="City",
        index="tag",
    )

    state: str = ContextField(
        description="State",
        index="tag",
    )

    phone: str = ContextField(
        description="Phone number",
        index="tag",
    )

    type: str = ContextField(
        description="Facility type: clinic, hospital",
        index="tag",
    )


class Provider(ContextModel):
    """Provider entity for the HealthConnect domain."""

    __redis_key_template__ = "healthcare_provider:{id}"

    id: str = ContextField(
        description="Provider ID",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Full name",
        index="text",
        weight=2.0,
    )

    specialty: str = ContextField(
        description="Medical specialty",
        index="tag",
    )

    location_id: str = ContextField(
        description="Primary location",
        index="tag",
    )

    accepting_new_patients: str = ContextField(
        description="Accepting new patients: yes/no",
        index="tag",
    )

    languages: str = ContextField(
        description="Languages spoken",
        index="text",
    )

    email: str = ContextField(
        description="Email",
        index="text",
    )

    location: Any = ContextRelationship(
        description="Primary location",
        source_field="location_id",
    )


class Patient(ContextModel):
    """Patient entity for the HealthConnect domain."""

    __redis_key_template__ = "healthcare_patient:{id}"

    id: str = ContextField(
        description="Patient ID",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Full name",
        index="text",
        weight=2.0,
    )

    email: str = ContextField(
        description="Email",
        index="text",
        no_stem=True,
    )

    phone: str = ContextField(
        description="Phone",
        index="tag",
    )

    dob: str = ContextField(
        description="Date of birth",
        index="tag",
    )

    preferred_language: str = ContextField(
        description="Preferred language",
        index="tag",
    )

    insurance_status: str = ContextField(
        description="Insurance: verified, pending, expired",
        index="tag",
    )

    primary_provider_id: str = ContextField(
        description="Primary provider",
        index="tag",
    )

    primary_provider: Any = ContextRelationship(
        description="Primary care provider",
        source_field="primary_provider_id",
    )


class Appointment(ContextModel):
    """Appointment entity for the HealthConnect domain."""

    __redis_key_template__ = "healthcare_appointment:{id}"

    id: str = ContextField(
        description="Appointment ID",
        is_key_component=True,
    )

    patient_id: str = ContextField(
        description="Patient",
        index="tag",
    )

    provider_id: str = ContextField(
        description="Provider",
        index="tag",
    )

    location_id: str = ContextField(
        description="Location",
        index="tag",
    )

    datetime: str = ContextField(
        description="Date and time",
        index="tag",
    )

    type: str = ContextField(
        description="Type: checkup, follow_up, consultation, procedure",
        index="tag",
    )

    status: str = ContextField(
        description="Status: scheduled, completed, no_show, cancelled",
        index="tag",
    )

    notes: str = ContextField(
        description="Appointment notes",
        index="text",
    )

    patient: Any = ContextRelationship(
        description="Patient",
        source_field="patient_id",
    )

    provider: Any = ContextRelationship(
        description="Provider",
        source_field="provider_id",
    )

    location: Any = ContextRelationship(
        description="Location",
        source_field="location_id",
    )


class Referral(ContextModel):
    """Referral entity for the HealthConnect domain."""

    __redis_key_template__ = "healthcare_referral:{id}"

    id: str = ContextField(
        description="Referral ID",
        is_key_component=True,
    )

    patient_id: str = ContextField(
        description="Patient being referred",
        index="tag",
    )

    referring_provider_id: str = ContextField(
        description="Referring provider",
        index="tag",
    )

    to_specialty: str = ContextField(
        description="Target specialty",
        index="tag",
    )

    to_provider_id: str = ContextField(
        description="Target provider (if known)",
        index="tag",
    )

    status: str = ContextField(
        description="Status: pending, scheduled, completed",
        index="tag",
    )

    urgency: str = ContextField(
        description="Urgency: routine, urgent, stat",
        index="tag",
    )

    notes: str = ContextField(
        description="Referral notes",
        index="text",
    )

    received_date: str = ContextField(
        description="Date received",
        index="tag",
    )

    patient: Any = ContextRelationship(
        description="Patient",
        source_field="patient_id",
    )

    referring_provider: Any = ContextRelationship(
        description="Referring provider",
        source_field="referring_provider_id",
    )


class Waitlist(ContextModel):
    """Waitlist entity for the HealthConnect domain."""

    __redis_key_template__ = "healthcare_waitlist:{id}"

    id: str = ContextField(
        description="Waitlist entry ID",
        is_key_component=True,
    )

    patient_id: str = ContextField(
        description="Patient",
        index="tag",
    )

    preferred_provider_id: str = ContextField(
        description="Preferred provider",
        index="tag",
    )

    location_id: str = ContextField(
        description="Preferred location",
        index="tag",
    )

    appointment_type: str = ContextField(
        description="Appointment type needed",
        index="tag",
    )

    flexibility: str = ContextField(
        description="Schedule flexibility: mornings, afternoons, any_time, specific_days",
        index="tag",
    )

    added_date: str = ContextField(
        description="Date added to waitlist",
        index="tag",
    )

    notes: str = ContextField(
        description="Additional notes",
        index="text",
    )

    patient: Any = ContextRelationship(
        description="Patient",
        source_field="patient_id",
    )

    preferred_provider: Any = ContextRelationship(
        description="Preferred provider",
        source_field="preferred_provider_id",
    )
