#!/usr/bin/env python3
"""
update_timeline.py — Append a new entry to a patient's timeline.md and
optionally update INDEX.md key metrics.

Usage:
    python3 update_timeline.py "<patient_name>" "<date>" "<doc_type>" "<summary>" "<filepath>"

Arguments:
    patient_name  Name matching a directory under ~/.openclaw/patients/
    date          Event date in YYYY-MM-DD format
    doc_type      Document type (e.g. 肿瘤标志物, CT, 化疗, 病理, 血常规)
    summary       Brief one-line summary of the event
    filepath      Relative path to the source document inside the patient dir
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def patients_root() -> Path:
    """Return the root patients directory (~/.openclaw/patients)."""
    return Path.home() / ".openclaw" / "patients"


def parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD date string. Raises ValueError on bad format."""
    return datetime.strptime(date_str.strip(), "%Y-%m-%d")


def read_text(path: Path) -> str:
    """Read a file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text to a file."""
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Timeline table helpers
# ---------------------------------------------------------------------------

TABLE_HEADER = "| 日期 | 类型 | 摘要 | 文件路径 |"
TABLE_SEP = "| --- | --- | --- | --- |"


def detect_sort_order(rows: list[str]) -> str:
    """Detect whether existing rows are sorted newest-first or oldest-first.

    Returns "desc" (newest first) or "asc" (oldest first).
    Defaults to "desc" if undetermined.
    """
    dates: list[str] = []
    for row in rows:
        cols = [c.strip() for c in row.strip().strip("|").split("|")]
        if cols and re.match(r"\d{4}-\d{2}-\d{2}", cols[0]):
            dates.append(cols[0])
    if len(dates) >= 2:
        if dates[0] >= dates[1]:
            return "desc"
        return "asc"
    return "desc"


def insert_row_sorted(rows: list[str], new_row: str, order: str) -> list[str]:
    """Insert *new_row* into *rows* maintaining date sort order."""
    new_date = new_row.strip().strip("|").split("|")[0].strip()
    result: list[str] = []
    inserted = False
    for row in rows:
        cols = [c.strip() for c in row.strip().strip("|").split("|")]
        row_date = cols[0] if cols else ""
        if not inserted and re.match(r"\d{4}-\d{2}-\d{2}", row_date):
            if order == "desc" and new_date > row_date:
                result.append(new_row)
                inserted = True
            elif order == "asc" and new_date < row_date:
                result.append(new_row)
                inserted = True
        result.append(row)
    if not inserted:
        result.append(new_row)
    return result


def update_timeline(patient_dir: Path, date: str, doc_type: str,
                    summary: str, filepath: str) -> None:
    """Append or insert a new row into timeline.md."""
    timeline_path = patient_dir / "timeline.md"

    new_row = f"| {date} | {doc_type} | {summary} | {filepath} |"

    if not timeline_path.exists():
        # Create the file with header + new row
        content = f"{TABLE_HEADER}\n{TABLE_SEP}\n{new_row}\n"
        write_text(timeline_path, content)
        return

    text = read_text(timeline_path)
    lines = text.splitlines()

    # Separate header / separator from data rows
    header_lines: list[str] = []
    data_rows: list[str] = []
    past_header = False
    for line in lines:
        stripped = line.strip()
        if not past_header:
            if stripped.startswith("|"):
                header_lines.append(line)
                if re.match(r"\|\s*-", stripped):
                    past_header = True
                continue
            # Non-table preamble (e.g. a title) — keep in header
            header_lines.append(line)
        else:
            if stripped.startswith("|") and stripped.endswith("|"):
                data_rows.append(stripped)
            else:
                # Preserve trailing blank lines etc. by keeping in header
                # Actually these are footer lines — we just ignore empty lines
                pass

    order = detect_sort_order(data_rows)
    data_rows = insert_row_sorted(data_rows, new_row, order)

    # Rebuild file
    rebuilt = "\n".join(header_lines) + "\n" + "\n".join(data_rows) + "\n"
    write_text(timeline_path, rebuilt)


# ---------------------------------------------------------------------------
# INDEX.md key-metrics updater
# ---------------------------------------------------------------------------

def extract_key_values_from_report(report_path: Path) -> dict[str, str]:
    """Try to extract key lab values from a report file.

    Looks for patterns like 'CEA: 12.3 ng/mL' or 'CEA　12.3' in the file.
    Returns a dict mapping metric name -> value string.
    """
    if not report_path.exists():
        return {}

    text = read_text(report_path)
    results: dict[str, str] = {}

    # Common tumor markers and blood count metrics
    markers = [
        "CEA", "CA-199", "CA199", "CA-125", "CA125", "AFP", "CA-153", "CA153",
        "CA-724", "CA724", "NSE", "SCC", "CYFRA21-1", "PSA",
        "白细胞", "WBC", "血红蛋白", "HGB", "血小板", "PLT",
        "中性粒细胞", "NEUT", "淋巴细胞", "LYM",
    ]

    for marker in markers:
        # Match patterns: "CEA: 12.3 ng/mL", "CEA 12.3", "CEA：12.3ng/ml"
        pattern = rf"{re.escape(marker)}\s*[：:]\s*([\d.]+\s*\S*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[marker] = match.group(1).strip()

    return results


def update_index_metrics(patient_dir: Path, doc_type: str,
                         filepath: str) -> None:
    """Update INDEX.md '关键指标（最新值）' section if applicable."""
    index_path = patient_dir / "INDEX.md"
    if not index_path.exists():
        return

    # Only update for specific doc types
    type_lower = doc_type.lower()
    if "肿瘤标志物" not in doc_type and "肿标" not in doc_type and "血常规" not in doc_type:
        return

    # Resolve the report file path
    report_path = patient_dir / filepath
    values = extract_key_values_from_report(report_path)
    if not values:
        return

    text = read_text(index_path)

    # Find the key-metrics section
    section_pattern = r"(##\s*关键指标[^\n]*\n)"
    match = re.search(section_pattern, text)
    if not match:
        return

    # For each extracted value, try to update the existing table row
    for metric, value in values.items():
        # Look for a row like "| CEA | ... |" and update the value column
        row_pattern = rf"(\|\s*{re.escape(metric)}\s*\|)[^\n]*"
        row_match = re.search(row_pattern, text, re.IGNORECASE)
        if row_match:
            # Replace the row, keeping the metric name column intact
            new_row = f"| {metric} | {value} |"
            text = text[:row_match.start()] + new_row + text[row_match.end():]

    write_text(index_path, text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 6:
        print(
            "Usage: python3 update_timeline.py "
            '"<patient_name>" "<date>" "<doc_type>" "<summary>" "<filepath>"',
            file=sys.stderr,
        )
        sys.exit(1)

    patient_name, date_str, doc_type, summary, filepath = sys.argv[1:6]

    # Validate date
    try:
        parse_date(date_str)
    except ValueError:
        print(f"ERROR: Invalid date format '{date_str}'. Expected YYYY-MM-DD.",
              file=sys.stderr)
        sys.exit(1)

    # Locate patient directory
    patient_dir = patients_root() / patient_name
    if not patient_dir.is_dir():
        print(f"ERROR: Patient directory not found: {patient_dir}",
              file=sys.stderr)
        sys.exit(1)

    # Update timeline
    try:
        update_timeline(patient_dir, date_str, doc_type, summary, filepath)
    except UnicodeDecodeError as exc:
        print(f"ERROR: File encoding issue while reading timeline.md: {exc}",
              file=sys.stderr)
        sys.exit(1)

    # Update INDEX.md key metrics if applicable
    try:
        update_index_metrics(patient_dir, doc_type, filepath)
    except Exception as exc:
        # Non-fatal — timeline was already updated
        print(f"WARNING: Could not update INDEX.md metrics: {exc}",
              file=sys.stderr)

    print(f"OK: Added entry for {date_str} {doc_type}")


if __name__ == "__main__":
    main()
