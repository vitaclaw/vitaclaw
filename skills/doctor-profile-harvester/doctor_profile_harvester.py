#!/usr/bin/env python3
"""CLI for harvesting public doctor profiles before ranking."""

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

from doctor_profile_harvester import (  # noqa: E402
    DoctorProfileHarvester,
    load_sources_file,
    render_harvest_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Harvest public doctor profiles from hospital pages")
    parser.add_argument("--sources-json", required=True)
    parser.add_argument("--mode", choices=("auto", "static", "browser"), default="auto")
    parser.add_argument("--limit-per-source", type=int, default=None)
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    result = DoctorProfileHarvester().harvest_sources(
        load_sources_file(args.sources_json),
        mode=args.mode,
        per_source_limit=args.limit_per_source,
    )
    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(result["candidates"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(render_harvest_markdown(result))


if __name__ == "__main__":
    main()
