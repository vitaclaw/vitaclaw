#!/usr/bin/env python3
"""Run the patient archive + timeline support workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_scenario_runtime import HealthScenarioRuntime  # noqa: E402
from health_timeline_builder import HealthTimelineBuilder  # noqa: E402
from patient_archive_bridge import PatientArchiveBridge  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw patient records workflow")
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--memory-dir", default=None)
    parser.add_argument("--patients-root", default=None)
    parser.add_argument("--patient-id", default=None)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    runtime = HealthScenarioRuntime(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
    )
    bridge = PatientArchiveBridge(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )
    timeline = HealthTimelineBuilder(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )

    archive_summary = bridge.sync_to_workspace(write=True)
    timeline_result = timeline.build(write=True)
    follow_up_tasks = []
    if archive_summary.get("unclassified_count"):
        follow_up_tasks.append(
            runtime.build_task(
                title="整理未分类病历",
                reason=f"当前还有 {archive_summary['unclassified_count']} 份未分类病历文件待整理。",
                next_step="先清空一批未分类原始文件，并补摘要/时间线。",
                follow_up="若本周仍未处理，会继续提醒。",
                priority="medium" if archive_summary["unclassified_count"] < 5 else "high",
                topic="patient-archive",
                source_refs=[archive_summary.get("summary_path") or str(runtime.writer.files_dir / "patient-archive-summary.md")],
            )
        )

    sections = {
        "## 记录": [
            f"患者档案：{archive_summary.get('patient_id', 'pending')}",
            f"未分类文件：{archive_summary.get('unclassified_count', 0)}",
            f"最新时间线事件：{archive_summary.get('latest_timeline_date', 'pending')}",
        ],
        "## 解读": ["这条支持型 workflow 负责把病历归档、Apple Health 摘要和统一时间轴串起来。"],
        "## 趋势": [f"统一时间轴条目数：{timeline_result.get('entry_count', 0)}"],
        "## 风险": [
            "未分类病历越积越多，会降低后续就诊 briefing 和长期趋势的完整度。"
            if archive_summary.get("unclassified_count")
            else "当前没有明显的归档积压风险。"
        ],
        "## 建议": [
            "优先整理未分类文件，再刷新 timeline，最后生成门诊 briefing。",
        ],
        "## 必须就医": ["这条 workflow 不直接做医疗判断，如档案中含急性异常请按原报告和医生要求升级。"],
    }
    result = runtime.persist_result(
        filename=f"patient-records-workflow-{runtime.writer.base_dir.name}.md",
        title="Patient Records Workflow",
        date_str=runtime.writer._now().date().isoformat(),
        sections=sections,
        sources=[
            archive_summary.get("summary_path") or str(runtime.writer.files_dir / "patient-archive-summary.md"),
            timeline_result.get("timeline_path") or str(runtime.writer.files_dir / "health-timeline.md"),
        ],
        evidence=["病历支持 workflow 以 patient archive + timeline refresh 为中心，不直接替代医疗结论。"],
        scenario="patient-records-workflow",
        file_type="patient-records-workflow",
        summary="病历归档与时间线支持 workflow",
        follow_up_tasks=follow_up_tasks,
        writebacks=[
            archive_summary.get("summary_path") or str(runtime.writer.files_dir / "patient-archive-summary.md"),
            timeline_result.get("timeline_path") or str(runtime.writer.files_dir / "health-timeline.md"),
        ],
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["markdown"])


if __name__ == "__main__":
    main()
