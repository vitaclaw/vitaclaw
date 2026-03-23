#!/usr/bin/env python3
"""Build Iteration 1 governance reports for health-core and out-of-scope skills."""

from __future__ import annotations

import argparse
from datetime import datetime

from skill_catalog import build_manifest_records, manifest_summary, repo_root, write_json


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build skill governance reports")
    parser.add_argument(
        "--output",
        default="reports/skill-governance-report.json",
        help="Output report path relative to repo root",
    )
    args = parser.parse_args()

    records = build_manifest_records()
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
