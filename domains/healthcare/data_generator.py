"""Generate sample data for the Healthcare demo.

Adapted from healthcare_context_surface_example/healthcare_sample_data.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.domain_contract import GeneratedDataset  # noqa: E402

OUTPUT_DIR = ROOT / "output" / "healthcare"

DEMO_USER_ID = "P001"

# ═══════════════════════════════════════════════════════════════════════════
#  LOCATIONS (2)
# ═══════════════════════════════════════════════════════════════════════════

LOCATIONS = [
    {
        "id": "LOC001",
        "name": "Downtown Medical Center",
        "address": "100 Main Street, Suite 200",
        "city": "San Francisco",
        "state": "CA",
        "phone": "415-555-1000",
        "type": "clinic",
    },
    {
        "id": "LOC002",
        "name": "Westside Family Health",
        "address": "2500 Ocean Avenue",
        "city": "San Francisco",
        "state": "CA",
        "phone": "415-555-2000",
        "type": "clinic",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  PROVIDERS (5)
# ═══════════════════════════════════════════════════════════════════════════

PROVIDERS = [
    {
        "id": "DR001",
        "name": "Dr. Sofia Martinez",
        "specialty": "primary_care",
        "location_id": "LOC001",
        "accepting_new_patients": "yes",
        "languages": "en,es",
        "email": "s.martinez@downtownmed.com",
    },
    {
        "id": "DR002",
        "name": "Dr. Raj Patel",
        "specialty": "internal_medicine",
        "location_id": "LOC001",
        "accepting_new_patients": "yes",
        "languages": "en,hi",
        "email": "r.patel@downtownmed.com",
    },
    {
        "id": "DR003",
        "name": "Dr. Jennifer Kim",
        "specialty": "obstetrics",
        "location_id": "LOC002",
        "accepting_new_patients": "no",
        "languages": "en,ko",
        "email": "j.kim@westsidehealth.com",
    },
    {
        "id": "DR004",
        "name": "Dr. Marcus Thompson",
        "specialty": "cardiology",
        "location_id": "LOC001",
        "accepting_new_patients": "yes",
        "languages": "en",
        "email": "m.thompson@downtownmed.com",
    },
    {
        "id": "DR005",
        "name": "Dr. Linda Chen",
        "specialty": "orthopedics",
        "location_id": "LOC002",
        "accepting_new_patients": "yes",
        "languages": "en,zh",
        "email": "l.chen@westsidehealth.com",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  PATIENTS (8)
# ═══════════════════════════════════════════════════════════════════════════

PATIENTS = [
    {
        "id": "P001",
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "555-0101",
        "dob": "1985-03-15",
        "preferred_language": "en",
        "insurance_status": "verified",
        "primary_provider_id": "DR001",
    },
    {
        "id": "P002",
        "name": "Sarah Johnson",
        "email": "sarah.j@email.com",
        "phone": "555-0102",
        "dob": "1990-07-22",
        "preferred_language": "en",
        "insurance_status": "verified",
        "primary_provider_id": "DR002",
    },
    {
        "id": "P003",
        "name": "Maria Garcia",
        "email": "maria.garcia@email.com",
        "phone": "555-0103",
        "dob": "1978-11-08",
        "preferred_language": "es",
        "insurance_status": "verified",
        "primary_provider_id": "DR001",
    },
    {
        "id": "P004",
        "name": "James Wilson",
        "email": "jwilson@email.com",
        "phone": "555-0104",
        "dob": "1965-01-30",
        "preferred_language": "en",
        "insurance_status": "expired",
        "primary_provider_id": "DR002",
    },
    {
        "id": "P005",
        "name": "Emily Chen",
        "email": "emily.chen@email.com",
        "phone": "555-0105",
        "dob": "1992-09-12",
        "preferred_language": "zh",
        "insurance_status": "verified",
        "primary_provider_id": "DR005",
    },
    {
        "id": "P006",
        "name": "Michael Brown",
        "email": "mbrown@email.com",
        "phone": "555-0106",
        "dob": "1955-04-18",
        "preferred_language": "en",
        "insurance_status": "pending",
        "primary_provider_id": "DR001",
    },
    {
        "id": "P007",
        "name": "Ana Rodriguez",
        "email": "ana.rod@email.com",
        "phone": "555-0107",
        "dob": "1988-12-03",
        "preferred_language": "es",
        "insurance_status": "verified",
        "primary_provider_id": "DR003",
    },
    {
        "id": "P008",
        "name": "David Lee",
        "email": "david.lee@email.com",
        "phone": "555-0108",
        "dob": "1972-06-25",
        "preferred_language": "en",
        "insurance_status": "verified",
        "primary_provider_id": "DR002",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  APPOINTMENTS (10)
# ═══════════════════════════════════════════════════════════════════════════

APPOINTMENTS = [
    {
        "id": "A001",
        "patient_id": "P001",
        "provider_id": "DR001",
        "location_id": "LOC001",
        "datetime": "2026-03-10T09:00:00",
        "type": "checkup",
        "status": "completed",
        "notes": "Annual physical, all vitals normal",
    },
    {
        "id": "A002",
        "patient_id": "P001",
        "provider_id": "DR001",
        "location_id": "LOC001",
        "datetime": "2026-03-17T10:00:00",
        "type": "follow_up",
        "status": "scheduled",
        "notes": "Follow up on blood work",
    },
    {
        "id": "A003",
        "patient_id": "P002",
        "provider_id": "DR002",
        "location_id": "LOC001",
        "datetime": "2026-03-11T14:00:00",
        "type": "consultation",
        "status": "no_show",
        "notes": "Patient did not arrive, no call",
    },
    {
        "id": "A004",
        "patient_id": "P003",
        "provider_id": "DR001",
        "location_id": "LOC001",
        "datetime": "2026-03-12T11:00:00",
        "type": "checkup",
        "status": "completed",
        "notes": "Diabetes management review",
    },
    {
        "id": "A005",
        "patient_id": "P004",
        "provider_id": "DR003",
        "location_id": "LOC002",
        "datetime": "2026-03-11T15:30:00",
        "type": "procedure",
        "status": "cancelled",
        "notes": "Insurance expired, rescheduling needed",
    },
    {
        "id": "A006",
        "patient_id": "P005",
        "provider_id": "DR005",
        "location_id": "LOC002",
        "datetime": "2026-03-13T09:30:00",
        "type": "follow_up",
        "status": "scheduled",
        "notes": "Post-surgery check",
    },
    {
        "id": "A007",
        "patient_id": "P006",
        "provider_id": "DR001",
        "location_id": "LOC001",
        "datetime": "2026-03-10T16:00:00",
        "type": "consultation",
        "status": "no_show",
        "notes": "New patient intake - missed",
    },
    {
        "id": "A008",
        "patient_id": "P007",
        "provider_id": "DR003",
        "location_id": "LOC002",
        "datetime": "2026-03-14T10:00:00",
        "type": "checkup",
        "status": "scheduled",
        "notes": "Prenatal visit",
    },
    {
        "id": "A009",
        "patient_id": "P008",
        "provider_id": "DR002",
        "location_id": "LOC001",
        "datetime": "2026-03-09T11:00:00",
        "type": "procedure",
        "status": "completed",
        "notes": "Minor procedure completed successfully",
    },
    {
        "id": "A010",
        "patient_id": "P002",
        "provider_id": "DR002",
        "location_id": "LOC001",
        "datetime": "2026-03-18T14:00:00",
        "type": "consultation",
        "status": "scheduled",
        "notes": "Rescheduled from no-show",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  REFERRALS (6)
# ═══════════════════════════════════════════════════════════════════════════

REFERRALS = [
    {
        "id": "R001",
        "patient_id": "P001",
        "referring_provider_id": "DR001",
        "to_specialty": "cardiology",
        "to_provider_id": "DR004",
        "status": "pending",
        "urgency": "routine",
        "notes": "Elevated cholesterol, recommend cardiac evaluation",
        "received_date": "2026-03-10",
    },
    {
        "id": "R002",
        "patient_id": "P003",
        "referring_provider_id": "DR001",
        "to_specialty": "endocrinology",
        "to_provider_id": "",
        "status": "scheduled",
        "urgency": "routine",
        "notes": "Diabetes specialist consultation",
        "received_date": "2026-03-05",
    },
    {
        "id": "R003",
        "patient_id": "P004",
        "referring_provider_id": "DR002",
        "to_specialty": "orthopedics",
        "to_provider_id": "DR005",
        "status": "pending",
        "urgency": "urgent",
        "notes": "Severe knee pain, possible surgery needed",
        "received_date": "2026-03-08",
    },
    {
        "id": "R004",
        "patient_id": "P006",
        "referring_provider_id": "DR002",
        "to_specialty": "oncology",
        "to_provider_id": "",
        "status": "pending",
        "urgency": "stat",
        "notes": "Abnormal lab results, immediate evaluation needed",
        "received_date": "2026-03-11",
    },
    {
        "id": "R005",
        "patient_id": "P008",
        "referring_provider_id": "DR002",
        "to_specialty": "neurology",
        "to_provider_id": "",
        "status": "completed",
        "urgency": "routine",
        "notes": "Headache evaluation completed",
        "received_date": "2026-02-20",
    },
    {
        "id": "R006",
        "patient_id": "P005",
        "referring_provider_id": "DR005",
        "to_specialty": "physical_therapy",
        "to_provider_id": "",
        "status": "scheduled",
        "urgency": "routine",
        "notes": "Post-surgery rehabilitation",
        "received_date": "2026-03-09",
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  WAITLIST (4)
# ═══════════════════════════════════════════════════════════════════════════

WAITLIST = [
    {
        "id": "W001",
        "patient_id": "P002",
        "preferred_provider_id": "DR001",
        "location_id": "LOC001",
        "appointment_type": "consultation",
        "flexibility": "mornings",
        "added_date": "2026-03-08",
        "notes": "Wants to switch from Dr. Patel",
    },
    {
        "id": "W002",
        "patient_id": "P004",
        "preferred_provider_id": "DR003",
        "location_id": "LOC002",
        "appointment_type": "procedure",
        "flexibility": "any_time",
        "added_date": "2026-03-11",
        "notes": "Waiting for insurance to be resolved",
    },
    {
        "id": "W003",
        "patient_id": "P006",
        "preferred_provider_id": "DR001",
        "location_id": "LOC001",
        "appointment_type": "checkup",
        "flexibility": "afternoons",
        "added_date": "2026-03-10",
        "notes": "Missed first appointment, wants to reschedule",
    },
    {
        "id": "W004",
        "patient_id": "P007",
        "preferred_provider_id": "DR003",
        "location_id": "LOC002",
        "appointment_type": "follow_up",
        "flexibility": "specific_days",
        "added_date": "2026-03-12",
        "notes": "Only available Tuesdays and Thursdays",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — write JSONL files
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

    print("Writing JSONL files:")
    write_jsonl(resolved_output_dir, "locations.jsonl", LOCATIONS)
    write_jsonl(resolved_output_dir, "providers.jsonl", PROVIDERS)
    write_jsonl(resolved_output_dir, "patients.jsonl", PATIENTS)
    write_jsonl(resolved_output_dir, "appointments.jsonl", APPOINTMENTS)
    write_jsonl(resolved_output_dir, "referrals.jsonl", REFERRALS)
    write_jsonl(resolved_output_dir, "waitlist.jsonl", WAITLIST)

    demo = PATIENTS[0]
    if update_env_file:
        update_env("DEMO_USER_ID", demo["id"])
        update_env("DEMO_USER_NAME", demo["name"])
        update_env("DEMO_USER_EMAIL", demo["email"])
    print(f"\nDemo user: {demo['name']} ({demo['id']})")
    print("Done.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates={
            "DEMO_USER_ID": demo["id"],
            "DEMO_USER_NAME": demo["name"],
            "DEMO_USER_EMAIL": demo["email"],
        },
        summary={
            "locations": len(LOCATIONS),
            "providers": len(PROVIDERS),
            "patients": len(PATIENTS),
            "appointments": len(APPOINTMENTS),
            "referrals": len(REFERRALS),
            "waitlist": len(WAITLIST),
        },
    )


def main() -> None:
    generate_demo_data(output_dir=OUTPUT_DIR, update_env_file=True)


if __name__ == "__main__":
    main()
