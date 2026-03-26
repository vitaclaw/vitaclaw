#!/usr/bin/env python3
"""Import Huawei Health export data into HealthDataStore JSONL records."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills._shared.huawei_health_importer import HuaweiHealthImporter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Huawei Health data from a Settings export ZIP file"
    )
    parser.add_argument("export_zip", help="Path to Huawei Health export ZIP file")
    parser.add_argument("--person-id", default=None, help="Person ID for family multi-person support")
    parser.add_argument("--start-date", default=None, help="Optional start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Optional end date YYYY-MM-DD")
    parser.add_argument("--data-dir", default=None, help="Override data storage directory")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    importer = HuaweiHealthImporter(
        data_dir=args.data_dir,
        person_id=args.person_id,
    )

    result = importer.import_export(
        export_path=args.export_zip,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    # Markdown output
    print("# Huawei Health Import Summary\n")
    print(f"- Records imported: {result.get('imported', 0)}")
    print(f"- Duplicates skipped: {result.get('skipped_dupes', 0)}")
    if result.get("by_type"):
        print("\n## By Type\n")
        for rec_type, count in sorted(result["by_type"].items()):
            print(f"- {rec_type}: {count}")
    errors = result.get("errors", [])
    if errors:
        print("\n## Errors\n")
        for err in errors:
            print(f"- {err}")
    if not errors:
        print("\nImport completed successfully.")


if __name__ == "__main__":
    main()
