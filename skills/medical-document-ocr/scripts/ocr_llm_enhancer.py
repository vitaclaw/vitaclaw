#!/usr/bin/env python3
"""OCR LLM enhancer: post-processing module for OCR field enhancement.

Takes raw OCR extracted fields and optionally uses an LLM callback to:
1. Correct misread values using medical context
2. Identify field types
3. Add missing units

Then enriches all fields (LLM-enhanced or original) with:
- LOINC codes via ConceptResolver
- Suggested tracking skill via ConceptResolver.get_producers()
- Logs unmapped concepts as warnings

Design: The enhancer does NOT call any LLM API directly. It accepts a
callback function that the host AI runtime provides. This keeps the module
decoupled from any specific LLM provider (per D-05).
"""

from __future__ import annotations

import json
import re
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


class OCRLLMEnhancer:
    """LLM-enhanced post-processor for OCR extracted fields.

    Enriches fields with LOINC codes and skill routing suggestions.
    Optionally uses an LLM callback to correct OCR extraction errors.
    Falls back gracefully when LLM is unavailable.
    """

    def __init__(self, concept_resolver=None, llm_callback=None):
        """Initialize enhancer.

        Args:
            concept_resolver: ConceptResolver instance (or creates default).
            llm_callback: Callable that takes a prompt string and returns
                LLM response string, or None for no-LLM mode.
        """
        self._resolver = concept_resolver or ConceptResolver()
        self._llm_callback = llm_callback

    def enhance(self, extracted_fields: list[dict], raw_text: str = "") -> list[dict]:
        """Enhance extracted OCR fields with LLM correction, LOINC codes, and skill routing.

        Args:
            extracted_fields: List of field dicts from OCR pipeline.
            raw_text: Raw OCR text for LLM context.

        Returns:
            Enhanced field list with loinc_code and suggested_skill added.
        """
        if not extracted_fields:
            return []

        # Step 1: Optionally use LLM to correct values
        working_fields = list(extracted_fields)
        if self._llm_callback is not None:
            try:
                prompt = self._build_llm_prompt(extracted_fields, raw_text)
                response = self._llm_callback(prompt)
                if response is not None:
                    working_fields = self._parse_llm_response(response, extracted_fields)
            except Exception as e:
                print(f"[WARN] LLM enhancement failed, using raw extraction: {e}", file=sys.stderr)
                working_fields = list(extracted_fields)

        # Step 2: Enrich each field with LOINC code and suggested skill
        enhanced: list[dict] = []
        for field in working_fields:
            enriched = dict(field)
            concept_id = enriched.get("concept_id", "")

            # Look up LOINC code
            loinc_code = None
            if concept_id:
                loinc_code = self._resolver.get_loinc(concept_id)

            enriched["loinc_code"] = loinc_code

            # Look up suggested skill
            suggested_skill = ""
            if concept_id:
                producers = self._resolver.get_producers(concept_id)
                if producers:
                    suggested_skill = producers[0].get("skill", "")

            enriched["suggested_skill"] = suggested_skill

            # Log unmapped concepts
            if not concept_id:
                item_name = enriched.get("item_name", "unknown")
                print(f"[WARN] Unmapped OCR field: {item_name}", file=sys.stderr)

            enhanced.append(enriched)

        return enhanced

    def _build_llm_prompt(self, extracted_fields: list[dict], raw_text: str) -> str:
        """Build a structured prompt for LLM field correction.

        Args:
            extracted_fields: Current extracted fields as initial extraction.
            raw_text: Raw OCR text for context.

        Returns:
            Prompt string requesting JSON output.
        """
        fields_json = json.dumps(
            [
                {
                    "item_name": f.get("item_name", ""),
                    "value": f.get("value", ""),
                    "unit": f.get("unit", ""),
                    "reference_range": f.get("reference_range", ""),
                    "confidence": f.get("confidence", 0),
                }
                for f in extracted_fields
            ],
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""You are a medical document OCR correction assistant. Given raw OCR text and an initial extraction of lab results from a Chinese medical document, please:

1. Correct any misread values using medical context (e.g., implausible lab values)
2. Identify the correct field types
3. Add missing units where they can be inferred from context

Raw OCR text:
{raw_text}

Initial extraction (JSON):
{fields_json}

Return ONLY a JSON array of corrected fields. Each object should have:
- item_name: string
- value: string
- unit: string
- reference_range: string
- confidence: number (0-1)

Return JSON only, no explanation."""
        return prompt

    def _parse_llm_response(self, response: str, original_fields: list[dict]) -> list[dict]:
        """Parse LLM JSON response and merge with original fields.

        Args:
            response: LLM response string (may contain markdown fences).
            original_fields: Original fields to fall back to and merge concept_id from.

        Returns:
            Merged field list with LLM corrections applied.
        """
        # Strip markdown code fences if present
        text = response.strip()
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return list(original_fields)

        if not isinstance(parsed, list):
            return list(original_fields)

        # Build lookup from original fields by item_name for concept_id preservation
        original_by_name: dict[str, dict] = {}
        for f in original_fields:
            name = f.get("item_name", "")
            if name:
                original_by_name[name] = f

        # Merge: take LLM corrections but preserve concept_id and other metadata from originals
        merged: list[dict] = []
        for llm_field in parsed:
            if not isinstance(llm_field, dict):
                continue
            name = llm_field.get("item_name", "")
            original = original_by_name.get(name, {})

            result = dict(original)  # Start from original to keep all metadata
            # Apply LLM corrections
            for key in ("value", "unit", "reference_range", "confidence"):
                if key in llm_field:
                    result[key] = llm_field[key]
            if "item_name" in llm_field:
                result["item_name"] = llm_field["item_name"]

            merged.append(result)

        if not merged:
            return list(original_fields)

        return merged
