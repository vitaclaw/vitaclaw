#!/usr/bin/env python3
"""Tests for stateful heartbeat reminder management."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from health_heartbeat import HealthHeartbeat  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402
from health_reminder_center import HealthReminderCenter  # noqa: E402


class HealthReminderCenterTest(unittest.TestCase):
    def _write_item_file(self, memory_dir: str, slug: str, body: str) -> None:
        path = Path(memory_dir) / "items" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.strip() + "\n", encoding="utf-8")

    def test_quiet_hours_defer_medium_priority_push_but_keep_issue_visible(self):
        fixed_now = lambda: datetime(2026, 3, 15, 22, 30, 0)

        with tempfile.TemporaryDirectory() as memory_dir:
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=fixed_now)
            writer.update_daily_snapshot()
            self._write_item_file(
                memory_dir,
                "appointments",
                """
                ---
                item: appointments
                ---

                # Appointment Records

                ## Recent Status
                - Latest appointment: 2026-03-01 心内科复诊
                - Next follow-up: 2026-03-16
                - Next follow-up details: 心内科复诊，带近 2 周家庭血压记录
                - Preparation status: 已预约

                ## History
                | Date | Department / Doctor | Purpose | Status | Owner | Notes |
                | --- | --- | --- | --- | --- | --- |
                | 2026-03-01 | 心内科 | 高血压复诊 | completed | self | 调整生活方式，2 周后复诊 |
                """,
            )

            result = HealthHeartbeat(memory_dir=memory_dir, now_fn=fixed_now).run(write_report=True)

            due_issue = next(
                issue for issue in result["issues"] if issue["title"] == "复查/复诊即将到期"
            )
            self.assertEqual(due_issue["delivery_status"], "deferred")
            self.assertIn("安静时段", due_issue["delivery_note"])
            self.assertEqual(result["push_issues"], [])

            task_board = Path(result["task_board_path"])
            task_state = Path(result["task_state_path"])
            self.assertTrue(task_board.exists())
            self.assertTrue(task_state.exists())

            state = json.loads(task_state.read_text(encoding="utf-8"))
            self.assertTrue(any(task["title"] == "复查/复诊即将到期" for task in state["tasks"]))

    def test_completed_task_is_silenced_on_later_runs(self):
        fixed_now = lambda: datetime(2026, 3, 15, 10, 0, 0)

        with tempfile.TemporaryDirectory() as memory_dir:
            self._write_item_file(
                memory_dir,
                "medications",
                """
                ---
                item: medications
                ---

                # Medication Records

                ## Recent Status
                - Latest: 氨氯地平 5mg qd
                - Adherence: 近 7 天 100%
                - Next refill: 2026-03-16
                - Stock coverage days: 2
                - Risks: 暂无

                ## History
                | Date | Medication | Dose | Frequency | Status | Notes |
                | --- | --- | --- | --- | --- | --- |
                | 2026-03-15 | 氨氯地平 | 5mg | qd | active | 余量 2 天 |
                """,
            )

            heartbeat = HealthHeartbeat(memory_dir=memory_dir, now_fn=fixed_now)
            first = heartbeat.run(write_report=True)
            low_stock = next(issue for issue in first["issues"] if issue["title"] == "药物库存偏低")

            center = HealthReminderCenter(memory_dir=memory_dir, now_fn=fixed_now)
            updated = center.complete_task(low_stock["task_id"], note="已处理库存")
            self.assertIsNotNone(updated)
            self.assertEqual(updated["status"], "completed")

            second = heartbeat.run(write_report=True)
            silenced = next(issue for issue in second["issues"] if issue["title"] == "药物库存偏低")
            self.assertEqual(silenced["delivery_status"], "manual_silence")
            self.assertFalse(any(issue["title"] == "药物库存偏低" for issue in second["push_issues"]))


if __name__ == "__main__":
    unittest.main()
