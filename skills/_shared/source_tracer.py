#!/usr/bin/env python3
"""Bidirectional source tracing for VitaClaw health memory.

Given any summary/digest, trace back to the original JSONL records.
Given any JSONL record, find which summaries reference it.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .health_data_store import HealthDataStore


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class SourceTracer:
    """Trace data lineage between summaries and raw JSONL records."""

    def __init__(
        self,
        data_dir: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
    ):
        if workspace_root:
            self._workspace = Path(workspace_root)
        else:
            self._workspace = _repo_root()

        if memory_dir:
            self._memory = Path(memory_dir)
        else:
            self._memory = self._workspace / "memory" / "health"

        if data_dir:
            self._data = Path(data_dir)
        else:
            self._data = self._workspace / "data"

    def trace_summary_to_records(
        self,
        concept: str,
        date: str | None = None,
        window_days: int = 7,
    ) -> list[dict]:
        """Given a concept mentioned in a summary, find the underlying JSONL records.

        Args:
            concept: Concept slug (e.g. "blood-pressure") or record type (e.g. "bp").
            date: Reference date (YYYY-MM-DD). Defaults to today.
            window_days: How many days back to search.

        Returns:
            List of matching JSONL records, sorted by timestamp.
        """
        try:
            from .concept_resolver import ConceptResolver

            resolver = ConceptResolver()
            concept_id, defn = resolver.resolve_concept(concept)
            producers = defn.get("producers", [])
        except (ImportError, KeyError):
            producers = []

        if not producers:
            return []

        if date:
            ref_date = datetime.fromisoformat(date)
        else:
            ref_date = datetime.now()

        from datetime import timedelta

        start = (ref_date - timedelta(days=window_days)).isoformat()[:10]
        end = ref_date.isoformat()[:10]

        records: list[dict] = []
        for producer in producers:
            skill = producer.get("skill", "")
            record_type = producer.get("record_type", "")
            if skill and record_type:
                store = HealthDataStore(skill, data_dir=str(self._data))
                records.extend(store.query(record_type, start=start, end=end))

        records.sort(key=lambda r: r.get("timestamp", ""))
        return records

    def trace_record_to_summaries(self, record: dict) -> list[dict]:
        """Given a JSONL record, find which memory files might reference it.

        Returns list of {path, type, relevance} for memory files that
        likely contain derived information from this record.
        """
        timestamp = record.get("timestamp", "")
        record_date = timestamp[:10] if timestamp else ""
        record_type = record.get("type", "")

        results: list[dict] = []

        if not record_date:
            return results

        # Check daily log
        daily_path = self._memory / "daily" / f"{record_date}.md"
        if daily_path.exists():
            results.append(
                {
                    "path": str(daily_path),
                    "type": "daily",
                    "relevance": "direct",
                }
            )

        # Check item files — map record type to item slug
        type_to_item = {
            "bp": "blood-pressure",
            "glucose": "blood-sugar",
            "weight": "weight",
            "sleep_session": "sleep",
            "intake": "caffeine",
            "dose": "medications",
            "dose_log": "supplements",
            "heart_rate": "heart-rate-hrv",
            "hrv": "heart-rate-hrv",
        }
        item_slug = type_to_item.get(record_type)
        if item_slug:
            item_path = self._memory / "items" / f"{item_slug}.md"
            if item_path.exists():
                results.append(
                    {
                        "path": str(item_path),
                        "type": "item",
                        "relevance": "aggregated",
                    }
                )

        # Check weekly digest
        weekly_path = self._memory / "weekly-digest.md"
        if weekly_path.exists():
            results.append(
                {
                    "path": str(weekly_path),
                    "type": "weekly_digest",
                    "relevance": "summarized",
                }
            )

        # Check monthly digest
        monthly_path = self._memory / "monthly-digest.md"
        if monthly_path.exists():
            results.append(
                {
                    "path": str(monthly_path),
                    "type": "monthly_digest",
                    "relevance": "summarized",
                }
            )

        return results

    def build_source_comment(self, source_refs: list[str]) -> str:
        """Format source references as an HTML comment for embedding in markdown.

        Example output:
            <!-- sources: items/blood-pressure.md, daily/2026-03-20.md, heartbeat:2026-03-20 -->
        """
        if not source_refs:
            return ""
        return f"<!-- sources: {', '.join(source_refs)} -->"
