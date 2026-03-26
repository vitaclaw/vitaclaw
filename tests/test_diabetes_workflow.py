#!/usr/bin/env python3
"""End-to-end tests for the diabetes daily workflow."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "chronic-condition-monitor"
sys.path.insert(0, str(SKILL_DIR))

from chronic_condition_monitor import ChronicConditionMonitor  # noqa: E402


class DiabetesWorkflowTest(unittest.TestCase):
    def test_glucose_and_weight_sync_into_health_memory(self):
        def fixed_now():
            return datetime(2026, 3, 15, 14, 30, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            monitor = ChronicConditionMonitor(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=fixed_now,
            )

            with redirect_stdout(io.StringIO()):
                monitor.record(
                    "glucose",
                    {"value": 6.8},
                    context="fasting",
                    timestamp="2026-03-08T07:00:00",
                )
                monitor.record(
                    "glucose",
                    {"value": 8.5},
                    context="post_lunch_2h",
                    timestamp="2026-03-08T14:00:00",
                )
                monitor.record(
                    "glucose",
                    {"value": 7.2},
                    context="fasting",
                    timestamp="2026-03-10T07:00:00",
                )
                monitor.record(
                    "glucose",
                    {"value": 9.8},
                    context="post_lunch_2h",
                    timestamp="2026-03-10T14:00:00",
                )
                monitor.record(
                    "weight",
                    {"kg": 72.3, "height_cm": 170},
                    timestamp="2026-03-08T07:05:00",
                )
                monitor.record(
                    "weight",
                    {"kg": 72.5, "height_cm": 170},
                    timestamp="2026-03-10T07:05:00",
                )

            daily_path = Path(memory_dir) / "daily" / "2026-03-10.md"
            blood_sugar_path = Path(memory_dir) / "items" / "blood-sugar.md"
            weight_path = Path(memory_dir) / "items" / "weight.md"

            self.assertTrue(daily_path.exists())
            self.assertTrue(blood_sugar_path.exists())
            self.assertTrue(weight_path.exists())

            daily_text = daily_path.read_text(encoding="utf-8")
            self.assertIn("## Blood Sugar [chronic-condition-monitor · 14:00]", daily_text)
            self.assertIn("Fasting: 7.2 mmol/L (High)", daily_text)
            self.assertIn("2h post-lunch: 9.8 mmol/L (In range)", daily_text)
            self.assertIn("Daily mean: 8.5 mmol/L", daily_text)
            self.assertIn("Estimated HbA1c: ~7.0%", daily_text)
            self.assertIn("## Weight [chronic-condition-monitor · 07:05]", daily_text)

            blood_sugar_text = blood_sugar_path.read_text(encoding="utf-8")
            self.assertIn("Latest fasting: 7.2 mmol/L (2026-03-10)", blood_sugar_text)
            self.assertIn("Latest postprandial: 9.8 mmol/L (2026-03-10)", blood_sugar_text)
            self.assertIn("30-day fasting average: 7.0 mmol/L", blood_sugar_text)
            self.assertIn("30-day postprandial average: 9.2 mmol/L", blood_sugar_text)
            self.assertIn("Estimated HbA1c (eHbA1c): ~6.7%", blood_sugar_text)
            self.assertIn("TIR (3.9-10.0 mmol/L): 100.0%", blood_sugar_text)

            weight_text = weight_path.read_text(encoding="utf-8")
            self.assertIn("Latest: 72.5 kg (2026-03-10)", weight_text)
            self.assertIn("30-day trend: Stable", weight_text)
            self.assertIn("BMI: 25.1", weight_text)


if __name__ == "__main__":
    unittest.main()
