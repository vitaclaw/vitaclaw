#!/usr/bin/env python3
"""Read-through helper for aggregating data across VitaClaw skills.

v2: Registry-driven discovery. New concepts added to health-concepts.yaml
are automatically discoverable via read() — no code changes needed.
Legacy per-concept methods preserved as thin wrappers.
"""

from __future__ import annotations

from .health_data_store import HealthDataStore


class CrossSkillReader:
    """Provide a small, stable API for multi-skill data access.

    Primary API (registry-driven):
        reader.read("blood-pressure", start, end)  # discovers all producers
        reader.read_all(["blood-pressure", "weight"], start, end)

    Legacy API (preserved for backward compatibility):
        reader.read_blood_pressure(start, end)
        reader.read_glucose_data(start, end)
    """

    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir
        self._stores: dict[str, HealthDataStore] = {}
        self._resolver = None  # lazy-loaded

    def _store(self, skill_name: str) -> HealthDataStore:
        if skill_name not in self._stores:
            self._stores[skill_name] = HealthDataStore(skill_name, data_dir=self.data_dir)
        return self._stores[skill_name]

    def _get_resolver(self):
        """Lazy-load ConceptResolver to avoid import cost when not needed."""
        if self._resolver is None:
            try:
                from .concept_resolver import ConceptResolver

                self._resolver = ConceptResolver()
            except Exception:
                self._resolver = None
        return self._resolver

    # ── Registry-driven API ──────────────────────────────────

    def read(self, concept: str, start=None, end=None, person_id: str | None = None) -> list[dict]:
        """Read records for a concept by querying all registered producers.

        Args:
            concept: Concept ID (e.g. "blood-pressure") or canonical_type (e.g. "bp").
            start: Start time filter.
            end: End time filter.
            person_id: Optional person filter. None=all, "self"=primary user, other=specific person.

        Returns:
            Merged and time-sorted records from all producer skills.
        """
        resolver = self._get_resolver()
        if resolver is None:
            return []

        try:
            concept_id, defn = resolver.resolve_concept(concept)
        except KeyError:
            return []

        producers = defn.get("producers", [])
        if not producers:
            return []

        merged: list[dict] = []
        for producer in producers:
            skill = producer.get("skill", "")
            record_type = producer.get("record_type", "")
            if skill and record_type:
                records = self._store(skill).query(record_type, start=start, end=end, person_id=person_id)
                merged.extend(records)

        merged.sort(key=lambda r: r.get("timestamp", ""))
        return merged

    def read_all(
        self, concepts: list[str], start=None, end=None, person_id: str | None = None
    ) -> dict[str, list[dict]]:
        """Read multiple concepts at once. Returns {concept_id: [records]}."""
        result: dict[str, list[dict]] = {}
        resolver = self._get_resolver()
        if resolver is None:
            return result

        for concept in concepts:
            try:
                concept_id, _ = resolver.resolve_concept(concept)
            except KeyError:
                concept_id = concept
            result[concept_id] = self.read(concept, start=start, end=end, person_id=person_id)
        return result

    # ── Legacy API (thin wrappers — backward compatible) ─────

    def read_caffeine_intakes(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("caffeine-tracker").query("intake", start=start, end=end, person_id=person_id)

    def read_sleep_data(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("sleep-analyzer").query("sleep_session", start=start, end=end, person_id=person_id)

    def read_supplement_doses(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("supplement-manager").query("dose_log", start=start, end=end, person_id=person_id)

    def read_supplement_regimen(self, person_id: str | None = None) -> list[dict]:
        records = self._store("supplement-manager").query("supplement", person_id=person_id)
        return [record for record in records if record.get("data", {}).get("status") == "active"]

    def read_blood_pressure(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("blood-pressure-tracker").query("bp", start=start, end=end, person_id=person_id)

    def read_chronic_blood_pressure(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("chronic-condition-monitor").query("bp", start=start, end=end, person_id=person_id)

    def read_glucose_data(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("chronic-condition-monitor").query("glucose", start=start, end=end, person_id=person_id)

    def read_weight_data(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("chronic-condition-monitor").query("weight", start=start, end=end, person_id=person_id)

    def read_medication_doses(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("medication-reminder").query("dose", start=start, end=end, person_id=person_id)

    def read_heart_rate(self, start=None, end=None, person_id: str | None = None) -> list[dict]:
        return self._store("wearable-analysis-agent").query("heart_rate", start=start, end=end, person_id=person_id)

    # ── Graph-driven queries ──────────────────────────────────

    def _get_graph(self):
        """Lazy-load HealthKnowledgeGraph."""
        if not hasattr(self, "_graph"):
            try:
                from .health_knowledge_graph import HealthKnowledgeGraph

                self._graph = HealthKnowledgeGraph(data_dir=self.data_dir)
            except Exception:
                self._graph = None
        return self._graph

    def _get_correlation_engine(self):
        """Lazy-load CorrelationEngine."""
        if not hasattr(self, "_correlation_engine"):
            try:
                from .correlation_engine import CorrelationEngine

                self._correlation_engine = CorrelationEngine(data_dir=self.data_dir)
            except Exception:
                self._correlation_engine = None
        return self._correlation_engine

    def related_to(self, concept: str, depth: int = 2) -> list[dict]:
        """Query related entities via the knowledge graph.

        Args:
            concept: Concept name (e.g. "blood-pressure").
            depth: Traversal depth in the graph (default 2).

        Returns:
            List of related entity dicts from the knowledge graph.
        """
        graph = self._get_graph()
        if graph is None:
            return []
        node = graph.find_node_by_name(concept)
        if not node:
            return []
        return graph.query_neighbors(node["id"], depth=depth)

    def correlations(self, concept_a: str, concept_b: str, window: int = 30) -> dict:
        """Compute time-series correlation between two concepts.

        Args:
            concept_a: First concept name.
            concept_b: Second concept name.
            window: Number of days to analyze.

        Returns:
            Dict with correlation, direction, strength, sample_count.
        """
        engine = self._get_correlation_engine()
        if engine is None:
            return {"correlation": 0.0, "direction": "none", "strength": "none", "sample_count": 0}

        # Resolve primary fields from concept registry
        resolver = self._get_resolver()
        field_a = self._primary_field(concept_a, resolver)
        field_b = self._primary_field(concept_b, resolver)

        result = engine.correlate(concept_a, field_a, concept_b, field_b, window_days=window)
        return result.to_dict()

    @staticmethod
    def _primary_field(concept: str, resolver) -> str:
        """Get the first numeric field name for a concept from the registry."""
        if resolver is None:
            return "value"
        try:
            defn = resolver.get_concept(concept)
            for fname, fdef in defn.get("fields", {}).items():
                if fdef.get("type") in ("integer", "number"):
                    return fname
        except (KeyError, AttributeError):
            pass
        return "value"
