#!/usr/bin/env python3
"""Xiaomi/Mi Fitness data importer -- CSV parsing into HealthDataStore."""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from .health_importer_base import HealthImporterBase

# ---------------------------------------------------------------------------
# Column name candidates for defensive discovery (case-insensitive)
# Covers both legacy Mi Fit and new Mi Fitness export formats.
# ---------------------------------------------------------------------------

# Heart rate
_HR_DATE_COLS = ("date", "day", "record_date")
_HR_TIME_COLS = ("time", "record_time", "timestamp")
_HR_VALUE_COLS = ("heartrate", "heart_rate", "bpm", "value", "avg_bpm", "heartRate")

# Steps / Activity
_STEP_DATE_COLS = ("date", "day", "record_date")
_STEP_COUNT_COLS = ("steps", "step", "step_count", "total_steps", "count")
_STEP_DISTANCE_COLS = ("distance", "distance_m", "distance_meters")
_STEP_CALORIES_COLS = ("calories", "kcal", "calories_burned", "calorie")
_STEP_ACTIVE_COLS = ("active_minutes", "active_min", "move_minutes")

# Sleep
_SLEEP_DATE_COLS = ("date", "day", "record_date")
_SLEEP_START_COLS = ("bedtime", "bed_time", "start_time", "start", "sleep_start", "bedTime")
_SLEEP_END_COLS = ("wakeuptime", "wake_up_time", "wake_time", "end_time", "end", "wakeUpTime")
_SLEEP_TOTAL_COLS = ("totalmin", "total_min", "duration_min", "duration", "sleep_duration", "totalMin")
_SLEEP_DEEP_COLS = ("deepsleepmin", "deep_sleep_min", "deep_min", "deep_sleep", "deepSleepMin")
_SLEEP_LIGHT_COLS = ("lightsleepmin", "light_sleep_min", "light_min", "light_sleep", "lightSleepMin")
_SLEEP_REM_COLS = ("remsleepmin", "rem_sleep_min", "rem_min", "rem_sleep", "remSleepMin")

# Weight / Body
_WEIGHT_DATE_COLS = ("date", "day", "record_date")
_WEIGHT_TIME_COLS = ("time", "record_time", "timestamp")
_WEIGHT_VALUE_COLS = ("weight", "weight_kg", "body_weight", "value")

# Filename-based type detection
_HEART_RATE_INDICATORS = ("heartrate", "heart_rate", "hr_")
_STEP_INDICATORS = ("activity_minute", "activity", "step", "daily_activity")
_SLEEP_INDICATORS = ("sleep",)
_WEIGHT_INDICATORS = ("body", "weight")


def _find_column(headers: list[str], candidates: tuple[str, ...]) -> str | None:
    """Find the first matching column name from candidates (case-insensitive)."""
    lower_headers = {h.lower().strip(): h for h in headers}
    for candidate in candidates:
        if candidate.lower() in lower_headers:
            return lower_headers[candidate.lower()]
    return None


def _safe_float(value: str | int | float) -> float | None:
    """Parse a value to float, returning None on failure."""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _safe_int(value: str | int | float) -> int | None:
    """Parse a value to int, returning None on failure."""
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


class XiaomiHealthImporter(HealthImporterBase):
    """Import Xiaomi/Mi Fitness data from account.xiaomi.com export ZIP.

    Handles CSV files with various formats from both legacy Mi Fit
    and new Mi Fitness apps. File naming typically follows patterns like
    HEARTRATE_AUTO_*.csv, ACTIVITY_MINUTE_*.csv, SLEEP_*.csv, BODY_*.csv.
    """

    PLATFORM = "xiaomi"

    def _discover_files(self, extracted_dir: Path) -> list[Path]:
        """Find CSV files in extracted directory."""
        files = list(extracted_dir.rglob("*.csv"))
        return sorted(files)

    def _parse_records(self, data_file: Path) -> list[dict]:
        """Parse a CSV data file into health records."""
        suffix = data_file.suffix.lower()
        if suffix != ".csv":
            return []
        return self._parse_csv(data_file)

    # ------------------------------------------------------------------
    # CSV parsing
    # ------------------------------------------------------------------

    def _parse_csv(self, csv_path: Path) -> list[dict]:
        """Parse a Xiaomi CSV, auto-detecting data type from filename and headers."""
        try:
            text = csv_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = csv_path.read_text(encoding="latin-1")

        reader = csv.DictReader(text.strip().splitlines())
        if not reader.fieldnames:
            return []

        headers = list(reader.fieldnames)
        filename_lower = csv_path.stem.lower()

        # Detect type from filename first
        if any(ind in filename_lower for ind in _HEART_RATE_INDICATORS):
            return self._parse_heart_rate_rows(reader, headers)

        if any(ind in filename_lower for ind in _SLEEP_INDICATORS):
            return self._parse_sleep_rows(reader, headers)

        if any(ind in filename_lower for ind in _STEP_INDICATORS):
            return self._parse_step_rows(reader, headers)

        if any(ind in filename_lower for ind in _WEIGHT_INDICATORS):
            return self._parse_weight_rows(reader, headers)

        # Try to infer from columns
        if _find_column(headers, _HR_VALUE_COLS) and not _find_column(headers, _STEP_COUNT_COLS):
            return self._parse_heart_rate_rows(reader, headers)

        if _find_column(headers, _STEP_COUNT_COLS):
            return self._parse_step_rows(reader, headers)

        if _find_column(headers, _SLEEP_TOTAL_COLS):
            return self._parse_sleep_rows(reader, headers)

        if _find_column(headers, _WEIGHT_VALUE_COLS) and not _find_column(headers, _STEP_COUNT_COLS):
            return self._parse_weight_rows(reader, headers)

        # Unknown CSV format -- skip with warning
        print(f"[WARN] Unrecognized Xiaomi CSV format in {csv_path.name}: columns={headers}", file=sys.stderr)
        return []

    def _parse_heart_rate_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse heart rate CSV rows."""
        date_col = _find_column(headers, _HR_DATE_COLS)
        time_col = _find_column(headers, _HR_TIME_COLS)
        val_col = _find_column(headers, _HR_VALUE_COLS)

        if not val_col:
            return []

        records = []
        for row in reader:
            bpm = _safe_int(row.get(val_col, ""))
            if bpm is None:
                continue

            ts = self._build_timestamp(row, date_col, time_col)
            if not ts:
                continue

            records.append({
                "type": "heart_rate",
                "timestamp": ts,
                "data": {"value": bpm},
            })
        return records

    def _parse_step_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse step count CSV rows."""
        date_col = _find_column(headers, _STEP_DATE_COLS)
        count_col = _find_column(headers, _STEP_COUNT_COLS)
        dist_col = _find_column(headers, _STEP_DISTANCE_COLS)
        cal_col = _find_column(headers, _STEP_CALORIES_COLS)
        active_col = _find_column(headers, _STEP_ACTIVE_COLS)

        if not count_col:
            return []

        records = []
        for row in reader:
            step_count = _safe_int(row.get(count_col, ""))
            if step_count is None:
                continue

            ts = self._build_timestamp(row, date_col, None)
            if not ts:
                continue

            data: dict = {"count": step_count}
            if dist_col:
                dist = _safe_float(row.get(dist_col, ""))
                if dist is not None:
                    data["distance_m"] = dist
            if cal_col:
                cal = _safe_float(row.get(cal_col, ""))
                if cal is not None:
                    data["calories"] = cal
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
        date_col = _find_column(headers, _SLEEP_DATE_COLS)
        start_col = _find_column(headers, _SLEEP_START_COLS)
        end_col = _find_column(headers, _SLEEP_END_COLS)
        total_col = _find_column(headers, _SLEEP_TOTAL_COLS)
        deep_col = _find_column(headers, _SLEEP_DEEP_COLS)
        light_col = _find_column(headers, _SLEEP_LIGHT_COLS)
        rem_col = _find_column(headers, _SLEEP_REM_COLS)

        if not total_col and not (start_col and end_col):
            return []

        records = []
        for row in reader:
            data: dict = {}
            ts = ""

            if total_col:
                total_min = _safe_int(row.get(total_col, ""))
                if total_min is not None:
                    data["total_min"] = total_min

            if deep_col:
                deep = _safe_int(row.get(deep_col, ""))
                if deep is not None:
                    data["deep_sleep_min"] = deep

            if light_col:
                light = _safe_int(row.get(light_col, ""))
                if light is not None:
                    data["light_sleep_min"] = light

            if rem_col:
                rem = _safe_int(row.get(rem_col, ""))
                if rem is not None:
                    data["rem_sleep_min"] = rem

            if start_col:
                bedtime = row.get(start_col, "").strip()
                if bedtime:
                    data["bedtime"] = bedtime
                    ts = bedtime

            if end_col:
                wake = row.get(end_col, "").strip()
                if wake:
                    data["wake_time"] = wake
                    if not ts:
                        ts = wake

            if not ts and date_col:
                date_val = row.get(date_col, "").strip()
                if date_val:
                    ts = date_val

            if not ts or not data:
                continue

            ts = self._normalize_xiaomi_timestamp(ts)
            records.append({
                "type": "sleep_session",
                "timestamp": ts,
                "data": data,
            })
        return records

    def _parse_weight_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse weight/body CSV rows."""
        date_col = _find_column(headers, _WEIGHT_DATE_COLS)
        time_col = _find_column(headers, _WEIGHT_TIME_COLS)
        val_col = _find_column(headers, _WEIGHT_VALUE_COLS)

        if not val_col:
            return []

        records = []
        for row in reader:
            weight = _safe_float(row.get(val_col, ""))
            if weight is None:
                continue

            ts = self._build_timestamp(row, date_col, time_col)
            if not ts:
                continue

            records.append({
                "type": "weight",
                "timestamp": ts,
                "data": {"value": weight},
            })
        return records

    # ------------------------------------------------------------------
    # Timestamp utilities
    # ------------------------------------------------------------------

    def _build_timestamp(
        self,
        row: dict,
        date_col: str | None,
        time_col: str | None,
    ) -> str:
        """Build a normalized timestamp from separate date and time columns.

        Xiaomi CSVs often have separate 'date' and 'time' columns.
        """
        date_val = ""
        time_val = ""

        if date_col:
            date_val = row.get(date_col, "").strip()
        if time_col:
            time_val = row.get(time_col, "").strip()

        if not date_val:
            return ""

        if time_val:
            ts_str = f"{date_val}T{time_val}"
        elif len(date_val) == 10:
            ts_str = f"{date_val}T00:00:00"
        else:
            ts_str = date_val

        return self._normalize_xiaomi_timestamp(ts_str)

    def _normalize_xiaomi_timestamp(self, ts_str: str) -> str:
        """Normalize Xiaomi timestamps.

        Xiaomi typically uses local time. Formats seen:
        - "2026-03-26" (date only)
        - "2026-03-26 10:00:00" (space separator)
        - "2026-03-26T10:00:00" (ISO without tz)
        - Epoch seconds/milliseconds (rare)
        """
        ts_str = ts_str.strip()
        if not ts_str:
            return datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Check for epoch (all digits)
        if ts_str.isdigit() and len(ts_str) >= 10:
            epoch_seconds = int(ts_str) / 1000 if len(ts_str) > 10 else int(ts_str)
            dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
            return dt.isoformat(timespec="seconds")

        # Replace space separator with T
        if " " in ts_str and "T" not in ts_str:
            ts_str = ts_str.replace(" ", "T", 1)

        # Date only -> add time
        if len(ts_str) == 10:
            ts_str = f"{ts_str}T00:00:00"

        return self._normalize_timestamp(ts_str)
