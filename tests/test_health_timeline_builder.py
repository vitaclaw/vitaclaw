#!/usr/bin/env python3
"""Tests for unified health timeline generation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from health_memory import HealthMemoryWriter  # noqa: E402
from health_timeline_builder import HealthTimelineBuilder  # noqa: E402


class HealthTimelineBuilderTest(unittest.TestCase):
    def test_build_merges_archive_apple_health_and_workspace_items(self):
        fixed_now = lambda: datetime(2026, 4, 3, 15, 0, 0)

        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as patients_dir:
            workspace_root = Path(workspace_dir)
            (workspace_root / "MEMORY.md").write_text("# VitaClaw Long-Term Memory\n", encoding="utf-8")

            writer = HealthMemoryWriter(workspace_root=workspace_dir, now_fn=fixed_now)
            writer.update_blood_pressure(
                latest_record={
                    "timestamp": "2026-04-02T20:15:00",
                    "note": "血压升高",
                    "data": {"sys": 138, "dia": 86, "hr": 72, "context": "evening"},
                },
                day_records=[
                    {
                        "timestamp": "2026-04-02T20:15:00",
                        "note": "血压升高",
                        "data": {"sys": 138, "dia": 86, "hr": 72, "context": "evening"},
                    }
                ],
                window_records=[
                    {
                        "timestamp": "2026-04-02T20:15:00",
                        "note": "血压升高",
                        "data": {"sys": 138, "dia": 86, "hr": 72, "context": "evening"},
                    }
                ],
            )
            writer.update_weekly_digest("# 健康周报 -- 2026-03-30 ~ 2026-04-05\n\n本周总体稳定。")
            writer.update_monthly_digest("# 健康月报 -- 2026-04\n\n统计区间：2026-04-01 ~ 2026-04-30\n")

            patient_dir = Path(patients_dir) / "PT-TIMELINE01"
            (patient_dir / "09_Apple_Health").mkdir(parents=True, exist_ok=True)
            (patient_dir / "INDEX.md").write_text("# 病历索引 — PT-TIMELINE01\n", encoding="utf-8")
            (patient_dir / "timeline.md").write_text(
                "\n".join(
                    [
                        "# 病历时间线 — PT-TIMELINE01",
                        "",
                        "| 日期 | 文档类型 | 摘要 | 文件路径 |",
                        "|------|----------|------|---------|",
                        "| 2026-04-01 | 门诊复诊 | 建议继续监测血压 | 06_治疗决策历史/2026-04-01_followup.md |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (patient_dir / "09_Apple_Health" / "体重变化.md").write_text(
                "\n".join(
                    [
                        "# 体重变化 — PT-TIMELINE01",
                        "",
                        "| 日期 | 体重(kg) | 趋势 | 变化 |",
                        "| --- | --- | --- | --- |",
                        "| 2026-04-02 | 69.8 | ↓ | -0.7 kg |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = HealthTimelineBuilder(
                workspace_root=workspace_dir,
                patients_root=patients_dir,
                patient_id="PT-TIMELINE01",
                now_fn=fixed_now,
            ).build(write=True)

            self.assertGreater(result["entry_count"], 0)
            timeline_text = Path(result["timeline_path"]).read_text(encoding="utf-8")
            self.assertIn("门诊复诊", timeline_text)
            self.assertIn("Apple Health 体重", timeline_text)
            self.assertIn("健康周报", timeline_text)
            self.assertIn("blood pressure", timeline_text.lower())
