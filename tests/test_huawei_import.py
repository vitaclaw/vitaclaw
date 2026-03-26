#!/usr/bin/env python3
"""Tests for Huawei Health importer."""

from __future__ import annotations

import csv
import io
import json
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

from skills._shared.huawei_health_importer import HuaweiHealthImporter  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic fixture helpers
# ---------------------------------------------------------------------------

def _make_heart_rate_csv() -> str:
    """Huawei heart rate CSV with typical column names."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["startTime", "endTime", "heartRate"])
    writer.writerow(["2026-03-26 10:00:00", "2026-03-26 10:00:00", "72"])
    writer.writerow(["2026-03-26 10:05:00", "2026-03-26 10:05:00", "75"])
    writer.writerow(["2026-03-26 10:10:00", "2026-03-26 10:10:00", "68"])
    return buf.getvalue()


def _make_step_count_csv() -> str:
    """Huawei step count CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["startTime", "endTime", "step"])
    writer.writerow(["2026-03-26 00:00:00", "2026-03-26 23:59:59", "8500"])
    writer.writerow(["2026-03-25 00:00:00", "2026-03-25 23:59:59", "10200"])
    return buf.getvalue()


def _make_sleep_csv() -> str:
    """Huawei sleep data CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["startTime", "endTime", "duration(min)"])
    writer.writerow(["2026-03-25 23:30:00", "2026-03-26 07:00:00", "450"])
    return buf.getvalue()


def _make_heart_rate_json() -> str:
    """Huawei heart rate in JSON format (alternative export)."""
    records = [
        {"startTime": "2026-03-26 09:00:00", "heartRate": 80},
        {"startTime": "2026-03-26 09:05:00", "heartRate": 82},
    ]
    return json.dumps(records, ensure_ascii=False)


def _make_gpx_file() -> str:
    """Minimal GPX activity file."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Huawei Health"
     xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Morning Run</name>
    <type>running</type>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50</ele>
        <time>2026-03-26T08:00:00Z</time>
      </trkpt>
      <trkpt lat="39.9050" lon="116.4080">
        <ele>51</ele>
        <time>2026-03-26T08:30:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""


def _make_huawei_zip(tmpdir: str) -> Path:
    """Create a synthetic Huawei Health export ZIP."""
    zip_path = Path(tmpdir) / "huawei_export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Health data/heart_rate.csv", _make_heart_rate_csv())
        zf.writestr("Health data/step_count.csv", _make_step_count_csv())
        zf.writestr("Health data/sleep.csv", _make_sleep_csv())
        zf.writestr("Health data/heart_rate_detail.json", _make_heart_rate_json())
        zf.writestr("Motion path detail data/2026-03-26_running.gpx", _make_gpx_file())
    return zip_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class DiscoverFilesTest(unittest.TestCase):
    """Tests for HuaweiHealthImporter._discover_files."""

    def test_discover_csv_json_gpx_files(self):
        """_discover_files finds CSV, JSON, and GPX files in extracted Huawei export ZIP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = _make_huawei_zip(tmpdir)
            importer = HuaweiHealthImporter()
            extracted = importer._extract_zip(str(zip_path))
            files = importer._discover_files(extracted)

            extensions = {f.suffix.lower() for f in files}
            self.assertIn(".csv", extensions)
            self.assertIn(".json", extensions)
            self.assertIn(".gpx", extensions)
            self.assertGreaterEqual(len(files), 5)


class ParseRecordsTest(unittest.TestCase):
    """Tests for HuaweiHealthImporter._parse_records."""

    def setUp(self):
        self.importer = HuaweiHealthImporter()

    def test_parse_heart_rate_csv(self):
        """Parses Huawei heart rate CSV into heart_rate records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "heart_rate.csv"
            csv_path.write_text(_make_heart_rate_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            hr_records = [r for r in records if r["type"] == "heart_rate"]
            self.assertEqual(len(hr_records), 3)
            for rec in hr_records:
                self.assertIn("value", rec["data"])
                self.assertIsInstance(rec["data"]["value"], int)

    def test_parse_step_count_csv(self):
        """Parses Huawei step count CSV into steps records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "step_count.csv"
            csv_path.write_text(_make_step_count_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            step_records = [r for r in records if r["type"] == "steps"]
            self.assertEqual(len(step_records), 2)
            for rec in step_records:
                self.assertIn("count", rec["data"])

    def test_parse_sleep_csv(self):
        """Parses Huawei sleep CSV into sleep_session records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sleep.csv"
            csv_path.write_text(_make_sleep_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            sleep_records = [r for r in records if r["type"] == "sleep_session"]
            self.assertEqual(len(sleep_records), 1)
            rec = sleep_records[0]
            self.assertIn("total_min", rec["data"])
            self.assertEqual(rec["data"]["total_min"], 450)

    def test_parse_heart_rate_json(self):
        """Parses Huawei heart rate JSON into heart_rate records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "heart_rate_detail.json"
            json_path.write_text(_make_heart_rate_json(), encoding="utf-8")

            records = self.importer._parse_records(json_path)
            hr_records = [r for r in records if r["type"] == "heart_rate"]
            self.assertEqual(len(hr_records), 2)
            self.assertEqual(hr_records[0]["data"]["value"], 80)

    def test_handles_unexpected_columns_gracefully(self):
        """Missing/unexpected CSV columns produce warning, not error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "weird_data.csv"
            csv_path.write_text("col_alpha,col_beta\nfoo,bar\n", encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            # Should not crash, returns empty list
            self.assertIsInstance(records, list)

    def test_parse_gpx_activity(self):
        """Parses GPX files into activity records with timestamps and duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gpx_path = Path(tmpdir) / "running.gpx"
            gpx_path.write_text(_make_gpx_file(), encoding="utf-8")

            records = self.importer._parse_records(gpx_path)
            self.assertGreaterEqual(len(records), 1)
            rec = records[0]
            self.assertEqual(rec["type"], "activity")
            self.assertIn("duration_seconds", rec["data"])


class FullImportFlowTest(unittest.TestCase):
    """Test full import_export with synthetic Huawei ZIP."""

    def test_full_import_produces_correct_records(self):
        """Full import_export with synthetic Huawei ZIP produces correct records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = _make_huawei_zip(tmpdir)
            data_dir = Path(tmpdir) / "data_out"
            importer = HuaweiHealthImporter(data_dir=str(data_dir))

            result = importer.import_export(str(zip_path))

            self.assertIn("imported", result)
            self.assertGreater(result["imported"], 0)
            self.assertIn("by_type", result)
            # Should have multiple types from our fixture
            self.assertIn("heart_rate", result["by_type"])
            self.assertIn("steps", result["by_type"])


class HuaweiImporterPlatformTest(unittest.TestCase):
    """Tests for HuaweiHealthImporter class attributes."""

    def test_platform_is_huawei_health(self):
        importer = HuaweiHealthImporter()
        self.assertEqual(importer.PLATFORM, "huawei-health")

    def test_inherits_from_health_importer_base(self):
        from skills._shared.health_importer_base import HealthImporterBase
        self.assertTrue(issubclass(HuaweiHealthImporter, HealthImporterBase))


if __name__ == "__main__":
    unittest.main()
