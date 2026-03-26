#!/usr/bin/env python3
"""Shared base class for health data importers (Google Fit, Huawei, Xiaomi)."""

from __future__ import annotations

import sys
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .health_data_store import HealthDataStore


# Mapping from canonical record type to the skill name that owns the data directory.
# Per D-08: heart_rate -> heart-rate-tracker, steps -> step-tracker, etc.
_TYPE_TO_SKILL: dict[str, str] = {
    "heart_rate": "heart-rate-tracker",
    "steps": "step-tracker",
    "sleep_session": "sleep-tracker",
    "weight": "weight-tracker",
    "bp": "blood-pressure-tracker",
    "activity": "activity-tracker",
}


class HealthImporterBase:
    """Base class for health data importers.

    Provides ZIP extraction, record mapping, fuzzy dedup (60s timestamp
    window, 5% value tolerance), and person_id passthrough. Platform-specific
    subclasses implement ``_discover_files`` and ``_parse_records``.
    """

    PLATFORM = "unknown"  # Subclass overrides: "google-fit", "huawei-health", "xiaomi"

    def __init__(self, data_dir: str | None = None, person_id: str | None = None):
        self.person_id = person_id
        self._data_dir = data_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_export(
        self,
        export_path: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """Main entry: extract ZIP -> discover files -> parse -> dedup -> store.

        Returns::

            {
                "imported": int,
                "skipped_dupes": int,
                "errors": [str],
                "by_type": {record_type: count},
            }
        """
        errors: list[str] = []

        # 1. Extract ZIP
        extracted_dir = self._extract_zip(export_path)

        # 2. Discover data files
        data_files = self._discover_files(extracted_dir)

        # 3. Parse records from all discovered files
        all_records: list[dict] = []
        for data_file in data_files:
            try:
                records = self._parse_records(data_file)
                all_records.extend(records)
            except Exception as exc:
                errors.append(f"Error parsing {data_file.name}: {exc}")
                print(f"[WARN] Error parsing {data_file.name}: {exc}", file=sys.stderr)

        # 4. Filter by date range if specified
        if start_date or end_date:
            all_records = self._filter_by_date(all_records, start_date, end_date)

        # 5. Store with fuzzy dedup
        result = self._store_records(all_records)
        result["errors"] = errors
        return result

    # ------------------------------------------------------------------
    # ZIP Extraction
    # ------------------------------------------------------------------

    def _extract_zip(self, zip_path: str) -> Path:
        """Extract ZIP to temp dir, return extraction root."""
        tmp_dir = Path(tempfile.mkdtemp(prefix="vitaclaw_import_"))
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
        return tmp_dir

    # ------------------------------------------------------------------
    # Subclass hooks (must override)
    # ------------------------------------------------------------------

    def _discover_files(self, extracted_dir: Path) -> list[Path]:
        """Subclass: return list of data files to process."""
        raise NotImplementedError

    def _parse_records(self, data_file: Path) -> list[dict]:
        """Subclass: parse file into list of {type, timestamp, data, _meta}."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Fuzzy Dedup
    # ------------------------------------------------------------------

    def is_fuzzy_duplicate(
        self,
        new_record: dict,
        existing: dict,
        time_window_seconds: int = 60,
        value_tolerance: float = 0.05,
    ) -> bool:
        """Check if two records are fuzzy duplicates.

        Uses 60s timestamp window and 5% value tolerance per D-10.
        """
        # Must be same record type
        if new_record.get("type") != existing.get("type"):
            return False

        # Must be same person
        if new_record.get("person_id") != existing.get("person_id"):
            return False

        # Timestamp within window
        ts_new = self._parse_iso_timestamp(new_record["timestamp"])
        ts_existing = self._parse_iso_timestamp(existing["timestamp"])
        if abs((ts_new - ts_existing).total_seconds()) > time_window_seconds:
            return False

        # Numeric values within tolerance
        new_data = new_record.get("data", {})
        existing_data = existing.get("data", {})
        for key in new_data:
            new_val = new_data[key]
            existing_val = existing_data.get(key)
            if isinstance(new_val, (int, float)) and isinstance(existing_val, (int, float)):
                if existing_val == 0:
                    if new_val != 0:
                        return False
                elif abs(new_val - existing_val) / abs(existing_val) > value_tolerance:
                    return False

        return True

    def _fuzzy_dedup(self, new_record: dict, existing_records: list[dict]) -> bool:
        """Return True if new_record is a fuzzy duplicate of any existing record.

        Pre-filters by record_type and same-day range per Pitfall 3.
        """
        rec_type = new_record.get("type")
        try:
            new_ts = self._parse_iso_timestamp(new_record["timestamp"])
        except (KeyError, ValueError):
            return False

        # Pre-filter: same type and timestamp within +/- 1 day
        day_window = timedelta(days=1)
        candidates = [
            r for r in existing_records
            if r.get("type") == rec_type
            and abs((self._parse_iso_timestamp(r["timestamp"]) - new_ts).total_seconds())
            < day_window.total_seconds()
        ]

        return any(self.is_fuzzy_duplicate(new_record, c) for c in candidates)

    # ------------------------------------------------------------------
    # Record Storage
    # ------------------------------------------------------------------

    def _store_records(self, records: list[dict]) -> dict:
        """Write records via HealthDataStore with dedup.

        Groups records by type, maps type to skill_name via _TYPE_TO_SKILL.
        Returns counts dict.
        """
        imported = 0
        skipped_dupes = 0
        by_type: dict[str, int] = {}
        import_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Group records by type for efficient dedup
        records_by_type: dict[str, list[dict]] = {}
        for rec in records:
            rec_type = rec.get("type", "unknown")
            records_by_type.setdefault(rec_type, []).append(rec)

        for rec_type, type_records in records_by_type.items():
            skill_name = _TYPE_TO_SKILL.get(rec_type, rec_type)
            store = HealthDataStore(skill_name, data_dir=self._data_dir)

            # Load existing records for this type (pre-filtered for dedup)
            existing = store.query(record_type=rec_type)

            for rec in type_records:
                # Attach person_id for dedup comparison
                rec_with_pid = dict(rec)
                rec_with_pid["person_id"] = self.person_id

                if self._fuzzy_dedup(rec_with_pid, existing):
                    skipped_dupes += 1
                    continue

                meta = rec.get("_meta", {})
                meta["source"] = "import"
                meta["device"] = self.PLATFORM
                meta["import_timestamp"] = import_timestamp

                stored = store.append(
                    record_type=rec_type,
                    data=rec.get("data", {}),
                    note=rec.get("note", ""),
                    timestamp=rec.get("timestamp"),
                    meta=meta,
                    person_id=self.person_id,
                )
                # Add stored record to existing for subsequent dedup within batch
                existing.append(stored)
                imported += 1
                by_type[rec_type] = by_type.get(rec_type, 0) + 1

        return {
            "imported": imported,
            "skipped_dupes": skipped_dupes,
            "by_type": by_type,
        }

    # ------------------------------------------------------------------
    # Timestamp Utilities
    # ------------------------------------------------------------------

    def _normalize_timestamp(self, ts_str: str, tz_offset: str | None = None) -> str:
        """Normalize timestamp to ISO 8601 with timezone per Pitfall 4."""
        if not ts_str:
            return datetime.now(timezone.utc).isoformat(timespec="seconds")

        # If already has timezone info, return as-is
        if "+" in ts_str[10:] or ts_str.endswith("Z"):
            return ts_str.replace("Z", "+00:00")

        # Append timezone offset if provided
        if tz_offset:
            return f"{ts_str}{tz_offset}"

        # Default: assume UTC
        return f"{ts_str}+00:00"

    @staticmethod
    def _parse_iso_timestamp(ts_str: str) -> datetime:
        """Parse an ISO 8601 timestamp string into a datetime object."""
        # Handle 'Z' suffix
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)

    # ------------------------------------------------------------------
    # Date filtering
    # ------------------------------------------------------------------

    def _filter_by_date(
        self,
        records: list[dict],
        start_date: str | None,
        end_date: str | None,
    ) -> list[dict]:
        """Filter records by optional start/end date (YYYY-MM-DD)."""
        filtered = []
        for rec in records:
            ts_str = rec.get("timestamp", "")
            if not ts_str:
                continue
            date_part = ts_str[:10]
            if start_date and date_part < start_date:
                continue
            if end_date and date_part > end_date:
                continue
            filtered.append(rec)
        return filtered
