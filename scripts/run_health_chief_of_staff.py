#!/usr/bin/env python3
"""Chief-led team entrypoint for VitaClaw Iteration 3."""

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

from health_team_runtime import HealthTeamOrchestrator  # noqa: E402
from doctor_profile_harvester import (  # noqa: E402
    DoctorProfileHarvester,
    load_sources_file,
    merge_doctor_candidates,
)


def _parse_packages(raw: str | None) -> list[str]:
    if not raw:
        return ["core"]
    result = []
    for item in raw.split(","):
        clean = item.strip()
        if clean and clean not in result:
            result.append(clean)
    return result or ["core"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run chief-led VitaClaw team workflows")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--workspace-root", default=None, help="Workspace root")
    parser.add_argument("--patients-root", default=None, help="Patients archive root")
    parser.add_argument("--patient-id", default=None, help="Patient id / archive directory")
    parser.add_argument("--packages", default="core", help="Comma-separated packages: core,family-care,oncology,labs")
    parser.add_argument("--context", choices=("direct", "group", "public"), default="direct", help="Conversation context")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")

    subparsers = parser.add_subparsers(dest="command", required=True)

    bp = subparsers.add_parser("hypertension-daily", help="Run chief-led hypertension daily workflow")
    bp.add_argument("--systolic", type=int, default=None)
    bp.add_argument("--diastolic", type=int, default=None)
    bp.add_argument("--pulse", type=int, default=None)
    bp.add_argument("--context-label", default="home")
    bp.add_argument("--timestamp", default=None)
    bp.add_argument("--diet-summary", default=None)
    bp.add_argument("--exercise-summary", default=None)
    bp.add_argument("--symptoms", default=None)
    bp.add_argument("--medication", action="append", dest="medications", default=[])
    bp.add_argument("--adherence", default=None)
    bp.add_argument("--next-refill", default=None)
    bp.add_argument("--stock-coverage-days", type=int, default=None)
    bp.add_argument("--next-follow-up", default=None)
    bp.add_argument("--next-follow-up-details", default=None)

    dm = subparsers.add_parser("diabetes-daily", help="Run chief-led diabetes workflow")
    dm.add_argument("--glucose", action="append", default=[], help="value|context|timestamp")
    dm.add_argument("--weight-kg", type=float, default=None)
    dm.add_argument("--height-cm", type=float, default=None)
    dm.add_argument("--meals-summary", default=None)
    dm.add_argument("--exercise-summary", default=None)
    dm.add_argument("--medication", action="append", dest="medications", default=[])
    dm.add_argument("--adherence", default=None)
    dm.add_argument("--next-follow-up", default=None)
    dm.add_argument("--next-follow-up-details", default=None)

    ck = subparsers.add_parser("annual-checkup", help="Run chief-led annual checkup workflow")
    ck.add_argument("--report-date", required=True)
    ck.add_argument("--item", action="append", default=[], help="category|item|value|unit|reference_range|status")
    ck.add_argument("--next-follow-up", default=None)
    ck.add_argument("--next-follow-up-details", default=None)

    doctor = subparsers.add_parser("doctor-match", help="Run chief-led doctor matching workflow")
    doctor.add_argument("--patient-json", required=True)
    doctor.add_argument("--doctors-json", default=None)
    doctor.add_argument("--doctor-seeds-json", default=None)
    doctor.add_argument("--harvest-mode", choices=("auto", "static", "browser"), default="auto")
    doctor.add_argument("--harvest-output", default=None)
    doctor.add_argument("--top-n", type=int, default=5)
    doctor.add_argument("--pubmed-mode", choices=("off", "auto", "required"), default="auto")

    subparsers.add_parser("heartbeat", help="Run chief-led team heartbeat")
    return parser


def _parse_glucose(entries: list[str]) -> list[dict]:
    result = []
    for raw in entries:
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) < 2:
            continue
        try:
            value = float(parts[0])
        except ValueError:
            continue
        result.append(
            {
                "value": value,
                "context": parts[1],
                "timestamp": parts[2] if len(parts) > 2 and parts[2] else None,
            }
        )
    return result


def _parse_checkup_items(entries: list[str]) -> list[dict]:
    result = []
    for raw in entries:
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) < 6:
            continue
        result.append(
            {
                "category": parts[0],
                "item": parts[1],
                "value": parts[2],
                "unit": parts[3],
                "reference_range": parts[4],
                "status": parts[5],
            }
        )
    return result


def _load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_or_harvest_doctors(args) -> tuple[list[dict], dict | None]:
    doctors = _load_json(args.doctors_json) if args.doctors_json else []
    harvest_result = None
    if args.doctor_seeds_json:
        harvest_result = DoctorProfileHarvester().harvest_sources(
            load_sources_file(args.doctor_seeds_json),
            mode=args.harvest_mode,
        )
        doctors = merge_doctor_candidates(doctors, harvest_result["candidates"])
        if args.harvest_output:
            Path(args.harvest_output).write_text(
                json.dumps(doctors, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    return doctors, harvest_result


def _render_markdown(result: dict) -> str:
    lines = [f"# Health Chief Of Staff -- {result.get('scenario', 'heartbeat')}", ""]
    lines.append("## Team")
    lines.append("")
    lines.append(f"- Routed roles: {', '.join(result.get('routed_roles', [])) or 'none'}")
    lines.append(f"- Team board: {result.get('team_board_path', 'pending')}")
    lines.append(f"- Chief summary: {result.get('chief_summary_path', 'pending')}")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append(f"- Scenario output: {result.get('output_path', 'pending')}")
    lines.append(f"- Dispatch log: {result.get('dispatch_log_path', 'pending')}")
    if result.get("writebacks"):
        for item in result["writebacks"]:
            lines.append(f"- Writeback: {item}")
    lines.append("")
    lines.append("## Follow-up")
    lines.append("")
    for task in result.get("follow_up_tasks", []) or [{"title": "none", "next_step": "当前没有新增 follow-up。"}]:
        lines.append(f"- {task.get('title', 'pending')}: {task.get('next_step', 'pending')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    orchestrator = HealthTeamOrchestrator(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
        patients_root=args.patients_root,
        patient_id=args.patient_id,
        packages=_parse_packages(args.packages),
    )

    if args.command == "hypertension-daily":
        result = orchestrator.dispatch_flagship_scenario(
            "hypertension-daily-copilot",
            payload={
                "systolic": args.systolic,
                "diastolic": args.diastolic,
                "pulse": args.pulse,
                "context": args.context_label,
                "timestamp": args.timestamp,
                "diet_summary": args.diet_summary,
                "exercise_summary": args.exercise_summary,
                "symptoms": args.symptoms,
                "medications": args.medications,
                "adherence": args.adherence,
                "next_refill": args.next_refill,
                "stock_coverage_days": args.stock_coverage_days,
                "next_follow_up": args.next_follow_up,
                "next_follow_up_details": args.next_follow_up_details,
            },
            context=args.context,
        )
    elif args.command == "diabetes-daily":
        result = orchestrator.dispatch_flagship_scenario(
            "diabetes-control-hub",
            payload={
                "glucose_entries": _parse_glucose(args.glucose),
                "weight_kg": args.weight_kg,
                "height_cm": args.height_cm,
                "meals_summary": args.meals_summary,
                "exercise_summary": args.exercise_summary,
                "medications": args.medications,
                "adherence": args.adherence,
                "next_follow_up": args.next_follow_up,
                "next_follow_up_details": args.next_follow_up_details,
            },
            context=args.context,
        )
    elif args.command == "annual-checkup":
        result = orchestrator.dispatch_flagship_scenario(
            "annual-checkup-advisor",
            payload={
                "items": _parse_checkup_items(args.item),
                "report_date": args.report_date,
                "next_follow_up": args.next_follow_up,
                "next_follow_up_details": args.next_follow_up_details,
            },
            context=args.context,
        )
    elif args.command == "doctor-match":
        if not args.doctors_json and not args.doctor_seeds_json:
            parser.error("doctor-match requires --doctors-json or --doctor-seeds-json")
        doctors, harvest_result = _load_or_harvest_doctors(args)
        result = orchestrator.dispatch_flagship_scenario(
            "doctor-fit-finder",
            payload={
                "patient_profile": _load_json(args.patient_json),
                "doctors": doctors,
                "top_n": args.top_n,
                "pubmed_mode": args.pubmed_mode,
            },
            context=args.context,
        )
        if harvest_result is not None:
            result["harvest"] = harvest_result
            result["harvested_candidate_count"] = len(harvest_result["candidates"])
    else:
        result = orchestrator.run_team_heartbeat()
        result["scenario"] = "team-heartbeat"

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(_render_markdown(result))


if __name__ == "__main__":
    main()
