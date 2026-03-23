#!/usr/bin/env python3
"""Import Apple Health export.xml into a patient archive and workspace."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from apple_health_bridge import AppleHealthImporter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Apple Health export.xml into a patient archive"
    )
    parser.add_argument("export_xml", help="Path to Apple Health export.xml")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--start-date", default=None, help="Optional start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Optional end date YYYY-MM-DD")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--no-sync-workspace",
        action="store_true",
        help="Do not sync archive summary back into workspace files",
    )
    args = parser.parse_args()

    result = AppleHealthImporter(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    ).import_export(
        export_xml=args.export_xml,
        start_date=args.start_date,
        end_date=args.end_date,
        sync_workspace=not args.no_sync_workspace,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    if not result.get("success", True):
        print(f"[ERROR] {result.get('error', 'import failed')}")
        raise SystemExit(1)

    print(f"# Apple Health Import -- {result['patient_id']}\n")
    print(f"- Output dir: {result['output_dir']}")
    date_range = result.get("date_range") or {}
    if date_range:
        print(f"- Date range: {date_range.get('start')} ~ {date_range.get('end')}")
    print(f"- Records processed: {result.get('records_processed', 0)}")
    print(f"- Files created: {', '.join(result.get('files_created', []))}")
    print(f"- Correlation report: {result.get('correlation_report')}")


if __name__ == "__main__":
    main()
