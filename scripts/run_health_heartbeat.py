#!/usr/bin/env python3
"""Run VitaClaw health heartbeat checks and optionally write a report."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "_shared"))

from health_heartbeat import HealthHeartbeat  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw health heartbeat checks")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    parser.add_argument("--no-write-report", action="store_true", help="Do not write heartbeat report into memory/health/heartbeat/")
    args = parser.parse_args()

    heartbeat = HealthHeartbeat(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )
    result = heartbeat.run(write_report=not args.no_write_report)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["markdown"])
        if result.get("report_path"):
            print(f"\n[heartbeat report] {result['report_path']}")
        if result.get("task_board_path"):
            print(f"[task board] {result['task_board_path']}")
        if result.get("push_issues") is not None:
            print(f"[pushable issues] {len(result['push_issues'])}")


if __name__ == "__main__":
    main()
