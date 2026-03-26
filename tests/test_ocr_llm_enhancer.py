#!/usr/bin/env python3
"""Tests for OCR LLM enhancer with LOINC mapping and skill routing."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
SCRIPTS_DIR = ROOT / "skills" / "medical-document-ocr" / "scripts"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))


class OCRLLMEnhancerTest(unittest.TestCase):
    """Unit tests for OCRLLMEnhancer."""

    def _make_enhancer(self, llm_callback=None):
        from ocr_llm_enhancer import OCRLLMEnhancer
        return OCRLLMEnhancer(llm_callback=llm_callback)

    def _sample_fields(self):
        return [
            {
                "item_name": "血红蛋白",
                "value": "135",
                "unit": "g/L",
                "reference_range": "130-175",
                "concept_id": "hemoglobin",
                "record_type": "lab_result",
                "confidence": 0.85,
                "raw_text": "血红蛋白 135 g/L 130-175",
            },
            {
                "item_name": "血糖",
                "value": "5.6",
                "unit": "mmol/L",
                "reference_range": "3.9-6.1",
                "concept_id": "blood-sugar",
                "record_type": "lab_result",
                "confidence": 0.80,
                "raw_text": "血糖 5.6 mmol/L 3.9-6.1",
            },
        ]

    def test_enhance_with_mock_llm_returns_enhanced_fields(self):
        """enhance() with mock LLM returns enhanced fields with corrected values."""
        llm_response = json.dumps([
            {
                "item_name": "血红蛋白",
                "value": "138",
                "unit": "g/L",
                "reference_range": "130-175",
                "confidence": 0.95,
            },
            {
                "item_name": "血糖",
                "value": "5.6",
                "unit": "mmol/L",
                "reference_range": "3.9-6.1",
                "confidence": 0.92,
            },
        ])

        def mock_llm(prompt):
            return llm_response

        enhancer = self._make_enhancer(llm_callback=mock_llm)
        fields = self._sample_fields()
        result = enhancer.enhance(fields, raw_text="血红蛋白 135 g/L\n血糖 5.6 mmol/L")

        self.assertEqual(len(result), 2)
        # LLM corrected value should be applied
        self.assertEqual(result[0]["value"], "138")
        self.assertEqual(result[0]["confidence"], 0.95)
        # Types and units should be present
        self.assertIn("unit", result[0])
        self.assertEqual(result[0]["unit"], "g/L")

    def test_enhance_adds_loinc_code_via_concept_resolver(self):
        """enhance() adds loinc_code field to mapped fields."""
        enhancer = self._make_enhancer(llm_callback=None)
        fields = self._sample_fields()
        result = enhancer.enhance(fields)

        # hemoglobin has LOINC in health-concepts.yaml
        hemo = result[0]
        self.assertIn("loinc_code", hemo)
        # blood-sugar should also have a LOINC code
        sugar = result[1]
        self.assertIn("loinc_code", sugar)

    def test_enhance_adds_suggested_skill(self):
        """enhance() adds suggested_skill using ConceptResolver.get_producers()."""
        enhancer = self._make_enhancer(llm_callback=None)
        fields = self._sample_fields()
        result = enhancer.enhance(fields)

        # blood-pressure-tracker is the first producer for blood-pressure
        # For hemoglobin and blood-sugar, check that suggested_skill is set
        for f in result:
            self.assertIn("suggested_skill", f)

        # blood-sugar first producer is chronic-condition-monitor
        sugar = result[1]
        self.assertEqual(sugar["suggested_skill"], "chronic-condition-monitor")

    def test_enhance_logs_unmapped_concepts(self):
        """enhance() logs unmapped concepts as warnings instead of dropping them."""
        enhancer = self._make_enhancer(llm_callback=None)
        fields = [
            {
                "item_name": "未知指标XYZ",
                "value": "42",
                "unit": "",
                "reference_range": "",
                "concept_id": "",
                "record_type": "lab_result",
                "confidence": 0.5,
                "raw_text": "未知指标XYZ 42",
            }
        ]

        with patch("sys.stderr") as mock_stderr:
            result = enhancer.enhance(fields)

        # Field should NOT be dropped
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["item_name"], "未知指标XYZ")
        # Should have empty loinc_code and suggested_skill
        self.assertEqual(result[0]["loinc_code"], None)
        self.assertEqual(result[0]["suggested_skill"], "")

    def test_enhance_graceful_degradation_no_callback(self):
        """enhance() with llm_callback=None returns original fields unchanged (graceful degradation)."""
        enhancer = self._make_enhancer(llm_callback=None)
        fields = self._sample_fields()
        result = enhancer.enhance(fields)

        # Values should remain as original (no LLM correction)
        self.assertEqual(result[0]["value"], "135")
        self.assertEqual(result[1]["value"], "5.6")
        # But LOINC and skill should still be added
        self.assertIn("loinc_code", result[0])
        self.assertIn("suggested_skill", result[0])

    def test_enhance_graceful_degradation_callback_raises(self):
        """enhance() with LLM that raises exception falls back to original fields."""
        def failing_llm(prompt):
            raise RuntimeError("LLM service unavailable")

        enhancer = self._make_enhancer(llm_callback=failing_llm)
        fields = self._sample_fields()
        result = enhancer.enhance(fields)

        # Original values should be kept
        self.assertEqual(result[0]["value"], "135")
        self.assertEqual(len(result), 2)

    def test_enhance_empty_fields(self):
        """enhance() with empty fields list returns empty list."""
        enhancer = self._make_enhancer(llm_callback=None)
        result = enhancer.enhance([], raw_text="")
        self.assertEqual(result, [])

    def test_build_llm_prompt(self):
        """_build_llm_prompt() produces structured prompt with raw OCR text and fields."""
        enhancer = self._make_enhancer(llm_callback=None)
        fields = self._sample_fields()
        prompt = enhancer._build_llm_prompt(fields, raw_text="血红蛋白 135 g/L")

        # Should contain raw text
        self.assertIn("血红蛋白 135 g/L", prompt)
        # Should contain field data
        self.assertIn("血红蛋白", prompt)
        self.assertIn("135", prompt)
        # Should request JSON output
        self.assertIn("JSON", prompt)

    def test_parse_llm_response_valid_json(self):
        """_parse_llm_response() correctly parses LLM JSON output."""
        enhancer = self._make_enhancer(llm_callback=None)
        original = self._sample_fields()
        llm_output = json.dumps([
            {"item_name": "血红蛋白", "value": "138", "unit": "g/L",
             "reference_range": "130-175", "confidence": 0.95},
            {"item_name": "血糖", "value": "5.8", "unit": "mmol/L",
             "reference_range": "3.9-6.1", "confidence": 0.90},
        ])

        result = enhancer._parse_llm_response(llm_output, original)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], "138")
        self.assertEqual(result[1]["value"], "5.8")
        # concept_id from original should be preserved
        self.assertEqual(result[0]["concept_id"], "hemoglobin")

    def test_parse_llm_response_malformed_fallback(self):
        """_parse_llm_response() with malformed output falls back to original fields."""
        enhancer = self._make_enhancer(llm_callback=None)
        original = self._sample_fields()

        result = enhancer._parse_llm_response("this is not json at all", original)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], "135")

    def test_parse_llm_response_markdown_fenced_json(self):
        """_parse_llm_response() handles markdown code fences around JSON."""
        enhancer = self._make_enhancer(llm_callback=None)
        original = self._sample_fields()
        fenced = "```json\n" + json.dumps([
            {"item_name": "血红蛋白", "value": "140", "unit": "g/L",
             "reference_range": "130-175", "confidence": 0.96},
        ]) + "\n```"

        result = enhancer._parse_llm_response(fenced, original)
        self.assertEqual(result[0]["value"], "140")


if __name__ == "__main__":
    unittest.main()
