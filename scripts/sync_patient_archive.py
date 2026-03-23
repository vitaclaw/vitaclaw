#!/usr/bin/env python3
"""Sync a medical-record-organizer patient archive into a VitaClaw workspace."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from patient_archive_bridge import PatientArchiveBridge  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync patient archive summary into memory/health/files"
    )
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
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
        help="Do not write summary into workspace files",
    )
    args = parser.parse_args()

    bridge = PatientArchiveBridge(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )
    summary = bridge.sync_to_workspace(write=not args.no_write)

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    print(bridge.render_markdown(summary))
    if summary.get("summary_path"):
        print(f"已写入: {summary['summary_path']}")
    if summary.get("link_path"):
        print(f"已链接: {summary['link_path']}")


if __name__ == "__main__":
    main()
