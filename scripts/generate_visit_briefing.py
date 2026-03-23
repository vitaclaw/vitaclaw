#!/usr/bin/env python3
"""Generate a visit briefing from VitaClaw health memory."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_visit_workflow import HealthVisitWorkflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate clinician-ready visit briefing")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--visit-date", default=None, help="Visit date YYYY-MM-DD")
    parser.add_argument("--department", default=None, help="Department / clinician")
    parser.add_argument("--purpose", default=None, help="Visit purpose")
    parser.add_argument("--owner", default=None, help="Visit owner / companion")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    parser.add_argument("--no-write", action="store_true", help="Do not write briefing file")
    args = parser.parse_args()

    result = HealthVisitWorkflow(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    ).generate_briefing(
        visit_date=args.visit_date,
        department=args.department,
        purpose=args.purpose,
        owner=args.owner,
        write=not args.no_write,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(result["markdown"])
    if result.get("path"):
        print(f"已写入: {result['path']}")


if __name__ == "__main__":
    main()
