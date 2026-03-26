#!/usr/bin/env python3
"""Generate a doctor-ready visit summary from VitaClaw health data."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills._shared.health_visit_summary import HealthVisitSummary  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate doctor-ready visit summary (Markdown/HTML/PDF)"
    )
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--person-id", default=None, help="Person ID (e.g. mom, dad)")
    parser.add_argument("--days", type=int, default=30, help="Number of days to include (default: 30)")
    parser.add_argument(
        "--format",
        choices=("markdown", "html", "pdf"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument("--output", default=None, help="Output file path (optional)")
    parser.add_argument("--no-write", action="store_true", help="Do not write output file")
    args = parser.parse_args()

    try:
        summary = HealthVisitSummary(
            data_dir=args.data_dir,
            person_id=args.person_id,
            workspace_root=args.workspace_root or ROOT,
            memory_dir=args.memory_dir,
        )
        result = summary.generate(
            days=args.days,
            format=args.format,
            write=not args.no_write,
        )

        # Handle custom output path
        if args.output and result.get("content"):
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            print(f"已写入: {args.output}")
        elif result.get("path"):
            print(f"已写入: {result['path']}")

        # Print content to stdout for markdown format
        if args.format == "markdown":
            print(result["content"])

        # Notify about PDF fallback
        if args.format == "pdf" and result.get("format") == "html":
            print(
                "[提示] weasyprint 未安装，已回退为 HTML 格式。"
                "安装 weasyprint 后可生成 PDF。",
                file=sys.stderr,
            )

    except Exception as e:
        print(f"[错误] 生成就诊摘要失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
