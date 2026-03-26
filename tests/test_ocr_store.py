#!/usr/bin/env python3
"""Tests for OCR confirmation-to-storage bridge.

Validates that confirmed OCR fields are correctly stored into
HealthDataStore with provenance metadata, and that rejected/edited
fields are handled properly.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
SCRIPTS_DIR = ROOT / "skills" / "medical-document-ocr" / "scripts"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from ocr_store import store_confirmed_fields  # noqa: E402


def _sample_fields():
    """Return a list of sample confirmed fields mimicking OCR pipeline output."""
    return [
        {
            "item_name": "血红蛋白",
            "value": "135",
            "unit": "g/L",
            "reference_range": "130-175",
            "concept_id": "hemoglobin",
            "record_type": "lab_result",
            "confidence": 0.92,
            "status": "confirmed",
        },
        {
            "item_name": "白细胞",
            "value": "5.3",
            "unit": "10^9/L",
            "reference_range": "3.5-9.5",
            "concept_id": "wbc",
            "record_type": "lab_result",
            "confidence": 0.88,
            "status": "confirmed",
        },
        {
            "item_name": "收缩压",
            "value": "128",
            "unit": "mmHg",
            "reference_range": "90-140",
            "concept_id": "blood-pressure",
            "record_type": "bp",
            "confidence": 0.75,
            "status": "edited",
            "edited_value": "130",
        },
        {
            "item_name": "体温",
            "value": "36.5",
            "unit": "°C",
            "reference_range": "36-37.3",
            "concept_id": "temperature",
            "record_type": "temperature",
            "confidence": 0.40,
            "status": "rejected",
        },
    ]


class OCRStoreTest(unittest.TestCase):
    """Tests for store_confirmed_fields."""

    def test_store_confirmed_fields_writes_records(self, ):
        """Confirmed fields are written to HealthDataStore with correct record_type."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = _sample_fields()
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/memory/health/files/2026-03-26_lab.pdf",
                data_dir=tmp,
            )
            self.assertEqual(result["stored"], 3)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(len(result["errors"]), 0)
            self.assertEqual(len(result["records"]), 3)

    def test_store_maps_concept_to_skill(self):
        """concept_id is mapped to correct skill_name for HealthDataStore routing."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = [
                {
                    "item_name": "收缩压",
                    "value": "128",
                    "unit": "mmHg",
                    "reference_range": "90-140",
                    "concept_id": "blood-pressure",
                    "record_type": "bp",
                    "confidence": 0.90,
                    "status": "confirmed",
                },
            ]
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="physical_exam",
                archived_path="/test/archived.pdf",
                data_dir=tmp,
            )
            self.assertEqual(result["stored"], 1)
            # Should route to blood-pressure-tracker skill directory
            records_file = Path(tmp) / "blood-pressure-tracker" / "records.jsonl"
            self.assertTrue(records_file.exists(), f"Expected {records_file} to exist")

    def test_store_includes_ocr_source_meta(self):
        """Every stored record includes meta.source='ocr' and meta.document_type."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = [
                {
                    "item_name": "血红蛋白",
                    "value": "135",
                    "unit": "g/L",
                    "reference_range": "130-175",
                    "concept_id": "hemoglobin",
                    "record_type": "lab_result",
                    "confidence": 0.92,
                    "status": "confirmed",
                },
            ]
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/test/archived.pdf",
                data_dir=tmp,
            )
            record = result["records"][0]
            self.assertEqual(record["_meta"]["source"], "ocr")
            self.assertEqual(record["_meta"]["document_type"], "lab_test")

    def test_store_includes_archived_path_in_meta(self):
        """Every stored record includes archived_path in meta for document reference."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = [
                {
                    "item_name": "血红蛋白",
                    "value": "135",
                    "unit": "g/L",
                    "reference_range": "130-175",
                    "concept_id": "hemoglobin",
                    "record_type": "lab_result",
                    "confidence": 0.92,
                    "status": "confirmed",
                },
            ]
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/test/archived.pdf",
                data_dir=tmp,
            )
            record = result["records"][0]
            self.assertEqual(record["_meta"]["archived_path"], "/test/archived.pdf")

    def test_store_skips_rejected_fields(self):
        """Fields with status='rejected' are never stored."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = [
                {
                    "item_name": "体温",
                    "value": "36.5",
                    "unit": "°C",
                    "concept_id": "temperature",
                    "record_type": "temperature",
                    "confidence": 0.40,
                    "status": "rejected",
                },
            ]
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/test/archived.pdf",
                data_dir=tmp,
            )
            self.assertEqual(result["stored"], 0)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(len(result["records"]), 0)

    def test_store_uses_edited_value(self):
        """When status='edited', edited_value replaces original value."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = [
                {
                    "item_name": "血红蛋白",
                    "value": "135",
                    "unit": "g/L",
                    "reference_range": "130-175",
                    "concept_id": "hemoglobin",
                    "record_type": "lab_result",
                    "confidence": 0.92,
                    "status": "edited",
                    "edited_value": "140",
                },
            ]
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/test/archived.pdf",
                data_dir=tmp,
            )
            self.assertEqual(result["stored"], 1)
            record = result["records"][0]
            # The stored value should be the edited one
            self.assertEqual(record["data"]["value"], 140)

    def test_store_returns_summary(self):
        """store_confirmed_fields returns summary with stored/skipped counts."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = _sample_fields()
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/test/archived.pdf",
                data_dir=tmp,
            )
            self.assertIn("stored", result)
            self.assertIn("skipped", result)
            self.assertIn("errors", result)
            self.assertIn("records", result)
            self.assertIsInstance(result["stored"], int)
            self.assertIsInstance(result["skipped"], int)
            self.assertIsInstance(result["errors"], list)
            self.assertIsInstance(result["records"], list)

    def test_store_with_person_id(self):
        """person_id is passed through to HealthDataStore records."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fields = [
                {
                    "item_name": "血红蛋白",
                    "value": "135",
                    "unit": "g/L",
                    "reference_range": "130-175",
                    "concept_id": "hemoglobin",
                    "record_type": "lab_result",
                    "confidence": 0.92,
                    "status": "confirmed",
                },
            ]
            result = store_confirmed_fields(
                confirmed_fields=fields,
                document_type="lab_test",
                archived_path="/test/archived.pdf",
                person_id="mom",
                data_dir=tmp,
            )
            self.assertEqual(result["stored"], 1)
            record = result["records"][0]
            self.assertEqual(record.get("person_id"), "mom")


if __name__ == "__main__":
    unittest.main()
