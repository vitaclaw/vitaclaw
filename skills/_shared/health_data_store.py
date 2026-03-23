#!/usr/bin/env python3
"""Shared JSONL-backed storage for VitaClaw health skills."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_data_root(data_dir: str | None) -> Path:
    if data_dir:
        return Path(data_dir).expanduser().resolve()

    env_data_dir = (
        Path(env).expanduser().resolve()
        if (env := __import__("os").environ.get("VITACLAW_DATA_DIR"))
        else None
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
        return datetime.now().isoformat(timespec="seconds")
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
                    continue

                if isinstance(record, dict):
                    yield record

    def _read_all_records(self) -> list[dict]:
        records = list(self._iter_records() or [])
        records.sort(key=lambda item: item.get("timestamp", ""))
        return records

    def append(self, record_type: str, data: dict, note: str = "", timestamp=None) -> dict:
        timestamp = _normalize_timestamp(timestamp)
        record = {
            "id": f"{record_type}_{timestamp.replace(':', '').replace('-', '')}_{uuid.uuid4().hex[:8]}",
            "type": record_type,
            "timestamp": timestamp,
            "skill": self.skill_name,
            "note": note,
            "data": data,
        }

        with Path(self.data_file).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    def query(self, record_type: str | None = None, start=None, end=None) -> list[dict]:
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
            result.append(record)
        return result

    def get_latest(self, record_type: str | None = None, n: int = 1) -> list[dict]:
        if n <= 0:
            return []
        records = self.query(record_type=record_type)
        return list(reversed(records[-n:]))

    def trend(self, record_type: str, field: str, window: int = 90) -> dict:
        start = datetime.now() - timedelta(days=window)
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

    def consecutive_check(
        self, record_type: str, field: str, direction: str, count: int = 3
    ) -> bool:
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
        Path(self.config_file).write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return config
