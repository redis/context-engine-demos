"""Healthcare data-model definitions – single source of truth.

Adapted from the healthcare_context_surface_example.
Each EntitySpec drives:
  • ContextModel code generation
  • Redis Search index creation
  • Sample-data generation
"""

from __future__ import annotations

from backend.app.core.domain_schema import (
    EntitySpec,
    FieldSpec,
    RelationshipSpec,
    entity_by_class,
    entity_by_file,
)


ENTITY_SPECS: tuple[EntitySpec, ...] = (
    # ── Location ────────────────────────────────────────
    EntitySpec(
        class_name="Location",
        redis_key_template="healthcare_location:{id}",
        file_name="locations.jsonl",
        id_field="id",
        fields=(
            FieldSpec("id", "str", "Location ID", is_key_component=True),
            FieldSpec("name", "str", "Facility name", index="text", weight=2.0),
            FieldSpec("address", "str", "Street address", index="text"),
            FieldSpec("city", "str", "City", index="tag"),
            FieldSpec("state", "str", "State", index="tag"),
            FieldSpec("phone", "str", "Phone number", index="tag"),
            FieldSpec("type", "str", "Facility type: clinic, hospital", index="tag"),
        ),
    ),
    # ── Provider ────────────────────────────────────────
    EntitySpec(
        class_name="Provider",
        redis_key_template="healthcare_provider:{id}",
        file_name="providers.jsonl",
        id_field="id",
        fields=(
            FieldSpec("id", "str", "Provider ID", is_key_component=True),
            FieldSpec("name", "str", "Full name", index="text", weight=2.0),
            FieldSpec("specialty", "str", "Medical specialty", index="tag"),
            FieldSpec("location_id", "str", "Primary location", index="tag"),
            FieldSpec(
                "accepting_new_patients", "str", "Accepting new patients: yes/no", index="tag"
            ),
            FieldSpec("languages", "str", "Languages spoken", index="text"),
            FieldSpec("email", "str", "Email", index="text"),
        ),
        relationships=(RelationshipSpec("location", "Primary location", "location_id"),),
    ),
    # ── Patient ─────────────────────────────────────────
    EntitySpec(
        class_name="Patient",
        redis_key_template="healthcare_patient:{id}",
        file_name="patients.jsonl",
        id_field="id",
        fields=(
            FieldSpec("id", "str", "Patient ID", is_key_component=True),
            FieldSpec("name", "str", "Full name", index="text", weight=2.0),
            FieldSpec("email", "str", "Email", index="text", no_stem=True),
            FieldSpec("phone", "str", "Phone", index="tag"),
            FieldSpec("dob", "str", "Date of birth", index="tag"),
            FieldSpec("preferred_language", "str", "Preferred language", index="tag"),
            FieldSpec(
                "insurance_status", "str", "Insurance: verified, pending, expired", index="tag"
            ),
            FieldSpec("primary_provider_id", "str", "Primary provider", index="tag"),
        ),
        relationships=(
            RelationshipSpec("primary_provider", "Primary care provider", "primary_provider_id"),
        ),
    ),
    # ── Appointment ─────────────────────────────────────
    EntitySpec(
        class_name="Appointment",
        redis_key_template="healthcare_appointment:{id}",
        file_name="appointments.jsonl",
        id_field="id",
        fields=(
            FieldSpec("id", "str", "Appointment ID", is_key_component=True),
            FieldSpec("patient_id", "str", "Patient", index="tag"),
            FieldSpec("provider_id", "str", "Provider", index="tag"),
            FieldSpec("location_id", "str", "Location", index="tag"),
            FieldSpec("datetime", "str", "Date and time", index="tag"),
            FieldSpec(
                "type", "str", "Type: checkup, follow_up, consultation, procedure", index="tag"
            ),
            FieldSpec(
                "status", "str", "Status: scheduled, completed, no_show, cancelled", index="tag"
            ),
            FieldSpec("notes", "str", "Appointment notes", index="text"),
        ),
        relationships=(
            RelationshipSpec("patient", "Patient", "patient_id"),
            RelationshipSpec("provider", "Provider", "provider_id"),
            RelationshipSpec("location", "Location", "location_id"),
        ),
    ),
    # ── Referral ────────────────────────────────────────
    EntitySpec(
        class_name="Referral",
        redis_key_template="healthcare_referral:{id}",
        file_name="referrals.jsonl",
        id_field="id",
        fields=(
            FieldSpec("id", "str", "Referral ID", is_key_component=True),
            FieldSpec("patient_id", "str", "Patient being referred", index="tag"),
            FieldSpec("referring_provider_id", "str", "Referring provider", index="tag"),
            FieldSpec("to_specialty", "str", "Target specialty", index="tag"),
            FieldSpec("to_provider_id", "str", "Target provider (if known)", index="tag"),
            FieldSpec("status", "str", "Status: pending, scheduled, completed", index="tag"),
            FieldSpec("urgency", "str", "Urgency: routine, urgent, stat", index="tag"),
            FieldSpec("notes", "str", "Referral notes", index="text"),
            FieldSpec("received_date", "str", "Date received", index="tag"),
        ),
        relationships=(
            RelationshipSpec("patient", "Patient", "patient_id"),
            RelationshipSpec("referring_provider", "Referring provider", "referring_provider_id"),
        ),
    ),
    # ── Waitlist ────────────────────────────────────────
    EntitySpec(
        class_name="Waitlist",
        redis_key_template="healthcare_waitlist:{id}",
        file_name="waitlist.jsonl",
        id_field="id",
        fields=(
            FieldSpec("id", "str", "Waitlist entry ID", is_key_component=True),
            FieldSpec("patient_id", "str", "Patient", index="tag"),
            FieldSpec("preferred_provider_id", "str", "Preferred provider", index="tag"),
            FieldSpec("location_id", "str", "Preferred location", index="tag"),
            FieldSpec("appointment_type", "str", "Appointment type needed", index="tag"),
            FieldSpec(
                "flexibility",
                "str",
                "Schedule flexibility: mornings, afternoons, any_time, specific_days",
                index="tag",
            ),
            FieldSpec("added_date", "str", "Date added to waitlist", index="tag"),
            FieldSpec("notes", "str", "Additional notes", index="text"),
        ),
        relationships=(
            RelationshipSpec("patient", "Patient", "patient_id"),
            RelationshipSpec("preferred_provider", "Preferred provider", "preferred_provider_id"),
        ),
    ),
)

ENTITY_BY_FILE = entity_by_file(ENTITY_SPECS)
ENTITY_BY_CLASS = entity_by_class(ENTITY_SPECS)
