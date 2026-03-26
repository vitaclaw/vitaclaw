#!/usr/bin/env python3
"""Tests for persisting annual checkup results into health memory."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "checkup-report-interpreter"
sys.path.insert(0, str(SKILL_DIR))

from checkup_report_interpreter import CheckupReportInterpreter  # noqa: E402


class AnnualCheckupMemoryTest(unittest.TestCase):
    def test_structured_items_persist_into_memory(self):
        def fixed_now():
            return datetime(2026, 3, 15, 22, 0, 0)

        items = [
            {
                "category": "体格检查",
                "item": "身高",
                "value": "178",
                "unit": "cm",
                "reference_range": "",
                "status": "正常",
            },
            {
                "category": "体格检查",
                "item": "体重",
                "value": "85.0",
                "unit": "kg",
                "reference_range": "",
                "status": "异常",
            },
            {
                "category": "体格检查",
                "item": "血压",
                "value": "135/88",
                "unit": "mmHg",
                "reference_range": "",
                "status": "偏高",
            },
            {
                "category": "体格检查",
                "item": "静息心率",
                "value": "82",
                "unit": "bpm",
                "reference_range": "",
                "status": "偏高",
            },
            {
                "category": "血糖",
                "item": "空腹血糖",
                "value": "6.0",
                "unit": "mmol/L",
                "reference_range": "3.9-6.1",
                "status": "偏高",
            },
            {
                "category": "血糖",
                "item": "糖化血红蛋白",
                "value": "5.8",
                "unit": "%",
                "reference_range": "4.0-6.0",
                "status": "偏高",
            },
            {
                "category": "肝功能",
                "item": "ALT",
                "value": "65",
                "unit": "U/L",
                "reference_range": "9-50",
                "status": "偏高",
            },
            {
                "category": "血脂",
                "item": "甘油三酯",
                "value": "2.4",
                "unit": "mmol/L",
                "reference_range": "<1.7",
                "status": "偏高",
            },
        ]

        with tempfile.TemporaryDirectory() as memory_dir:
            interpreter = CheckupReportInterpreter(memory_dir=memory_dir, now_fn=fixed_now)
            prioritized = interpreter.prioritize(items)
            written = interpreter.persist_items_to_memory(
                prioritized,
                report_date="2026-03-10",
                report_path="/tmp/annual-checkup-2026.pdf",
            )

            self.assertGreaterEqual(len(written), 4)

            daily_path = Path(memory_dir) / "daily" / "2026-03-10.md"
            weight_path = Path(memory_dir) / "items" / "weight.md"
            blood_pressure_path = Path(memory_dir) / "items" / "blood-pressure.md"
            blood_sugar_path = Path(memory_dir) / "items" / "blood-sugar.md"
            annual_checkup_path = Path(memory_dir) / "items" / "annual-checkup.md"

            self.assertTrue(daily_path.exists())
            self.assertTrue(weight_path.exists())
            self.assertTrue(blood_pressure_path.exists())
            self.assertTrue(blood_sugar_path.exists())
            self.assertTrue(annual_checkup_path.exists())

            daily_text = daily_path.read_text(encoding="utf-8")
            self.assertIn("## Annual Checkup [checkup-report-interpreter · 22:00]", daily_text)
            self.assertIn("Source: annual-checkup-2026.pdf", daily_text)
            self.assertIn("Items extracted: 8", daily_text)
            self.assertIn("Abnormal findings: 7", daily_text)
            self.assertIn("ALT: 65 U/L", daily_text)

            weight_text = weight_path.read_text(encoding="utf-8")
            self.assertIn("Latest: 85.0 kg (2026-03-10)", weight_text)
            self.assertIn("BMI: 26.8", weight_text)

            bp_text = blood_pressure_path.read_text(encoding="utf-8")
            self.assertIn("Latest: 135/88 mmHg (2026-03-10 08:30, checkup)", bp_text)
            self.assertIn("| 2026-03-10 | 08:30 | 135 | 88 | 82 | checkup | 偏高 |", bp_text)

            glucose_text = blood_sugar_path.read_text(encoding="utf-8")
            self.assertIn("Latest fasting: 6.0 mmol/L (2026-03-10)", glucose_text)
            self.assertIn("Latest HbA1c: 5.8% (2026-03-10)", glucose_text)
            self.assertIn("| 2026-03-10 | 6.0 |  |  | 5.8 | Checkup fasting glucose; Checkup HbA1c |", glucose_text)

            checkup_text = annual_checkup_path.read_text(encoding="utf-8")
            self.assertIn("Latest annual checkup: 2026-03-10 (annual-checkup-2026.pdf)", checkup_text)
            self.assertIn("Next annual checkup: 2027-03-10", checkup_text)
            self.assertIn("Reminder window days: 30", checkup_text)


if __name__ == "__main__":
    unittest.main()
