#!/usr/bin/env python3
"""FHIR R4 bidirectional mapper for VitaClaw records.

Maps VitaClaw JSONL records to/from FHIR R4 resources:
  - Observation (vitals, labs)
  - MedicationStatement (medications)
  - Condition (conditions)

Uses the concept registry for LOINC coding.
"""

from __future__ import annotations

from datetime import datetime


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class FHIRMapper:
    """Bidirectional mapping between VitaClaw records and FHIR R4 resources."""

    # Map concept → FHIR resource type
    CONCEPT_TO_RESOURCE = {
        "blood-pressure": "Observation",
        "blood-sugar": "Observation",
        "weight": "Observation",
        "heart-rate": "Observation",
        "heart-rate-variability": "Observation",
        "temperature": "Observation",
        "spo2": "Observation",
        "kidney-function": "Observation",
        "liver-function": "Observation",
        "blood-lipids": "Observation",
        "tumor-markers": "Observation",
        "sleep": "Observation",
        "medication-dose": "MedicationStatement",
        "supplement-dose": "MedicationStatement",
    }

    def __init__(self):
        self._resolver = None

    def _get_resolver(self):
        if self._resolver is None:
            try:
                from concept_resolver import ConceptResolver

                self._resolver = ConceptResolver()
            except ImportError:
                pass
        return self._resolver

    # ── VitaClaw → FHIR ─────────────────────────────────────

    def to_fhir(self, record: dict) -> dict | None:
        """Convert a VitaClaw record to a FHIR R4 resource."""
        meta = record.get("_meta", {})
        concept = meta.get("concept", "")
        record_type = record.get("type", "")

        if not concept:
            resolver = self._get_resolver()
            if resolver:
                concept = resolver.resolve_from_type(record_type) or ""

        resource_type = self.CONCEPT_TO_RESOURCE.get(concept)
        if not resource_type:
            return None

        if resource_type == "Observation":
            return self._to_observation(record, concept)
        elif resource_type == "MedicationStatement":
            return self._to_medication_statement(record, concept)

        return None

    def _to_observation(self, record: dict, concept: str) -> dict:
        """Convert to FHIR Observation resource."""
        data = record.get("data", {})
        meta = record.get("_meta", {})
        loinc = meta.get("loinc", "")

        if not loinc:
            resolver = self._get_resolver()
            if resolver:
                loinc = resolver.get_loinc(concept) or ""

        observation = {
            "resourceType": "Observation",
            "id": record.get("id", ""),
            "status": "final",
            "code": {
                "coding": [],
                "text": concept,
            },
            "effectiveDateTime": record.get("timestamp", ""),
            "issued": _now_iso(),
        }

        if loinc:
            observation["code"]["coding"].append(
                {
                    "system": "http://loinc.org",
                    "code": loinc,
                    "display": concept,
                }
            )

        # Multi-component observations (like BP with systolic + diastolic)
        components = self._extract_components(data, concept)
        if components:
            observation["component"] = components
        else:
            # Single-value observation
            value = self._extract_primary_value(data, concept)
            if value is not None:
                observation["valueQuantity"] = value

        return observation

    def _extract_components(self, data: dict, concept: str) -> list[dict]:
        """Extract FHIR components for multi-value observations."""
        resolver = self._get_resolver()
        if not resolver:
            return []

        try:
            defn = resolver.get_concept(concept)
        except KeyError:
            return []

        components: list[dict] = []
        alias_map = {}
        for fname, fdef in defn.get("fields", {}).items():
            for alias in fdef.get("aliases", []):
                alias_map[alias] = fname

        numeric_fields = []
        for fname, fdef in defn.get("fields", {}).items():
            if fdef.get("type") in ("integer", "number") and fdef.get("unit"):
                numeric_fields.append((fname, fdef))

        if len(numeric_fields) <= 1:
            return []  # Single value, not multi-component

        for fname, fdef in numeric_fields:
            # Try canonical name first, then aliases
            value = data.get(fname)
            if value is None:
                for alias in fdef.get("aliases", []):
                    value = data.get(alias)
                    if value is not None:
                        break
            if value is None:
                continue

            component = {
                "code": {
                    "coding": [],
                    "text": fname,
                },
                "valueQuantity": {
                    "value": value,
                    "unit": fdef.get("unit", ""),
                    "system": "http://unitsofmeasure.org",
                },
            }
            field_loinc = fdef.get("loinc")
            if field_loinc:
                component["code"]["coding"].append(
                    {
                        "system": "http://loinc.org",
                        "code": field_loinc,
                        "display": fname,
                    }
                )
            components.append(component)

        return components

    def _extract_primary_value(self, data: dict, concept: str) -> dict | None:
        """Extract the primary numeric value for single-value observations."""
        resolver = self._get_resolver()
        if not resolver:
            # Fallback: find first numeric value
            for key, val in data.items():
                if isinstance(val, (int, float)):
                    return {"value": val, "unit": ""}
            return None

        try:
            defn = resolver.get_concept(concept)
        except KeyError:
            return None

        for fname, fdef in defn.get("fields", {}).items():
            if fdef.get("type") not in ("integer", "number"):
                continue
            value = data.get(fname)
            if value is None:
                for alias in fdef.get("aliases", []):
                    value = data.get(alias)
                    if value is not None:
                        break
            if value is not None:
                return {
                    "value": value,
                    "unit": fdef.get("unit", ""),
                    "system": "http://unitsofmeasure.org",
                }
        return None

    def _to_medication_statement(self, record: dict, concept: str) -> dict:
        """Convert to FHIR MedicationStatement."""
        data = record.get("data", {})
        med_name = data.get("name", "") or data.get("medication", "") or data.get("supplement", "")
        taken = data.get("taken", True)

        return {
            "resourceType": "MedicationStatement",
            "id": record.get("id", ""),
            "status": "active" if taken else "not-taken",
            "medicationCodeableConcept": {
                "text": med_name,
            },
            "effectiveDateTime": record.get("timestamp", ""),
            "dateAsserted": _now_iso(),
        }

    # ── FHIR → VitaClaw ─────────────────────────────────────

    def from_fhir(self, resource: dict, skill: str = "fhir-import") -> dict | None:
        """Convert a FHIR R4 resource to a VitaClaw record."""
        resource_type = resource.get("resourceType", "")

        if resource_type == "Observation":
            return self._from_observation(resource, skill)
        elif resource_type == "MedicationStatement":
            return self._from_medication_statement(resource, skill)

        return None

    def _from_observation(self, resource: dict, skill: str) -> dict:
        """Convert FHIR Observation to VitaClaw record."""
        # Extract LOINC code
        loinc = ""
        concept = ""
        for coding in resource.get("code", {}).get("coding", []):
            if coding.get("system") == "http://loinc.org":
                loinc = coding.get("code", "")
                break

        # Try to resolve concept from LOINC
        resolver = self._get_resolver()
        if resolver and loinc:
            for cid in resolver.list_concepts():
                if resolver.get_loinc(cid) == loinc:
                    concept = cid
                    break

        if not concept:
            concept = resource.get("code", {}).get("text", "unknown")

        # Extract data from components or valueQuantity
        data = {}
        components = resource.get("component", [])
        if components:
            for comp in components:
                field_name = comp.get("code", {}).get("text", "")
                vq = comp.get("valueQuantity", {})
                if field_name and "value" in vq:
                    data[field_name] = vq["value"]
        else:
            vq = resource.get("valueQuantity", {})
            if "value" in vq:
                data["value"] = vq["value"]

        # Determine record type from concept
        record_type = "observation"
        if resolver and concept:
            try:
                defn = resolver.get_concept(concept)
                record_type = defn.get("canonical_type", "observation")
            except KeyError:
                pass

        return {
            "type": record_type,
            "timestamp": resource.get("effectiveDateTime", _now_iso()),
            "skill": skill,
            "note": "Imported from FHIR Observation",
            "data": data,
            "_meta": {
                "domain": "health",
                "concept": concept,
                "loinc": loinc,
                "source": "import",
            },
        }

    def _from_medication_statement(self, resource: dict, skill: str) -> dict:
        """Convert FHIR MedicationStatement to VitaClaw record."""
        med_name = resource.get("medicationCodeableConcept", {}).get("text", "")
        status = resource.get("status", "")
        taken = status == "active"

        return {
            "type": "dose",
            "timestamp": resource.get("effectiveDateTime", _now_iso()),
            "skill": skill,
            "note": "Imported from FHIR MedicationStatement",
            "data": {
                "name": med_name,
                "taken": taken,
            },
            "_meta": {
                "domain": "health",
                "concept": "medication-dose",
                "source": "import",
            },
        }

    # ── FHIR Bundle ──────────────────────────────────────────

    def to_fhir_bundle(self, records: list[dict]) -> dict:
        """Convert multiple VitaClaw records to a FHIR Bundle."""
        entries: list[dict] = []
        for record in records:
            resource = self.to_fhir(record)
            if resource:
                entries.append(
                    {
                        "resource": resource,
                        "request": {
                            "method": "POST",
                            "url": resource["resourceType"],
                        },
                    }
                )

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "timestamp": _now_iso(),
            "entry": entries,
        }

    def from_fhir_bundle(self, bundle: dict, skill: str = "fhir-import") -> list[dict]:
        """Convert a FHIR Bundle to VitaClaw records."""
        records: list[dict] = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", entry)
            record = self.from_fhir(resource, skill=skill)
            if record:
                records.append(record)
        return records
