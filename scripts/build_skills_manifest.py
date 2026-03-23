#!/usr/bin/env python3
"""Build the canonical skills manifest for VitaClaw."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from skill_catalog import build_manifest_records, manifest_summary, repo_root, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VitaClaw skills manifest")
    parser.add_argument(
        "--output",
        default="skills-manifest.json",
        help="Output JSON file path relative to the repo root",
    )
    args = parser.parse_args()

    records = build_manifest_records()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(repo_root()),
        "summary": manifest_summary(records),
        "skills": records,
    }

    output_path = repo_root() / args.output
    write_json(output_path, payload)

    summary = payload["summary"]
    print(f"skills-manifest written to {output_path}")
    print(f"  total skills        : {summary['skill_count']}")
    print(f"  health skills       : {summary['health_skill_count']}")
    print(f"  with frontmatter    : {summary['with_frontmatter']}")
    print(f"  frontmatter valid   : {summary['frontmatter_valid']}")
    print(f"  with code           : {summary['with_code']}")
    print(f"  with cli entrypoint : {summary['with_cli_entrypoints']}")
    print(f"  with tests          : {summary['with_tests']}")


if __name__ == "__main__":
    main()
