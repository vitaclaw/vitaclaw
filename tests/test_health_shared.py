#!/usr/bin/env python3
"""Smoke tests for VitaClaw shared health foundations."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from cross_skill_reader import CrossSkillReader  # noqa: E402
from health_data_store import HealthDataStore  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402


class HealthDataStoreTest(unittest.TestCase):
    def test_append_query_trend_and_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("sleep-analyzer", data_dir=tmp_dir)
            store.append("sleep_session", {"score": 72, "total_min": 420})
            store.append("sleep_session", {"score": 81, "total_min": 465})

            records = store.query("sleep_session")
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["type"], "sleep_session")

            latest = store.get_latest("sleep_session", n=1)
            self.assertEqual(latest[0]["data"]["score"], 81)

            trend = store.trend("sleep_session", "score", window=30)
            self.assertEqual(trend["count"], 2)
            self.assertEqual(trend["direction"], "rising")
            self.assertEqual(trend["values"], [72, 81])

            self.assertTrue(store.consecutive_check("sleep_session", "score", "rising", count=2))
            self.assertFalse(store.consecutive_check("sleep_session", "score", "falling", count=2))

            store.set_config("thresholds", {"sleep_score_min": 75})
            self.assertEqual(store.get_config()["thresholds"]["sleep_score_min"], 75)


class HealthMemoryAndCrossSkillReaderTest(unittest.TestCase):
    def test_memory_writer_creates_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = HealthMemoryWriter(workspace_root=tmp_dir)
            writer.update_caffeine(
                level=115.0,
                intake_list=[
                    {"drink": "Americano", "mg": 95, "time": "08:30"},
                    {"drink": "Green tea", "mg": 30, "time": "11:00"},
                ],
                safe="22:15",
            )
            writer.update_sleep(
                last_night={
                    "date": "2026-03-14",
                    "score": 83,
                    "total_min": 445,
                    "efficiency_pct": 92.7,
                    "bedtime": "23:00",
                    "wake_time": "06:25",
                    "deep_min": 80,
                    "light_min": 235,
                    "rem_min": 95,
                    "awake_min": 35,
                },
                seven_day={
                    "avg_score": 79.5,
                    "avg_total_min": 430,
                    "avg_efficiency": 90.1,
                    "trend_direction": "rising",
                },
                correlations={"caffeine_effect": "300mg days tend to score lower"},
            )
            writer.update_supplements(
                active_regimen=[
                    {"name": "VD3", "dose": "2000IU", "timing": "08:00"},
                    {"name": "Magnesium", "dose": "200mg", "timing": "22:00"},
                ],
                today_adherence={"taken": 2, "expected": 2, "rate_pct": 100.0},
                warnings=["Iron and calcium should be separated"],
            )
            writer.update_weekly_digest("# 健康周报 -- 2026-03-10 ~ 2026-03-16\n\n本周总体稳定。")

            memory_root = Path(tmp_dir) / "memory" / "health"
            self.assertTrue((memory_root / "_health-profile.md").exists())
            self.assertTrue((memory_root / "items" / "caffeine.md").exists())
            self.assertTrue((memory_root / "items" / "sleep.md").exists())
            self.assertTrue((memory_root / "items" / "supplements.md").exists())
            self.assertTrue((memory_root / "weekly-digest.md").exists())

            context = writer.read_health_context()
            self.assertIn("Health Profile", context)
            self.assertIn("Caffeine", context)
            self.assertIn("Sleep", context)

    def test_cross_skill_reader_reads_shared_skill_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            HealthDataStore("caffeine-tracker", data_dir=tmp_dir).append(
                "intake", {"drink": "Americano", "mg": 95, "time": "08:30"}
            )
            HealthDataStore("sleep-analyzer", data_dir=tmp_dir).append(
                "sleep_session", {"date": "2026-03-14", "score": 83}
            )
            supplement_store = HealthDataStore("supplement-manager", data_dir=tmp_dir)
            supplement_store.append(
                "supplement",
                {"name": "VD3", "dose": "2000IU", "timing": "08:00", "status": "active"},
            )
            supplement_store.append(
                "dose_log",
                {"supplement": "VD3", "taken": True, "time": "08:05"},
            )
            HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir).append(
                "bp", {"sys": 128, "dia": 82}
            )
            HealthDataStore("medication-reminder", data_dir=tmp_dir).append(
                "dose", {"name": "Amlodipine", "taken": True}
            )

            reader = CrossSkillReader(data_dir=tmp_dir)
            self.assertEqual(len(reader.read_caffeine_intakes()), 1)
            self.assertEqual(len(reader.read_sleep_data()), 1)
            self.assertEqual(len(reader.read_supplement_doses()), 1)
            self.assertEqual(len(reader.read_supplement_regimen()), 1)
            self.assertEqual(len(reader.read_blood_pressure()), 1)
            self.assertEqual(len(reader.read_medication_doses()), 1)


if __name__ == "__main__":
    unittest.main()
