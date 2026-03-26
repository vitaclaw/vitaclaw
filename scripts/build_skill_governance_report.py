#!/usr/bin/env python3
"""Build governance reports with A-F quality scoring for VitaClaw skills."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from skill_catalog import build_manifest_records, manifest_summary, repo_root, write_json


# ---------------------------------------------------------------------------
# Quality scoring
# ---------------------------------------------------------------------------

GRADE_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0, "F"),
]

_BARE_EXCEPT_RE = re.compile(r"^\s*except\s*:", re.MULTILINE)


def _score_to_grade(score: float) -> str:
    """Convert a percentage score to an A-F grade."""
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _check_bare_excepts(skill_dir: Path) -> bool:
    """Return True if any Python file in skill_dir has bare except clauses."""
    for py_file in skill_dir.rglob("*.py"):
        if not py_file.is_file():
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _BARE_EXCEPT_RE.search(text):
            return True
    return False


def _check_ruff(skill_dir: Path) -> bool | None:
    """Run ruff check on skill's Python files. Returns True if clean, False if errors, None if ruff unavailable."""
    py_files = [str(p) for p in skill_dir.rglob("*.py") if p.is_file()]
    if not py_files:
        return None
    try:
        result = subprocess.run(
            ["ruff", "check", "--quiet"] + py_files,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _check_proprietary_conflicts(record: dict) -> bool:
    """Return True if there are proprietary copyright conflicts."""
    evidence = record.get("license_evidence") or ""
    return "proprietary" in evidence.lower()


def compute_quality_score(record: dict) -> dict:
    """Score a skill on 7 quality dimensions and assign an A-F grade.

    For prompt-only skills (no Python), code-related dimensions are scored
    as N/A and excluded from the weighted total.
    """
    skill_dir = repo_root() / record["path"]
    has_code = record.get("has_code", False)

    # Define dimensions: (name, weight, value_or_none)
    # value is True (pass), False (fail), or None (N/A)
    dimensions: dict[str, dict] = {}

    # (1) Frontmatter completeness (20%)
    frontmatter_ok = record.get("frontmatter_valid", False)
    dimensions["frontmatter"] = {"weight": 20, "value": frontmatter_ok, "label": "Frontmatter"}

    # (2) Has Python implementation (15%)
    if has_code:
        dimensions["code"] = {"weight": 15, "value": True, "label": "Code"}
    else:
        dimensions["code"] = {"weight": 15, "value": None, "label": "Code"}

    # (3) Has tests (20%)
    if has_code:
        dimensions["tests"] = {"weight": 20, "value": record.get("has_tests", False), "label": "Tests"}
    else:
        dimensions["tests"] = {"weight": 20, "value": None, "label": "Tests"}

    # (4) Code passes ruff (15%)
    if has_code:
        ruff_result = _check_ruff(skill_dir)
        dimensions["lint"] = {"weight": 15, "value": ruff_result, "label": "Lint"}
    else:
        dimensions["lint"] = {"weight": 15, "value": None, "label": "Lint"}

    # (5) SKILL.md description length >50 chars (10%)
    description = record.get("description") or ""
    dimensions["docs"] = {"weight": 10, "value": len(description) > 50, "label": "Docs"}

    # (6) No bare except clauses (10%)
    if has_code:
        has_bare = _check_bare_excepts(skill_dir)
        dimensions["no_bare_except"] = {"weight": 10, "value": not has_bare, "label": "NoBarExcept"}
    else:
        dimensions["no_bare_except"] = {"weight": 10, "value": None, "label": "NoBarExcept"}

    # (7) No proprietary copyright conflicts (10%)
    has_conflict = _check_proprietary_conflicts(record)
    dimensions["license"] = {"weight": 10, "value": not has_conflict, "label": "License"}

    # Calculate weighted score, excluding N/A dimensions
    issues: list[str] = []
    applicable_weight = 0
    earned_weight = 0

    for dim_key, dim in dimensions.items():
        val = dim["value"]
        if val is None:
            continue  # N/A, excluded from scoring
        applicable_weight += dim["weight"]
        if val:
            earned_weight += dim["weight"]
        else:
            issues.append(f"{dim['label']}: failed")

    if applicable_weight > 0:
        score = (earned_weight / applicable_weight) * 100
    else:
        score = 100.0  # All dimensions N/A -- no issues detected

    grade = _score_to_grade(score)

    return {
        "score": round(score, 1),
        "grade": grade,
        "dimensions": {
            k: {"pass": v["value"], "weight": v["weight"], "label": v["label"]}
            for k, v in dimensions.items()
        },
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Quality report generation
# ---------------------------------------------------------------------------

def _dim_indicator(dim_result: dict) -> str:
    """Return a single-char indicator for a dimension result."""
    val = dim_result.get("pass")
    if val is None:
        return "N/A"
    return "Y" if val else "N"


def generate_quality_report_markdown(records: list[dict], scores: list[dict]) -> str:
    """Generate a markdown quality report sorted worst-first."""
    # Pair records with scores and sort by score ascending (worst first)
    paired = sorted(zip(records, scores), key=lambda p: p[1]["score"])

    # Grade distribution
    grade_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for _, s in paired:
        grade_counts[s["grade"]] = grade_counts.get(s["grade"], 0) + 1

    lines: list[str] = []
    lines.append("# Skill Quality Scores")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"**Total skills:** {len(paired)}")
    lines.append("")
    lines.append("## Grade Distribution")
    lines.append("")
    for grade in ["A", "B", "C", "D", "F"]:
        lines.append(f"- **{grade}:** {grade_counts[grade]}")
    lines.append("")
    lines.append("## Quality Scores")
    lines.append("")
    lines.append("| Skill | Grade | Score | Frontmatter | Code | Tests | Lint | Docs | Issues |")
    lines.append("|-------|-------|-------|-------------|------|-------|------|------|--------|")

    for record, score in paired:
        dims = score["dimensions"]
        issues_str = "; ".join(score["issues"]) if score["issues"] else "-"
        lines.append(
            f"| {record['slug']} "
            f"| {score['grade']} "
            f"| {score['score']:.0f}% "
            f"| {_dim_indicator(dims['frontmatter'])} "
            f"| {_dim_indicator(dims['code'])} "
            f"| {_dim_indicator(dims['tests'])} "
            f"| {_dim_indicator(dims['lint'])} "
            f"| {_dim_indicator(dims['docs'])} "
            f"| {issues_str} |"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Original governance reports
# ---------------------------------------------------------------------------

def build_health_core_report(records: list[dict]) -> dict:
    health_core = [record for record in records if record["governance_scope"] == "health-core"]
    return {
        "summary": manifest_summary(health_core),
        "skills": [
            {
                "slug": record["slug"],
                "path": record["path"],
                "distribution_tier": record["distribution_tier"],
                "audit_status": record["audit_status"],
                "license_evidence": record["license_evidence"],
                "user_invocable": record["user_invocable"],
                "allowed_tools": record["allowed_tools"],
                "category": record["category"],
                "frontmatter_valid": record["frontmatter_valid"],
                "frontmatter_validation_errors": record["frontmatter_validation_errors"],
            }
            for record in sorted(health_core, key=lambda item: (item["distribution_tier"] or "", item["slug"]))
        ],
    }


def build_out_of_scope_report(records: list[dict]) -> dict:
    out_of_scope = [record for record in records if record["governance_scope"] == "out-of-scope"]
    return {
        "summary": manifest_summary(out_of_scope),
        "skills": [
            {
                "slug": record["slug"],
                "path": record["path"],
                "frontmatter_valid": record["frontmatter_valid"],
                "frontmatter_validation_errors": record["frontmatter_validation_errors"],
            }
            for record in sorted(out_of_scope, key=lambda item: item["slug"])
            if not record["frontmatter_valid"]
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build skill governance reports")
    parser.add_argument(
        "--output",
        default="reports/skill-governance-report.json",
        help="Output report path relative to repo root",
    )
    parser.add_argument(
        "--quality-report",
        action="store_true",
        help="Generate A-F quality scores report",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        dest="output_format",
        help="Output format for quality report (default: markdown)",
    )
    args = parser.parse_args()

    records = build_manifest_records()

    if args.quality_report:
        # Compute quality scores for all skills
        scores = [compute_quality_score(record) for record in records]

        # Generate markdown report
        md_content = generate_quality_report_markdown(records, scores)
        md_path = repo_root() / "reports" / "skill-quality-scores.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_content, encoding="utf-8")
        print(f"Quality report written to {md_path}")

        # Grade distribution summary
        grade_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for s in scores:
            grade_counts[s["grade"]] = grade_counts.get(s["grade"], 0) + 1
        print(f"  Total skills: {len(scores)}")
        for grade in ["A", "B", "C", "D", "F"]:
            print(f"  {grade}: {grade_counts[grade]}")

        if args.output_format == "json":
            json_payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "total_skills": len(scores),
                "grade_distribution": grade_counts,
                "skills": [
                    {
                        "slug": record["slug"],
                        "path": record["path"],
                        **score,
                    }
                    for record, score in sorted(
                        zip(records, scores), key=lambda p: p[1]["score"]
                    )
                ],
            }
            json_path = repo_root() / "reports" / "skill-quality-scores.json"
            write_json(json_path, json_payload)
            print(f"JSON quality report written to {json_path}")
    else:
        # Original governance report
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "repo_root": str(repo_root()),
            "summary": manifest_summary(records),
            "health_core": build_health_core_report(records),
            "out_of_scope_audit": build_out_of_scope_report(records),
        }
        write_json(repo_root() / args.output, payload)


if __name__ == "__main__":
    main()
