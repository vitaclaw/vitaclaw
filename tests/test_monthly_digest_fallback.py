#!/usr/bin/env python3
"""Tests for local fallback monthly digest generation."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DIR = ROOT / "skills" / "weekly-health-digest"
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(WEEKLY_DIR))
sys.path.insert(0, str(SHARED_DIR))

from health_data_store import HealthDataStore  # noqa: E402
from weekly_health_digest import WeeklyHealthDigest  # noqa: E402


class MonthlyDigestFallbackTest(unittest.TestCase):
    def test_generate_monthly_uses_local_fallback_and_writes_memory(self):
        fixed_now = lambda: datetime(2026, 3, 31, 20, 0, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            HealthDataStore("caffeine-tracker", data_dir=data_dir).append(
                "intake", {"drink": "Americano", "mg": 95}, timestamp="2026-03-03T08:30:00"
            )
            HealthDataStore("caffeine-tracker", data_dir=data_dir).append(
                "intake", {"drink": "Latte", "mg": 80}, timestamp="2026-03-20T10:00:00"
            )
            HealthDataStore("sleep-analyzer", data_dir=data_dir).append(
                "sleep_session",
                {"date": "2026-03-05", "score": 79, "total_min": 425, "efficiency_pct": 88},
                timestamp="2026-03-05T07:00:00",
            )
            HealthDataStore("sleep-analyzer", data_dir=data_dir).append(
                "sleep_session",
                {"date": "2026-03-18", "score": 84, "total_min": 445, "efficiency_pct": 91},
                timestamp="2026-03-18T07:00:00",
            )
            supplement_store = HealthDataStore("supplement-manager", data_dir=data_dir)
            supplement_store.append("dose_log", {"supplement": "VD3", "taken": True}, timestamp="2026-03-06T08:00:00")
            supplement_store.append("dose_log", {"supplement": "VD3", "taken": False}, timestamp="2026-03-21T08:00:00")
            HealthDataStore("blood-pressure-tracker", data_dir=data_dir).append(
                "bp", {"sys": 134, "dia": 84}, timestamp="2026-03-14T20:10:00"
            )
            HealthDataStore("medication-reminder", data_dir=data_dir).append(
                "dose", {"name": "Amlodipine", "taken": True}, timestamp="2026-03-15T08:00:00"
            )

            old_key = os.environ.pop("OPENROUTER_API_KEY", None)
            try:
                digest = WeeklyHealthDigest(
                    data_dir=data_dir,
                    memory_dir=memory_dir,
                    now_fn=fixed_now,
                )
                content = digest.generate_monthly(month_of="2026-03-15")
            finally:
                if old_key is not None:
                    os.environ["OPENROUTER_API_KEY"] = old_key

            self.assertIn("# 健康月报 -- 2026-03", content)
            self.assertIn("## 指标对比", content)
            self.assertIn("## 下月建议", content)

            monthly_digest_path = Path(memory_dir) / "monthly-digest.md"
            self.assertTrue(monthly_digest_path.exists())
            self.assertIn("# 健康月报 -- 2026-03", monthly_digest_path.read_text(encoding="utf-8"))
            archive_path = Path(memory_dir) / "monthly" / "2026-03.md"
            self.assertTrue(archive_path.exists())


if __name__ == "__main__":
    unittest.main()
