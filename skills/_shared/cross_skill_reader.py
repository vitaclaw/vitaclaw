#!/usr/bin/env python3
"""Read-through helper for aggregating data across VitaClaw skills."""

from __future__ import annotations

from health_data_store import HealthDataStore


class CrossSkillReader:
    """Provide a small, stable API for multi-skill data access."""

    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir
        self._stores: dict[str, HealthDataStore] = {}

    def _store(self, skill_name: str) -> HealthDataStore:
        if skill_name not in self._stores:
            self._stores[skill_name] = HealthDataStore(skill_name, data_dir=self.data_dir)
        return self._stores[skill_name]

    def read_caffeine_intakes(self, start=None, end=None) -> list[dict]:
        return self._store("caffeine-tracker").query("intake", start=start, end=end)

    def read_sleep_data(self, start=None, end=None) -> list[dict]:
        return self._store("sleep-analyzer").query("sleep_session", start=start, end=end)

    def read_supplement_doses(self, start=None, end=None) -> list[dict]:
        return self._store("supplement-manager").query("dose_log", start=start, end=end)

    def read_supplement_regimen(self) -> list[dict]:
        records = self._store("supplement-manager").query("supplement")
        return [record for record in records if record.get("data", {}).get("status") == "active"]

    def read_blood_pressure(self, start=None, end=None) -> list[dict]:
        return self._store("blood-pressure-tracker").query("bp", start=start, end=end)

    def read_chronic_blood_pressure(self, start=None, end=None) -> list[dict]:
        return self._store("chronic-condition-monitor").query("bp", start=start, end=end)

    def read_glucose_data(self, start=None, end=None) -> list[dict]:
        return self._store("chronic-condition-monitor").query("glucose", start=start, end=end)

    def read_weight_data(self, start=None, end=None) -> list[dict]:
        return self._store("chronic-condition-monitor").query("weight", start=start, end=end)

    def read_medication_doses(self, start=None, end=None) -> list[dict]:
        return self._store("medication-reminder").query("dose", start=start, end=end)
