#!/usr/bin/env python3
"""Run the productized annual checkup advisor workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_flagship_scenarios import AnnualCheckupAdvisorWorkflow  # noqa: E402


def _build_workflow(args) -> AnnualCheckupAdvisorWorkflow:
    return AnnualCheckupAdvisorWorkflow(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )


def _load_previous_items(path: str | None) -> list[dict] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw annual checkup advisor")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--data-dir", default=None, help="Shared data directory")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_report = subparsers.add_parser("import-report", help="Import a structured or PDF annual checkup report")
    import_report.add_argument("--items-json", default=None, help="Path to structured checkup items JSON")
    import_report.add_argument("--pdf-path", default=None, help="Path to the raw annual checkup PDF")
    import_report.add_argument("--previous-items-json", default=None, help="Optional previous-year structured items JSON")
    import_report.add_argument("--report-date", default=None, help="Report date in YYYY-MM-DD")
    import_report.add_argument("--next-follow-up", default=None)
    import_report.add_argument("--next-follow-up-details", default=None)

    subparsers.add_parser("follow-up-review", help="Review annual checkup follow-up state")

    args = parser.parse_args()
    workflow = _build_workflow(args)

    if args.command == "import-report":
        result = workflow.import_report(
            items_json_path=args.items_json,
            pdf_path=args.pdf_path,
            report_date=args.report_date,
            previous_items=_load_previous_items(args.previous_items_json),
            next_follow_up=args.next_follow_up,
            next_follow_up_details=args.next_follow_up_details,
        )
    else:
        result = workflow.follow_up_review()

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(result["markdown"])


if __name__ == "__main__":
    main()
