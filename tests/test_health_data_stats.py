#!/usr/bin/env python3
"""Unit tests for HealthDataStore.stats() and global_stats() data observability methods."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skills._shared.health_data_store import HealthDataStore


class HealthDataStatsTest(unittest.TestCase):
    """Tests for stats() instance method."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _write_records(self, skill: str, records: list[dict]) -> None:
        """Helper to write synthetic JSONL records."""
        skill_dir = Path(self.data_dir) / skill
        skill_dir.mkdir(parents=True, exist_ok=True)
        with (skill_dir / "records.jsonl").open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def test_stats_empty_skill(self):
        """stats() on empty skill returns zero counts and None timestamps."""
        store = HealthDataStore("empty-skill", data_dir=self.data_dir)
        result = store.stats()
        self.assertEqual(result["record_count"], 0)
        self.assertIsNone(result["last_updated"])
        self.assertIsNone(result["earliest_record"])
        self.assertIsNone(result["latest_record"])
        self.assertEqual(result["time_span_days"], 0)

    def test_stats_with_records(self):
        """stats() on skill with 3 records returns correct count, timestamps, and span."""
        self._write_records("bp-tracker", [
            {"id": "r1", "type": "bp", "timestamp": "2024-01-01T10:00:00", "data": {}},
            {"id": "r2", "type": "bp", "timestamp": "2024-01-15T10:00:00", "data": {}},
            {"id": "r3", "type": "bp", "timestamp": "2024-04-01T10:00:00", "data": {}},
        ])
        store = HealthDataStore("bp-tracker", data_dir=self.data_dir)
        result = store.stats()
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["earliest_record"], "2024-01-01T10:00:00")
        self.assertEqual(result["latest_record"], "2024-04-01T10:00:00")
        self.assertEqual(result["last_updated"], "2024-04-01T10:00:00")
        self.assertEqual(result["time_span_days"], 91)

    def test_stats_person_id_filter_mom(self):
        """stats(person_id='mom') returns only mom's records."""
        self._write_records("bp-tracker", [
            {"id": "r1", "type": "bp", "timestamp": "2024-01-01T10:00:00", "data": {}, "person_id": "mom"},
            {"id": "r2", "type": "bp", "timestamp": "2024-01-10T10:00:00", "data": {}},
            {"id": "r3", "type": "bp", "timestamp": "2024-02-01T10:00:00", "data": {}, "person_id": "mom"},
            {"id": "r4", "type": "bp", "timestamp": "2024-03-01T10:00:00", "data": {}, "person_id": "dad"},
        ])
        store = HealthDataStore("bp-tracker", data_dir=self.data_dir)
        result = store.stats(person_id="mom")
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["earliest_record"], "2024-01-01T10:00:00")
        self.assertEqual(result["latest_record"], "2024-02-01T10:00:00")
        self.assertEqual(result["time_span_days"], 31)

    def test_stats_person_id_filter_self(self):
        """stats(person_id='self') returns records without person_id field."""
        self._write_records("bp-tracker", [
            {"id": "r1", "type": "bp", "timestamp": "2024-01-01T10:00:00", "data": {}},
            {"id": "r2", "type": "bp", "timestamp": "2024-01-20T10:00:00", "data": {}},
            {"id": "r3", "type": "bp", "timestamp": "2024-02-01T10:00:00", "data": {}, "person_id": "mom"},
        ])
        store = HealthDataStore("bp-tracker", data_dir=self.data_dir)
        result = store.stats(person_id="self")
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["earliest_record"], "2024-01-01T10:00:00")
        self.assertEqual(result["latest_record"], "2024-01-20T10:00:00")
        self.assertEqual(result["time_span_days"], 19)


class HealthDataGlobalStatsTest(unittest.TestCase):
    """Tests for global_stats() classmethod."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _write_records(self, skill: str, records: list[dict]) -> None:
        skill_dir = Path(self.data_dir) / skill
        skill_dir.mkdir(parents=True, exist_ok=True)
        with (skill_dir / "records.jsonl").open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def test_global_stats_multiple_skills(self):
        """global_stats() scans all subdirectories with records.jsonl."""
        self._write_records("bp-tracker", [
            {"id": "r1", "type": "bp", "timestamp": "2024-01-01T10:00:00", "data": {}},
            {"id": "r2", "type": "bp", "timestamp": "2024-02-01T10:00:00", "data": {}},
        ])
        self._write_records("sleep-analyzer", [
            {"id": "s1", "type": "sleep", "timestamp": "2024-03-01T10:00:00", "data": {}},
        ])
        result = HealthDataStore.global_stats(data_dir=self.data_dir)
        self.assertEqual(result["skills_count"], 2)
        self.assertEqual(result["total_records"], 3)
        self.assertIn("bp-tracker", result["skills"])
        self.assertIn("sleep-analyzer", result["skills"])
        self.assertEqual(result["skills"]["bp-tracker"]["record_count"], 2)
        self.assertEqual(result["skills"]["sleep-analyzer"]["record_count"], 1)

    def test_global_stats_person_id_filter(self):
        """global_stats(person_id='mom') filters each skill to mom only."""
        self._write_records("bp-tracker", [
            {"id": "r1", "type": "bp", "timestamp": "2024-01-01T10:00:00", "data": {}, "person_id": "mom"},
            {"id": "r2", "type": "bp", "timestamp": "2024-02-01T10:00:00", "data": {}},
        ])
        result = HealthDataStore.global_stats(data_dir=self.data_dir, person_id="mom")
        self.assertEqual(result["total_records"], 1)
        self.assertEqual(result["skills"]["bp-tracker"]["record_count"], 1)

    def test_global_stats_empty_data_dir(self):
        """global_stats() on empty data dir returns zero counts."""
        result = HealthDataStore.global_stats(data_dir=self.data_dir)
        self.assertEqual(result["skills_count"], 0)
        self.assertEqual(result["total_records"], 0)
        self.assertEqual(result["skills"], {})


if __name__ == "__main__":
    unittest.main()
