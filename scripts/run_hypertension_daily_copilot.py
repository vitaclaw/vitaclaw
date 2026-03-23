#!/usr/bin/env python3
"""Run the productized hypertension daily copilot workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_flagship_scenarios import HypertensionDailyCopilot  # noqa: E402


def _build_copilot(args) -> HypertensionDailyCopilot:
    return HypertensionDailyCopilot(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw hypertension daily copilot")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--data-dir", default=None, help="Shared data directory")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily-entry", help="Run a daily hypertension entry")
    daily.add_argument("--systolic", type=int, default=None)
    daily.add_argument("--diastolic", type=int, default=None)
    daily.add_argument("--pulse", type=int, default=None)
    daily.add_argument("--context", default="home")
    daily.add_argument("--timestamp", default=None)
    daily.add_argument("--med", action="append", default=[], help="Medication as name|dose|frequency|notes")
    daily.add_argument("--adherence", default=None)
    daily.add_argument("--next-refill", default=None)
    daily.add_argument("--stock-coverage-days", type=int, default=None)
    daily.add_argument("--diet-summary", default=None)
    daily.add_argument("--exercise-summary", default=None)
    daily.add_argument("--weight", type=float, default=None)
    daily.add_argument("--symptoms", default=None)
    daily.add_argument("--next-follow-up", default=None)
    daily.add_argument("--next-follow-up-details", default=None)

    weekly = subparsers.add_parser("weekly-review", help="Generate a weekly hypertension review")
    weekly.add_argument("--week-of", default=None, help="Any date inside the target week (YYYY-MM-DD)")

    subparsers.add_parser("medication-review", help="Review hypertension medication and refill state")

    args = parser.parse_args()
    copilot = _build_copilot(args)

    if args.command == "daily-entry":
        result = copilot.daily_entry(
            systolic=args.systolic,
            diastolic=args.diastolic,
            pulse=args.pulse,
            context=args.context,
            timestamp=args.timestamp,
            medications=args.med,
            adherence=args.adherence,
            next_refill=args.next_refill,
            stock_coverage_days=args.stock_coverage_days,
            diet_summary=args.diet_summary,
            exercise_summary=args.exercise_summary,
            weight=args.weight,
            symptoms=args.symptoms,
            next_follow_up=args.next_follow_up,
            next_follow_up_details=args.next_follow_up_details,
        )
    elif args.command == "weekly-review":
        result = copilot.weekly_review(week_of=args.week_of)
    else:
        result = copilot.medication_review()

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(result["markdown"])


if __name__ == "__main__":
    main()
