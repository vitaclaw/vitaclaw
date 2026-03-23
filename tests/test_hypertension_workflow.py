#!/usr/bin/env python3
"""End-to-end tests for the hypertension daily workflow."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "blood-pressure-tracker"
sys.path.insert(0, str(SKILL_DIR))

from blood_pressure_tracker import BloodPressureTracker  # noqa: E402


class HypertensionWorkflowTest(unittest.TestCase):
    def test_record_syncs_store_and_memory(self):
        fixed_now = lambda: datetime(2026, 3, 15, 13, 25, 36)

        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            tracker = BloodPressureTracker(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=fixed_now,
            )

            with redirect_stdout(io.StringIO()):
                tracker.record(145, 92, hr=80, context="morning", timestamp="2026-03-10T07:30:00")
                tracker.record(138, 86, hr=76, context="morning", timestamp="2026-03-14T07:20:00")
                tracker.record(132, 84, hr=72, context="evening", timestamp="2026-03-14T20:10:00")

            records = tracker.store.query("bp")
            self.assertEqual(len(records), 3)

            daily_old = Path(memory_dir) / "daily" / "2026-03-10.md"
            daily_latest = Path(memory_dir) / "daily" / "2026-03-14.md"
            item_path = Path(memory_dir) / "items" / "blood-pressure.md"

            self.assertTrue(daily_old.exists())
            self.assertTrue(daily_latest.exists())
            self.assertTrue(item_path.exists())

            daily_latest_text = daily_latest.read_text(encoding="utf-8")
            self.assertIn("07:20: 138/86 mmHg, pulse 76 [morning] -- 1级高血压", daily_latest_text)
            self.assertIn("20:10: 132/84 mmHg, pulse 72 [evening] -- 1级高血压", daily_latest_text)
            self.assertIn("Daily average: 135.0/85.0 mmHg", daily_latest_text)

            item_text = item_path.read_text(encoding="utf-8")
            self.assertIn("Latest: 132/84 mmHg (2026-03-14 20:10, evening)", item_text)
            self.assertIn("7-day average: 138.3/87.3 mmHg across 3 readings", item_text)
            self.assertIn("| 2026-03-14 | 20:10 | 132 | 84 | 72 | evening | 1级高血压 |", item_text)
            self.assertIn("| 2026-03-10 | 07:30 | 145 | 92 | 80 | morning | 2级高血压 |", item_text)


if __name__ == "__main__":
    unittest.main()
