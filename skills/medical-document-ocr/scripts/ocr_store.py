#!/usr/bin/env python3
"""OCR confirmation-to-storage bridge.

Takes confirmed fields from OCR staging output (produced by ocr_pipeline.py)
and stores them in HealthDataStore with appropriate skill mappings and
provenance metadata.

CRITICAL: This module only stores fields that the user has explicitly
confirmed or edited. Rejected fields are skipped. OCR data NEVER
reaches HealthDataStore without user confirmation.

Usage:
  python ocr_store.py confirmed.json --person-id <pid> --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _setup_imports():
    """Add shared modules to path."""
    shared = str(_repo_root() / "skills" / "_shared")
    if shared not in sys.path:
        sys.path.insert(0, shared)


_setup_imports()

from concept_resolver import ConceptResolver  # noqa: E402
from health_data_store import HealthDataStore  # noqa: E402

# Concept ID -> skill name mapping for HealthDataStore routing.
# Uses the first producer skill from health-concepts.yaml as the canonical store.
_CONCEPT_SKILL_MAP = {
    "blood-pressure": "blood-pressure-tracker",
    "blood-sugar": "chronic-condition-monitor",
    "heart-rate": "wearable-analysis-agent",
    "heart-rate-variability": "wearable-analysis-agent",
    "temperature": "lab-results",
    "spo2": "lab-results",
    "weight": "chronic-condition-monitor",
    "sleep": "sleep-analyzer",
    "caffeine": "caffeine-tracker",
    "supplement-dose": "supplement-manager",
    "supplement": "supplement-manager",
    "medication-dose": "medication-reminder",
    "kidney-function": "lab-results",
    "liver-function": "lab-results",
    "blood-lipids": "lab-results",
    "tumor-markers": "lab-results",
}

# Fallback skill for unknown concept IDs
_DEFAULT_SKILL = "lab-results"


def _resolve_skill_name(concept_id: str, resolver: ConceptResolver | None = None) -> str:
    """Map concept_id to the HealthDataStore skill name.

    First tries static map, then falls back to ConceptResolver producers.
    """
    if concept_id in _CONCEPT_SKILL_MAP:
        return _CONCEPT_SKILL_MAP[concept_id]

    # Try ConceptResolver for dynamic lookup
    if resolver and concept_id:
        try:
            producers = resolver.get_producers(concept_id)
            if producers:
                return producers[0].get("skill", _DEFAULT_SKILL)
        except Exception:
            pass

    return _DEFAULT_SKILL


def _parse_numeric(value: str) -> float | str:
    """Attempt to parse a string value as a number.

    Returns float if numeric, otherwise returns original string.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def store_confirmed_fields(
    confirmed_fields: list[dict],
    document_type: str,
    archived_path: str,
    person_id: str | None = None,
    data_dir: str | None = None,
    timestamp: str | None = None,
) -> dict:
    """Store user-confirmed OCR fields into HealthDataStore.

    Each confirmed field becomes a HealthDataStore record routed to the
    appropriate skill based on concept_id -> skill_name mapping.

    Args:
        confirmed_fields: List of field dicts, each with:
            - item_name, value, unit, reference_range, concept_id, record_type
            - status: "confirmed" | "edited" | "rejected"
            - edited_value: (optional) user-corrected value
        document_type: physical_exam | lab_test | outpatient | prescription
        archived_path: Path where original document was archived (OCR-05)
        person_id: Optional person_id for family member data isolation
        data_dir: Optional override for data directory
        timestamp: Optional document date (defaults to now)

    Returns:
        {"stored": N, "skipped": N, "errors": [], "records": [...]}
    """
    resolver = ConceptResolver()
    stored_count = 0
    skipped_count = 0
    errors: list[str] = []
    records: list[dict] = []

    for field in confirmed_fields:
        status = field.get("status", "confirmed")

        # Skip rejected fields -- user explicitly declined
        if status == "rejected":
            skipped_count += 1
            continue

        # Determine the value to store
        if status == "edited" and "edited_value" in field:
            raw_value = field["edited_value"]
        else:
            raw_value = field.get("value", "")

        # Parse numeric values
        value = _parse_numeric(raw_value)

        # Resolve concept to skill name for routing
        concept_id = field.get("concept_id", "")
        skill_name = _resolve_skill_name(concept_id, resolver)

        # Build record data
        record_data = {
            "item_name": field.get("item_name", ""),
            "value": value,
            "unit": field.get("unit", ""),
            "reference_range": field.get("reference_range", ""),
        }

        # Build provenance meta
        meta = {
            "source": "ocr",
            "document_type": document_type,
            "archived_path": archived_path,
            "concept_id": concept_id,
            "confidence": field.get("confidence", 0),
            "device": "ocr-scan",
        }

        # Determine record_type from field or default
        record_type = field.get("record_type", "lab_result")

        try:
            store = HealthDataStore(skill_name, data_dir=data_dir)
            record = store.append(
                record_type=record_type,
                data=record_data,
                note=f"OCR: {field.get('item_name', '')}",
                timestamp=timestamp,
                meta=meta,
                person_id=person_id,
            )
            records.append(record)
            stored_count += 1
        except Exception as e:
            errors.append(f"Failed to store {field.get('item_name', '?')}: {e}")

    return {
        "stored": stored_count,
        "skipped": skipped_count,
        "errors": errors,
        "records": records,
    }


def main():
    """CLI entry point: accept JSON file with confirmed fields, store them."""
    parser = argparse.ArgumentParser(
        description="Store confirmed OCR fields into HealthDataStore."
    )
    parser.add_argument(
        "confirmed_json",
        help="Path to JSON file with confirmed fields and document metadata",
    )
    parser.add_argument("--person-id", default=None, help="Person ID for family support")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    # Load confirmed fields from JSON
    json_path = Path(args.confirmed_json).expanduser().resolve()
    if not json_path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {json_path}"}))
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    confirmed_fields = data.get("confirmed_fields", data.get("extracted_fields", []))
    document_type = data.get("document_type", data.get("document_type_key", "lab_test"))
    archived_path = data.get("archived_path", "")
    timestamp = data.get("timestamp")

    result = store_confirmed_fields(
        confirmed_fields=confirmed_fields,
        document_type=document_type,
        archived_path=archived_path,
        person_id=args.person_id,
        timestamp=timestamp,
    )

    if args.format == "json":
        # Omit full records for cleaner JSON output
        output = {
            "success": True,
            "stored": result["stored"],
            "skipped": result["skipped"],
            "errors": result["errors"],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        _print_markdown(result)


def _print_markdown(result: dict):
    """Print storage result in human-readable markdown."""
    print("# OCR Storage Result\n")
    print(f"**Stored:** {result['stored']} fields")
    print(f"**Skipped:** {result['skipped']} fields")

    if result["errors"]:
        print(f"\n## Errors\n")
        for err in result["errors"]:
            print(f"- {err}")

    if result["records"]:
        print(f"\n## Stored Records\n")
        print("| Item | Value | Skill | Record Type |")
        print("|------|-------|-------|-------------|")
        for rec in result["records"]:
            item = rec.get("data", {}).get("item_name", "")
            val = rec.get("data", {}).get("value", "")
            skill = rec.get("skill", "")
            rtype = rec.get("type", "")
            print(f"| {item} | {val} | {skill} | {rtype} |")


if __name__ == "__main__":
    main()
