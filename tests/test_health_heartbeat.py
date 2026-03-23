#!/usr/bin/env python3
"""Tests for proactive heartbeat checks."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from health_data_store import HealthDataStore  # noqa: E402
from health_heartbeat import HealthHeartbeat  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402


class HealthHeartbeatTest(unittest.TestCase):
    def _write_item_file(self, memory_dir: str, slug: str, body: str) -> None:
        path = Path(memory_dir) / "items" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.strip() + "\n", encoding="utf-8")

    def test_detects_missing_records_risk_and_digest_due(self):
        fixed_now = lambda: datetime(2026, 3, 15, 21, 0, 0)  # Sunday

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=fixed_now)
            writer.update_blood_pressure(
                latest_record={
                    "timestamp": "2026-03-12T08:30:00",
                    "note": "2级高血压",
                    "data": {"sys": 148, "dia": 96, "hr": 82, "context": "morning"},
                },
                day_records=[
                    {
                        "timestamp": "2026-03-12T08:30:00",
                        "note": "2级高血压",
                        "data": {"sys": 148, "dia": 96, "hr": 82, "context": "morning"},
                    }
                ],
                window_records=[
                    {
                        "timestamp": "2026-03-10T08:30:00",
                        "note": "2级高血压",
                        "data": {"sys": 145, "dia": 92, "hr": 80, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-11T08:30:00",
                        "note": "2级高血压",
                        "data": {"sys": 142, "dia": 90, "hr": 78, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-12T08:30:00",
                        "note": "2级高血压",
                        "data": {"sys": 148, "dia": 96, "hr": 82, "context": "morning"},
                    },
                ],
            )
            HealthDataStore("blood-pressure-tracker", data_dir=data_dir).append(
                "bp", {"sys": 145, "dia": 92, "context": "morning"}, timestamp="2026-03-10T08:30:00"
            )
            HealthDataStore("blood-pressure-tracker", data_dir=data_dir).append(
                "bp", {"sys": 142, "dia": 90, "context": "morning"}, timestamp="2026-03-11T08:30:00"
            )
            HealthDataStore("blood-pressure-tracker", data_dir=data_dir).append(
                "bp", {"sys": 148, "dia": 96, "context": "morning"}, timestamp="2026-03-12T08:30:00"
            )

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=fixed_now,
            )
            result = heartbeat.run(write_report=True)

            self.assertIn("血压记录缺失", result["markdown"])
            self.assertIn("血压连续偏高", result["markdown"])
            self.assertIn("本周周报待生成", result["markdown"])

            report_path = Path(result["report_path"])
            self.assertTrue(report_path.exists())
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("# Health Heartbeat -- 2026-03-15", report_text)
            self.assertIn("高优先级", report_text)

    def test_blank_item_templates_do_not_trigger_false_positive_missing_reminders(self):
        fixed_now = lambda: datetime(2026, 3, 19, 10, 0, 0)  # Thursday

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=fixed_now)
            self._write_item_file(
                memory_dir,
                "medications",
                """
                ---
                item: medications
                ---

                # Medication Records

                ## Recent Status
                - Latest: pending
                - Adherence: pending
                - Next refill: pending
                - Stock coverage days: pending
                - Risks: pending

                ## History
                | Date | Medication | Dose | Frequency | Status | Notes |
                | --- | --- | --- | --- | --- | --- |
                """,
            )
            self._write_item_file(
                memory_dir,
                "supplements",
                """
                ---
                item: supplements
                ---

                # Supplement Records

                ## Recent Status
                - Latest: pending
                - Today's adherence: pending
                - Warnings: pending

                ## History
                | Date | Active Items | Taken | Expected | Adherence | Warnings | Notes |
                | --- | --- | --- | --- | --- | --- | --- |
                """,
            )
            self._write_item_file(
                memory_dir,
                "sleep",
                """
                ---
                item: sleep
                ---

                # Sleep

                ## Recent Status
                - Latest: pending
                - Score: pending

                ## History
                | Date | Score | Duration | Notes |
                | --- | --- | --- | --- |
                """,
            )

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=fixed_now,
            )
            result = heartbeat.run(write_report=False)

            self.assertEqual(result["issues"], [])
            self.assertIn("当前没有检测到需要提醒的事项", result["markdown"])
            self.assertNotIn("用药记录缺失", result["markdown"])
            self.assertNotIn("补剂记录缺失", result["markdown"])
            self.assertNotIn("睡眠记录缺失", result["markdown"])

    def test_detects_follow_up_and_refill_due(self):
        fixed_now = lambda: datetime(2026, 3, 15, 9, 0, 0)  # Sunday

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=fixed_now)
            writer.update_daily_snapshot()
            today_path = Path(memory_dir) / "daily" / "2026-03-15.md"
            today_path.write_text(
                today_path.read_text(encoding="utf-8")
                + "\n## Medication [manual · 09:00]\n- Adherence logged today\n",
                encoding="utf-8",
            )

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
                - Next refill: 2026-03-18
                - Stock coverage days: 2
                - Risks: 暂无

                ## History
                | Date | Medication | Dose | Frequency | Status | Notes |
                | --- | --- | --- | --- | --- | --- |
                | 2026-03-15 | 氨氯地平 | 5mg | qd | active | 余量 2 天 |
                """,
            )

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=fixed_now,
            )
            result = heartbeat.run(write_report=False)

            self.assertIn("复查/复诊即将到期", result["markdown"])
            self.assertIn("门诊前 briefing 待生成", result["markdown"])
            self.assertIn("药物续配即将到期", result["markdown"])
            self.assertIn("药物库存偏低", result["markdown"])

    def test_detects_monthly_digest_and_memory_distillation_due(self):
        fixed_now = lambda: datetime(2026, 4, 2, 9, 0, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as workspace_dir:
            workspace_root = Path(workspace_dir)
            (workspace_root / "MEMORY.md").write_text(
                "# VitaClaw Long-Term Memory\n\n## 当前重点任务\n- 建立完整健康基线\n",
                encoding="utf-8",
            )
            writer = HealthMemoryWriter(workspace_root=str(workspace_root), now_fn=fixed_now)
            writer.update_daily_snapshot()

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                workspace_root=str(workspace_root),
                now_fn=fixed_now,
            )
            result = heartbeat.run(write_report=False)

            self.assertIn("上月月报缺失", result["markdown"])

    def test_detects_missing_visit_followup_document(self):
        fixed_now = lambda: datetime(2026, 4, 3, 9, 0, 0)

        with tempfile.TemporaryDirectory() as memory_dir:
            self._write_item_file(
                memory_dir,
                "appointments",
                """
                ---
                item: appointments
                ---

                # Appointment Records

                ## Recent Status
                - Latest appointment: 2026-04-02 心内科复诊
                - Next follow-up: 2026-04-16
                - Next follow-up details: 继续带 2 周家庭血压记录
                - Preparation status: 本次复诊已完成

                ## History
                | Date | Department / Doctor | Purpose | Status | Owner | Notes |
                | --- | --- | --- | --- | --- | --- |
                | 2026-04-02 | 心内科 | 高血压复诊 | completed | self | 建议继续监测 |
                """,
            )

            result = HealthHeartbeat(memory_dir=memory_dir, now_fn=fixed_now).run(write_report=False)
            self.assertIn("门诊后 follow-up 待记录", result["markdown"])

    def test_detects_annual_checkup_due(self):
        fixed_now = lambda: datetime(2027, 2, 20, 9, 0, 0)

        with tempfile.TemporaryDirectory() as memory_dir:
            self._write_item_file(
                memory_dir,
                "annual-checkup",
                """
                ---
                item: annual-checkup
                ---

                # Annual Checkup Records

                ## Recent Status
                - Latest annual checkup: 2026-03-10 (annual-checkup-2026.pdf)
                - Next annual checkup: 2027-03-10
                - Reminder window days: 30
                - Preparation status: 待预约
                - Notes: ALT 偏高

                ## History
                | Date | Source | Status | Next Annual Checkup | Notes |
                | --- | --- | --- | --- | --- |
                | 2026-03-10 | annual-checkup-2026.pdf | completed | 2027-03-10 | ALT 偏高 |
                """,
            )

            result = HealthHeartbeat(memory_dir=memory_dir, now_fn=fixed_now).run(write_report=False)
            self.assertIn("年度体检即将到期", result["markdown"])

    def test_detects_pending_patient_archive_and_unsynced_updates(self):
        fixed_now = lambda: datetime(2026, 4, 3, 10, 0, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as patients_dir:
            workspace_root = Path(workspace_dir)
            (workspace_root / "MEMORY.md").write_text(
                "# VitaClaw Long-Term Memory\n\n## 当前重点任务\n- 建立完整健康基线\n",
                encoding="utf-8",
            )
            patient_dir = Path(patients_dir) / "PT-ARCHIVE01"
            (patient_dir / "10_原始文件" / "未分类").mkdir(parents=True, exist_ok=True)
            (patient_dir / "INDEX.md").write_text("# 病历索引 — PT-ARCHIVE01\n", encoding="utf-8")
            (patient_dir / "timeline.md").write_text(
                "\n".join(
                    [
                        "# 病历时间线 — PT-ARCHIVE01",
                        "",
                        "| 日期 | 文档类型 | 摘要 | 文件路径 |",
                        "|------|----------|------|---------|",
                        "| 2026-04-02 | 影像复查 | CT提示结节稳定 | 04_影像学/CT/2026-04-02_ct.md |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (patient_dir / "10_原始文件" / "未分类" / "raw-image.jpg").write_text("image\n", encoding="utf-8")

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                workspace_root=str(workspace_root),
                patients_root=patients_dir,
                patient_id="PT-ARCHIVE01",
                now_fn=fixed_now,
            )
            result = heartbeat.run(write_report=False)

            self.assertIn("待整理病历", result["markdown"])
            self.assertIn("病历归档有新更新待同步", result["markdown"])


if __name__ == "__main__":
    unittest.main()
