#!/usr/bin/env python3
"""Tests for Iteration 2 flagship scenario entrypoints."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skills._shared.health_flagship_scenarios import (
    AnnualCheckupAdvisorWorkflow,
    DiabetesControlHub,
    HypertensionDailyCopilot,
)


class FlagshipScenarioTest(unittest.TestCase):
    def test_hypertension_daily_entry_creates_output_task_board_and_audit(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            result = HypertensionDailyCopilot(
                data_dir=data_dir,
                memory_dir=memory_dir,
            ).daily_entry(
                systolic=148,
                diastolic=96,
                pulse=82,
                context="morning",
                medications=["Amlodipine|5mg|qd|on-time"],
                adherence="近7天 100%",
                next_refill="2026-03-20",
                stock_coverage_days=5,
                diet_summary="外卖偏咸",
                exercise_summary="晚饭后快走30分钟",
            )

            output_path = Path(result["output_path"])
            audit_path = Path(memory_dir) / "files" / "write-audit.md"
            behavior_path = Path(memory_dir) / "items" / "behavior-plans.md"

            self.assertTrue(output_path.exists())
            self.assertTrue(audit_path.exists())
            self.assertTrue(behavior_path.exists())
            self.assertIsNotNone(result["task_board_path"])

            markdown = output_path.read_text(encoding="utf-8")
            self.assertIn("## 记录", markdown)
            self.assertIn("## 风险", markdown)
            self.assertIn("## Sources", markdown)
            self.assertIn("## Evidence", markdown)
            self.assertIn("高血压", markdown)

            audit_text = audit_path.read_text(encoding="utf-8")
            self.assertIn("hypertension-daily-copilot", audit_text)
            self.assertIn("高血压日常闭环写回", audit_text)

            behavior_text = behavior_path.read_text(encoding="utf-8")
            self.assertIn("补齐下一次家庭血压记录", behavior_text)

    def test_diabetes_daily_log_creates_output_and_behavior_plan(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            result = DiabetesControlHub(
                data_dir=data_dir,
                memory_dir=memory_dir,
            ).daily_log(
                glucose_entries=[
                    {"value": 6.8, "context": "fasting", "timestamp": "2026-03-15T07:00:00"},
                    {"value": 9.4, "context": "post_lunch_2h", "timestamp": "2026-03-15T14:00:00"},
                ],
                weight_kg=72.4,
                height_cm=170,
                meals_summary="午餐白米饭偏多",
                exercise_summary="晚饭后散步20分钟",
                medications=["Metformin|500mg|bid|with meals"],
                adherence="近7天 92%",
            )

            output_path = Path(result["output_path"])
            behavior_path = Path(memory_dir) / "items" / "behavior-plans.md"
            task_board = Path(result["task_board_path"])

            self.assertTrue(output_path.exists())
            self.assertTrue(behavior_path.exists())
            self.assertTrue(task_board.exists())

            output_text = output_path.read_text(encoding="utf-8")
            self.assertIn("## 建议", output_text)
            self.assertIn("血糖", output_text)

            behavior_text = behavior_path.read_text(encoding="utf-8")
            self.assertIn("补齐下一次血糖记录", behavior_text)

    def test_annual_checkup_import_creates_followup_tasks(self):
        items = [
            {
                "category": "血糖",
                "item": "空腹血糖",
                "value": "6.4",
                "unit": "mmol/L",
                "reference_range": "3.9-6.1",
                "status": "偏高",
            },
            {
                "category": "肝功能",
                "item": "ALT",
                "value": "88",
                "unit": "U/L",
                "reference_range": "0-40",
                "status": "偏高",
            },
            {
                "category": "血脂",
                "item": "甘油三酯",
                "value": "2.6",
                "unit": "mmol/L",
                "reference_range": "0-1.7",
                "status": "偏高",
            },
        ]

        with tempfile.TemporaryDirectory() as memory_dir:
            result = AnnualCheckupAdvisorWorkflow(
                memory_dir=memory_dir,
            ).import_report(
                items=items,
                report_date="2026-03-10",
                next_follow_up="2026-03-17",
                next_follow_up_details="复查肝功能",
            )

            output_path = Path(result["output_path"])
            annual_path = Path(memory_dir) / "items" / "annual-checkup.md"
            appointments_path = Path(memory_dir) / "items" / "appointments.md"
            task_board = Path(result["task_board_path"])

            self.assertTrue(output_path.exists())
            self.assertTrue(annual_path.exists())
            self.assertTrue(appointments_path.exists())
            self.assertTrue(task_board.exists())
            self.assertGreaterEqual(result["follow_up_task_count"], 1)

            output_text = output_path.read_text(encoding="utf-8")
            self.assertIn("Annual Checkup Advisor", output_text)
            self.assertIn("ALT", output_text)
            self.assertIn("## 必须就医", output_text)


if __name__ == "__main__":
    unittest.main()
