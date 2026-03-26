#!/usr/bin/env python3
"""File-system-first knowledge graph for VitaClaw Digital Twin.

Three-layer node model (Graphiti-inspired):
  - Episode: timestamped events (a BP reading, a medication dose)
  - Entity: persistent concepts (blood-pressure, metformin, hypertension)
  - Community: emergent patterns (cardiovascular risk cluster)

Storage: JSONL append-only files in data/_graph/
  - nodes.jsonl
  - edges.jsonl

Bi-temporal timestamps (Graphiti-style):
  - created_at: when the node/edge was added to the graph
  - valid_at: when the fact became true in the real world
  - invalid_at: when the fact stopped being true (soft-delete)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _local_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class HealthKnowledgeGraph:
    """JSONL-backed knowledge graph with in-memory index."""

    # v1 entity types (health domain)
    HEALTH_ENTITY_TYPES = {
        "health_concept",
        "medication",
        "condition",
        "device",
        "body_system",
    }
    # v2 entity types (future domains — accepted but not specially processed)
    EXTENDED_ENTITY_TYPES = {
        "preference",
        "personality_trait",
        "life_event",
        "person",
        "behavioral_pattern",
    }
    ALL_TYPES = {"episode", "community"} | HEALTH_ENTITY_TYPES | EXTENDED_ENTITY_TYPES

    def __init__(self, data_dir: str | None = None):
        if data_dir:
            self._graph_dir = Path(data_dir) / "_graph"
        else:
            self._graph_dir = _repo_root() / "data" / "_graph"
        self._graph_dir.mkdir(parents=True, exist_ok=True)

        self._nodes_file = self._graph_dir / "nodes.jsonl"
        self._edges_file = self._graph_dir / "edges.jsonl"

        # In-memory indexes (loaded lazily)
        self._nodes: dict[str, dict] = {}
        self._edges: dict[str, dict] = {}
        self._adjacency: dict[str, list[str]] = {}  # node_id -> [edge_ids]
        self._name_index: dict[str, str] = {}  # lowercase name -> node_id
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._load_nodes()
        self._load_edges()
        self._loaded = True

    def _load_nodes(self) -> None:
        if not self._nodes_file.exists():
            return
        for line in self._nodes_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                node = json.loads(line)
                node_id = node.get("id", "")
                if node_id:
                    self._nodes[node_id] = node
                    name = node.get("name", "").lower()
                    if name:
                        self._name_index[name] = node_id
            except json.JSONDecodeError:
                continue

    def _load_edges(self) -> None:
        if not self._edges_file.exists():
            return
        for line in self._edges_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                edge = json.loads(line)
                edge_id = edge.get("id", "")
                if edge_id:
                    self._edges[edge_id] = edge
                    src = edge.get("source", "")
                    tgt = edge.get("target", "")
                    if src:
                        self._adjacency.setdefault(src, []).append(edge_id)
                    if tgt:
                        self._adjacency.setdefault(tgt, []).append(edge_id)
            except json.JSONDecodeError:
                continue

    def _append_node(self, node: dict) -> None:
        with self._nodes_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")

    def _append_edge(self, edge: dict) -> None:
        with self._edges_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    # ── Node Operations ──────────────────────────────────────

    def add_entity(
        self,
        name: str,
        entity_type: str,
        domain: str = "health",
        properties: dict | None = None,
        valid_at: str | None = None,
        source_record_ids: list[str] | None = None,
    ) -> dict:
        """Add or return an entity node."""
        self._ensure_loaded()

        # Check if entity already exists by name
        existing_id = self._name_index.get(name.lower())
        if existing_id and existing_id in self._nodes:
            return self._nodes[existing_id]

        now = _local_now()
        node = {
            "id": f"entity_{uuid.uuid4().hex[:8]}",
            "type": entity_type,
            "name": name,
            "domain": domain,
            "layer": "entity",
            "properties": properties or {},
            "created_at": now,
            "valid_at": valid_at or now,
            "invalid_at": None,
            "source_record_ids": source_record_ids or [],
        }
        self._nodes[node["id"]] = node
        self._name_index[name.lower()] = node["id"]
        self._append_node(node)
        return node

    def add_episode(
        self,
        name: str,
        domain: str = "health",
        properties: dict | None = None,
        valid_at: str | None = None,
        source_record_ids: list[str] | None = None,
    ) -> dict:
        """Add an episode node (timestamped event)."""
        self._ensure_loaded()
        now = _local_now()
        node = {
            "id": f"episode_{uuid.uuid4().hex[:8]}",
            "type": "episode",
            "name": name,
            "domain": domain,
            "layer": "episode",
            "properties": properties or {},
            "created_at": now,
            "valid_at": valid_at or now,
            "invalid_at": None,
            "source_record_ids": source_record_ids or [],
        }
        self._nodes[node["id"]] = node
        self._append_node(node)
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        properties: dict | None = None,
        valid_at: str | None = None,
    ) -> dict:
        """Add a relationship edge between two nodes."""
        self._ensure_loaded()

        # Check for existing edge with same source/target/relation
        for eid in self._adjacency.get(source_id, []):
            e = self._edges.get(eid, {})
            if e.get("target") == target_id and e.get("relation") == relation and e.get("invalid_at") is None:
                return e

        now = _local_now()
        edge = {
            "id": f"edge_{uuid.uuid4().hex[:8]}",
            "source": source_id,
            "target": target_id,
            "relation": relation,
            "weight": weight,
            "properties": properties or {},
            "created_at": now,
            "valid_at": valid_at or now,
            "invalid_at": None,
        }
        self._edges[edge["id"]] = edge
        self._adjacency.setdefault(source_id, []).append(edge["id"])
        self._adjacency.setdefault(target_id, []).append(edge["id"])
        self._append_edge(edge)
        return edge

    # ── Query Operations ─────────────────────────────────────

    def get_node(self, node_id: str) -> dict | None:
        self._ensure_loaded()
        return self._nodes.get(node_id)

    def find_node_by_name(self, name: str) -> dict | None:
        self._ensure_loaded()
        node_id = self._name_index.get(name.lower())
        return self._nodes.get(node_id) if node_id else None

    def query_neighbors(self, node_id: str, relation: str | None = None, depth: int = 1) -> list[dict]:
        """Find neighboring nodes, optionally filtered by relation type."""
        self._ensure_loaded()
        visited: set[str] = set()
        result: list[dict] = []
        frontier = [node_id]

        for _ in range(depth):
            next_frontier: list[str] = []
            for nid in frontier:
                if nid in visited:
                    continue
                visited.add(nid)
                for eid in self._adjacency.get(nid, []):
                    edge = self._edges.get(eid, {})
                    if edge.get("invalid_at"):
                        continue
                    if relation and edge.get("relation") != relation:
                        continue
                    neighbor_id = edge["target"] if edge["source"] == nid else edge["source"]
                    if neighbor_id not in visited:
                        neighbor = self._nodes.get(neighbor_id)
                        if neighbor and not neighbor.get("invalid_at"):
                            result.append(neighbor)
                            next_frontier.append(neighbor_id)
            frontier = next_frontier

        return result

    def query_temporal(
        self,
        entity_name: str,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict]:
        """Find episodes connected to an entity within a time range."""
        self._ensure_loaded()
        entity = self.find_node_by_name(entity_name)
        if not entity:
            return []

        episodes = self.query_neighbors(entity["id"])
        result: list[dict] = []
        for ep in episodes:
            if ep.get("layer") != "episode":
                continue
            valid_at = ep.get("valid_at", "")
            if start and valid_at < start:
                continue
            if end and valid_at > end:
                continue
            result.append(ep)

        result.sort(key=lambda n: n.get("valid_at", ""))
        return result

    def stats(self) -> dict:
        """Return graph statistics."""
        self._ensure_loaded()
        active_nodes = [n for n in self._nodes.values() if not n.get("invalid_at")]
        active_edges = [e for e in self._edges.values() if not e.get("invalid_at")]
        return {
            "total_nodes": len(self._nodes),
            "active_nodes": len(active_nodes),
            "total_edges": len(self._edges),
            "active_edges": len(active_edges),
            "node_types": list(set(n.get("type", "") for n in active_nodes)),
        }
