#!/usr/bin/env python3
"""Run due VitaClaw health operations for automation / cron."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_operations import HealthOperationsRunner  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run due VitaClaw health operations")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--force-weekly", action="store_true", help="Force current-week digest generation")
    parser.add_argument("--force-monthly", action="store_true", help="Force current-month digest generation")
    parser.add_argument("--force-distill", action="store_true", help="Force MEMORY.md distillation")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    parser.add_argument("--no-write", action="store_true", help="Do not write report/state files")
    args = parser.parse_args()

    result = HealthOperationsRunner(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    ).run(
        force_weekly=args.force_weekly,
        force_monthly=args.force_monthly,
        force_distill=args.force_distill,
        write=not args.no_write,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"# Health Operations -- {result['date']}\n")
    print("## Actions")
    for action in result["actions"] or ["本轮没有触发新的后台运营动作。"]:
        print(f"- {action}")
    print("\n## Heartbeat")
    print(f"- Total issues: {result['heartbeat_issue_count']}")
    print(f"- Pushable issues: {result['heartbeat_push_count']}")
    if result.get("report_path"):
        print(f"\n已写入: {result['report_path']}")


if __name__ == "__main__":
    main()
