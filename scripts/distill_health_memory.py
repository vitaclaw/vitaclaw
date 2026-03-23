#!/usr/bin/env python3
"""Distill recent health operations into VitaClaw long-term memory."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_memory_distiller import HealthMemoryDistiller  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Distill recent health operations into MEMORY.md"
    )
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write back to MEMORY.md",
    )
    args = parser.parse_args()

    result = HealthMemoryDistiller(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    ).run(write=not args.no_write)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"# Health Memory Distillation -- {result['date']}\n")
    print("## 最近健康运营摘要")
    for line in result["summary_lines"]:
        print(line)
    print("\n## 当前重点任务")
    for line in result["task_lines"]:
        print(line)
    print("\n## 风险与待跟进")
    for line in result["risk_lines"]:
        print(line)
    if result["memory_path"]:
        print(f"\n已写回: {result['memory_path']}")


if __name__ == "__main__":
    main()
