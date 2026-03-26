#!/usr/bin/env python3
"""Tests for Google Fit importer."""

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
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from skills._shared.google_fit_importer import GoogleFitImporter  # noqa: E402


def _make_heart_rate_csv() -> str:
    """Create a synthetic Google Fit heart rate CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "bpm"])
    writer.writerow(["2026-03-26T10:00:00+08:00", "72"])
    writer.writerow(["2026-03-26T10:05:00+08:00", "75"])
    writer.writerow(["2026-03-26T10:10:00+08:00", "68"])
    return buf.getvalue()


def _make_daily_activity_csv() -> str:
    """Create a synthetic Google Fit daily activity CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "steps", "calories", "distance_m", "active_minutes"])
    writer.writerow(["2026-03-26", "8500", "320", "6200", "45"])
    writer.writerow(["2026-03-25", "10200", "410", "7800", "62"])
    return buf.getvalue()


def _make_sleep_csv() -> str:
    """Create a synthetic Google Fit sleep CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["start_time", "end_time", "duration_min"])
    writer.writerow(["2026-03-25T23:30:00+08:00", "2026-03-26T07:00:00+08:00", "450"])
    return buf.getvalue()


def _make_tcx_activity() -> str:
    """Create a minimal synthetic TCX activity file."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Running">
      <Id>2026-03-26T08:00:00+08:00</Id>
      <Lap StartTime="2026-03-26T08:00:00+08:00">
        <TotalTimeSeconds>1800</TotalTimeSeconds>
        <DistanceMeters>5000</DistanceMeters>
        <Calories>350</Calories>
        <AverageHeartRateBpm><Value>145</Value></AverageHeartRateBpm>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""


def _make_takeout_zip(tmpdir: str) -> Path:
    """Create a synthetic Google Takeout ZIP."""
    zip_path = Path(tmpdir) / "takeout.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Takeout/Fit/Daily activity metrics/daily_activity_2026.csv", _make_daily_activity_csv())
        zf.writestr("Takeout/Fit/Heart rate/heart_rate_2026.csv", _make_heart_rate_csv())
        zf.writestr("Takeout/Fit/Sleep/sleep_2026.csv", _make_sleep_csv())
        zf.writestr("Takeout/Fit/Activities/running_2026-03-26.tcx", _make_tcx_activity())
    return zip_path


class DiscoverFilesTest(unittest.TestCase):
    """Tests for GoogleFitImporter._discover_files."""

    def test_discover_csv_and_tcx_files(self):
        """_discover_files finds CSV and TCX files in extracted Takeout directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = _make_takeout_zip(tmpdir)
            importer = GoogleFitImporter()
            extracted = importer._extract_zip(str(zip_path))
            files = importer._discover_files(extracted)

            extensions = {f.suffix.lower() for f in files}
            self.assertIn(".csv", extensions)
            self.assertIn(".tcx", extensions)
            self.assertGreaterEqual(len(files), 4)


class ParseRecordsTest(unittest.TestCase):
    """Tests for GoogleFitImporter._parse_records."""

    def setUp(self):
        self.importer = GoogleFitImporter()

    def test_parse_heart_rate_csv(self):
        """Parses heart rate CSV into records with correct type and data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "heart_rate_2026.csv"
            csv_path.write_text(_make_heart_rate_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            self.assertEqual(len(records), 3)
            for rec in records:
                self.assertEqual(rec["type"], "heart_rate")
                self.assertIn("value", rec["data"])

    def test_parse_daily_activity_csv(self):
        """Parses daily activity CSV into step records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "daily_activity_2026.csv"
            csv_path.write_text(_make_daily_activity_csv(), encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            self.assertEqual(len(records), 2)
            for rec in records:
                self.assertEqual(rec["type"], "steps")
                self.assertIn("count", rec["data"])

    def test_parse_tcx_activity(self):
        """Parses TCX activity files into activity records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tcx_path = Path(tmpdir) / "running_2026-03-26.tcx"
            tcx_path.write_text(_make_tcx_activity(), encoding="utf-8")

            records = self.importer._parse_records(tcx_path)
            self.assertGreaterEqual(len(records), 1)
            rec = records[0]
            self.assertEqual(rec["type"], "activity")
            self.assertEqual(rec["data"]["sport"], "Running")
            self.assertIn("duration_seconds", rec["data"])

    def test_handles_malformed_csv_gracefully(self):
        """Missing/malformed CSV columns produce warning, not error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "bad_heart_rate.csv"
            csv_path.write_text("weird_column,another\nfoo,bar\n", encoding="utf-8")

            records = self.importer._parse_records(csv_path)
            # Should not crash, just return empty or skip bad rows
            self.assertIsInstance(records, list)


class FullImportFlowTest(unittest.TestCase):
    """Tests for full import_export flow."""

    def test_full_import_export_with_synthetic_zip(self):
        """Full import_export flow with synthetic Takeout ZIP produces correct records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = _make_takeout_zip(tmpdir)
            data_dir = Path(tmpdir) / "data_out"
            importer = GoogleFitImporter(data_dir=str(data_dir))

            result = importer.import_export(str(zip_path))

            self.assertIn("imported", result)
            self.assertGreater(result["imported"], 0)
            self.assertIn("by_type", result)
            # Should have heart_rate, steps, activity, and sleep_session
            self.assertIn("heart_rate", result["by_type"])
            self.assertIn("steps", result["by_type"])


class GoogleFitImporterPlatformTest(unittest.TestCase):
    """Tests for GoogleFitImporter class attributes."""

    def test_platform_is_google_fit(self):
        importer = GoogleFitImporter()
        self.assertEqual(importer.PLATFORM, "google-fit")


if __name__ == "__main__":
    unittest.main()
