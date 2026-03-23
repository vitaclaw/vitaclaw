#!/usr/bin/env python3
"""Run the productized diabetes control hub workflow."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_flagship_scenarios import DiabetesControlHub  # noqa: E402


def _parse_glucose_entries(values: list[str]) -> list[dict]:
    entries = []
    for raw in values or []:
        parts = [part.strip() for part in raw.split("|")]
        if not parts or not parts[0]:
            continue
        entry = {
            "value": float(parts[0]),
            "context": parts[1] if len(parts) > 1 else "",
        }
        if len(parts) > 2 and parts[2]:
            entry["timestamp"] = parts[2]
        if len(parts) > 3 and parts[3]:
            entry["note"] = parts[3]
        entries.append(entry)
    return entries


def _build_hub(args) -> DiabetesControlHub:
    return DiabetesControlHub(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VitaClaw diabetes control hub")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--data-dir", default=None, help="Shared data directory")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory name")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily-log", help="Run a daily diabetes log")
    daily.add_argument("--glucose", action="append", default=[], help="Glucose as value|context|timestamp|note")
    daily.add_argument("--weight", type=float, default=None)
    daily.add_argument("--height-cm", type=float, default=None)
    daily.add_argument("--meals-summary", default=None)
    daily.add_argument("--exercise-summary", default=None)
    daily.add_argument("--med", action="append", default=[], help="Medication as name|dose|frequency|notes")
    daily.add_argument("--adherence", default=None)
    daily.add_argument("--next-follow-up", default=None)
    daily.add_argument("--next-follow-up-details", default=None)
    daily.add_argument("--symptoms", default=None)

    weekly = subparsers.add_parser("weekly-review", help="Generate a weekly diabetes review")
    weekly.add_argument("--week-of", default=None, help="Any date inside the target week (YYYY-MM-DD)")

    subparsers.add_parser("checkup-review", help="Review diabetes-related checkup follow-up state")

    args = parser.parse_args()
    hub = _build_hub(args)

    if args.command == "daily-log":
        result = hub.daily_log(
            glucose_entries=_parse_glucose_entries(args.glucose),
            weight_kg=args.weight,
            height_cm=args.height_cm,
            meals_summary=args.meals_summary,
            exercise_summary=args.exercise_summary,
            medications=args.med,
            adherence=args.adherence,
            next_follow_up=args.next_follow_up,
            next_follow_up_details=args.next_follow_up_details,
            symptoms=args.symptoms,
        )
    elif args.command == "weekly-review":
        result = hub.weekly_review(week_of=args.week_of)
    else:
        result = hub.checkup_review()

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(result["markdown"])


if __name__ == "__main__":
    main()
