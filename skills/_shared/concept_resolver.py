#!/usr/bin/env python3
"""Concept resolver: normalize field names, validate ranges, resolve LOINC codes.

Driven by schemas/health-concepts.yaml — no hardcoded mappings.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@functools.lru_cache(maxsize=1)
def _load_registry() -> dict:
    """Load and cache the concept registry YAML."""
    import yaml  # lazy import — yaml is only needed here

    path = _repo_root() / "schemas" / "health-concepts.yaml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ConceptNotFoundError(KeyError):
    """Raised when a concept ID is not in the registry."""


class FieldValidationError(ValueError):
    """Raised when a field value is outside plausible range."""


class ConceptResolver:
    """Registry-driven concept resolution for VitaClaw health data.

    Responsibilities:
      1. Resolve concept ID from canonical_type or aliases
      2. Normalize field names (alias → canonical)
      3. Validate field values against plausible ranges
      4. Return LOINC codes for concepts and fields
      5. Discover producer skills for a concept
    """

    def __init__(self, registry: dict | None = None):
        raw = registry or _load_registry()
        self._concepts: dict[str, dict] = raw.get("concepts", {})
        # Build reverse indexes
        self._type_to_concept: dict[str, str] = {}
        self._alias_index: dict[str, dict[str, str]] = {}  # concept -> {alias: canonical}
        self._build_indexes()

    def _build_indexes(self) -> None:
        for concept_id, defn in self._concepts.items():
            canonical_type = defn.get("canonical_type", "")
            if canonical_type:
                self._type_to_concept[canonical_type] = concept_id

            alias_map: dict[str, str] = {}
            for field_name, field_def in defn.get("fields", {}).items():
                for alias in field_def.get("aliases", []):
                    alias_map[alias] = field_name
            self._alias_index[concept_id] = alias_map

    # ── Public API ───────────────────────────────────────────

    def list_concepts(self) -> list[str]:
        """Return all registered concept IDs."""
        return list(self._concepts.keys())

    def get_concept(self, concept_id: str) -> dict:
        """Return full concept definition by ID."""
        if concept_id not in self._concepts:
            raise ConceptNotFoundError(concept_id)
        return self._concepts[concept_id]

    def resolve_from_type(self, record_type: str) -> str | None:
        """Map a JSONL record 'type' field to its concept ID."""
        return self._type_to_concept.get(record_type)

    def resolve_concept(self, identifier: str) -> tuple[str, dict]:
        """Resolve concept by ID or canonical_type. Returns (concept_id, definition)."""
        if identifier in self._concepts:
            return identifier, self._concepts[identifier]
        concept_id = self._type_to_concept.get(identifier)
        if concept_id:
            return concept_id, self._concepts[concept_id]
        raise ConceptNotFoundError(identifier)

    def normalize_fields(self, concept_id: str, data: dict) -> dict:
        """Normalize aliased field names to canonical names.

        Example: {"sys": 148, "dia": 96} → {"systolic": 148, "diastolic": 96}
        Unknown keys are passed through unchanged.
        """
        alias_map = self._alias_index.get(concept_id, {})
        if not alias_map:
            return dict(data)

        normalized: dict[str, Any] = {}
        for key, value in data.items():
            canonical = alias_map.get(key, key)
            normalized[canonical] = value
        return normalized

    def validate_fields(self, concept_id: str, data: dict, *, strict: bool = False) -> list[str]:
        """Validate field values against plausible ranges.

        Returns list of error messages. Empty list = all valid.
        If strict=True, raises FieldValidationError on first error.
        """
        defn = self._concepts.get(concept_id)
        if not defn:
            return [] if not strict else []

        errors: list[str] = []
        fields = defn.get("fields", {})
        for field_name, field_def in fields.items():
            if field_name not in data:
                continue
            value = data[field_name]
            field_range = field_def.get("range")
            if field_range and isinstance(value, (int, float)):
                lo, hi = field_range
                if not (lo <= value <= hi):
                    msg = f"Value out of plausible range for {field_name}: {value} (expected {lo}–{hi})"
                    if strict:
                        raise FieldValidationError(msg)
                    errors.append(msg)
        return errors

    def get_loinc(self, concept_id: str, field: str | None = None) -> str | None:
        """Return LOINC code for concept (panel) or specific field."""
        defn = self._concepts.get(concept_id)
        if not defn:
            return None
        if field is None:
            return defn.get("loinc")
        field_def = defn.get("fields", {}).get(field, {})
        return field_def.get("loinc")

    def get_producers(self, concept_id: str) -> list[dict]:
        """Return list of {skill, record_type} that produce this concept."""
        defn = self._concepts.get(concept_id)
        if not defn:
            return []
        return defn.get("producers", [])

    def get_consumers(self, concept_id: str) -> list[str]:
        """Return list of skill names that consume this concept."""
        defn = self._concepts.get(concept_id)
        if not defn:
            return []
        return defn.get("consumers", [])

    def get_vital_bounds(self) -> dict[str, tuple[float, float]]:
        """Build VITAL_BOUNDS dict from registry — replaces hardcoded bounds.

        Returns {canonical_field_name: (lo, hi)} for all fields with ranges.
        """
        bounds: dict[str, tuple[float, float]] = {}
        for defn in self._concepts.values():
            for field_name, field_def in defn.get("fields", {}).items():
                field_range = field_def.get("range")
                if field_range:
                    bounds[field_name] = tuple(field_range)  # type: ignore[arg-type]
        return bounds

    def normalize_and_validate(self, concept_id: str, data: dict, *, strict: bool = False) -> tuple[dict, list[str]]:
        """Normalize aliases then validate ranges. Returns (normalized_data, errors)."""
        normalized = self.normalize_fields(concept_id, data)
        errors = self.validate_fields(concept_id, normalized, strict=strict)
        return normalized, errors

    def concept_for_record(self, record: dict) -> str | None:
        """Given a JSONL record dict, return its concept_id or None."""
        record_type = record.get("type", "")
        return self.resolve_from_type(record_type)

    def enrich_meta(self, concept_id: str) -> dict:
        """Return _meta-compatible dict for a concept (for use in record envelopes)."""
        defn = self._concepts.get(concept_id, {})
        return {
            "domain": defn.get("domain", "health"),
            "concept": concept_id,
            "loinc": defn.get("loinc"),
        }
