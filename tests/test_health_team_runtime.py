#!/usr/bin/env python3
"""Tests for chief-led Iteration 3 team orchestration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skills._shared.health_team_runtime import HealthTeamOrchestrator


class HealthTeamRuntimeTest(unittest.TestCase):
    def test_chief_dispatches_hypertension_to_metrics_and_lifestyle(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(data_dir=data_dir, memory_dir=memory_dir)
            result = orchestrator.dispatch_flagship_scenario(
                "hypertension-daily-copilot",
                payload={
                    "systolic": 148,
                    "diastolic": 96,
                    "pulse": 80,
                    "diet_summary": "外卖偏咸",
                    "exercise_summary": "晚饭后快走 30 分钟",
                    "medications": ["Amlodipine|5mg|qd|on-time"],
                    "adherence": "近7天 100%",
                },
            )

            self.assertEqual(result["routed_roles"], ["health-metrics", "health-lifestyle"])
            self.assertTrue(Path(result["team_board_path"]).exists())
            self.assertTrue(Path(result["chief_summary_path"]).exists())
            self.assertTrue(Path(result["dispatch_log_path"]).exists())
            self.assertIn("health-metrics", result["role_brief_paths"])
            self.assertIn("health-lifestyle", result["role_brief_paths"])

            chief_text = Path(result["chief_summary_path"]).read_text(encoding="utf-8")
            self.assertIn("health-chief-of-staff", chief_text)
            self.assertIn("health-metrics", chief_text)

            dispatch_log = Path(result["dispatch_log_path"]).read_text(encoding="utf-8")
            self.assertIn('"role": "health-chief-of-staff"', dispatch_log)
            self.assertIn('"event": "brief-generated"', dispatch_log)

    def test_hypertensive_crisis_is_escalated_to_safety(self):
        with tempfile.TemporaryDirectory() as data_dir, tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(data_dir=data_dir, memory_dir=memory_dir)
            result = orchestrator.dispatch_flagship_scenario(
                "hypertension-daily-copilot",
                payload={
                    "systolic": 186,
                    "diastolic": 122,
                    "symptoms": "胸痛",
                },
            )

            self.assertIn("health-safety", result["routed_roles"])
            safety_brief = Path(result["role_brief_paths"]["health-safety"]).read_text(encoding="utf-8")
            self.assertIn("必须就医", safety_brief)
            self.assertIn("立即", safety_brief)

    def test_group_context_disables_long_term_memory_loading(self):
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir)
            result = orchestrator.dispatch_flagship_scenario(
                "annual-checkup-advisor",
                payload={
                    "items": [
                        {
                            "category": "血糖",
                            "item": "空腹血糖",
                            "value": "6.4",
                            "unit": "mmol/L",
                            "reference_range": "3.9-6.1",
                            "status": "偏高",
                        }
                    ],
                    "report_date": "2026-03-10",
                },
                context="group",
            )

            self.assertFalse(result["context_policy"]["load_long_term_memory"])
            self.assertFalse(result["policies"]["health-chief-of-staff"]["long_term_memory_allowed"])
            self.assertFalse(result["policies"]["health-research"]["long_term_memory_allowed"])

    def test_role_policies_enforce_isolation_defaults(self):
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir, packages=["family-care", "oncology"])
            policies = orchestrator.role_policies()
            enabled_roles = orchestrator.enabled_roles()

            self.assertIn("health-family", enabled_roles)
            self.assertIn("health-oncology", enabled_roles)
            self.assertTrue(policies["health-records"]["raw_archive_allowed"])
            self.assertFalse(policies["health-research"]["raw_archive_allowed"])
            self.assertFalse(policies["health-research"]["long_term_memory_allowed"])
            self.assertEqual(policies["health-safety"]["can_write"], ["alert", "task", "role-brief"])

    def test_team_heartbeat_refreshes_team_board(self):
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir)
            result = orchestrator.run_team_heartbeat()

            self.assertTrue(Path(result["team_board_path"]).exists())
            board_text = Path(result["team_board_path"]).read_text(encoding="utf-8")
            self.assertIn("health-chief-of-staff", board_text)


if __name__ == "__main__":
    unittest.main()
