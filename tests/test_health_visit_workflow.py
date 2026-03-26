#!/usr/bin/env python3
"""Tests for visit briefing and follow-up workflows."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from skills._shared.health_memory import HealthMemoryWriter
from skills._shared.health_visit_workflow import HealthVisitWorkflow


class HealthVisitWorkflowTest(unittest.TestCase):
    def test_generate_briefing_and_record_followup(self):
        def fixed_now():
            return datetime(2026, 4, 3, 9, 0, 0)

        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace_root = Path(workspace_dir)
            (workspace_root / "MEMORY.md").write_text("# VitaClaw Long-Term Memory\n", encoding="utf-8")

            writer = HealthMemoryWriter(workspace_root=workspace_dir, now_fn=fixed_now)
            writer.update_blood_pressure(
                latest_record={
                    "timestamp": "2026-04-02T08:00:00",
                    "note": "家庭晨起血压偏高",
                    "data": {"sys": 146, "dia": 94, "hr": 76, "context": "morning"},
                },
                day_records=[
                    {
                        "timestamp": "2026-04-02T08:00:00",
                        "note": "家庭晨起血压偏高",
                        "data": {"sys": 146, "dia": 94, "hr": 76, "context": "morning"},
                    }
                ],
                window_records=[
                    {
                        "timestamp": "2026-03-31T08:00:00",
                        "note": "家庭晨起血压偏高",
                        "data": {"sys": 142, "dia": 92, "hr": 74, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-04-01T08:00:00",
                        "note": "家庭晨起血压偏高",
                        "data": {"sys": 145, "dia": 93, "hr": 75, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-04-02T08:00:00",
                        "note": "家庭晨起血压偏高",
                        "data": {"sys": 146, "dia": 94, "hr": 76, "context": "morning"},
                    },
                ],
            )
            writer.update_weekly_digest("# 健康周报 -- 2026-03-30 ~ 2026-04-05\n\n本周血压波动偏高。")
            writer.update_appointments(
                visit_date="2026-03-20",
                department_doctor="心内科 / 张医生",
                purpose="高血压复诊",
                status="completed",
                owner="self",
                notes="建议继续家庭监测",
                latest_appointment="2026-03-20 高血压复诊",
                next_follow_up="2026-04-05",
                next_follow_up_details="心内科复诊，带近 2 周家庭血压记录",
                preparation_status="已预约",
            )

            workflow = HealthVisitWorkflow(workspace_root=workspace_dir, now_fn=fixed_now)

            briefing = workflow.generate_briefing(
                visit_date="2026-04-05",
                department="心内科 / 张医生",
                purpose="高血压复诊",
                write=True,
            )
            self.assertIn("Visit Briefing -- 2026-04-05", briefing["markdown"])
            self.assertTrue(Path(briefing["path"]).exists())
            self.assertIn("Questions To Ask", Path(briefing["path"]).read_text(encoding="utf-8"))

            followup = workflow.record_follow_up(
                visit_date="2026-04-05",
                department="心内科",
                doctor="张医生",
                purpose="高血压复诊",
                summary="医生建议继续家庭监测，暂不调整药物。",
                plan="保持现有用药，2 周后回访并继续晨起/睡前记录。",
                next_follow_up="2026-04-19",
                next_follow_up_details="带近 2 周家庭血压记录，关注晨峰。",
                owner="self",
                write=True,
            )
            self.assertTrue(Path(followup["path"]).exists())

            appointments_text = (writer.items_dir / "appointments.md").read_text(encoding="utf-8")
            self.assertIn("2026-04-19", appointments_text)
            self.assertIn("本次复诊已完成，待执行 follow-up", appointments_text)

            daily_text = (writer.daily_dir / "2026-04-05.md").read_text(encoding="utf-8")
            self.assertIn("Appointment Follow-up", daily_text)
            self.assertIn("visit-follow-up-2026-04-05.md", daily_text)


if __name__ == "__main__":
    unittest.main()
