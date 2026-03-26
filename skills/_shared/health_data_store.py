#!/usr/bin/env python3
"""Shared JSONL-backed storage for VitaClaw health skills."""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Validation pattern for person_id slugs (kebab-case, starts with alphanumeric)
_PERSON_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_PERSON_ID_MAX_LEN = 32


def _validate_person_id(person_id: str | None) -> str | None:
    """Validate and normalize person_id. Returns effective_pid (None for self)."""
    if person_id is None or person_id == "self":
        return None
    if not isinstance(person_id, str):
        raise ValueError(f"person_id must be a string, got {type(person_id).__name__}")
    if len(person_id) > _PERSON_ID_MAX_LEN:
        raise ValueError(f"person_id must be at most {_PERSON_ID_MAX_LEN} characters, got {len(person_id)}")
    if not _PERSON_ID_PATTERN.match(person_id):
        raise ValueError(
            f"person_id must be kebab-case (lowercase alphanumeric + hyphens, "
            f"starting with alphanumeric): {person_id!r}"
        )
    return person_id


def _local_now() -> datetime:
    """Return the current time with local timezone info attached."""
    return datetime.now().astimezone()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_data_root(data_dir: str | None) -> Path:
    if data_dir:
        return Path(data_dir).expanduser().resolve()

    env_data_dir = (
        Path(env).expanduser().resolve() if (env := __import__("os").environ.get("VITACLAW_DATA_DIR")) else None
    )
    if env_data_dir:
        return env_data_dir

    return _repo_root() / "data"


def _normalize_boundary(value, is_end: bool = False) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")

    text = str(value).strip()
    if not text:
        return None
    if len(text) == 10 and text.count("-") == 2:
        suffix = "T23:59:59" if is_end else "T00:00:00"
        return f"{text}{suffix}"
    return text


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_number(value: float | None) -> float | None:
    if value is None:
        return None
    rounded = round(value, 3)
    if rounded.is_integer():
        return int(rounded)
    return rounded


def _normalize_timestamp(value) -> str:
    if value is None:
        return _local_now().isoformat(timespec="seconds")
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")

    text = str(value).strip()
    if len(text) == 10 and text.count("-") == 2:
        return f"{text}T00:00:00"
    return text


class HealthDataStore:
    """Append-only JSONL store with a tiny analytics layer."""

    def __init__(self, skill_name: str, data_dir: str | None = None):
        self.skill_name = skill_name
        self.data_root = _resolve_data_root(data_dir)
        self.skill_dir = self.data_root / skill_name
        self.skill_dir.mkdir(parents=True, exist_ok=True)

        self.data_file = str(self.skill_dir / "records.jsonl")
        self.config_file = str(self.skill_dir / "config.json")
        self.charts_dir = str(self.skill_dir / "charts")
        Path(self.charts_dir).mkdir(parents=True, exist_ok=True)

        # Post-append hooks: list of callables invoked with (record) after write
        self._hooks: list = []

    def add_hook(self, hook) -> None:
        """Register a post-append hook. Hook signature: (record: dict) -> Any."""
        self._hooks.append(hook)

    def remove_hook(self, hook) -> None:
        """Remove a previously registered hook."""
        self._hooks = [h for h in self._hooks if h is not hook]

    def _iter_records(self):
        data_path = Path(self.data_file)
        if not data_path.exists():
            return

        with data_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    import sys

                    print(f"[WARN] Skipping corrupted JSONL line in {self.data_file}: {line[:80]}", file=sys.stderr)
                    continue

                if isinstance(record, dict):
                    yield record

    def _read_all_records(self) -> list[dict]:
        records = list(self._iter_records() or [])
        records.sort(key=lambda item: item.get("timestamp", ""))
        return records

    # Plausible ranges for common health metrics. Values outside these ranges
    # are rejected as likely input errors.
    VITAL_BOUNDS = {
        "systolic": (40, 300),
        "diastolic": (20, 200),
        "heart_rate": (20, 300),
        "glucose": (0.5, 50.0),  # mmol/L
        "weight": (1, 500),  # kg
        "temperature": (30.0, 45.0),  # °C
        "spo2": (50, 100),  # %
    }

    def append(
        self,
        record_type: str,
        data: dict,
        note: str = "",
        timestamp=None,
        meta: dict | None = None,
        sign: bool = False,
        person_id: str | None = None,
    ) -> dict:
        """Append a health record.

        Args:
            record_type: The record type (e.g. "bp", "glucose").
            data: Metric-specific payload.
            note: Optional human-readable note.
            timestamp: Optional timestamp (str or datetime). Defaults to now.
            meta: Optional _meta dict for provenance/semantics. Structure:
                {
                    "domain": "health",          # health | cognitive | behavioral | social
                    "concept": "blood-pressure",  # concept registry ID
                    "loinc": "85354-9",           # LOINC panel code
                    "source": "manual",           # manual | device | import | agent_inferred
                    "device": null,               # device identifier if applicable
                    "confidence": 1.0,            # 0.0-1.0 confidence score
                    "twin_id": "...",             # digital twin instance ID
                }
                All fields optional. Unknown domains are stored as-is (passthrough).
        """
        # Validate and normalize person_id
        effective_pid = _validate_person_id(person_id)

        # Validate numeric health values against plausible ranges
        for key, (lo, hi) in self.VITAL_BOUNDS.items():
            if key in data:
                val = data[key]
                if isinstance(val, (int, float)) and not (lo <= val <= hi):
                    raise ValueError(f"Value out of plausible range for {key}: {val} (expected {lo}–{hi})")

        timestamp = _normalize_timestamp(timestamp)

        # Dedup: reject exact duplicates based on (type, timestamp, data_hash, person_id)
        data_hash = hashlib.md5(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
        for existing in self._iter_records():
            existing_pid = existing.get("person_id")  # None if absent (= self)
            if (
                existing.get("type") == record_type
                and existing.get("timestamp") == timestamp
                and existing_pid == effective_pid
                and hashlib.md5(
                    json.dumps(existing.get("data", {}), sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest()[:12]
                == data_hash
            ):
                return existing  # Return existing record instead of duplicating

        record = {
            "id": f"{record_type}_{timestamp.replace(':', '').replace('-', '')}_{uuid.uuid4().hex[:8]}",
            "type": record_type,
            "timestamp": timestamp,
            "skill": self.skill_name,
            "note": note,
            "data": data,
        }

        # Only add person_id to record when not "self" (D-06: absence = self)
        if effective_pid is not None:
            record["person_id"] = effective_pid

        # Attach _meta if provided — domain-agnostic envelope for Digital Twin
        if meta is not None:
            enriched_meta = dict(meta)
            enriched_meta.setdefault("domain", "health")
            enriched_meta.setdefault("ingested_at", _local_now().isoformat(timespec="seconds"))
            if "recorded_at" not in enriched_meta:
                enriched_meta["recorded_at"] = timestamp
            record["_meta"] = enriched_meta

        # Optional Ed25519 signature via TwinIdentity
        if sign:
            try:
                from .twin_identity import TwinIdentity

                identity = TwinIdentity()
                sig = identity.sign_record(record)
                if sig:
                    record.setdefault("_meta", {})["signature"] = sig
            except Exception:
                pass  # Signing is best-effort; keys may not exist

        with Path(self.data_file).open("a", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

        # Fire post-append hooks (event-driven alerts, graph population, etc.)
        for hook in self._hooks:
            try:
                hook(record)
            except Exception:
                pass  # Hook failure must never block data persistence

        return record

    def query(
        self,
        record_type: str | None = None,
        start=None,
        end=None,
        person_id: str | None = None,
    ) -> list[dict]:
        start_boundary = _normalize_boundary(start, is_end=False)
        end_boundary = _normalize_boundary(end, is_end=True)

        result = []
        for record in self._read_all_records():
            timestamp = record.get("timestamp", "")
            if record_type and record.get("type") != record_type:
                continue
            if start_boundary and timestamp < start_boundary:
                continue
            if end_boundary and timestamp > end_boundary:
                continue

            # person_id filtering (D-04):
            #   None  -> no filter (all records, backward compat)
            #   "self" -> records with absent or "self" person_id
            #   other -> records with exactly that person_id
            if person_id is not None:
                record_pid = record.get("person_id")
                if person_id == "self":
                    if record_pid is not None and record_pid != "self":
                        continue
                else:
                    if record_pid != person_id:
                        continue

            result.append(record)
        return result

    def get_latest(self, record_type: str | None = None, n: int = 1) -> list[dict]:
        if n <= 0:
            return []
        records = self.query(record_type=record_type)
        return list(reversed(records[-n:]))

    def trend(self, record_type: str, field: str, window: int = 90) -> dict:
        start = _local_now() - timedelta(days=window)
        records = self.query(record_type=record_type, start=start)

        points: list[tuple[str, float]] = []
        for record in records:
            value = _safe_float(record.get("data", {}).get(field))
            if value is None:
                continue
            points.append((record.get("timestamp", ""), value))

        values = [value for _, value in points]
        count = len(values)
        if count == 0:
            return {
                "count": 0,
                "mean": None,
                "slope": 0,
                "direction": "stable",
                "values": [],
            }

        mean = sum(values) / count
        if count < 2:
            slope = 0.0
        else:
            x_values = list(range(count))
            x_mean = sum(x_values) / count
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            numerator = sum((x - x_mean) * (y - mean) for x, y in zip(x_values, values))
            slope = numerator / denominator if denominator else 0.0

        tolerance = max(abs(mean) * 0.005, 0.1)
        if slope > tolerance:
            direction = "rising"
        elif slope < -tolerance:
            direction = "falling"
        else:
            direction = "stable"

        return {
            "count": count,
            "mean": _round_number(mean),
            "slope": _round_number(slope),
            "direction": direction,
            "values": [_round_number(value) for value in values],
        }

    def consecutive_check(self, record_type: str, field: str, direction: str, count: int = 3) -> bool:
        if count <= 1:
            return False

        values = []
        for record in self.query(record_type=record_type):
            value = _safe_float(record.get("data", {}).get(field))
            if value is not None:
                values.append(value)

        latest_values = values[-count:]
        if len(latest_values) < count:
            return False

        if direction == "rising":
            return all(curr > prev for prev, curr in zip(latest_values, latest_values[1:]))
        if direction == "falling":
            return all(curr < prev for prev, curr in zip(latest_values, latest_values[1:]))
        raise ValueError("direction must be 'rising' or 'falling'")

    # ── Data Observability ─────────────────────────────────

    def stats(self, person_id: str | None = None) -> dict:
        """Return per-skill data statistics.

        Args:
            person_id: Optional filter. None=all records, "self"=primary user,
                       other=specific person_id.

        Returns:
            Dict with record_count, last_updated, earliest_record,
            latest_record, time_span_days.
        """
        count = 0
        earliest: str | None = None
        latest: str | None = None

        for record in self._iter_records():
            # Apply person_id filtering (same logic as query())
            if person_id is not None:
                record_pid = record.get("person_id")
                if person_id == "self":
                    if record_pid is not None and record_pid != "self":
                        continue
                else:
                    if record_pid != person_id:
                        continue

            ts = record.get("timestamp", "")
            if not ts:
                count += 1
                continue

            count += 1
            if earliest is None or ts < earliest:
                earliest = ts
            if latest is None or ts > latest:
                latest = ts

        # Calculate time span
        time_span_days = 0
        if count >= 2 and earliest and latest:
            try:
                fmt = "%Y-%m-%dT%H:%M:%S"
                earliest_dt = datetime.strptime(earliest[:19], fmt)
                latest_dt = datetime.strptime(latest[:19], fmt)
                time_span_days = (latest_dt - earliest_dt).days
            except (ValueError, IndexError):
                time_span_days = 0

        return {
            "record_count": count,
            "last_updated": latest,
            "earliest_record": earliest,
            "latest_record": latest,
            "time_span_days": time_span_days,
        }

    @classmethod
    def global_stats(cls, data_dir: str | None = None, person_id: str | None = None) -> dict:
        """Aggregate stats across all skill data directories.

        Args:
            data_dir: Optional override for data root directory.
            person_id: Optional person_id filter applied to each skill.

        Returns:
            Dict with skills (name->stats), total_records, skills_count.
        """
        data_root = _resolve_data_root(data_dir)
        skills: dict[str, dict] = {}
        total_records = 0

        if data_root.is_dir():
            for child in sorted(data_root.iterdir()):
                if child.is_dir() and (child / "records.jsonl").exists():
                    store = cls(child.name, data_dir=str(data_root))
                    skill_stats = store.stats(person_id=person_id)
                    if skill_stats["record_count"] > 0:
                        skills[child.name] = skill_stats
                        total_records += skill_stats["record_count"]

        return {
            "skills": skills,
            "total_records": total_records,
            "skills_count": len(skills),
        }

    def get_config(self) -> dict:
        config_path = Path(self.config_file)
        if not config_path.exists():
            return {}
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def set_config(self, key: str, value) -> dict:
        config = self.get_config()
        config[key] = value
        Path(self.config_file).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return config
