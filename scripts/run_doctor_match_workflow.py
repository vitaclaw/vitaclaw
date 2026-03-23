#!/usr/bin/env python3
"""Run VitaClaw's public doctor matching workflow."""

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

from doctor_match_workflow import DoctorMatchWorkflow  # noqa: E402
from doctor_matching import load_json_file  # noqa: E402
from doctor_profile_harvester import (  # noqa: E402
    DoctorProfileHarvester,
    load_sources_file,
    merge_doctor_candidates,
)


def _load_or_harvest_doctors(
    doctors_json: str | None,
    doctor_seeds_json: str | None,
    harvest_mode: str,
    harvest_output: str | None = None,
) -> tuple[list[dict], dict | None]:
    doctors = load_json_file(doctors_json) if doctors_json else []
    harvest_result = None
    if doctor_seeds_json:
        harvester = DoctorProfileHarvester()
        harvest_result = harvester.harvest_sources(
            load_sources_file(doctor_seeds_json),
            mode=harvest_mode,
        )
        doctors = merge_doctor_candidates(doctors, harvest_result["candidates"])
        if harvest_output:
            Path(harvest_output).write_text(
                json.dumps(doctors, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    return doctors, harvest_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw doctor matching workflow")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--patient-json", required=True, help="Path to patient profile JSON")
    parser.add_argument("--doctors-json", default=None, help="Path to doctor candidates JSON")
    parser.add_argument("--doctor-seeds-json", default=None, help="Path to hospital public sources JSON")
    parser.add_argument(
        "--harvest-mode",
        choices=("auto", "static", "browser"),
        default="auto",
        help="How to harvest doctors from public hospital pages before matching",
    )
    parser.add_argument("--harvest-output", default=None, help="Optional output path for harvested doctors JSON")
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--pubmed-mode", choices=("off", "auto", "required"), default="auto")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    if not args.doctors_json and not args.doctor_seeds_json:
        parser.error("one of --doctors-json or --doctor-seeds-json is required")

    doctors, harvest_result = _load_or_harvest_doctors(
        doctors_json=args.doctors_json,
        doctor_seeds_json=args.doctor_seeds_json,
        harvest_mode=args.harvest_mode,
        harvest_output=args.harvest_output,
    )

    result = DoctorMatchWorkflow(
        workspace_root=args.workspace_root,
        memory_dir=args.memory_dir,
    ).match_doctors(
        patient_profile=load_json_file(args.patient_json),
        doctors=doctors,
        top_n=args.top_n,
        pubmed_mode=args.pubmed_mode,
    )
    if harvest_result is not None:
        result["harvest"] = harvest_result
        result["harvested_candidate_count"] = len(harvest_result["candidates"])

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(result["markdown"])


if __name__ == "__main__":
    main()
