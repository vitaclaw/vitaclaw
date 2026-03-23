#!/usr/bin/env python3
"""Generate a unified health timeline for a VitaClaw workspace."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_timeline_builder import HealthTimelineBuilder  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate unified health timeline from archive + workspace"
    )
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--days", type=int, default=180, help="How many recent days to include")
    parser.add_argument("--max-entries", type=int, default=120, help="Maximum timeline entries")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write timeline file into memory/health/files",
    )
    args = parser.parse_args()

    result = HealthTimelineBuilder(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    ).build(days=args.days, max_entries=args.max_entries, write=not args.no_write)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(result["markdown"])
    if result.get("timeline_path"):
        print(f"已写入: {result['timeline_path']}")


if __name__ == "__main__":
    main()
