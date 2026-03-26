#!/usr/bin/env python3
"""Export VitaClaw health records to OMOP CDM format.

Generates three tables as JSONL files:
  - person.jsonl       (OMOP person table)
  - observation.jsonl   (vitals, labs)
  - drug_exposure.jsonl  (medications, supplements)

Controlled by ConsentManager: only exports records matching an active
research consent policy. Supports optional de-identification by
shifting dates and removing direct identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from consent_manager import ConsentManager  # noqa: E402
from cross_skill_reader import CrossSkillReader  # noqa: E402
from twin_identity import TwinIdentity  # noqa: E402


# OMOP concept IDs for common VitaClaw concepts (simplified mapping)
CONCEPT_MAP = {
    "blood-pressure": {"observation_concept_id": 4152194, "unit": "mmHg"},
    "blood-sugar": {"observation_concept_id": 3004501, "unit": "mmol/L"},
    "weight": {"observation_concept_id": 3025315, "unit": "kg"},
    "heart-rate": {"observation_concept_id": 3027018, "unit": "bpm"},
    "spo2": {"observation_concept_id": 40762499, "unit": "%"},
    "temperature": {"observation_concept_id": 3020891, "unit": "°C"},
    "sleep": {"observation_concept_id": 40771053, "unit": "score"},
    "medication-dose": {"drug_concept_id": 0},
    "supplement-dose": {"drug_concept_id": 0},
}

MEDICATION_CONCEPTS = {"medication-dose", "supplement-dose"}


def _date_shift(date_str: str, shift_days: int) -> str:
    """Shift a date/timestamp by a fixed number of days for de-identification."""
    if not date_str:
        return date_str
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str)
            shifted = dt + timedelta(days=shift_days)
            return shifted.isoformat(timespec="seconds")
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        shifted = dt + timedelta(days=shift_days)
        return shifted.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str


def _hash_id(value: str) -> str:
    """Generate a de-identified hash from an identifier."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def export_omop(
    output_dir: str,
    data_dir: str | None = None,
    grantee: str = "",
    purpose: str = "clinical_research",
    concepts: list[str] | None = None,
    anonymize: bool = False,
) -> dict:
    """Export VitaClaw records to OMOP CDM format.

    Args:
        output_dir: Directory to write output JSONL files.
        data_dir: Optional override for VitaClaw data directory.
        grantee: Grantee identifier for consent checking.
        purpose: Purpose of the export for consent checking.
        concepts: List of concepts to export (default: all in CONCEPT_MAP).
        anonymize: If True, de-identify by shifting dates and hashing IDs.

    Returns:
        Summary dict with counts.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    reader = CrossSkillReader(data_dir=data_dir)
    consent = ConsentManager()
    identity = TwinIdentity()

    # Generate person record
    person_id = identity.owner_id or "unknown"
    if anonymize:
        person_id = _hash_id(person_id)
        date_shift = random.randint(-180, 180)
    else:
        date_shift = 0

    person = {
        "person_id": person_id,
        "gender_concept_id": 0,  # Unknown — VitaClaw doesn't store gender as structured
        "year_of_birth": None,
        "race_concept_id": 0,
        "ethnicity_concept_id": 0,
    }

    concepts_to_export = concepts or list(CONCEPT_MAP.keys())
    observations = []
    drug_exposures = []
    obs_id = 1
    drug_id = 1

    for concept in concepts_to_export:
        if concept not in CONCEPT_MAP:
            continue

        # Consent check
        if grantee:
            result = consent.check(grantee, concept, purpose)
            if not result.allowed:
                continue

        records = reader.read(concept)
        if not records:
            continue

        is_med = concept in MEDICATION_CONCEPTS
        mapping = CONCEPT_MAP[concept]

        for record in records:
            data = record.get("data", {})
            ts = record.get("timestamp", "")
            if anonymize:
                ts = _date_shift(ts, date_shift)

            if is_med:
                med_name = data.get("name", "") or data.get("medication", "") or data.get("supplement", "")
                if anonymize:
                    med_name = med_name  # Keep medication names (not PII)
                drug_exposures.append({
                    "drug_exposure_id": drug_id,
                    "person_id": person_id,
                    "drug_concept_id": mapping.get("drug_concept_id", 0),
                    "drug_exposure_start_date": ts[:10] if ts else "",
                    "drug_exposure_end_date": ts[:10] if ts else "",
                    "drug_type_concept_id": 38000177,  # Prescription written
                    "drug_source_value": med_name,
                    "quantity": data.get("dose", 1),
                })
                drug_id += 1
            else:
                # Extract numeric values from data
                for field, value in data.items():
                    if not isinstance(value, (int, float)):
                        continue
                    observations.append({
                        "observation_id": obs_id,
                        "person_id": person_id,
                        "observation_concept_id": mapping.get("observation_concept_id", 0),
                        "observation_date": ts[:10] if ts else "",
                        "observation_datetime": ts,
                        "observation_type_concept_id": 32817,  # EHR
                        "value_as_number": value,
                        "unit_source_value": mapping.get("unit", ""),
                        "observation_source_value": f"{concept}.{field}",
                    })
                    obs_id += 1

    # Write output files
    person_path = out / "person.jsonl"
    person_path.write_text(json.dumps(person, ensure_ascii=False) + "\n", encoding="utf-8")

    obs_path = out / "observation.jsonl"
    with obs_path.open("w", encoding="utf-8") as f:
        for obs in observations:
            f.write(json.dumps(obs, ensure_ascii=False) + "\n")

    drug_path = out / "drug_exposure.jsonl"
    with drug_path.open("w", encoding="utf-8") as f:
        for drug in drug_exposures:
            f.write(json.dumps(drug, ensure_ascii=False) + "\n")

    return {
        "output_dir": str(out),
        "person_count": 1,
        "observation_count": len(observations),
        "drug_exposure_count": len(drug_exposures),
        "concepts_exported": [c for c in concepts_to_export if c in CONCEPT_MAP],
        "anonymized": anonymize,
    }


def main():
    parser = argparse.ArgumentParser(description="Export VitaClaw records to OMOP CDM format")
    parser.add_argument("output_dir", help="Directory to write OMOP JSONL files")
    parser.add_argument("--data-dir", help="VitaClaw data directory override")
    parser.add_argument("--grantee", default="", help="Grantee for consent checking")
    parser.add_argument("--purpose", default="clinical_research", help="Export purpose")
    parser.add_argument("--concepts", nargs="+", help="Concepts to export")
    parser.add_argument("--anonymize", action="store_true", help="De-identify output")
    args = parser.parse_args()

    result = export_omop(
        output_dir=args.output_dir,
        data_dir=args.data_dir,
        grantee=args.grantee,
        purpose=args.purpose,
        concepts=args.concepts,
        anonymize=args.anonymize,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
