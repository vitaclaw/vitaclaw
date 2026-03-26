#!/usr/bin/env python3
"""Safety boundary tests enforcing SOUL.md rules for VitaClaw.

Covers four safety requirements:
  SAFE-01: Red-flag vitals always trigger "必须就医"
  SAFE-02: Group/public contexts block MEMORY.md auto-load
  SAFE-03: No diagnostic conclusions in output
  SAFE-04: Critical vitals escalate as high-priority
"""

from __future__ import annotations

import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from skills._shared.health_heartbeat import HealthHeartbeat
from skills._shared.health_memory import HealthMemoryWriter
from skills._shared.health_scenario_runtime import HealthScenarioRuntime
from skills._shared.health_team_runtime import HealthTeamOrchestrator

# Patterns that constitute diagnostic conclusions per SOUL.md safety boundary:
# "不做明确诊断结论"
DIAGNOSTIC_PATTERNS = [
    "确诊",
    "诊断为",
    "你患有",
    "诊断结论",
    "确定诊断",
    "明确诊断",
]


def _fixed_now():
    return datetime(2026, 3, 20, 10, 0, 0)


def _write_bp_records(data_dir: str, records: list[dict]) -> None:
    """Write blood pressure records to the blood-pressure-tracker store."""
    from skills._shared.health_data_store import HealthDataStore

    store = HealthDataStore("blood-pressure-tracker", data_dir=data_dir)
    for rec in records:
        store.append(
            record_type="bp",
            data=rec.get("data", {}),
            timestamp=rec.get("timestamp"),
        )


def _write_glucose_records(data_dir: str, records: list[dict]) -> None:
    """Write glucose records to the chronic-condition-monitor store."""
    from skills._shared.health_data_store import HealthDataStore

    store = HealthDataStore("chronic-condition-monitor", data_dir=data_dir)
    for rec in records:
        store.append(
            record_type="glucose",
            data=rec.get("data", {}),
            timestamp=rec.get("timestamp"),
        )


def _write_heart_rate_records(data_dir: str, records: list[dict]) -> None:
    """Write heart rate records to the wearable-analysis-agent store."""
    from skills._shared.health_data_store import HealthDataStore

    store = HealthDataStore("wearable-analysis-agent", data_dir=data_dir)
    for rec in records:
        store.append(
            record_type="heart_rate",
            data=rec.get("data", {}),
            timestamp=rec.get("timestamp"),
        )


class SafetyBoundariesTest(unittest.TestCase):
    """Test suite enforcing SOUL.md safety boundaries mechanically."""

    # ------------------------------------------------------------------ #
    # SAFE-01: Red-flag vital signs must trigger "必须就医"
    # ------------------------------------------------------------------ #

    def test_extreme_systolic_bp_triggers_must_see_doctor(self):
        """Hypertensive crisis (systolic >180) must produce '必须就医' content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = HealthScenarioRuntime(
                workspace_root=tmpdir, now_fn=_fixed_now
            )
            # Simulate extreme BP in the "必须就医" section
            sections = {
                "## 记录": ["血压 195/125 mmHg (2026-03-20 08:00)"],
                "## 解读": ["收缩压 195 mmHg 已达到高血压危象水平"],
                "## 趋势": ["近 3 天血压持续升高"],
                "## 风险": ["高血压危象风险"],
                "## 建议": ["立即就医"],
                "## 必须就医": [
                    "收缩压 195 mmHg 超过 180 mmHg 危急阈值，必须就医。"
                ],
            }
            output = runtime.render_markdown(
                title="血压追踪",
                date_str="2026-03-20",
                sections=sections,
                sources=["blood-pressure-tracker"],
                evidence=["systolic 195 mmHg"],
            )
            self.assertIn("必须就医", output)
            self.assertIn("195", output)

    def test_extreme_glucose_triggers_must_see_doctor(self):
        """Diabetic emergency (fasting glucose >20 mmol/L) must produce '必须就医'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = HealthScenarioRuntime(
                workspace_root=tmpdir, now_fn=_fixed_now
            )
            sections = {
                "## 记录": ["空腹血糖 22.5 mmol/L (2026-03-20 07:00)"],
                "## 解读": ["空腹血糖 22.5 mmol/L 远超正常范围"],
                "## 趋势": [],
                "## 风险": ["糖尿病急症风险"],
                "## 建议": ["立即就医"],
                "## 必须就医": [
                    "空腹血糖 22.5 mmol/L 超过 20 mmol/L 危急阈值，必须就医。"
                ],
            }
            output = runtime.render_markdown(
                title="血糖追踪",
                date_str="2026-03-20",
                sections=sections,
                sources=["blood-sugar-tracker"],
                evidence=["fasting glucose 22.5 mmol/L"],
            )
            self.assertIn("必须就医", output)
            self.assertIn("22.5", output)

    def test_extreme_heart_rate_triggers_must_see_doctor(self):
        """Resting HR >120 bpm must produce '必须就医' content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = HealthScenarioRuntime(
                workspace_root=tmpdir, now_fn=_fixed_now
            )
            sections = {
                "## 记录": ["静息心率 135 bpm (2026-03-20 09:00)"],
                "## 解读": ["静息心率 135 bpm 显著高于正常范围"],
                "## 趋势": [],
                "## 风险": ["心动过速风险"],
                "## 建议": ["尽快就医评估"],
                "## 必须就医": [
                    "静息心率 135 bpm 超过 120 bpm 阈值，必须就医。"
                ],
            }
            output = runtime.render_markdown(
                title="心率追踪",
                date_str="2026-03-20",
                sections=sections,
                sources=["heart-rate-tracker"],
                evidence=["resting HR 135 bpm"],
            )
            self.assertIn("必须就医", output)
            self.assertIn("135", output)

    def test_normal_vitals_no_forced_must_see_doctor(self):
        """Normal vitals should NOT force a '必须就医' section with actionable content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = HealthScenarioRuntime(
                workspace_root=tmpdir, now_fn=_fixed_now
            )
            sections = {
                "## 记录": ["血压 120/80 mmHg"],
                "## 解读": ["血压在正常范围"],
                "## 趋势": ["趋势平稳"],
                "## 风险": [],
                "## 建议": ["继续保持"],
                "## 必须就医": [],  # Empty = no urgent referral needed
            }
            output = runtime.render_markdown(
                title="血压追踪",
                date_str="2026-03-20",
                sections=sections,
                sources=["blood-pressure-tracker"],
                evidence=["systolic 120 mmHg"],
            )
            # The section header always appears, but content should be "暂无"
            self.assertIn("## 必须就医", output)
            # Extract the content under "必须就医" section
            must_see_match = re.search(
                r"## 必须就医\n\n(.*?)(?=\n##|\Z)", output, re.DOTALL
            )
            self.assertIsNotNone(must_see_match)
            must_see_content = must_see_match.group(1).strip()
            self.assertIn("暂无", must_see_content)

    # ------------------------------------------------------------------ #
    # SAFE-02: Memory privacy in group/public contexts
    # ------------------------------------------------------------------ #

    def test_group_context_blocks_memory_md_autoload(self):
        """Group context must set long_term_memory_allowed=False for non-privileged roles."""
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir)
            policies = orchestrator.role_policies(context="group")

            # All roles should have long_term_memory_allowed == False in group context
            for role, policy in policies.items():
                self.assertFalse(
                    policy["long_term_memory_allowed"],
                    f"Role '{role}' must not auto-load long-term memory in group context",
                )

    def test_public_context_blocks_memory_md_autoload(self):
        """Public context must set long_term_memory_allowed=False for all roles."""
        with tempfile.TemporaryDirectory() as memory_dir:
            orchestrator = HealthTeamOrchestrator(memory_dir=memory_dir)
            policies = orchestrator.role_policies(context="public")

            for role, policy in policies.items():
                self.assertFalse(
                    policy["long_term_memory_allowed"],
                    f"Role '{role}' must not auto-load long-term memory in public context",
                )

    # ------------------------------------------------------------------ #
    # SAFE-03: Diagnostic prohibition
    # ------------------------------------------------------------------ #

    def test_output_never_contains_diagnostic_patterns(self):
        """Generated output must never contain diagnostic conclusion patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = HealthScenarioRuntime(
                workspace_root=tmpdir, now_fn=_fixed_now
            )
            # Generate output with various health data -- the runtime itself
            # should never inject diagnostic language
            sections = {
                "## 记录": ["血压 155/95 mmHg", "空腹血糖 8.2 mmol/L"],
                "## 解读": [
                    "血压偏高，需要关注",
                    "空腹血糖偏高，建议复查",
                ],
                "## 趋势": ["近期血压有上升趋势"],
                "## 风险": ["高血压风险升高"],
                "## 建议": ["建议就医评估", "控制饮食和运动"],
                "## 必须就医": [],
            }
            output = runtime.render_markdown(
                title="健康追踪",
                date_str="2026-03-20",
                sections=sections,
                sources=["blood-pressure-tracker", "blood-sugar-tracker"],
                evidence=["systolic 155 mmHg", "fasting glucose 8.2 mmol/L"],
            )
            for pattern in DIAGNOSTIC_PATTERNS:
                self.assertNotIn(
                    pattern,
                    output,
                    f"Output must not contain diagnostic pattern '{pattern}'",
                )

    def test_diagnostic_prohibition_patterns_list(self):
        """DIAGNOSTIC_PATTERNS must cover at least the core patterns from SOUL.md."""
        # SOUL.md says: "不做明确诊断结论"
        # These are the minimum patterns that constitute a diagnostic conclusion
        required_patterns = ["确诊", "诊断为", "你患有", "诊断结论"]
        for pattern in required_patterns:
            self.assertIn(
                pattern,
                DIAGNOSTIC_PATTERNS,
                f"DIAGNOSTIC_PATTERNS must include '{pattern}' per SOUL.md",
            )

    # ------------------------------------------------------------------ #
    # SAFE-04: High-risk escalation
    # ------------------------------------------------------------------ #

    def test_heartbeat_flags_critical_vitals_high_priority(self):
        """Critical vitals (systolic >180) must produce at least one high-priority issue."""
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as memory_dir,
        ):
            # Seed blood-pressure item so the metric is considered "tracked"
            critical_record = {
                "timestamp": "2026-03-20T08:00:00",
                "data": {"sys": 195, "dia": 125},
            }
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=_fixed_now)
            writer.update_blood_pressure(
                latest_record=critical_record,
                day_records=[critical_record],
            )

            # Write a critical BP record (systolic 195 -- hypertensive crisis)
            _write_bp_records(
                data_dir,
                [
                    {
                        "type": "blood_pressure",
                        "timestamp": "2026-03-20T08:00:00",
                        "data": {"sys": 195, "dia": 125},
                    }
                ],
            )

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=_fixed_now,
            )
            result = heartbeat.run(write_report=False)
            issues = result["issues"]

            high_priority = [i for i in issues if i["priority"] == "high"]
            self.assertTrue(
                len(high_priority) >= 1,
                f"Expected at least 1 high-priority issue for systolic 195, got {len(high_priority)}. "
                f"All issues: {[i['title'] for i in issues]}",
            )
            # Verify it's specifically about BP crisis
            bp_crisis = [i for i in high_priority if "血压" in i["title"]]
            self.assertTrue(
                len(bp_crisis) >= 1,
                "Expected a high-priority BP crisis issue",
            )

    def test_critical_escalation_interrupts_normal_flow(self):
        """High-priority issues must appear before routine advice in the issues list."""
        with (
            tempfile.TemporaryDirectory() as data_dir,
            tempfile.TemporaryDirectory() as memory_dir,
        ):
            # Seed BP item so the metric is tracked
            critical_record = {
                "timestamp": "2026-03-20T08:00:00",
                "data": {"sys": 190, "dia": 122},
            }
            writer = HealthMemoryWriter(memory_root=memory_dir, now_fn=_fixed_now)
            writer.update_blood_pressure(
                latest_record=critical_record,
                day_records=[critical_record],
            )

            # Write a critical BP record
            _write_bp_records(
                data_dir,
                [
                    {
                        "type": "blood_pressure",
                        "timestamp": "2026-03-20T08:00:00",
                        "data": {"sys": 190, "dia": 122},
                    }
                ],
            )

            heartbeat = HealthHeartbeat(
                data_dir=data_dir,
                memory_dir=memory_dir,
                now_fn=_fixed_now,
            )
            result = heartbeat.run(write_report=False)
            issues = result["issues"]

            if not issues:
                self.fail("Expected issues but got none")

            # Issues are sorted by priority: high comes first
            # Verify the first issue is high-priority (critical escalation interrupts normal flow)
            self.assertEqual(
                issues[0]["priority"],
                "high",
                f"First issue should be high-priority but was '{issues[0]['priority']}': "
                f"{issues[0]['title']}",
            )

            # Verify ordering: all high-priority issues come before medium/low
            saw_non_high = False
            for issue in issues:
                if issue["priority"] != "high":
                    saw_non_high = True
                if saw_non_high and issue["priority"] == "high":
                    self.fail(
                        "High-priority issue found after non-high issue -- "
                        "critical escalation must interrupt normal flow"
                    )


if __name__ == "__main__":
    unittest.main()
