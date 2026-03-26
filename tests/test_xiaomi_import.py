#!/usr/bin/env python3
"""Tests for Xiaomi/Mi Fitness importer."""

from __future__ import annotations

import csv
import io
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
SCRIPTS_DIR = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from skills._shared.xiaomi_health_importer import XiaomiHealthImporter  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic fixture helpers
# ---------------------------------------------------------------------------

def _make_heart_rate_csv() -> str:
    """Xiaomi heart rate CSV with typical HEARTRATE_AUTO column names."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "time", "heartRate"])
    writer.writerow(["2026-03-26", "10:00:00", "72"])
    writer.writerow(["2026-03-26", "10:05:00", "75"])
    writer.writerow(["2026-03-26", "10:10:00", "68"])
    return buf.getvalue()


def _make_step_csv() -> str:
    """Xiaomi step count CSV with ACTIVITY_MINUTE columns."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "steps", "distance", "calories"])
    writer.writerow(["2026-03-26", "8500", "6200", "320"])
    writer.writerow(["2026-03-25", "10200", "7800", "410"])
    return buf.getvalue()


def _make_sleep_csv() -> str:
    """Xiaomi sleep CSV with SLEEP columns."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "bedTime", "wakeUpTime", "deepSleepMin", "lightSleepMin", "remSleepMin", "totalMin"])
    writer.writerow(["2026-03-26", "2026-03-25 23:30:00", "2026-03-26 07:00:00", "120", "210", "90", "450"])
    return buf.getvalue()


def _make_weight_csv() -> str:
    """Xiaomi body weight CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "time", "weight"])
    writer.writerow(["2026-03-26", "08:00:00", "72.5"])
    return buf.getvalue()


def _make_xiaomi_zip(tmpdir: str) -> Path:
    """Create a synthetic Xiaomi/Mi Fitness export ZIP."""
    zip_path = Path(tmpdir) / "xiaomi_export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("HEARTRATE_AUTO_2026.csv", _make_heart_rate_csv())
        zf.writestr("ACTIVITY_MINUTE_2026.csv", _make_step_csv())
        zf.writestr("SLEEP_2026.csv", _make_sleep_csv())
        zf.writestr("BODY_2026.csv", _make_weight_csv())
    return zip_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class DiscoverFilesTest(unittest.TestCase):
    """Tests for XiaomiHealthImporter._discover_files."""

    def test_discover_csv_files(self):
        """_discover_files finds CSV files in extracted Xiaomi export ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = _make_xiaomi_zip(tmpdir)
            importer = XiaomiHealthImporter()
            extracted = importer._extract_zip(str(zip_path))
            files = importer._discover_files(extracted)

            extensions = {f.suffix.lower() for f in files}
            self.assertIn(".csv", extensions)
            self.assertGreaterEqual(len(files), 4)


class ParseRecordsTest(unittest.TestCase):
    """Tests for XiaomiHealthImporter._parse_records."""

    def setUp(self):
        self.importer = XiaomiHealthImporter()

    def test_parse_heart_rate_csv(self):
        """Parses Xiaomi heart rate CSV into heart_rate records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "HEARTRATE_AUTO_2026.csv"
            csv_path.write_text(_make_heart_rate_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            hr_records = [r for r in records if r["type"] == "heart_rate"]
            self.assertEqual(len(hr_records), 3)
            for rec in hr_records:
                self.assertIn("value", rec["data"])
                self.assertIsInstance(rec["data"]["value"], int)

    def test_parse_step_csv(self):
        """Parses Xiaomi step count CSV into steps records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "ACTIVITY_MINUTE_2026.csv"
            csv_path.write_text(_make_step_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            step_records = [r for r in records if r["type"] == "steps"]
            self.assertEqual(len(step_records), 2)
            for rec in step_records:
                self.assertIn("count", rec["data"])

    def test_parse_sleep_csv(self):
        """Parses Xiaomi sleep CSV into sleep_session records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "SLEEP_2026.csv"
            csv_path.write_text(_make_sleep_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            sleep_records = [r for r in records if r["type"] == "sleep_session"]
            self.assertEqual(len(sleep_records), 1)
            rec = sleep_records[0]
            self.assertIn("total_min", rec["data"])
            self.assertEqual(rec["data"]["total_min"], 450)

    def test_handles_unexpected_columns_gracefully(self):
        """Missing/unexpected CSV columns produce warning, not error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "unknown_data.csv"
            csv_path.write_text("weird_col_a,weird_col_b\nfoo,bar\n", encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            # Should not crash, returns empty list
            self.assertIsInstance(records, list)


class FullImportFlowTest(unittest.TestCase):
    """Test full import_export with synthetic Xiaomi ZIP."""

    def test_full_import_produces_correct_records(self):
        """Full import_export with synthetic Xiaomi ZIP produces correct records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = _make_xiaomi_zip(tmpdir)
            data_dir = Path(tmpdir) / "data_out"
            importer = XiaomiHealthImporter(data_dir=str(data_dir))

            result = importer.import_export(str(zip_path))

            self.assertIn("imported", result)
            self.assertGreater(result["imported"], 0)
            self.assertIn("by_type", result)
            # Should have heart_rate, steps from our fixture
            self.assertIn("heart_rate", result["by_type"])
            self.assertIn("steps", result["by_type"])


class XiaomiImporterPlatformTest(unittest.TestCase):
    """Tests for XiaomiHealthImporter class attributes."""

    def test_platform_is_xiaomi(self):
        importer = XiaomiHealthImporter()
        self.assertEqual(importer.PLATFORM, "xiaomi")

    def test_inherits_from_health_importer_base(self):
        from skills._shared.health_importer_base import HealthImporterBase
        self.assertTrue(issubclass(XiaomiHealthImporter, HealthImporterBase))


if __name__ == "__main__":
    unittest.main()
