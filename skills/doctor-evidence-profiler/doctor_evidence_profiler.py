#!/usr/bin/env python3
"""CLI for conservative public doctor evidence profiling."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from doctor_matching import DoctorEvidenceProfiler, load_json_file  # noqa: E402


def _load_doctor(args) -> dict:
    if args.doctor_json:
        return load_json_file(args.doctor_json)
    return {
        "name": args.name,
        "english_name": args.english_name,
        "hospital": args.hospital,
        "department": args.department,
        "specialties": args.specialties,
        "official_profile_url": args.profile_url,
        "pubmed_query": args.pubmed_query,
    }


def _load_patient(args) -> dict | None:
    if args.patient_json:
        return load_json_file(args.patient_json)
    if not any([args.patient_condition, args.patient_goal, args.patient_finding]):
        return None
    return {
        "conditions": args.patient_condition,
        "goals": args.patient_goal,
        "abnormal_findings": args.patient_finding,
    }


def _markdown(result: dict) -> str:
    lines = [f"# Doctor Evidence Profile -- {result.get('doctor_name', 'Unknown')}", ""]
    lines.append("## 公开简介画像")
    lines.append("")
    for item in result.get("profile_summary", []) or ["- 暂无。"]:
        lines.append(item if item.startswith("- ") else f"- {item}")
    lines.append("")
    lines.append("## 学术与证据信号")
    lines.append("")
    lines.append(f"- Evidence signal: {result.get('evidence_signal', 'limited')}")
    lines.append(f"- PubMed query: {result.get('pubmed_query', 'not used')}")
    lines.append(f"- Paper count: {result.get('paper_count', 0)}")
    lines.append(f"- Relevant paper count: {result.get('relevant_paper_count', 0)}")
    lines.append("")
    lines.append("## 代表论文")
    lines.append("")
    papers = result.get("selected_papers") or []
    if not papers:
        lines.append("- 暂无。")
    for paper in papers[:5]:
        title = paper.get("title", "Untitled")
        year = paper.get("year", "?")
        journal = paper.get("journal", "?")
        lines.append(f"- {title} ({journal}, {year})")
        if paper.get("matched_terms"):
            lines.append(f"  匹配主题：{', '.join(paper['matched_terms'])}")
    if result.get("notes"):
        lines.append("")
        lines.append("## 局限")
        lines.append("")
        for note in result["notes"]:
            lines.append(f"- {note}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a public doctor evidence profile")
    parser.add_argument("--doctor-json", default=None)
    parser.add_argument("--patient-json", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--english-name", default=None)
    parser.add_argument("--hospital", default=None)
    parser.add_argument("--department", default=None)
    parser.add_argument("--specialty", action="append", dest="specialties", default=[])
    parser.add_argument("--profile-url", default=None)
    parser.add_argument("--pubmed-query", default=None)
    parser.add_argument("--patient-condition", action="append", default=[])
    parser.add_argument("--patient-goal", action="append", default=[])
    parser.add_argument("--patient-finding", action="append", default=[])
    parser.add_argument("--pubmed-mode", choices=("off", "auto", "required"), default="auto")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    result = DoctorEvidenceProfiler().profile(
        _load_doctor(args),
        patient_profile=_load_patient(args),
        pubmed_mode=args.pubmed_mode,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(_markdown(result))


if __name__ == "__main__":
    main()
