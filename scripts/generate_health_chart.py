#!/usr/bin/env python3
"""Generate health metric trend charts via CLI.

Usage:
    python scripts/generate_health_chart.py --metric bp --days 30
    python scripts/generate_health_chart.py --metric glucose --days 90 --format json
    python scripts/generate_health_chart.py --metric sleep --days 7 --person-id mom
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "_shared"))

from health_chart_engine import HealthChartEngine  # noqa: E402

_METRIC_NAMES = {
    "bp": "Blood Pressure",
    "glucose": "Blood Glucose",
    "weight": "Weight",
    "sleep": "Sleep",
}

_METRIC_NAMES_ZH = {
    "bp": "血压",
    "glucose": "血糖",
    "weight": "体重",
    "sleep": "睡眠",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate health metric trend charts")
    parser.add_argument(
        "--metric",
        required=True,
        choices=["bp", "glucose", "weight", "sleep"],
        help="Health metric to chart",
    )
    parser.add_argument("--days", type=int, default=30, help="Time range in days (default: 30)")
    parser.add_argument("--person-id", default=None, help="Person ID (default: self)")
    parser.add_argument("--data-dir", default=None, help="Data directory override")
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "json"],
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    engine = HealthChartEngine(data_dir=args.data_dir, person_id=args.person_id)

    # Dispatch to the correct chart generator
    generators = {
        "bp": engine.generate_blood_pressure_chart,
        "glucose": engine.generate_blood_glucose_chart,
        "weight": engine.generate_weight_chart,
        "sleep": engine.generate_sleep_chart,
    }

    chart_path = generators[args.metric](days=args.days)

    if not chart_path:
        metric_zh = _METRIC_NAMES_ZH[args.metric]
        print(
            f"[WARN] No {metric_zh} data found for the past {args.days} days.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.format == "json":
        result = {
            "metric": args.metric,
            "metric_name": _METRIC_NAMES[args.metric],
            "metric_name_zh": _METRIC_NAMES_ZH[args.metric],
            "days": args.days,
            "person_id": args.person_id or "self",
            "path": chart_path,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        metric_zh = _METRIC_NAMES_ZH[args.metric]
        print(f"## {metric_zh}趋势图 (近{args.days}天)")
        print()
        print(f"Chart saved: `{chart_path}`")
        print()
        print(f"![{metric_zh}趋势]({chart_path})")


if __name__ == "__main__":
    main()
