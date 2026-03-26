#!/usr/bin/env python3
"""Huawei Health data importer -- CSV/JSON/GPX parsing into HealthDataStore."""

from __future__ import annotations

import csv
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from .health_importer_base import HealthImporterBase

# GPX namespace
_GPX_NS = "http://www.topografix.com/GPX/1/1"

# ---------------------------------------------------------------------------
# Column name candidates for defensive discovery (case-insensitive)
# ---------------------------------------------------------------------------

# Heart rate
_HR_TIMESTAMP_COLS = ("starttime", "start_time", "timestamp", "time", "date_time")
_HR_VALUE_COLS = ("heartrate", "heart_rate", "bpm", "value", "avg_bpm")

# Steps
_STEP_TIMESTAMP_COLS = ("starttime", "start_time", "date", "timestamp")
_STEP_COUNT_COLS = ("step", "steps", "step_count", "total_steps", "count")
_STEP_DISTANCE_COLS = ("distance", "distance_m", "distance_meters")
_STEP_CALORIES_COLS = ("calories", "kcal", "calories_burned", "calorie")

# Sleep
_SLEEP_START_COLS = ("starttime", "start_time", "bedtime", "sleep_start")
_SLEEP_END_COLS = ("endtime", "end_time", "wake_time", "sleep_end")
_SLEEP_DURATION_COLS = ("duration(min)", "duration_min", "duration", "total_min", "sleep_duration")

# Weight
_WEIGHT_TIMESTAMP_COLS = ("starttime", "start_time", "date", "timestamp", "time")
_WEIGHT_VALUE_COLS = ("weight", "weight_kg", "value", "body_weight")

# Blood pressure
_BP_TIMESTAMP_COLS = ("starttime", "start_time", "date", "timestamp", "time")
_BP_SBP_COLS = ("systolic", "sbp", "systolic_pressure")
_BP_DBP_COLS = ("diastolic", "dbp", "diastolic_pressure")


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


# ---------------------------------------------------------------------------
# Filename-based type detection indicators
# ---------------------------------------------------------------------------

_HEART_RATE_INDICATORS = ("heart_rate", "heart rate", "heartrate", "hr_")
_STEP_INDICATORS = ("step", "walk", "activity_minute")
_SLEEP_INDICATORS = ("sleep",)
_WEIGHT_INDICATORS = ("weight", "body_weight", "body_mass")
_BP_INDICATORS = ("blood_pressure", "bloodpressure", "bp_")


class HuaweiHealthImporter(HealthImporterBase):
    """Import Huawei Health data from a Settings export ZIP.

    Handles CSV files (heart rate, steps, sleep, weight, blood pressure),
    JSON files (heart rate details), and GPX files (activity routes).
    Huawei export structure varies but typically contains directories like
    'Health data/', 'Motion path detail data/', 'Sport Health Data/'.
    """

    PLATFORM = "huawei-health"

    def _discover_files(self, extracted_dir: Path) -> list[Path]:
        """Walk extracted directory for CSV, JSON, and GPX files."""
        files: list[Path] = []
        for ext in ("*.csv", "*.json", "*.gpx"):
            files.extend(extracted_dir.rglob(ext))
        return sorted(files)

    def _parse_records(self, data_file: Path) -> list[dict]:
        """Parse a data file into health records.

        Routes to type-specific parser based on file extension.
        """
        suffix = data_file.suffix.lower()
        if suffix == ".csv":
            return self._parse_csv(data_file)
        if suffix == ".json":
            return self._parse_json(data_file)
        if suffix == ".gpx":
            return self._parse_gpx(data_file)
        return []

    # ------------------------------------------------------------------
    # CSV parsing
    # ------------------------------------------------------------------

    def _parse_csv(self, csv_path: Path) -> list[dict]:
        """Parse a Huawei Health CSV, auto-detecting data type from filename and headers."""
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

        if any(ind in filename_lower for ind in _STEP_INDICATORS):
            return self._parse_step_rows(reader, headers)

        if any(ind in filename_lower for ind in _SLEEP_INDICATORS):
            return self._parse_sleep_rows(reader, headers)

        if any(ind in filename_lower for ind in _WEIGHT_INDICATORS):
            return self._parse_weight_rows(reader, headers)

        if any(ind in filename_lower for ind in _BP_INDICATORS):
            return self._parse_bp_rows(reader, headers)

        # Try to infer from columns
        if _find_column(headers, _HR_VALUE_COLS) and _find_column(headers, _HR_TIMESTAMP_COLS):
            # Check if it's actually step data (has step column)
            if _find_column(headers, _STEP_COUNT_COLS):
                return self._parse_step_rows(reader, headers)
            return self._parse_heart_rate_rows(reader, headers)

        if _find_column(headers, _STEP_COUNT_COLS):
            return self._parse_step_rows(reader, headers)

        if _find_column(headers, _SLEEP_DURATION_COLS):
            return self._parse_sleep_rows(reader, headers)

        if _find_column(headers, _WEIGHT_VALUE_COLS):
            return self._parse_weight_rows(reader, headers)

        if _find_column(headers, _BP_SBP_COLS):
            return self._parse_bp_rows(reader, headers)

        # Unknown CSV format -- skip with warning
        print(f"[WARN] Unrecognized Huawei CSV format in {csv_path.name}: columns={headers}", file=sys.stderr)
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
            ts = self._normalize_huawei_timestamp(ts)
            records.append({
                "type": "heart_rate",
                "timestamp": ts,
                "data": {"value": bpm},
            })
        return records

    def _parse_step_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse step count CSV rows."""
        ts_col = _find_column(headers, _STEP_TIMESTAMP_COLS)
        count_col = _find_column(headers, _STEP_COUNT_COLS)
        dist_col = _find_column(headers, _STEP_DISTANCE_COLS)
        cal_col = _find_column(headers, _STEP_CALORIES_COLS)

        if not ts_col or not count_col:
            return []

        records = []
        for row in reader:
            ts = row.get(ts_col, "").strip()
            step_count = _safe_int(row.get(count_col, ""))
            if not ts or step_count is None:
                continue

            ts = self._normalize_huawei_timestamp(ts)
            data: dict = {"count": step_count}
            if dist_col:
                dist = _safe_float(row.get(dist_col, ""))
                if dist is not None:
                    data["distance_m"] = dist
            if cal_col:
                cal = _safe_float(row.get(cal_col, ""))
                if cal is not None:
                    data["calories"] = cal

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

        if not dur_col and not (start_col and end_col):
            return []

        records = []
        for row in reader:
            data: dict = {}
            ts = ""

            if dur_col:
                duration = _safe_int(row.get(dur_col, ""))
                if duration is not None:
                    data["total_min"] = duration

            if start_col:
                start_ts = row.get(start_col, "").strip()
                if start_ts:
                    ts = start_ts
                    data["bedtime"] = start_ts

            if end_col:
                end_ts = row.get(end_col, "").strip()
                if end_ts:
                    data["wake_time"] = end_ts
                    if not ts:
                        ts = end_ts

            if not ts or not data:
                continue

            ts = self._normalize_huawei_timestamp(ts)
            records.append({
                "type": "sleep_session",
                "timestamp": ts,
                "data": data,
            })
        return records

    def _parse_weight_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse weight CSV rows."""
        ts_col = _find_column(headers, _WEIGHT_TIMESTAMP_COLS)
        val_col = _find_column(headers, _WEIGHT_VALUE_COLS)
        if not ts_col or not val_col:
            return []

        records = []
        for row in reader:
            ts = row.get(ts_col, "").strip()
            weight = _safe_float(row.get(val_col, ""))
            if not ts or weight is None:
                continue
            ts = self._normalize_huawei_timestamp(ts)
            records.append({
                "type": "weight",
                "timestamp": ts,
                "data": {"value": weight},
            })
        return records

    def _parse_bp_rows(self, reader: csv.DictReader, headers: list[str]) -> list[dict]:
        """Parse blood pressure CSV rows."""
        ts_col = _find_column(headers, _BP_TIMESTAMP_COLS)
        sbp_col = _find_column(headers, _BP_SBP_COLS)
        dbp_col = _find_column(headers, _BP_DBP_COLS)
        if not ts_col or not sbp_col or not dbp_col:
            return []

        records = []
        for row in reader:
            ts = row.get(ts_col, "").strip()
            sbp = _safe_int(row.get(sbp_col, ""))
            dbp = _safe_int(row.get(dbp_col, ""))
            if not ts or sbp is None or dbp is None:
                continue
            ts = self._normalize_huawei_timestamp(ts)
            records.append({
                "type": "bp",
                "timestamp": ts,
                "data": {"systolic": sbp, "diastolic": dbp},
            })
        return records

    # ------------------------------------------------------------------
    # JSON parsing
    # ------------------------------------------------------------------

    def _parse_json(self, json_path: Path) -> list[dict]:
        """Parse Huawei JSON data files (heart rate details, etc.)."""
        try:
            text = json_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = json_path.read_text(encoding="latin-1")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"[WARN] Failed to parse JSON {json_path.name}: {exc}", file=sys.stderr)
            return []

        # Handle both array of records and single object
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return []

        filename_lower = json_path.stem.lower()
        records = []

        for item in data:
            if not isinstance(item, dict):
                continue

            # Try to detect record type from filename or fields
            if any(ind in filename_lower for ind in _HEART_RATE_INDICATORS) or "heartRate" in item or "heart_rate" in item:
                rec = self._parse_json_heart_rate(item)
                if rec:
                    records.append(rec)
            elif any(ind in filename_lower for ind in _STEP_INDICATORS) or "step" in item or "steps" in item:
                rec = self._parse_json_steps(item)
                if rec:
                    records.append(rec)
            elif any(ind in filename_lower for ind in _SLEEP_INDICATORS) or "sleep" in filename_lower:
                rec = self._parse_json_sleep(item)
                if rec:
                    records.append(rec)
            else:
                # Try heart rate as default for unknown JSON with heartRate field
                rec = self._parse_json_heart_rate(item)
                if rec:
                    records.append(rec)

        return records

    def _parse_json_heart_rate(self, item: dict) -> dict | None:
        """Parse a single heart rate JSON record."""
        ts = item.get("startTime") or item.get("start_time") or item.get("timestamp", "")
        hr = item.get("heartRate") or item.get("heart_rate") or item.get("bpm")
        if not ts or hr is None:
            return None
        bpm = _safe_int(hr)
        if bpm is None:
            return None
        ts = self._normalize_huawei_timestamp(str(ts))
        return {
            "type": "heart_rate",
            "timestamp": ts,
            "data": {"value": bpm},
        }

    def _parse_json_steps(self, item: dict) -> dict | None:
        """Parse a single step count JSON record."""
        ts = item.get("startTime") or item.get("start_time") or item.get("date", "")
        count = item.get("step") or item.get("steps") or item.get("step_count")
        if not ts or count is None:
            return None
        step_count = _safe_int(count)
        if step_count is None:
            return None
        ts = self._normalize_huawei_timestamp(str(ts))
        return {
            "type": "steps",
            "timestamp": ts,
            "data": {"count": step_count},
        }

    def _parse_json_sleep(self, item: dict) -> dict | None:
        """Parse a single sleep JSON record."""
        ts = item.get("startTime") or item.get("start_time") or item.get("bedtime", "")
        duration = item.get("duration") or item.get("duration_min") or item.get("total_min")
        if not ts:
            return None
        ts = self._normalize_huawei_timestamp(str(ts))
        data: dict = {}
        if duration is not None:
            dur_val = _safe_int(duration)
            if dur_val is not None:
                data["total_min"] = dur_val
        if not data:
            return None
        return {
            "type": "sleep_session",
            "timestamp": ts,
            "data": data,
        }

    # ------------------------------------------------------------------
    # GPX parsing
    # ------------------------------------------------------------------

    def _parse_gpx(self, gpx_path: Path) -> list[dict]:
        """Parse a GPX activity file into activity records."""
        try:
            tree = ET.parse(gpx_path)
        except ET.ParseError as exc:
            print(f"[WARN] Failed to parse GPX {gpx_path.name}: {exc}", file=sys.stderr)
            return []

        root = tree.getroot()
        ns = {"gpx": _GPX_NS}
        records = []

        for trk in root.findall("gpx:trk", ns):
            name = trk.findtext("gpx:name", default="Activity", namespaces=ns)
            sport = trk.findtext("gpx:type", default="unknown", namespaces=ns)

            # Collect all timestamps from track points
            timestamps: list[datetime] = []
            for trkpt in trk.findall(".//gpx:trkpt", ns):
                time_elem = trkpt.find("gpx:time", ns)
                if time_elem is not None and time_elem.text:
                    try:
                        ts = self._parse_iso_timestamp(time_elem.text.strip())
                        timestamps.append(ts)
                    except (ValueError, TypeError):
                        continue

            if not timestamps:
                continue

            start_time = min(timestamps)
            end_time = max(timestamps)
            duration_seconds = int((end_time - start_time).total_seconds())

            ts_str = start_time.isoformat(timespec="seconds")
            if not ts_str.endswith("+00:00") and "+" not in ts_str[10:]:
                ts_str = self._normalize_timestamp(ts_str)

            records.append({
                "type": "activity",
                "timestamp": ts_str,
                "data": {
                    "sport": sport,
                    "name": name,
                    "duration_seconds": duration_seconds,
                },
            })

        return records

    # ------------------------------------------------------------------
    # Timestamp utilities
    # ------------------------------------------------------------------

    def _normalize_huawei_timestamp(self, ts_str: str) -> str:
        """Normalize Huawei timestamps.

        Huawei uses various formats:
        - Local time: "2026-03-26 10:00:00"
        - Epoch milliseconds: "1774520338000"
        - ISO with timezone: "2026-03-26T10:00:00+08:00"

        Detects format and normalizes to ISO 8601 with timezone.
        """
        ts_str = ts_str.strip()
        if not ts_str:
            return datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Check for epoch milliseconds (all digits, >10 chars)
        if ts_str.isdigit() and len(ts_str) >= 10:
            epoch_seconds = int(ts_str) / 1000 if len(ts_str) > 10 else int(ts_str)
            dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
            return dt.isoformat(timespec="seconds")

        # Replace space separator with T for ISO format
        if " " in ts_str and "T" not in ts_str:
            ts_str = ts_str.replace(" ", "T", 1)

        return self._normalize_timestamp(ts_str)
