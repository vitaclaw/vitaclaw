#!/usr/bin/env python3
"""Tests for HealthImporterBase shared importer class."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from skills._shared.health_importer_base import HealthImporterBase  # noqa: E402


class _TestImporter(HealthImporterBase):
    """Concrete subclass for testing base class mechanics."""

    PLATFORM = "test-device"

    def _discover_files(self, extracted_dir: Path) -> list[Path]:
        return sorted(extracted_dir.rglob("*.csv"))

    def _parse_records(self, data_file: Path) -> list[dict]:
        records = []
        for line in data_file.read_text(encoding="utf-8").strip().splitlines()[1:]:
            parts = line.split(",")
            if len(parts) < 3:
                continue
            records.append({
                "type": parts[0],
                "timestamp": parts[1],
                "data": {"value": float(parts[2])},
            })
        return records


class FuzzyDedupTest(unittest.TestCase):
    """Tests for is_fuzzy_duplicate / _fuzzy_dedup logic."""

    def setUp(self):
        self.importer = _TestImporter()

    def test_fuzzy_duplicate_same_type_close_time_close_value(self):
        """Records with same type, person_id, timestamp within 60s, values within 5% are duplicates."""
        new = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:30+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        existing = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 73},
            "person_id": None,
        }
        self.assertTrue(self.importer.is_fuzzy_duplicate(new, existing))

    def test_fuzzy_duplicate_different_types(self):
        """Different record types are never duplicates."""
        new = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        existing = {
            "type": "steps",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        self.assertFalse(self.importer.is_fuzzy_duplicate(new, existing))

    def test_fuzzy_duplicate_timestamps_over_60s_apart(self):
        """Timestamps more than 60 seconds apart are not duplicates."""
        new = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:02:00+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        existing = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        self.assertFalse(self.importer.is_fuzzy_duplicate(new, existing))

    def test_fuzzy_duplicate_values_over_5pct_different(self):
        """Values more than 5% different are not duplicates."""
        new = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 80},
            "person_id": None,
        }
        existing = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        # 80 vs 72 => ~11% difference
        self.assertFalse(self.importer.is_fuzzy_duplicate(new, existing))

    def test_fuzzy_duplicate_different_person_ids(self):
        """Different person_ids are never duplicates."""
        new = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": "alice",
        }
        existing = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": "bob",
        }
        self.assertFalse(self.importer.is_fuzzy_duplicate(new, existing))

    def test_fuzzy_duplicate_none_vs_string_person_id(self):
        """None person_id vs string person_id are different."""
        new = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": None,
        }
        existing = {
            "type": "heart_rate",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 72},
            "person_id": "alice",
        }
        self.assertFalse(self.importer.is_fuzzy_duplicate(new, existing))

    def test_fuzzy_duplicate_zero_value(self):
        """Zero existing value: only zero new value is a duplicate."""
        new_zero = {
            "type": "steps",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 0},
            "person_id": None,
        }
        existing_zero = {
            "type": "steps",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 0},
            "person_id": None,
        }
        self.assertTrue(self.importer.is_fuzzy_duplicate(new_zero, existing_zero))

        new_nonzero = {
            "type": "steps",
            "timestamp": "2026-03-26T10:00:00+08:00",
            "data": {"value": 5},
            "person_id": None,
        }
        self.assertFalse(self.importer.is_fuzzy_duplicate(new_nonzero, existing_zero))


class ExtractZipTest(unittest.TestCase):
    """Tests for _extract_zip functionality."""

    def test_extract_zip_returns_directory_with_contents(self):
        """_extract_zip extracts ZIP contents to a temporary directory."""
        importer = _TestImporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("data/test.csv", "type,timestamp,value\nheart_rate,2026-03-26T10:00:00+08:00,72\n")

            extracted = importer._extract_zip(str(zip_path))
            self.assertTrue(extracted.is_dir())
            csv_files = list(extracted.rglob("*.csv"))
            self.assertEqual(len(csv_files), 1)
            self.assertIn("test.csv", csv_files[0].name)


class StoreRecordsTest(unittest.TestCase):
    """Tests for _store_records with HealthDataStore integration."""

    def test_store_records_writes_via_health_data_store(self):
        """_store_records writes records via HealthDataStore.append with correct meta."""
        with tempfile.TemporaryDirectory() as tmpdir:
            importer = _TestImporter(data_dir=tmpdir)
            records = [
                {
                    "type": "heart_rate",
                    "timestamp": "2026-03-26T10:00:00+08:00",
                    "data": {"value": 72},
                },
            ]
            result = importer._store_records(records)
            self.assertEqual(result["imported"], 1)
            self.assertEqual(result["skipped_dupes"], 0)

            # Verify the record was written to JSONL
            jsonl_path = Path(tmpdir) / "heart-rate-tracker" / "records.jsonl"
            self.assertTrue(jsonl_path.exists())
            stored = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
            self.assertEqual(stored["type"], "heart_rate")
            self.assertEqual(stored["_meta"]["source"], "import")
            self.assertEqual(stored["_meta"]["device"], "test-device")

    def test_store_records_skips_fuzzy_duplicates(self):
        """_store_records skips fuzzy duplicate records and reports counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            importer = _TestImporter(data_dir=tmpdir)
            records = [
                {
                    "type": "heart_rate",
                    "timestamp": "2026-03-26T10:00:00+08:00",
                    "data": {"value": 72},
                },
            ]
            # Import once
            importer._store_records(records)

            # Import again with fuzzy-similar record
            records2 = [
                {
                    "type": "heart_rate",
                    "timestamp": "2026-03-26T10:00:30+08:00",
                    "data": {"value": 73},
                },
            ]
            result = importer._store_records(records2)
            self.assertEqual(result["imported"], 0)
            self.assertEqual(result["skipped_dupes"], 1)

    def test_store_records_with_person_id(self):
        """_store_records passes person_id to HealthDataStore.append."""
        with tempfile.TemporaryDirectory() as tmpdir:
            importer = _TestImporter(data_dir=tmpdir, person_id="alice")
            records = [
                {
                    "type": "heart_rate",
                    "timestamp": "2026-03-26T10:00:00+08:00",
                    "data": {"value": 72},
                },
            ]
            importer._store_records(records)

            jsonl_path = Path(tmpdir) / "heart-rate-tracker" / "records.jsonl"
            stored = json.loads(jsonl_path.read_text(encoding="utf-8").strip())
            self.assertEqual(stored["person_id"], "alice")


class ImportExportOrchestrationTest(unittest.TestCase):
    """Tests for import_export end-to-end orchestration."""

    def test_import_export_orchestrates_full_flow(self):
        """import_export: extract -> discover -> parse -> dedup -> store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test ZIP
            zip_path = Path(tmpdir) / "export.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                csv_content = (
                    "type,timestamp,value\n"
                    "heart_rate,2026-03-26T10:00:00+08:00,72\n"
                    "heart_rate,2026-03-26T10:05:00+08:00,75\n"
                    "steps,2026-03-26T10:00:00+08:00,5000\n"
                )
                zf.writestr("data/metrics.csv", csv_content)

            data_dir = Path(tmpdir) / "data_out"
            importer = _TestImporter(data_dir=str(data_dir))
            result = importer.import_export(str(zip_path))

            self.assertIn("imported", result)
            self.assertIn("skipped_dupes", result)
            self.assertIn("by_type", result)
            self.assertEqual(result["imported"], 3)
            self.assertEqual(result["skipped_dupes"], 0)
            self.assertIn("heart_rate", result["by_type"])
            self.assertIn("steps", result["by_type"])


class NormalizeTimestampTest(unittest.TestCase):
    """Tests for timestamp normalization."""

    def test_normalize_iso_passthrough(self):
        importer = _TestImporter()
        ts = "2026-03-26T10:00:00+08:00"
        result = importer._normalize_timestamp(ts)
        self.assertIn("2026-03-26", result)

    def test_normalize_adds_utc_when_no_tz(self):
        importer = _TestImporter()
        ts = "2026-03-26T10:00:00"
        result = importer._normalize_timestamp(ts, tz_offset="+08:00")
        self.assertIn("+08:00", result)


if __name__ == "__main__":
    unittest.main()
