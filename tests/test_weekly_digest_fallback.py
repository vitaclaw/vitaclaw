#!/usr/bin/env python3
"""Tests for local fallback weekly digest generation."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from skills._shared.health_data_store import HealthDataStore

ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DIR = ROOT / "skills" / "weekly-health-digest"
sys.path.insert(0, str(WEEKLY_DIR))

from weekly_health_digest import WeeklyHealthDigest  # noqa: E402


class WeeklyDigestFallbackTest(unittest.TestCase):
    def test_generate_uses_local_fallback_and_writes_memory(self):
        def fixed_now():
            return datetime(2026, 3, 15, 21, 0, 0)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            HealthDataStore("caffeine-tracker", data_dir=data_dir).append(
                "intake", {"drink": "Americano", "mg": 95}, timestamp="2026-03-10T08:30:00"
            )
            HealthDataStore("caffeine-tracker", data_dir=data_dir).append(
                "intake", {"drink": "Green tea", "mg": 30}, timestamp="2026-03-12T11:00:00"
            )
            HealthDataStore("sleep-analyzer", data_dir=data_dir).append(
                "sleep_session",
                {"date": "2026-03-10", "score": 82, "total_min": 430, "efficiency_pct": 90},
                timestamp="2026-03-10T07:00:00",
            )
            supplement_store = HealthDataStore("supplement-manager", data_dir=data_dir)
            supplement_store.append("dose_log", {"supplement": "VD3", "taken": True}, timestamp="2026-03-11T08:00:00")
            supplement_store.append("dose_log", {"supplement": "VD3", "taken": False}, timestamp="2026-03-12T08:00:00")
            HealthDataStore("blood-pressure-tracker", data_dir=data_dir).append(
                "bp", {"sys": 136, "dia": 86}, timestamp="2026-03-14T20:10:00"
            )

            old_key = os.environ.pop("OPENROUTER_API_KEY", None)
            try:
                digest = WeeklyHealthDigest(
                    data_dir=data_dir,
                    memory_dir=memory_dir,
                    now_fn=fixed_now,
                )
                content = digest.generate(week_of="2026-03-15")
            finally:
                if old_key is not None:
                    os.environ["OPENROUTER_API_KEY"] = old_key

            self.assertIn("# 健康周报 -- 2026-03-09 ~ 2026-03-15", content)
            self.assertIn("## 数据概览", content)
            self.assertIn("咖啡因日均(mg)", content)
            self.assertIn("## 建议", content)

            weekly_digest_path = Path(memory_dir) / "weekly-digest.md"
            self.assertTrue(weekly_digest_path.exists())
            self.assertIn("# 健康周报 -- 2026-03-09 ~ 2026-03-15", weekly_digest_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
