#!/usr/bin/env python3
"""Tests for automated health operations runner."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from skills._shared.health_data_store import HealthDataStore
from skills._shared.health_memory import HealthMemoryWriter
from skills._shared.health_operations import HealthOperationsRunner


class HealthOperationsRunnerTest(unittest.TestCase):
    def test_generates_due_weekly_digest(self):
        def fixed_now():
            return datetime(2026, 3, 15, 21, 0, 0)  # Sunday

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as workspace_dir:
            workspace_root = Path(workspace_dir)
            (workspace_root / "MEMORY.md").write_text("# VitaClaw Long-Term Memory\n", encoding="utf-8")

            store = HealthDataStore("caffeine-tracker", data_dir=data_dir)
            store.append("intake", {"drink": "Americano", "mg": 95, "time": "08:30"}, timestamp="2026-03-12T08:30:00")
            store.append("intake", {"drink": "Green tea", "mg": 30, "time": "11:00"}, timestamp="2026-03-13T11:00:00")

            result = HealthOperationsRunner(
                data_dir=data_dir,
                workspace_root=workspace_dir,
                now_fn=fixed_now,
            ).run(write=True)

            self.assertEqual(result["generated_weekly"], ["2026-03-09"])
            self.assertTrue((workspace_root / "memory" / "health" / "weekly-digest.md").exists())
            self.assertTrue(Path(result["report_path"]).exists())

    def test_generates_previous_month_digest_and_distills_memory(self):
        def fixed_now():
            return datetime(2026, 4, 2, 9, 0, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as workspace_dir:
            workspace_root = Path(workspace_dir)
            (workspace_root / "MEMORY.md").write_text(
                "# VitaClaw Long-Term Memory\n\n## 当前重点任务\n- 建立完整健康基线\n",
                encoding="utf-8",
            )
            writer = HealthMemoryWriter(workspace_root=workspace_dir, now_fn=fixed_now)
            writer.update_daily_snapshot()

            store = HealthDataStore("caffeine-tracker", data_dir=data_dir)
            store.append("intake", {"drink": "Americano", "mg": 95, "time": "08:30"}, timestamp="2026-03-10T08:30:00")
            store.append("intake", {"drink": "Green tea", "mg": 30, "time": "11:00"}, timestamp="2026-03-18T11:00:00")

            result = HealthOperationsRunner(
                data_dir=data_dir,
                workspace_root=workspace_dir,
                now_fn=fixed_now,
            ).run(write=True)

            self.assertEqual(result["generated_monthly"], ["2026-03"])
            self.assertTrue((workspace_root / "memory" / "health" / "monthly-digest.md").exists())
            memory_text = (workspace_root / "MEMORY.md").read_text(encoding="utf-8")
            self.assertIn("Last distilled: 2026-04-02", memory_text)


if __name__ == "__main__":
    unittest.main()
