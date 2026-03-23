#!/usr/bin/env python3
"""CLI for routing a patient problem to likely departments."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from doctor_matching import DepartmentFitRouter, load_json_file  # noqa: E402


def _load_patient(args) -> dict:
    if args.patient_json:
        return load_json_file(args.patient_json)
    return {
        "conditions": args.conditions,
        "symptoms": args.symptoms,
        "abnormal_findings": args.abnormal_findings,
        "goals": args.goals,
        "city": args.city,
        "district": args.district,
        "summary": args.summary,
    }


def _markdown(result: dict) -> str:
    lines = ["# Department Fit Router", ""]
    lines.append("## 推荐科室")
    lines.append("")
    for item in result.get("recommendations", []):
        lines.append(f"- {item['department']} (score {item['score']})")
        lines.append(f"  原因：{item['reason']}")
        if item.get("matched_terms"):
            lines.append(f"  命中线索：{', '.join(item['matched_terms'])}")
        lines.append(f"  就诊前准备：{item['preparation']}")
    lines.append("")
    lines.append("## 必须就医")
    lines.append("")
    must_seek = result.get("must_seek_care") or ["- 当前未触发先急诊后匹配的红旗信号。"]
    for item in must_seek:
        lines.append(item if item.startswith("- ") else f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Route a health problem to suitable departments")
    parser.add_argument("--patient-json", default=None)
    parser.add_argument("--condition", action="append", dest="conditions", default=[])
    parser.add_argument("--symptom", action="append", dest="symptoms", default=[])
    parser.add_argument("--abnormal-finding", action="append", dest="abnormal_findings", default=[])
    parser.add_argument("--goal", action="append", dest="goals", default=[])
    parser.add_argument("--city", default=None)
    parser.add_argument("--district", default=None)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    result = DepartmentFitRouter().route(_load_patient(args), top_n=args.top_n)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(_markdown(result))


if __name__ == "__main__":
    main()
