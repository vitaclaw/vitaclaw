#!/usr/bin/env python3
"""Tests for VitaClaw workspace template initialization."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import init_health_workspace  # noqa: E402


class InitHealthWorkspaceTest(unittest.TestCase):
    def test_available_templates_are_exposed(self):
        self.assertEqual(
            set(init_health_workspace.available_templates()),
            {
                "health-agent",
                "health-family-agent",
                "health-research-agent",
                "health-checkup-agent",
                "health-chronic-agent",
                "health-mental-support-agent",
                "health-postop-agent",
                "health-team-agent",
                "health-oncology-agent",
            },
        )

    def test_family_template_initializes_caregiver_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            logs = init_health_workspace.init_workspace(target_dir, template_name="health-family-agent")

            self.assertTrue(any("AGENTS.md" in log for log in logs))
            self.assertTrue((target_dir / "memory" / "health" / "_care-team.md").exists())

            agents_text = (target_dir / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("家人照护", agents_text)

    def test_health_agent_template_initializes_proactive_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            init_health_workspace.init_workspace(target_dir, template_name="health-agent")

            self.assertTrue((target_dir / "memory" / "health" / "items" / "annual-checkup.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "items" / "blood-sugar.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "items" / "heart-rate-hrv.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "heartbeat" / "preferences.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "quarterly" / ".gitkeep").exists())
            self.assertTrue((target_dir / "memory" / "health" / "heartbeat" / "task-board.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "items" / "behavior-plans.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "items" / "execution-barriers.md").exists())
            self.assertTrue((target_dir / "memory" / "health" / "team" / "team-board.md").exists())
            self.assertTrue((target_dir / "openclaw.health.json5").exists())

    def test_research_template_initializes_research_memory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            init_health_workspace.init_workspace(target_dir, template_name="health-research-agent")

            self.assertTrue((target_dir / "memory" / "research" / "watchlist.md").exists())

            agents_text = (target_dir / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("仅在 direct chat", agents_text)

    def test_onboarding_writes_identity_user_memory_and_profile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            init_health_workspace.init_workspace(target_dir, template_name="health-agent")

            answers = {
                "health_role": "个人健康总管",
                "audience": "本人",
                "scenario_focus": "hypertension",
                "primary_goals": "把血压稳定在家庭监测目标内;维持连续睡眠记录",
                "conditions_and_medications": "高血压;氨氯地平 5mg qd",
                "reminder_preference": "低打扰、先数据后建议、高风险强提醒",
                "reminder_strength": "proactive",
                "focus_closely": "blood-pressure; appointments",
                "high_risk_only_topics": "sleep; supplements",
                "default_cadence": "bp=12h; weekly-review=Sun 18:00",
                "care_team": "瑞金医院 心内科;张医生",
            }
            logs = init_health_workspace.apply_onboarding(
                target_dir,
                template_name="health-agent",
                answers=answers,
            )

            self.assertTrue(any("IDENTITY.md" in log for log in logs))
            identity_text = (target_dir / "IDENTITY.md").read_text(encoding="utf-8")
            user_text = (target_dir / "USER.md").read_text(encoding="utf-8")
            memory_text = (target_dir / "MEMORY.md").read_text(encoding="utf-8")
            profile_text = (target_dir / "memory" / "health" / "_health-profile.md").read_text(encoding="utf-8")
            pref_text = (target_dir / "memory" / "health" / "heartbeat" / "preferences.md").read_text(encoding="utf-8")
            plan_text = (target_dir / "memory" / "health" / "items" / "behavior-plans.md").read_text(encoding="utf-8")

            self.assertIn("个人健康总管", identity_text)
            self.assertIn("direct chat", identity_text)
            self.assertIn("低打扰、先数据后建议、高风险强提醒", user_text)
            self.assertIn("hypertension", memory_text)
            self.assertIn("长期稳定事实", memory_text)
            self.assertIn("高血压", memory_text)
            self.assertIn("氨氯地平 5mg qd", profile_text)
            self.assertIn("瑞金医院 心内科", profile_text)
            self.assertIn("Focus closely", pref_text)
            self.assertIn("补齐下一次家庭血压记录", plan_text)

    def test_chronic_template_applies_default_focus_profile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            init_health_workspace.init_workspace(target_dir, template_name="health-chronic-agent")
            init_health_workspace.apply_onboarding(
                target_dir,
                template_name="health-chronic-agent",
                answers={
                    "health_role": "慢病管理分身",
                    "audience": "本人",
                    "primary_goals": "稳定血压",
                    "conditions_and_medications": "高血压",
                    "reminder_preference": "高风险强提醒",
                    "care_team": "待补充",
                },
            )

            memory_text = (target_dir / "MEMORY.md").read_text(encoding="utf-8")
            pref_text = (target_dir / "memory" / "health" / "heartbeat" / "preferences.md").read_text(encoding="utf-8")
            self.assertIn("hypertension", memory_text)
            self.assertIn("blood-pressure; blood-sugar; medication; appointments", pref_text)

    def test_team_template_writes_chief_led_config_and_package_roles(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            init_health_workspace.init_workspace(
                target_dir,
                template_name="health-team-agent",
                packages=["family-care", "oncology"],
            )

            config_text = (target_dir / "openclaw.health.json5").read_text(encoding="utf-8")
            self.assertIn('entryAgent: "health-chief-of-staff"', config_text)
            self.assertIn('"health-family"', config_text)
            self.assertIn('"health-oncology"', config_text)
            self.assertIn("loadMemoryInGroupChats: false", config_text)

    def test_oncology_template_has_oncology_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            init_health_workspace.init_workspace(target_dir, template_name="health-oncology-agent")
            init_health_workspace.apply_onboarding(
                target_dir,
                template_name="health-oncology-agent",
                answers={
                    "health_role": "肿瘤专科支持分身",
                    "audience": "本人",
                    "primary_goals": "整理肿瘤标志物和复查节奏",
                    "conditions_and_medications": "结直肠癌术后随访",
                    "reminder_preference": "先证据后建议",
                    "care_team": "肿瘤科门诊",
                },
            )

            memory_text = (target_dir / "MEMORY.md").read_text(encoding="utf-8")
            config_text = (target_dir / "openclaw.health.json5").read_text(encoding="utf-8")
            self.assertIn("oncology-care", memory_text)
            self.assertIn('"health-oncology"', config_text)


if __name__ == "__main__":
    unittest.main()
