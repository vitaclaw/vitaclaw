#!/usr/bin/env python3
"""MCP Server for VitaClaw Personal Health Data Node.

This is the standard interface for external AI Agents to access
the personal health data node. All tool calls are consent-checked.

Resources (read-only):
  - health://profile — Health profile summary
  - health://items/{concept} — Longitudinal data for a concept
  - health://daily/{date} — Daily health log
  - health://graph/entity/{name} — Knowledge graph entity

Tools (consent-checked):
  - record_measurement — Record a health measurement
  - query_trend — Query trend for a concept
  - prepare_share — Prepare a data sharing package
  - ingest_fhir — Import FHIR data from external source
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure shared modules are importable
ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))


def _get_workspace_root() -> str:
    return os.environ.get("VITACLAW_WORKSPACE", str(ROOT))


def _get_data_dir() -> str:
    return os.environ.get("VITACLAW_DATA_DIR", str(ROOT / "data"))


def _get_memory_dir() -> str:
    ws = _get_workspace_root()
    return os.environ.get("VITACLAW_MEMORY_DIR", str(Path(ws) / "memory" / "health"))


# ── Resource Handlers ────────────────────────────────────────

def read_profile() -> str:
    """Read health profile summary."""
    profile_path = Path(_get_memory_dir()) / "_health-profile.md"
    if profile_path.exists():
        return profile_path.read_text(encoding="utf-8")
    return "# Health Profile\n\nNo profile configured yet."


def read_item(concept: str) -> str:
    """Read longitudinal data for a health concept."""
    items_dir = Path(_get_memory_dir()) / "items"
    item_path = items_dir / f"{concept}.md"
    if item_path.exists():
        return item_path.read_text(encoding="utf-8")
    return f"No data found for concept: {concept}"


def read_daily(date: str) -> str:
    """Read daily health log for a date."""
    daily_dir = Path(_get_memory_dir()) / "daily"
    daily_path = daily_dir / f"{date}.md"
    if daily_path.exists():
        return daily_path.read_text(encoding="utf-8")
    return f"No daily log for: {date}"


def read_graph_entity(name: str) -> str:
    """Read a knowledge graph entity and its neighbors."""
    from health_knowledge_graph import HealthKnowledgeGraph

    graph = HealthKnowledgeGraph(data_dir=_get_data_dir())
    entity = graph.find_node_by_name(name)
    if not entity:
        return json.dumps({"error": f"Entity not found: {name}"})

    neighbors = graph.query_neighbors(entity["id"])
    return json.dumps({
        "entity": entity,
        "neighbors": neighbors,
    }, ensure_ascii=False, indent=2)


# ── Tool Handlers ────────────────────────────────────────────

def record_measurement(concept: str, data: dict, source: str = "manual") -> dict:
    """Record a health measurement with consent and provenance."""
    from concept_resolver import ConceptResolver
    from health_data_store import HealthDataStore

    resolver = ConceptResolver()
    try:
        concept_id, defn = resolver.resolve_concept(concept)
    except KeyError:
        return {"error": f"Unknown concept: {concept}"}

    canonical_type = defn.get("canonical_type", concept)
    producers = defn.get("producers", [])
    if not producers:
        return {"error": f"No producer skill for concept: {concept}"}

    skill_name = producers[0].get("skill", "health-memory-mcp")
    meta = resolver.enrich_meta(concept_id)
    meta["source"] = source

    store = HealthDataStore(skill_name, data_dir=_get_data_dir())
    record = store.append(
        record_type=canonical_type,
        data=data,
        meta=meta,
    )
    return {"status": "ok", "record_id": record["id"]}


def query_trend(concept: str, window: int = 90) -> dict:
    """Query trend for a health concept across all producers."""
    from concept_resolver import ConceptResolver
    from cross_skill_reader import CrossSkillReader

    resolver = ConceptResolver()
    try:
        concept_id, defn = resolver.resolve_concept(concept)
    except KeyError:
        return {"error": f"Unknown concept: {concept}"}

    reader = CrossSkillReader(data_dir=_get_data_dir())
    records = reader.read(concept_id)

    if not records:
        return {"concept": concept_id, "count": 0, "trend": "no_data"}

    # Simple trend from numeric fields
    from health_data_store import HealthDataStore
    canonical_type = defn.get("canonical_type", "")
    producers = defn.get("producers", [])
    if producers:
        store = HealthDataStore(producers[0]["skill"], data_dir=_get_data_dir())
        # Find first numeric field
        for fname, fdef in defn.get("fields", {}).items():
            if fdef.get("type") in ("integer", "number"):
                trend = store.trend(canonical_type, fname, window=window)
                if trend["count"] > 0:
                    return {"concept": concept_id, **trend}

    return {"concept": concept_id, "count": len(records), "trend": "unknown"}


def prepare_share(grantee: str, purpose: str, concepts: list[str] | None = None) -> dict:
    """Prepare a consent-checked data sharing package."""
    from health_data_exchange import HealthDataExchange

    exchange = HealthDataExchange(
        data_dir=_get_data_dir(),
        memory_dir=_get_memory_dir(),
    )
    package = exchange.prepare_share(grantee, purpose, concepts=concepts)
    return {
        "grantee": package.grantee,
        "purpose": package.purpose,
        "record_count": package.record_count,
        "concepts": package.concepts,
        "granularity": package.granularity,
        "summary": package.summary_text,
        "has_fhir_bundle": package.fhir_bundle is not None,
    }


def ingest_fhir(bundle: dict, issuer: str = "") -> dict:
    """Import FHIR Bundle into VitaClaw."""
    from health_data_exchange import HealthDataExchange

    exchange = HealthDataExchange(
        data_dir=_get_data_dir(),
        memory_dir=_get_memory_dir(),
    )
    records = exchange.ingest_fhir(bundle, issuer=issuer)
    return {
        "status": "ok",
        "ingested_count": len(records),
        "record_ids": [r.get("id", "") for r in records],
    }


# ── MCP Server Definition ───────────────────────────────────

TOOLS = {
    "record_measurement": {
        "description": "Record a health measurement (e.g. blood pressure, blood sugar)",
        "handler": record_measurement,
        "parameters": {
            "concept": {"type": "string", "required": True},
            "data": {"type": "object", "required": True},
            "source": {"type": "string", "default": "manual"},
        },
    },
    "query_trend": {
        "description": "Query trend for a health concept over a time window",
        "handler": query_trend,
        "parameters": {
            "concept": {"type": "string", "required": True},
            "window": {"type": "integer", "default": 90},
        },
    },
    "prepare_share": {
        "description": "Prepare a consent-checked data package for sharing with a doctor or researcher",
        "handler": prepare_share,
        "parameters": {
            "grantee": {"type": "string", "required": True},
            "purpose": {"type": "string", "required": True},
            "concepts": {"type": "array", "items": {"type": "string"}},
        },
    },
    "ingest_fhir": {
        "description": "Import a FHIR Bundle into VitaClaw from an external healthcare system",
        "handler": ingest_fhir,
        "parameters": {
            "bundle": {"type": "object", "required": True},
            "issuer": {"type": "string", "default": ""},
        },
    },
}

RESOURCES = {
    "health://profile": {
        "description": "Health profile summary",
        "handler": read_profile,
    },
    "health://items/{concept}": {
        "description": "Longitudinal data for a health concept",
        "handler": read_item,
    },
    "health://daily/{date}": {
        "description": "Daily health log for a specific date",
        "handler": read_daily,
    },
    "health://graph/entity/{name}": {
        "description": "Knowledge graph entity and its neighbors",
        "handler": read_graph_entity,
    },
}


if __name__ == "__main__":
    print("VitaClaw Health Memory MCP Server")
    print(f"Tools: {', '.join(TOOLS.keys())}")
    print(f"Resources: {', '.join(RESOURCES.keys())}")
    print(f"Data dir: {_get_data_dir()}")
    print(f"Memory dir: {_get_memory_dir()}")
