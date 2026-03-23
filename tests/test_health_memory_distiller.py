#!/usr/bin/env python3
"""Tests for distilling recent operations back into MEMORY.md."""

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
from health_memory_distiller import HealthMemoryDistiller  # noqa: E402


class HealthMemoryDistillerTest(unittest.TestCase):
    def test_distills_recent_state_into_memory(self):
        fixed_now = lambda: datetime(2026, 3, 31, 21, 0, 0)

        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as patients_dir:
            workspace_root = Path(tmp_dir)
            memory_path = workspace_root / "MEMORY.md"
            memory_path.write_text(
                "# VitaClaw Long-Term Memory\n\n## 当前重点任务\n- 建立完整健康基线\n",
                encoding="utf-8",
            )
            patient_dir = Path(patients_dir) / "PT-LONG001"
            (patient_dir / "10_原始文件" / "未分类").mkdir(parents=True, exist_ok=True)
            (patient_dir / "INDEX.md").write_text(
                "# 病历索引 — PT-LONG001\n\n## 基本信息\n- **诊断**：高血压\n",
                encoding="utf-8",
            )
            (patient_dir / "timeline.md").write_text(
                "\n".join(
                    [
                        "# 病历时间线 — PT-LONG001",
                        "",
                        "| 日期 | 文档类型 | 摘要 | 文件路径 |",
                        "|------|----------|------|---------|",
                        "| 2026-03-29 | 门诊复诊 | 建议继续家庭血压监测 | 06_治疗决策历史/2026-03-29_followup.md |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            writer = HealthMemoryWriter(workspace_root=str(workspace_root), now_fn=fixed_now)
            writer.update_daily_snapshot()
            writer.update_blood_pressure(
                latest_record={
                    "timestamp": "2026-03-31T20:15:00",
                    "note": "血压升高",
                    "data": {"sys": 142, "dia": 91, "hr": 76, "context": "evening"},
                },
                day_records=[
                    {
                        "timestamp": "2026-03-31T20:15:00",
                        "note": "血压升高",
                        "data": {"sys": 142, "dia": 91, "hr": 76, "context": "evening"},
                    }
                ],
                window_records=[
                    {
                        "timestamp": "2026-03-28T08:20:00",
                        "note": "血压升高",
                        "data": {"sys": 145, "dia": 92, "hr": 80, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-30T08:10:00",
                        "note": "血压升高",
                        "data": {"sys": 141, "dia": 90, "hr": 78, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-31T20:15:00",
                        "note": "血压升高",
                        "data": {"sys": 142, "dia": 91, "hr": 76, "context": "evening"},
                    },
                ],
            )
            writer.update_weekly_digest("# 健康周报 -- 2026-03-29 ~ 2026-04-04\n\n本周总体稳定。")
            writer.update_monthly_digest("# 健康月报 -- 2026-03\n\n统计区间：2026-03-01 ~ 2026-03-31\n")
            writer.upsert_behavior_plan(
                plan_id="bp-next",
                scenario="hypertension-daily-copilot",
                title="补齐下一次家庭血压记录",
                cadence="daily",
                due_at="2026-04-01T08:00",
                topic="blood-pressure",
                risk_policy="focus-closely",
                consequence="连续性不足会削弱趋势判断。",
                next_step="明早完成一次家庭血压测量。",
            )
            writer.record_execution_barrier(
                scenario="behavior-plan",
                barrier="晚间经常忘记补录",
                impact="导致连续记录断档",
                pattern="follow_up_count=2",
                next_step="把补录动作绑定到睡前流程",
                source_refs=[str(writer.behavior_plans_path)],
            )

            result = HealthMemoryDistiller(
                workspace_root=str(workspace_root),
                patients_root=patients_dir,
                patient_id="PT-LONG001",
                now_fn=fixed_now,
            ).run(write=True)

            self.assertIsNotNone(result["memory_path"])
            updated_text = memory_path.read_text(encoding="utf-8")
            self.assertIn("## 最近健康运营摘要", updated_text)
            self.assertIn("- Last distilled: 2026-03-31", updated_text)
            self.assertIn("最近周报", updated_text)
            self.assertIn("血压", updated_text)
            self.assertIn("患者档案 PT-LONG001 已连接", updated_text)
            self.assertIn("行为计划", updated_text)
            self.assertIn("执行障碍", updated_text)
            self.assertIn("## 风险与待跟进", updated_text)
