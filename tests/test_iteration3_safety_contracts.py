#!/usr/bin/env python3
"""Safety and anti-hallucination style tests for Iteration 3 team workflows."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from health_team_runtime import HealthTeamOrchestrator  # noqa: E402


class Iteration3SafetyContractsTest(unittest.TestCase):
    def test_mixed_language_checkup_report_preserves_raw_evidence(self):
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir)
            result = orchestrator.dispatch_flagship_scenario(
                "annual-checkup-advisor",
                payload={
                    "report_date": "2026-03-10",
                    "items": [
                        {
                            "category": "Liver Function",
                            "item": "ALT",
                            "value": "88",
                            "unit": "U/L",
                            "reference_range": "0-40",
                            "status": "偏高",
                        },
                        {
                            "category": "血糖",
                            "item": "Fasting Glucose",
                            "value": "115",
                            "unit": "mg/dL",
                            "reference_range": "70-99",
                            "status": "high",
                        },
                    ],
                },
            )

            output_text = Path(result["output_path"]).read_text(encoding="utf-8")
            annual_item = Path(memory_dir) / "items" / "annual-checkup.md"
            annual_text = annual_item.read_text(encoding="utf-8")
            self.assertIn("ALT", output_text)
            self.assertIn("Fasting Glucose", annual_text)
            self.assertIn("mg/dL", annual_text)

    def test_ambiguous_report_input_does_not_write_memory_md_directly(self):
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir)
            result = orchestrator.dispatch_flagship_scenario(
                "annual-checkup-advisor",
                payload={
                    "report_date": "2026-03-10",
                    "items": [
                        {
                            "category": "Unknown",
                            "item": "Scan Summary",
                            "value": "see report",
                            "unit": "text",
                            "reference_range": "n/a",
                            "status": "pending review",
                        }
                    ],
                },
            )

            self.assertFalse(any(path.endswith("MEMORY.md") for path in result["writebacks"]))
            records_brief = Path(result["role_brief_paths"]["health-records"]).read_text(encoding="utf-8")
            self.assertIn("不直接改长期画像", records_brief)

    def test_group_context_keeps_public_agents_off_patient_archive(self):
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir, packages=["oncology"])
            policies = orchestrator.role_policies(context="public")

            self.assertFalse(policies["health-chief-of-staff"]["long_term_memory_allowed"])
            self.assertFalse(policies["health-research"]["raw_archive_allowed"])
            self.assertTrue(policies["health-oncology"]["raw_archive_allowed"])


if __name__ == "__main__":
    unittest.main()
