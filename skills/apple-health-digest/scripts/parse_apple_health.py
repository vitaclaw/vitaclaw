#!/usr/bin/env python3
"""
parse_apple_health.py — Parse Apple Health export.xml and generate Markdown reports.

Usage:
    python3 parse_apple_health.py "<export.xml>" "<patient_name>" "<output_dir>"

Arguments:
    export.xml     Path to the Apple Health export.xml file
    patient_name   Patient name (used in report headers)
    output_dir     Directory to write Markdown report files

Outputs Markdown files to output_dir and prints a JSON summary to stdout.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def parse_apple_date(date_str: str) -> datetime | None:
    """Parse Apple Health date format: '2025-01-15 08:30:00 +0800'."""
    # Strip timezone offset and parse the datetime portion
    # Apple Health uses format: YYYY-MM-DD HH:MM:SS ±HHMM
    try:
        # Remove the timezone offset for naive datetime parsing
        parts = date_str.strip().rsplit(" ", 1)
        if len(parts) == 2:
            dt_str, _ = parts
        else:
            dt_str = date_str.strip()
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, IndexError):
        return None


def format_date(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD."""
    return dt.strftime("%Y-%m-%d")


def format_date_key(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD for use as dict key."""
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

METRIC_TYPES = {
    "HKQuantityTypeIdentifierHeartRate": "heart_rate",
    "HKQuantityTypeIdentifierBloodPressureSystolic": "bp_systolic",
    "HKQuantityTypeIdentifierBloodPressureDiastolic": "bp_diastolic",
    "HKQuantityTypeIdentifierOxygenSaturation": "spo2",
    "HKQuantityTypeIdentifierBodyMass": "weight",
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKCategoryTypeIdentifierSleepAnalysis": "sleep",
}


def collect_records(xml_path: Path) -> dict[str, list[dict]]:
    """Stream-parse the XML and collect records by metric type.

    Uses iterparse for memory efficiency with large export files.
    """
    records: dict[str, list[dict]] = defaultdict(list)

    context = ET.iterparse(str(xml_path), events=("end",))
    for event, elem in context:
        if elem.tag == "Record":
            record_type = elem.get("type", "")
            metric = METRIC_TYPES.get(record_type)
            if metric:
                start_date = parse_apple_date(elem.get("startDate", ""))
                end_date = parse_apple_date(elem.get("endDate", ""))
                value_str = elem.get("value", "")
                unit = elem.get("unit", "")

                if start_date is not None:
                    record = {
                        "start": start_date,
                        "end": end_date,
                        "value_str": value_str,
                        "unit": unit,
                    }

                    # Parse numeric value (sleep is categorical)
                    if metric != "sleep":
                        try:
                            record["value"] = float(value_str)
                        except (ValueError, TypeError):
                            record["value"] = None
                    else:
                        record["value"] = value_str

                    records[metric].append(record)

            # Free memory for processed elements
            elem.clear()

    return dict(records)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_heart_rate(records: list[dict]) -> list[dict]:
    """Aggregate heart rate to daily avg/min/max."""
    daily: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r["value"] is not None:
            key = format_date_key(r["start"])
            daily[key].append(r["value"])

    result = []
    for date_key in sorted(daily.keys()):
        values = daily[date_key]
        result.append({
            "date": date_key,
            "avg": round(sum(values) / len(values), 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "count": len(values),
        })
    return result


def aggregate_steps(records: list[dict]) -> list[dict]:
    """Aggregate steps to daily totals."""
    daily: dict[str, float] = defaultdict(float)
    for r in records:
        if r["value"] is not None:
            key = format_date_key(r["start"])
            daily[key] += r["value"]

    result = []
    for date_key in sorted(daily.keys()):
        result.append({
            "date": date_key,
            "total": int(daily[date_key]),
        })
    return result


def aggregate_weight(records: list[dict]) -> list[dict]:
    """Get last weight reading per day."""
    daily: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    for r in records:
        if r["value"] is not None:
            key = format_date_key(r["start"])
            daily[key].append((r["start"], r["value"]))

    result = []
    for date_key in sorted(daily.keys()):
        # Take the last reading of the day
        readings = sorted(daily[date_key], key=lambda x: x[0])
        last_value = readings[-1][1]
        result.append({
            "date": date_key,
            "value": round(last_value, 1),
        })
    return result


def match_blood_pressure(systolic: list[dict], diastolic: list[dict]) -> list[dict]:
    """Match systolic and diastolic readings by timestamp (within 1 minute)."""
    result = []

    # Sort both lists by start time
    sys_sorted = sorted(systolic, key=lambda r: r["start"])
    dia_sorted = sorted(diastolic, key=lambda r: r["start"])

    dia_idx = 0
    for sys_rec in sys_sorted:
        if sys_rec["value"] is None:
            continue
        sys_time = sys_rec["start"]
        best_dia = None
        best_diff = timedelta(minutes=2)  # threshold

        # Search for a matching diastolic reading within 1 minute
        while dia_idx < len(dia_sorted) and dia_sorted[dia_idx]["start"] < sys_time - timedelta(minutes=1):
            dia_idx += 1

        search_idx = dia_idx
        while search_idx < len(dia_sorted) and dia_sorted[search_idx]["start"] <= sys_time + timedelta(minutes=1):
            if dia_sorted[search_idx]["value"] is not None:
                diff = abs(dia_sorted[search_idx]["start"] - sys_time)
                if diff < best_diff:
                    best_diff = diff
                    best_dia = dia_sorted[search_idx]
            search_idx += 1

        if best_dia is not None:
            result.append({
                "date": format_date(sys_time),
                "time": sys_time.strftime("%H:%M"),
                "systolic": round(sys_rec["value"]),
                "diastolic": round(best_dia["value"]),
            })

    return result


def aggregate_spo2(records: list[dict]) -> list[dict]:
    """Get SpO2 readings, deduplicated by day (daily avg)."""
    daily: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r["value"] is not None:
            key = format_date_key(r["start"])
            # SpO2 may be stored as fraction (0.98) or percent (98)
            val = r["value"]
            if val <= 1.0:
                val = val * 100
            daily[key].append(val)

    result = []
    for date_key in sorted(daily.keys()):
        values = daily[date_key]
        result.append({
            "date": date_key,
            "avg": round(sum(values) / len(values), 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
        })
    return result


def aggregate_sleep(records: list[dict]) -> list[dict]:
    """Aggregate sleep duration by day.

    Sleep records have startDate and endDate representing a sleep interval.
    We aggregate total sleep per night (assigned to the start date).
    We skip 'InBed' entries if 'Asleep' entries are present.
    """
    # Categorize records
    asleep_records = []
    inbed_records = []

    for r in records:
        val = str(r["value_str"]).lower() if r["value_str"] else ""
        if r["start"] and r["end"]:
            if "asleep" in val:
                asleep_records.append(r)
            elif "inbed" in val or val == "1":
                inbed_records.append(r)
            else:
                # Default: treat as sleep
                asleep_records.append(r)

    # Prefer asleep records; fall back to inbed if no asleep data
    use_records = asleep_records if asleep_records else inbed_records

    daily: dict[str, float] = defaultdict(float)
    for r in use_records:
        if r["start"] and r["end"]:
            duration_hours = (r["end"] - r["start"]).total_seconds() / 3600
            if 0 < duration_hours < 24:  # sanity check
                key = format_date_key(r["start"])
                daily[key] += duration_hours

    result = []
    for date_key in sorted(daily.keys()):
        hours = daily[date_key]
        h = int(hours)
        m = int((hours - h) * 60)
        result.append({
            "date": date_key,
            "hours": round(hours, 1),
            "display": f"{h}h{m:02d}m",
        })
    return result


# ---------------------------------------------------------------------------
# Trend computation
# ---------------------------------------------------------------------------

def trend_arrow(current: float, previous: float) -> str:
    """Return a trend arrow comparing current to previous value."""
    if previous == 0:
        return "→"
    ratio = current / previous
    if ratio > 1.10:
        return "↑"
    elif ratio < 0.90:
        return "↓"
    else:
        return "→"


def weight_trend_arrow(current: float, previous: float) -> str:
    """Return a trend arrow for weight (smaller threshold: 2%)."""
    if previous == 0:
        return "→"
    ratio = current / previous
    if ratio > 1.02:
        return "↑"
    elif ratio < 0.98:
        return "↓"
    else:
        return "→"


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def file_header(title: str, patient: str, start: str, end: str) -> str:
    """Generate standard file header."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"# {title} — {patient}\n"
        f"\n"
        f"> 数据来源：Apple Health 导出\n"
        f"> 数据范围：{start} ~ {end}\n"
        f"> 生成时间：{now}\n"
        f"\n"
    )


def write_heart_rate_md(data: list[dict], patient: str, output_dir: Path) -> Path | None:
    """Write 心率趋势.md."""
    if not data:
        return None

    # Limit to last 180 days
    cutoff = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    recent = [d for d in data if d["date"] >= cutoff]
    if not recent:
        recent = data[-180:]  # fallback: last 180 entries

    path = output_dir / "心率趋势.md"
    start_date = recent[0]["date"]
    end_date = recent[-1]["date"]

    lines = [file_header("心率趋势", patient, start_date, end_date)]
    lines.append("| 日期 | 平均心率(bpm) | 最低 | 最高 | 测量次数 |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")

    for row in recent:
        lines.append(
            f"| {row['date']} | {row['avg']} | {row['min']} | {row['max']} | {row['count']} |\n"
        )

    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_bp_md(data: list[dict], patient: str, output_dir: Path) -> Path | None:
    """Write 血压记录.md."""
    if not data:
        return None

    path = output_dir / "血压记录.md"
    start_date = data[0]["date"]
    end_date = data[-1]["date"]

    lines = [file_header("血压记录", patient, start_date, end_date)]
    lines.append("| 日期 | 时间 | 收缩压(mmHg) | 舒张压(mmHg) | 评估 |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")

    for row in data:
        assessment = ""
        if row["systolic"] >= 140 or row["diastolic"] >= 90:
            assessment = "⚠ 偏高"
        elif row["systolic"] <= 90 or row["diastolic"] <= 60:
            assessment = "⚠ 偏低"
        else:
            assessment = "正常"
        lines.append(
            f"| {row['date']} | {row['time']} | {row['systolic']} | {row['diastolic']} | {assessment} |\n"
        )

    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_spo2_md(data: list[dict], patient: str, output_dir: Path) -> Path | None:
    """Write 血氧记录.md."""
    if not data:
        return None

    path = output_dir / "血氧记录.md"
    start_date = data[0]["date"]
    end_date = data[-1]["date"]

    lines = [file_header("血氧记录", patient, start_date, end_date)]
    lines.append("| 日期 | 平均SpO2(%) | 最低(%) | 最高(%) | 评估 |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")

    for row in data:
        assessment = ""
        if row["min"] < 95:
            assessment = "⚠ 偏低"
        else:
            assessment = "正常"
        lines.append(
            f"| {row['date']} | {row['avg']} | {row['min']} | {row['max']} | {assessment} |\n"
        )

    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_weight_md(data: list[dict], patient: str, output_dir: Path) -> Path | None:
    """Write 体重变化.md."""
    if not data:
        return None

    path = output_dir / "体重变化.md"
    start_date = data[0]["date"]
    end_date = data[-1]["date"]

    lines = [file_header("体重变化", patient, start_date, end_date)]
    lines.append("| 日期 | 体重(kg) | 趋势 | 变化 |\n")
    lines.append("| --- | --- | --- | --- |\n")

    prev_value = None
    for row in data:
        if prev_value is not None:
            arrow = weight_trend_arrow(row["value"], prev_value)
            change = row["value"] - prev_value
            change_str = f"{change:+.1f} kg"
        else:
            arrow = "—"
            change_str = "基线"
        lines.append(
            f"| {row['date']} | {row['value']} | {arrow} | {change_str} |\n"
        )
        prev_value = row["value"]

    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_steps_md(data: list[dict], patient: str, output_dir: Path) -> Path | None:
    """Write 步数记录.md."""
    if not data:
        return None

    path = output_dir / "步数记录.md"
    start_date = data[0]["date"]
    end_date = data[-1]["date"]

    # Compute weekly averages
    week_totals: dict[str, list[int]] = defaultdict(list)
    for row in data:
        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        # ISO week key
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        week_totals[week_key].append(row["total"])

    lines = [file_header("步数记录", patient, start_date, end_date)]
    lines.append("| 日期 | 步数 | 周均步数 |\n")
    lines.append("| --- | --- | --- |\n")

    current_week = None
    for row in data:
        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        iso_year, iso_week, _ = dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        if week_key != current_week:
            week_avg = int(sum(week_totals[week_key]) / len(week_totals[week_key]))
            week_display = f"{week_avg:,}"
            current_week = week_key
        else:
            week_display = ""

        lines.append(
            f"| {row['date']} | {row['total']:,} | {week_display} |\n"
        )

    path.write_text("".join(lines), encoding="utf-8")
    return path


def write_sleep_md(data: list[dict], patient: str, output_dir: Path) -> Path | None:
    """Write 睡眠记录.md."""
    if not data:
        return None

    path = output_dir / "睡眠记录.md"
    start_date = data[0]["date"]
    end_date = data[-1]["date"]

    lines = [file_header("睡眠记录", patient, start_date, end_date)]
    lines.append("| 日期 | 睡眠时长 | 小时数 | 评估 |\n")
    lines.append("| --- | --- | --- | --- |\n")

    for row in data:
        assessment = ""
        if row["hours"] < 6:
            assessment = "⚠ 不足"
        elif row["hours"] > 10:
            assessment = "⚠ 过多"
        else:
            assessment = "正常"
        lines.append(
            f"| {row['date']} | {row['display']} | {row['hours']} | {assessment} |\n"
        )

    path.write_text("".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def compute_summary(
    records: dict[str, list[dict]],
    aggregated: dict,
    files_created: list[str],
    patient: str,
) -> dict:
    """Build the JSON summary dict."""
    total_records = sum(len(v) for v in records.values())

    # Overall date range
    all_dates: list[datetime] = []
    for metric_records in records.values():
        for r in metric_records:
            if r["start"]:
                all_dates.append(r["start"])

    date_range = {}
    if all_dates:
        date_range = {
            "start": format_date(min(all_dates)),
            "end": format_date(max(all_dates)),
        }

    metrics = {}

    # Heart rate
    hr_data = aggregated.get("heart_rate", [])
    if hr_data:
        all_avgs = [d["avg"] for d in hr_data]
        metrics["heart_rate"] = {
            "count": len(hr_data),
            "avg": round(sum(all_avgs) / len(all_avgs), 1),
            "latest": hr_data[-1]["avg"],
        }

    # Weight
    wt_data = aggregated.get("weight", [])
    if wt_data:
        latest = wt_data[-1]["value"]
        if len(wt_data) >= 2:
            first = wt_data[0]["value"]
            if latest > first * 1.02:
                wt_trend = "increasing"
            elif latest < first * 0.98:
                wt_trend = "decreasing"
            else:
                wt_trend = "stable"
        else:
            wt_trend = "stable"
        metrics["weight"] = {
            "count": len(wt_data),
            "latest": latest,
            "trend": wt_trend,
        }

    # Steps
    st_data = aggregated.get("steps", [])
    if st_data:
        totals = [d["total"] for d in st_data]
        metrics["steps"] = {
            "count": len(st_data),
            "daily_avg": int(sum(totals) / len(totals)),
            "latest": st_data[-1]["total"],
        }

    # Blood pressure
    bp_data = aggregated.get("bp", [])
    if bp_data:
        metrics["blood_pressure"] = {
            "count": len(bp_data),
            "latest_systolic": bp_data[-1]["systolic"],
            "latest_diastolic": bp_data[-1]["diastolic"],
        }

    # SpO2
    spo2_data = aggregated.get("spo2", [])
    if spo2_data:
        metrics["spo2"] = {
            "count": len(spo2_data),
            "latest_avg": spo2_data[-1]["avg"],
        }

    # Sleep
    sl_data = aggregated.get("sleep", [])
    if sl_data:
        hours = [d["hours"] for d in sl_data]
        metrics["sleep"] = {
            "count": len(sl_data),
            "avg_hours": round(sum(hours) / len(hours), 1),
            "latest": sl_data[-1]["hours"],
        }

    return {
        "success": True,
        "patient": patient,
        "records_processed": total_records,
        "date_range": date_range,
        "metrics": metrics,
        "files_created": files_created,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 4:
        print(
            "Usage: python3 parse_apple_health.py "
            '"<export.xml>" "<patient_name>" "<output_dir>"',
            file=sys.stderr,
        )
        sys.exit(1)

    xml_path = Path(sys.argv[1])
    patient_name = sys.argv[2]
    output_dir = Path(sys.argv[3])

    # Validate input
    if not xml_path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {xml_path}"}))
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect records from XML
    print(f"Parsing {xml_path}...", file=sys.stderr)
    records = collect_records(xml_path)
    print(
        f"Collected records: "
        + ", ".join(f"{k}={len(v)}" for k, v in records.items()),
        file=sys.stderr,
    )

    # Aggregate data
    aggregated: dict = {}
    aggregated["heart_rate"] = aggregate_heart_rate(records.get("heart_rate", []))
    aggregated["steps"] = aggregate_steps(records.get("steps", []))
    aggregated["weight"] = aggregate_weight(records.get("weight", []))
    aggregated["spo2"] = aggregate_spo2(records.get("spo2", []))
    aggregated["sleep"] = aggregate_sleep(records.get("sleep", []))

    # Match blood pressure
    aggregated["bp"] = match_blood_pressure(
        records.get("bp_systolic", []),
        records.get("bp_diastolic", []),
    )

    # Write Markdown files
    files_created: list[str] = []

    path = write_heart_rate_md(aggregated["heart_rate"], patient_name, output_dir)
    if path:
        files_created.append(path.name)

    path = write_bp_md(aggregated["bp"], patient_name, output_dir)
    if path:
        files_created.append(path.name)

    path = write_spo2_md(aggregated["spo2"], patient_name, output_dir)
    if path:
        files_created.append(path.name)

    path = write_weight_md(aggregated["weight"], patient_name, output_dir)
    if path:
        files_created.append(path.name)

    path = write_steps_md(aggregated["steps"], patient_name, output_dir)
    if path:
        files_created.append(path.name)

    path = write_sleep_md(aggregated["sleep"], patient_name, output_dir)
    if path:
        files_created.append(path.name)

    # Build and print summary
    summary = compute_summary(records, aggregated, files_created, patient_name)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
