#!/usr/bin/env python3
"""Auto-populate the knowledge graph from health record ingestion.

Hooks into HealthDataStore records to create graph nodes and edges.
When a BP record is appended, this creates:
  - An episode node for the measurement event
  - Entity nodes for the concept (blood-pressure) if not exists
  - Edges connecting episode → entity
"""

from __future__ import annotations

from .health_knowledge_graph import HealthKnowledgeGraph


class GraphPopulator:
    """Populate the knowledge graph from health records."""

    def __init__(self, graph: HealthKnowledgeGraph | None = None, data_dir: str | None = None):
        self._graph = graph or HealthKnowledgeGraph(data_dir=data_dir)

    @property
    def graph(self) -> HealthKnowledgeGraph:
        return self._graph

    def ingest_record(self, record: dict) -> dict:
        """Process a JSONL record and add nodes/edges to the graph.

        Returns summary of created nodes/edges.
        """
        record_type = record.get("type", "")
        record_id = record.get("id", "")
        timestamp = record.get("timestamp", "")
        data = record.get("data", {})
        meta = record.get("_meta", {})
        concept = meta.get("concept", "")

        created = {"episodes": [], "entities": [], "edges": []}

        if not record_type:
            return created

        # Resolve concept from meta or registry
        if not concept:
            try:
                from .concept_resolver import ConceptResolver

                resolver = ConceptResolver()
                concept = resolver.resolve_from_type(record_type) or ""
            except (ImportError, KeyError):
                concept = record_type

        # 1. Create episode node for this measurement
        episode = self._graph.add_episode(
            name=f"{concept or record_type}:{timestamp}",
            domain=meta.get("domain", "health"),
            properties={"record_type": record_type, "source": meta.get("source", "")},
            valid_at=timestamp,
            source_record_ids=[record_id],
        )
        created["episodes"].append(episode["id"])

        # 2. Ensure concept entity exists
        if concept:
            entity = self._graph.add_entity(
                name=concept,
                entity_type="health_concept",
                domain=meta.get("domain", "health"),
            )
            created["entities"].append(entity["id"])

            # 3. Connect episode → entity
            edge = self._graph.add_edge(
                source_id=episode["id"],
                target_id=entity["id"],
                relation="measured_by",
                valid_at=timestamp,
            )
            created["edges"].append(edge["id"])

        # 4. Extract medication entities from medication dose records
        if record_type == "dose":
            med_name = data.get("name", "") or data.get("medication", "")
            if med_name:
                med_entity = self._graph.add_entity(
                    name=med_name,
                    entity_type="medication",
                    domain="health",
                )
                created["entities"].append(med_entity["id"])
                edge = self._graph.add_edge(
                    source_id=episode["id"],
                    target_id=med_entity["id"],
                    relation="administered",
                    valid_at=timestamp,
                )
                created["edges"].append(edge["id"])

                # Link medication to concept it treats (if concept is known)
                if concept:
                    concept_entity = self._graph.find_node_by_name(concept)
                    if concept_entity:
                        self._graph.add_edge(
                            source_id=med_entity["id"],
                            target_id=concept_entity["id"],
                            relation="treats",
                        )

        # 5. Extract supplement entities
        if record_type == "dose_log":
            supp_name = data.get("supplement", "") or data.get("name", "")
            if supp_name:
                supp_entity = self._graph.add_entity(
                    name=supp_name,
                    entity_type="medication",  # supplements as medication subtype
                    domain="health",
                    properties={"subtype": "supplement"},
                )
                created["entities"].append(supp_entity["id"])
                self._graph.add_edge(
                    source_id=episode["id"],
                    target_id=supp_entity["id"],
                    relation="administered",
                    valid_at=timestamp,
                )

        return created

    def ingest_batch(self, records: list[dict]) -> dict:
        """Process multiple records. Returns aggregate summary."""
        total = {"episodes": 0, "entities": 0, "edges": 0}
        for record in records:
            result = self.ingest_record(record)
            total["episodes"] += len(result["episodes"])
            total["entities"] += len(result["entities"])
            total["edges"] += len(result["edges"])
        return total
