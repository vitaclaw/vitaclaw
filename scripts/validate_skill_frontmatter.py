#!/usr/bin/env python3
"""Validate SKILL.md frontmatter against VitaClaw's standard contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from skill_catalog import (
    REQUIRED_FRONTMATTER_KEYS,
    build_manifest_records,
    manifest_summary,
    repo_root,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate VitaClaw SKILL.md frontmatter")
    parser.add_argument(
        "--scope",
        choices=["all", "health-core", "out-of-scope"],
        default="all",
        help="Restrict validation to a governance scope",
    )
    parser.add_argument(
        "--output",
        default="reports/skill-frontmatter-report.json",
        help="Report path relative to the repo root",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with status 1 when any skill fails validation",
    )
    args = parser.parse_args()

    records = build_manifest_records()
    if args.scope != "all":
        records = [record for record in records if record["governance_scope"] == args.scope]

    invalid = [
        {
            "slug": record["slug"],
            "path": record["path"],
            "governance_scope": record["governance_scope"],
            "distribution_tier": record.get("distribution_tier"),
            "parse_errors": record["frontmatter_parse_errors"],
            "validation_errors": record["frontmatter_validation_errors"],
        }
        for record in records
        if not record["frontmatter_valid"]
    ]

    payload = {
        "scope": args.scope,
        "required_keys": REQUIRED_FRONTMATTER_KEYS,
        "summary": manifest_summary(records),
        "invalid_count": len(invalid),
        "invalid_skills": invalid,
    }
    output_path = repo_root() / args.output
    write_json(output_path, payload)

    print(f"frontmatter report written to {output_path}")
    print(f"  invalid skills: {len(invalid)} / {len(records)}")
    if invalid:
        for entry in invalid[:20]:
            problems = entry["parse_errors"] + entry["validation_errors"]
            print(f"  - {entry['slug']}: {', '.join(problems)}")
        if len(invalid) > 20:
            print(f"  ... and {len(invalid) - 20} more")

    if args.fail_on_error and invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
