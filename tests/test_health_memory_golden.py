#!/usr/bin/env python3
"""Golden tests for markdown outputs written by HealthMemoryWriter."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from skills._shared.health_memory import HealthMemoryWriter

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "health_memory_golden"


class HealthMemoryGoldenTest(unittest.TestCase):
    def _build_sample_tree(self, memory_root: Path) -> None:
        def fixed_now():
            return datetime(2026, 3, 15, 8, 30, 0)

        writer = HealthMemoryWriter(memory_root=str(memory_root), now_fn=fixed_now)

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
        writer.update_blood_pressure(
            latest_record={
                "timestamp": "2026-03-15T20:15:00",
                "note": "1级高血压",
                "data": {
                    "sys": 132,
                    "dia": 84,
                    "hr": 72,
                    "context": "evening",
                    "arm": "left",
                    "position": "sitting",
                },
            },
            day_records=[
                {
                    "timestamp": "2026-03-15T08:30:00",
                    "note": "1级高血压",
                    "data": {
                        "sys": 138,
                        "dia": 88,
                        "hr": 78,
                        "context": "morning",
                        "arm": "left",
                        "position": "sitting",
                    },
                },
                {
                    "timestamp": "2026-03-15T20:15:00",
                    "note": "1级高血压",
                    "data": {
                        "sys": 132,
                        "dia": 84,
                        "hr": 72,
                        "context": "evening",
                        "arm": "left",
                        "position": "sitting",
                    },
                },
            ],
            window_records=[
                {
                    "timestamp": "2026-03-10T07:20:00",
                    "note": "2级高血压",
                    "data": {"sys": 145, "dia": 92, "hr": 82, "context": "morning"},
                },
                {
                    "timestamp": "2026-03-12T07:10:00",
                    "note": "1级高血压",
                    "data": {"sys": 136, "dia": 86, "hr": 76, "context": "morning"},
                },
                {
                    "timestamp": "2026-03-14T20:10:00",
                    "note": "血压升高",
                    "data": {"sys": 128, "dia": 79, "hr": 70, "context": "evening"},
                },
                {
                    "timestamp": "2026-03-15T08:30:00",
                    "note": "1级高血压",
                    "data": {
                        "sys": 138,
                        "dia": 88,
                        "hr": 78,
                        "context": "morning",
                        "arm": "left",
                        "position": "sitting",
                    },
                },
                {
                    "timestamp": "2026-03-15T20:15:00",
                    "note": "1级高血压",
                    "data": {
                        "sys": 132,
                        "dia": 84,
                        "hr": 72,
                        "context": "evening",
                        "arm": "left",
                        "position": "sitting",
                    },
                },
            ],
        )
        writer.update_weekly_digest("# 健康周报 -- 2026-03-10 ~ 2026-03-16\n\n本周总体稳定。")

    def _read_tree(self, root: Path) -> dict[str, str]:
        snapshot = {}
        for path in sorted(root.rglob("*")):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                snapshot[path.relative_to(root).as_posix()] = text.rstrip() + "\n"
        return snapshot

    def test_writer_output_matches_golden_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory_root = Path(tmp_dir)
            self._build_sample_tree(memory_root)

            actual = self._read_tree(memory_root)
            expected = self._read_tree(FIXTURE_DIR)
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
