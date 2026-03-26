#!/usr/bin/env python3
"""Tests for Iteration 2 proactive service features."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime

from skills._shared.health_data_store import HealthDataStore
from skills._shared.health_heartbeat import HealthHeartbeat
from skills._shared.health_memory import HealthMemoryWriter


class Iteration2ActiveServiceTest(unittest.TestCase):
    def test_behavior_plan_due_and_execution_barrier_are_visible(self):
        def fixed_now():
            return datetime(2026, 3, 15, 9, 30, 0)

        with tempfile.TemporaryDirectory() as memory_dir:
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=fixed_now)
            writer.upsert_behavior_plan(
                plan_id="bp-next",
                scenario="hypertension-daily-copilot",
                title="补齐下一次家庭血压记录",
                cadence="daily",
                due_at="2026-03-15T10:00",
                topic="blood-pressure",
                risk_policy="focus-closely",
                consequence="连续性不足会削弱趋势判断。",
                next_step="按标准化方式完成下一次测量。",
            )
            writer.record_execution_barrier(
                scenario="behavior-plan",
                barrier="早晨测量总被会议打断",
                impact="连续三天没有按计划记录血压",
                pattern="follow_up_count=2",
                next_step="把测量时间提前到起床后 10 分钟",
                source_refs=[str(writer.behavior_plans_path)],
            )

            result = HealthHeartbeat(memory_dir=memory_dir, now_fn=fixed_now).run(write_report=False)
            self.assertIn("行为计划即将到点", result["markdown"])
            self.assertIn("执行障碍待处理", result["markdown"])

    def test_stalled_improvement_detection_for_blood_pressure(self):
        def fixed_now():
            return datetime(2026, 3, 15, 9, 0, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=fixed_now)
            for ts, sys_val, dia_val in (
                ("2026-03-02T08:00:00", 146, 94),
                ("2026-03-04T08:00:00", 145, 93),
                ("2026-03-06T08:00:00", 144, 92),
                ("2026-03-10T08:00:00", 144, 91),
                ("2026-03-12T08:00:00", 143, 90),
                ("2026-03-14T08:00:00", 144, 91),
            ):
                HealthDataStore("blood-pressure-tracker", data_dir=data_dir).append(
                    "bp",
                    {"sys": sys_val, "dia": dia_val, "context": "morning"},
                    timestamp=ts,
                )
            writer.update_blood_pressure(
                latest_record={
                    "timestamp": "2026-03-14T08:00:00",
                    "note": "2级高血压",
                    "data": {"sys": 144, "dia": 91, "context": "morning"},
                },
                day_records=[
                    {
                        "timestamp": "2026-03-14T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 144, "dia": 91, "context": "morning"},
                    }
                ],
                window_records=[
                    {
                        "timestamp": "2026-03-02T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 146, "dia": 94, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-04T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 145, "dia": 93, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-06T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 144, "dia": 92, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-10T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 144, "dia": 91, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-12T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 143, "dia": 90, "context": "morning"},
                    },
                    {
                        "timestamp": "2026-03-14T08:00:00",
                        "note": "2级高血压",
                        "data": {"sys": 144, "dia": 91, "context": "morning"},
                    },
                ],
            )

            result = HealthHeartbeat(data_dir=data_dir, memory_dir=memory_dir, now_fn=fixed_now).run(write_report=False)
            self.assertIn("血压改善停滞", result["markdown"])


if __name__ == "__main__":
    unittest.main()
