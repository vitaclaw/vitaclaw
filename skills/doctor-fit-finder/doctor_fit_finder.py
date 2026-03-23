#!/usr/bin/env python3
"""CLI for public doctor matching and ranking."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from doctor_matching import DoctorFitFinder, load_json_file  # noqa: E402


def _markdown(result: dict) -> str:
    lines = ["# Doctor Fit Finder", ""]
    lines.append("## 推荐科室")
    lines.append("")
    for item in result["route_result"].get("recommendations", []):
        lines.append(f"- {item['department']} (score {item['score']})")
        lines.append(f"  原因：{item['reason']}")
    lines.append("")
    lines.append("## Shortlist")
    lines.append("")
    for index, item in enumerate(result.get("ranked_doctors", []), start=1):
        doctor = item["doctor"]
        lines.append(
            f"- Top {index}: {doctor.get('name', 'Unknown')} | {doctor.get('hospital', 'Unknown')} | "
            f"{doctor.get('department', 'Unknown')} | score {item['score']}"
        )
        for reason in item.get("reasons", [])[:4]:
            lines.append(f"  推荐理由：{reason}")
        for concern in item.get("concerns", [])[:2]:
            lines.append(f"  注意：{concern}")
    if result["route_result"].get("must_seek_care"):
        lines.append("")
        lines.append("## 必须就医")
        lines.append("")
        for item in result["route_result"]["must_seek_care"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank public doctor candidates for a patient profile")
    parser.add_argument("--patient-json", required=True)
    parser.add_argument("--doctors-json", required=True)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--pubmed-mode", choices=("off", "auto", "required"), default="auto")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    patient = load_json_file(args.patient_json)
    doctors = load_json_file(args.doctors_json)
    result = DoctorFitFinder().rank(
        patient_profile=patient,
        doctors=doctors,
        top_n=args.top_n,
        pubmed_mode=args.pubmed_mode,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(_markdown(result))


if __name__ == "__main__":
    main()
