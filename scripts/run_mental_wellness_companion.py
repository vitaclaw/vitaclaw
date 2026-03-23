#!/usr/bin/env python3
"""Run the support-mode mental wellness companion workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_scenario_runtime import HealthScenarioRuntime  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402


CRISIS_KEYWORDS = (
    "不想活",
    "想死",
    "自杀",
    "self-harm",
    "suicide",
    "life is meaningless",
    "no hope",
)


def _has_crisis_signal(text: str) -> bool:
    lowered = (text or "").lower()
    return any(keyword.lower() in lowered for keyword in CRISIS_KEYWORDS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw mental wellness companion")
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--memory-dir", default=None)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--mood-summary", default=None)
    parser.add_argument("--sleep-summary", default=None)
    parser.add_argument("--stress-summary", default=None)
    parser.add_argument("--phq9", type=int, default=None)
    parser.add_argument("--gad7", type=int, default=None)
    args = parser.parse_args()

    runtime = HealthScenarioRuntime(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
    )
    writer = HealthMemoryWriter(
        workspace_root=args.workspace_root,
        memory_root=args.memory_dir,
    )
    date_str = datetime.now().date().isoformat()

    mood_text = " | ".join(
        part for part in (args.mood_summary, args.sleep_summary, args.stress_summary) if part
    )
    crisis = _has_crisis_signal(mood_text) or (args.phq9 is not None and args.phq9 >= 20) or (args.gad7 is not None and args.gad7 >= 15)

    writer._upsert_daily_section(
        date_str,
        "Mental Wellness",
        "mental-wellness-companion",
        [
            f"Mood: {args.mood_summary or 'pending'}",
            f"Sleep: {args.sleep_summary or 'pending'}",
            f"Stress: {args.stress_summary or 'pending'}",
            f"PHQ-9: {args.phq9 if args.phq9 is not None else 'pending'}",
            f"GAD-7: {args.gad7 if args.gad7 is not None else 'pending'}",
        ],
    )
    writer.upsert_behavior_plan(
        plan_id="mental-next-checkin",
        scenario="mental-wellness-companion",
        title="完成下一次支持性情绪/睡眠记录",
        cadence="daily",
        due_at=(datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat(timespec="minutes"),
        topic="mental-health-score",
        risk_policy="high-risk-only",
        consequence="睡眠-情绪恶化可能在没有被看见时继续累积。",
        next_step="明天完成一次简短心情和睡眠 check-in。",
    )

    follow_up_tasks = [
        runtime.build_task(
            title="完成下一次心理支持 check-in",
            reason="支持型心理场景依赖连续、低压力的短 check-in 来识别趋势。",
            next_step="明天补一条 mood/sleep/stress 简短记录。",
            follow_up="若明天仍未处理，会继续温和提醒。",
            priority="low" if not crisis else "high",
            topic="mental-health-score",
            source_refs=[str(writer.daily_dir / f"{date_str}.md"), str(writer.behavior_plans_path)],
            execution_mode="isolated-session" if crisis else "heartbeat",
        )
    ]

    sections = {
        "## 记录": [
            f"情绪摘要：{args.mood_summary or 'pending'}",
            f"睡眠摘要：{args.sleep_summary or 'pending'}",
            f"压力事件：{args.stress_summary or 'pending'}",
            f"PHQ-9：{args.phq9 if args.phq9 is not None else 'pending'}",
            f"GAD-7：{args.gad7 if args.gad7 is not None else 'pending'}",
        ],
        "## 解读": [
            "这是支持型心理健康场景，重点是连续追踪、睡眠情绪联动和危机分流，不替代治疗。",
        ],
        "## 趋势": ["先形成连续 check-in，再判断睡眠/情绪是否在持续恶化。"],
        "## 风险": ["检测到危机信号，需要优先转向专业帮助。"] if crisis else ["当前未触发危机关键词或高分危机阈值。"],
        "## 建议": [
            "先完成一条低负担 check-in，而不是一次性要求很多。",
            "如果最近睡眠也在走差，优先把睡眠和压力事件写清楚。",
        ],
        "## 必须就医": [
            "如存在自伤/自杀想法、极度绝望或强烈安全风险，请立即联系 120 / 911 / 988 或本地危机热线。"
        ] if crisis else ["当前没有触发必须就医级别结论，但若出现危机想法应立即升级。"],
    }

    result = runtime.persist_result(
        filename=f"mental-wellness-{date_str}.md",
        title="Mental Wellness Companion",
        date_str=date_str,
        sections=sections,
        sources=[str(writer.daily_dir / f"{date_str}.md"), str(writer.behavior_plans_path)],
        evidence=[
            "危机信号依据关键词扫描与 PHQ-9/GAD-7 高分阈值。",
            "该场景仅做支持性追踪与危机分流，不替代专业治疗。",
        ],
        scenario="mental-wellness-companion",
        file_type="mental-wellness-companion",
        summary=f"{date_str} 支持型心理健康记录",
        follow_up_tasks=follow_up_tasks,
        writebacks=[str(writer.daily_dir / f"{date_str}.md"), str(writer.behavior_plans_path)],
        alerts=["Crisis routing triggered"] if crisis else [],
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["markdown"])


if __name__ == "__main__":
    main()
