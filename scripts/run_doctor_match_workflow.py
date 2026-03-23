#!/usr/bin/env python3
"""Run VitaClaw's public doctor matching workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from doctor_match_workflow import DoctorMatchWorkflow  # noqa: E402
from doctor_matching import load_json_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw doctor matching workflow")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--patient-json", required=True, help="Path to patient profile JSON")
    parser.add_argument("--doctors-json", required=True, help="Path to doctor candidates JSON")
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--pubmed-mode", choices=("off", "auto", "required"), default="auto")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    result = DoctorMatchWorkflow(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
    ).match_doctors(
        patient_profile=load_json_file(args.patient_json),
        doctors=load_json_file(args.doctors_json),
        top_n=args.top_n,
        pubmed_mode=args.pubmed_mode,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(result["markdown"])


if __name__ == "__main__":
    main()
