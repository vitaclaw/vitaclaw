#!/usr/bin/env python3
"""Generate an annual health report from VitaClaw health data."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills._shared.health_annual_report import HealthAnnualReport  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive annual health report (HTML)",
    )
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--person-id", default=None, help="Person ID (e.g. mom, dad)")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Report year (default: current year)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: memory/health/files/annual-report-{year}.html)",
    )
    parser.add_argument(
        "--format",
        choices=("html", "json"),
        default="html",
        help="Output format (default: html)",
    )
    args = parser.parse_args()

    try:
        report = HealthAnnualReport(
            data_dir=args.data_dir,
            person_id=args.person_id,
            workspace_root=args.workspace_root,
            memory_dir=args.memory_dir,
            year=args.year,
        )
        result = report.generate(write=True)

        # Override output path if specified
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            result["path"] = args.output

        if args.format == "json":
            print(json.dumps(
                {"path": result["path"], "format": result["format"]},
                ensure_ascii=False,
                indent=2,
            ))
        else:
            print(f"年度健康报告已生成: {result['path']}")

    except Exception as e:
        print(f"[ERROR] 报告生成失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
