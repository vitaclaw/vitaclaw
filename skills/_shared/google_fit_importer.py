#!/usr/bin/env python3
"""Google Fit Takeout importer -- CSV + TCX parsing into HealthDataStore."""

from __future__ import annotations

import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from .health_importer_base import HealthImporterBase

# TCX namespace
_TCX_NS = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"

# Known CSV file type indicators (discovered from filename patterns)
_HEART_RATE_INDICATORS = ("heart_rate", "heart rate", "heartrate")
_DAILY_ACTIVITY_INDICATORS = ("daily_activity", "daily activity", "daily_metrics")
_SLEEP_INDICATORS = ("sleep",)

# Known CSV column names for each data type
_HR_TIMESTAMP_COLS = ("timestamp", "start_time", "date_time", "time")
_HR_VALUE_COLS = ("bpm", "heart_rate", "value", "avg_bpm", "average_bpm")

_STEPS_DATE_COLS = ("date", "day", "start_date")
_STEPS_COUNT_COLS = ("steps", "step_count", "total_steps")
_STEPS_CALORIES_COLS = ("calories", "kcal", "calories_burned")
_STEPS_DISTANCE_COLS = ("distance_m", "distance", "distance_meters")
_STEPS_ACTIVE_COLS = ("active_minutes", "active_min", "move_minutes")

_SLEEP_START_COLS = ("start_time", "start", "bedtime", "sleep_start")
_SLEEP_END_COLS = ("end_time", "end", "wake_time", "sleep_end")
_SLEEP_DURATION_COLS = ("duration_min", "duration", "total_min", "sleep_duration")


def _find_column(headers: list[str], candidates: tuple[str, ...]) -> str | None:
    """Find the first matching column name from candidates (case-insensitive)."""
    lower_headers = {h.lower().strip(): h for h in headers}
    for candidate in candidates:
        if candidate.lower() in lower_headers:
            return lower_headers[candidate.lower()]
    return None


def _safe_float(value: str) -> float | None:
    """Parse a string to float, returning None on failure."""
    try:
        return float(value.strip())
    except (TypeError, ValueError):
        return None


def _safe_int(value: str) -> int | None:
    """Parse a string to int, returning None on failure."""
    try:
        return int(float(value.strip()))
    except (TypeError, ValueError):
        return None


class GoogleFitImporter(HealthImporterBase):
    """Import Google Fit data from a Google Takeout ZIP.

    Handles CSV files (heart rate, daily activity, sleep) and TCX activity files.
    """

    PLATFORM = "google-fit"

    def _discover_files(self, extracted_dir: Path) -> list[Path]:
        """Walk extracted Takeout directory, find CSV and TCX files."""
        files: list[Path] = []
        for ext in ("*.csv", "*.tcx"):
            files.extend(extracted_dir.rglob(ext))
        return sorted(files)

    def _parse_records(self, data_file: Path) -> list[dict]:
        """Parse a data file into health records.

        Routes to type-specific parser based on file extension and name.
        """
        suffix = data_file.suffix.lower()
        if suffix == ".tcx":
            return self._parse_tcx(data_file)
        if suffix == ".csv":
            return self._parse_csv(data_file)
        return []

    # ------------------------------------------------------------------
    # CSV parsing
    # ------------------------------------------------------------------

    def _parse_csv(self, csv_path: Path) -> list[dict]:
        """Parse a Google Fit CSV file, auto-detecting the data type from headers."""
        try:
            text = csv_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = csv_path.read_text(encoding="latin-1")

        reader = csv.DictReader(text.strip().splitlines())
        if not reader.fieldnames:
            return []

        headers = list(reader.fieldnames)
        filename_lower = csv_path.stem.lower()

        # Detect type from filename first, then from columns
        if any(ind in filename_lower for ind in _HEART_RATE_INDICATORS):
            return self._parse_heart_rate_rows(reader, headers)

        if any(ind in filename_lower for ind in _DAILY_ACTIVITY_INDICATORS):
            return self._parse_daily_activity_rows(reader, headers)

        if any(ind in filename_lower for ind in _SLEEP_INDICATORS):
            return self._parse_sleep_rows(reader, headers)

        # Try to infer from column names
        if _find_column(headers, _HR_VALUE_COLS) and _find_column(headers, _HR_TIMESTAMP_COLS):
            return self._parse_heart_rate_rows(reader, headers)

        if _find_column(headers, _STEPS_COUNT_COLS):
            return self._parse_daily_activity_rows(reader, headers)

        if _find_column(headers, _SLEEP_DURATION_COLS):
            return self._parse_sleep_rows(reader, headers)

        # Unknown CSV format -- skip with warning
        print(f"[WARN] Unrecognized CSV format in {csv_path.name}: columns={headers}", file=sys.stderr)
        return []

    def _parse_heart_rate_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse heart rate CSV rows."""
        ts_col = _find_column(headers, _HR_TIMESTAMP_COLS)
        val_col = _find_column(headers, _HR_VALUE_COLS)
        if not ts_col or not val_col:
            return []

        records = []
        for row in reader:
            ts = row.get(ts_col, "").strip()
            bpm = _safe_int(row.get(val_col, ""))
            if not ts or bpm is None:
                continue
            ts = self._normalize_timestamp(ts)
            records.append({
                "type": "heart_rate",
                "timestamp": ts,
                "data": {"value": bpm},
            })
        return records

    def _parse_daily_activity_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse daily activity CSV rows into step records."""
        date_col = _find_column(headers, _STEPS_DATE_COLS)
        steps_col = _find_column(headers, _STEPS_COUNT_COLS)
        calories_col = _find_column(headers, _STEPS_CALORIES_COLS)
        distance_col = _find_column(headers, _STEPS_DISTANCE_COLS)
        active_col = _find_column(headers, _STEPS_ACTIVE_COLS)

        if not date_col or not steps_col:
            return []

        records = []
        for row in reader:
            date_val = row.get(date_col, "").strip()
            step_count = _safe_int(row.get(steps_col, ""))
            if not date_val or step_count is None:
                continue

            # Normalize date to timestamp
            if len(date_val) == 10:
                ts = f"{date_val}T00:00:00+00:00"
            else:
                ts = self._normalize_timestamp(date_val)

            data: dict = {"count": step_count}
            if calories_col:
                cal = _safe_float(row.get(calories_col, ""))
                if cal is not None:
                    data["calories"] = cal
            if distance_col:
                dist = _safe_float(row.get(distance_col, ""))
                if dist is not None:
                    data["distance_m"] = dist
            if active_col:
                active = _safe_int(row.get(active_col, ""))
                if active is not None:
                    data["active_minutes"] = active

            records.append({
                "type": "steps",
                "timestamp": ts,
                "data": data,
            })
        return records

    def _parse_sleep_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse sleep CSV rows."""
        start_col = _find_column(headers, _SLEEP_START_COLS)
        end_col = _find_column(headers, _SLEEP_END_COLS)
        dur_col = _find_column(headers, _SLEEP_DURATION_COLS)

        if not dur_col:
            return []

        records = []
        for row in reader:
            duration = _safe_int(row.get(dur_col, ""))
            if duration is None:
                continue

            data: dict = {"total_min": duration}

            ts = ""
            if start_col:
                ts = row.get(start_col, "").strip()
                data["bedtime"] = ts
            if end_col:
                wake = row.get(end_col, "").strip()
                data["wake_time"] = wake
                if not ts:
                    ts = wake

            if not ts:
                continue

            ts = self._normalize_timestamp(ts)
            records.append({
                "type": "sleep_session",
                "timestamp": ts,
                "data": data,
            })
        return records

    # ------------------------------------------------------------------
    # TCX parsing
    # ------------------------------------------------------------------

    def _parse_tcx(self, tcx_path: Path) -> list[dict]:
        """Parse a TCX activity file."""
        try:
            tree = ET.parse(tcx_path)
        except ET.ParseError as exc:
            print(f"[WARN] Failed to parse TCX {tcx_path.name}: {exc}", file=sys.stderr)
            return []

        root = tree.getroot()
        ns = {"tcx": _TCX_NS}
        records = []

        for activity in root.findall(".//tcx:Activity", ns):
            sport = activity.get("Sport", "Unknown")
            activity_id = activity.findtext("tcx:Id", default="", namespaces=ns).strip()
            ts = self._normalize_timestamp(activity_id) if activity_id else ""

            total_time = 0.0
            total_distance = 0.0
            total_calories = 0
            avg_hr_values: list[int] = []

            for lap in activity.findall("tcx:Lap", ns):
                time_text = lap.findtext("tcx:TotalTimeSeconds", default="0", namespaces=ns)
                dist_text = lap.findtext("tcx:DistanceMeters", default="0", namespaces=ns)
                cal_text = lap.findtext("tcx:Calories", default="0", namespaces=ns)
                total_time += _safe_float(time_text) or 0
                total_distance += _safe_float(dist_text) or 0
                total_calories += _safe_int(cal_text) or 0

                avg_hr_elem = lap.find("tcx:AverageHeartRateBpm/tcx:Value", ns)
                if avg_hr_elem is not None and avg_hr_elem.text:
                    hr_val = _safe_int(avg_hr_elem.text)
                    if hr_val:
                        avg_hr_values.append(hr_val)

            if not ts:
                continue

            data: dict = {
                "sport": sport,
                "duration_seconds": int(total_time),
                "distance_m": round(total_distance, 1),
                "calories": total_calories,
            }
            if avg_hr_values:
                data["avg_heart_rate"] = round(sum(avg_hr_values) / len(avg_hr_values))

            records.append({
                "type": "activity",
                "timestamp": ts,
                "data": data,
            })

        return records
