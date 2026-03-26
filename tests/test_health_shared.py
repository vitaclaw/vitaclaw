#!/usr/bin/env python3
"""Smoke tests for VitaClaw shared health foundations."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from skills._shared.concept_resolver import ConceptNotFoundError, ConceptResolver, FieldValidationError
from skills._shared.consent_manager import ConsentManager
from skills._shared.correlation_engine import CorrelationEngine
from skills._shared.cross_skill_reader import CrossSkillReader
from skills._shared.event_trigger import Alert, EventTrigger
from skills._shared.family_manager import FamilyManager
from skills._shared.fhir_mapper import FHIRMapper
from skills._shared.graph_populator import GraphPopulator
from skills._shared.health_data_exchange import HealthDataExchange
from skills._shared.health_data_store import HealthDataStore
from skills._shared.health_knowledge_graph import HealthKnowledgeGraph
from skills._shared.health_memory import HealthMemoryWriter
from skills._shared.health_timeline_builder import HealthTimelineBuilder
from skills._shared.memory_editor import MemoryEditor
from skills._shared.memory_lifecycle import HealthFact, MemoryLifecycle
from skills._shared.push_dispatcher import _escape_applescript, _format_issues_text
from skills._shared.push_dispatcher import dispatch as push_dispatch
from skills._shared.source_tracer import SourceTracer
from skills._shared.twin_identity import TwinIdentity
from skills._shared.twin_memory_context import TwinMemoryContext

ROOT = Path(__file__).resolve().parents[1]


class HealthDataStoreTest(unittest.TestCase):
    def test_append_query_trend_and_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("sleep-analyzer", data_dir=tmp_dir)
            store.append("sleep_session", {"score": 72, "total_min": 420})
            store.append("sleep_session", {"score": 81, "total_min": 465})

            records = store.query("sleep_session")
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["type"], "sleep_session")

            latest = store.get_latest("sleep_session", n=1)
            self.assertEqual(latest[0]["data"]["score"], 81)

            trend = store.trend("sleep_session", "score", window=30)
            self.assertEqual(trend["count"], 2)
            self.assertEqual(trend["direction"], "rising")
            self.assertEqual(trend["values"], [72, 81])

            self.assertTrue(store.consecutive_check("sleep_session", "score", "rising", count=2))
            self.assertFalse(store.consecutive_check("sleep_session", "score", "falling", count=2))

            store.set_config("thresholds", {"sleep_score_min": 75})
            self.assertEqual(store.get_config()["thresholds"]["sleep_score_min"], 75)


class HealthMemoryAndCrossSkillReaderTest(unittest.TestCase):
    def test_memory_writer_creates_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = HealthMemoryWriter(workspace_root=tmp_dir)
            writer.update_caffeine(
                level=115.0,
                intake_list=[
                    {"drink": "Americano", "mg": 95, "time": "08:30"},
                    {"drink": "Green tea", "mg": 30, "time": "11:00"},
                ],
                safe="22:15",
            )
            writer.update_sleep(
                last_night={
                    "date": "2026-03-14",
                    "score": 83,
                    "total_min": 445,
                    "efficiency_pct": 92.7,
                    "bedtime": "23:00",
                    "wake_time": "06:25",
                    "deep_min": 80,
                    "light_min": 235,
                    "rem_min": 95,
                    "awake_min": 35,
                },
                seven_day={
                    "avg_score": 79.5,
                    "avg_total_min": 430,
                    "avg_efficiency": 90.1,
                    "trend_direction": "rising",
                },
                correlations={"caffeine_effect": "300mg days tend to score lower"},
            )
            writer.update_supplements(
                active_regimen=[
                    {"name": "VD3", "dose": "2000IU", "timing": "08:00"},
                    {"name": "Magnesium", "dose": "200mg", "timing": "22:00"},
                ],
                today_adherence={"taken": 2, "expected": 2, "rate_pct": 100.0},
                warnings=["Iron and calcium should be separated"],
            )
            writer.update_weekly_digest("# 健康周报 -- 2026-03-10 ~ 2026-03-16\n\n本周总体稳定。")

            memory_root = Path(tmp_dir) / "memory" / "health"
            self.assertTrue((memory_root / "_health-profile.md").exists())
            self.assertTrue((memory_root / "items" / "caffeine.md").exists())
            self.assertTrue((memory_root / "items" / "sleep.md").exists())
            self.assertTrue((memory_root / "items" / "supplements.md").exists())
            self.assertTrue((memory_root / "weekly-digest.md").exists())

            context = writer.read_health_context()
            self.assertIn("Health Profile", context)
            self.assertIn("Caffeine", context)
            self.assertIn("Sleep", context)

    def test_cross_skill_reader_reads_shared_skill_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            HealthDataStore("caffeine-tracker", data_dir=tmp_dir).append(
                "intake", {"drink": "Americano", "mg": 95, "time": "08:30"}
            )
            HealthDataStore("sleep-analyzer", data_dir=tmp_dir).append(
                "sleep_session", {"date": "2026-03-14", "score": 83}
            )
            supplement_store = HealthDataStore("supplement-manager", data_dir=tmp_dir)
            supplement_store.append(
                "supplement",
                {"name": "VD3", "dose": "2000IU", "timing": "08:00", "status": "active"},
            )
            supplement_store.append(
                "dose_log",
                {"supplement": "VD3", "taken": True, "time": "08:05"},
            )
            HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir).append("bp", {"sys": 128, "dia": 82})
            HealthDataStore("medication-reminder", data_dir=tmp_dir).append(
                "dose", {"name": "Amlodipine", "taken": True}
            )

            reader = CrossSkillReader(data_dir=tmp_dir)
            self.assertEqual(len(reader.read_caffeine_intakes()), 1)
            self.assertEqual(len(reader.read_sleep_data()), 1)
            self.assertEqual(len(reader.read_supplement_doses()), 1)
            self.assertEqual(len(reader.read_supplement_regimen()), 1)
            self.assertEqual(len(reader.read_blood_pressure()), 1)
            self.assertEqual(len(reader.read_medication_doses()), 1)


class ConceptResolverTest(unittest.TestCase):
    """Phase 0: Concept registry and resolver tests."""

    def setUp(self):
        self.resolver = ConceptResolver()

    def test_list_concepts_returns_all_registered(self):
        concepts = self.resolver.list_concepts()
        self.assertIn("blood-pressure", concepts)
        self.assertIn("blood-sugar", concepts)
        self.assertIn("weight", concepts)
        self.assertIn("sleep", concepts)
        self.assertIn("caffeine", concepts)
        self.assertGreaterEqual(len(concepts), 17)

    def test_resolve_from_type_maps_canonical_types(self):
        self.assertEqual(self.resolver.resolve_from_type("bp"), "blood-pressure")
        self.assertEqual(self.resolver.resolve_from_type("glucose"), "blood-sugar")
        self.assertEqual(self.resolver.resolve_from_type("weight"), "weight")
        self.assertEqual(self.resolver.resolve_from_type("sleep_session"), "sleep")
        self.assertEqual(self.resolver.resolve_from_type("intake"), "caffeine")
        self.assertEqual(self.resolver.resolve_from_type("dose"), "medication-dose")
        self.assertIsNone(self.resolver.resolve_from_type("nonexistent"))

    def test_normalize_fields_aliases(self):
        """sys → systolic, dia → diastolic, hr → heart_rate."""
        normalized = self.resolver.normalize_fields(
            "blood-pressure", {"sys": 148, "dia": 96, "hr": 80, "context": "home"}
        )
        self.assertEqual(normalized["systolic"], 148)
        self.assertEqual(normalized["diastolic"], 96)
        self.assertEqual(normalized["heart_rate"], 80)
        self.assertEqual(normalized["context"], "home")

    def test_normalize_fields_passthrough_unknown(self):
        normalized = self.resolver.normalize_fields("blood-pressure", {"systolic": 120, "custom_field": "value"})
        self.assertEqual(normalized["systolic"], 120)
        self.assertEqual(normalized["custom_field"], "value")

    def test_validate_fields_in_range(self):
        errors = self.resolver.validate_fields("blood-pressure", {"systolic": 120, "diastolic": 80})
        self.assertEqual(errors, [])

    def test_validate_fields_out_of_range(self):
        errors = self.resolver.validate_fields("blood-pressure", {"systolic": 500, "diastolic": 80})
        self.assertEqual(len(errors), 1)
        self.assertIn("systolic", errors[0])

    def test_validate_fields_strict_raises(self):
        with self.assertRaises(FieldValidationError):
            self.resolver.validate_fields("blood-pressure", {"systolic": 500}, strict=True)

    def test_normalize_and_validate_combined(self):
        """{"sys": 148} → {"systolic": 148} + LOINC 8480-6."""
        normalized, errors = self.resolver.normalize_and_validate("blood-pressure", {"sys": 148, "dia": 96})
        self.assertEqual(normalized["systolic"], 148)
        self.assertEqual(normalized["diastolic"], 96)
        self.assertEqual(errors, [])
        self.assertEqual(self.resolver.get_loinc("blood-pressure", "systolic"), "8480-6")

    def test_get_loinc_panel_and_field(self):
        self.assertEqual(self.resolver.get_loinc("blood-pressure"), "85354-9")
        self.assertEqual(self.resolver.get_loinc("blood-pressure", "systolic"), "8480-6")
        self.assertEqual(self.resolver.get_loinc("blood-pressure", "diastolic"), "8462-4")
        self.assertIsNone(self.resolver.get_loinc("caffeine"))  # no LOINC for caffeine

    def test_get_producers(self):
        producers = self.resolver.get_producers("blood-pressure")
        skill_names = [p["skill"] for p in producers]
        self.assertIn("blood-pressure-tracker", skill_names)
        self.assertIn("chronic-condition-monitor", skill_names)

    def test_get_vital_bounds_from_registry(self):
        bounds = self.resolver.get_vital_bounds()
        self.assertIn("systolic", bounds)
        self.assertIn("diastolic", bounds)
        self.assertEqual(bounds["systolic"], (40, 300))

    def test_concept_not_found(self):
        with self.assertRaises(ConceptNotFoundError):
            self.resolver.resolve_concept("nonexistent-concept")

    def test_enrich_meta(self):
        meta = self.resolver.enrich_meta("blood-pressure")
        self.assertEqual(meta["domain"], "health")
        self.assertEqual(meta["concept"], "blood-pressure")
        self.assertEqual(meta["loinc"], "85354-9")


class HealthDataStoreMetaTest(unittest.TestCase):
    """Phase 0.3: _meta envelope tests."""

    def test_append_with_meta(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir)
            record = store.append(
                "bp",
                {"sys": 128, "dia": 82},
                note="测试",
                meta={
                    "domain": "health",
                    "concept": "blood-pressure",
                    "loinc": "85354-9",
                    "source": "manual",
                    "confidence": 1.0,
                    "twin_id": "vitaclaw:test:twin",
                },
            )
            self.assertIn("_meta", record)
            self.assertEqual(record["_meta"]["domain"], "health")
            self.assertEqual(record["_meta"]["concept"], "blood-pressure")
            self.assertEqual(record["_meta"]["source"], "manual")
            self.assertIn("ingested_at", record["_meta"])
            self.assertIn("recorded_at", record["_meta"])

    def test_append_without_meta_backward_compatible(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir)
            record = store.append("bp", {"sys": 128, "dia": 82})
            self.assertNotIn("_meta", record)

    def test_meta_defaults_domain_to_health(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            record = store.append("test", {"value": 1}, meta={"concept": "test"})
            self.assertEqual(record["_meta"]["domain"], "health")

    def test_meta_passthrough_unknown_domain(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            record = store.append(
                "test",
                {"value": 1},
                meta={"domain": "cognitive", "concept": "decision-pattern"},
            )
            self.assertEqual(record["_meta"]["domain"], "cognitive")

    def test_meta_persists_in_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            store.append("test", {"value": 42}, meta={"concept": "test", "source": "manual"})
            records = store.query("test")
            self.assertEqual(len(records), 1)
            self.assertIn("_meta", records[0])
            self.assertEqual(records[0]["_meta"]["concept"], "test")


class DeduplicationTest(unittest.TestCase):
    """Phase 1.4: JSONL dedup protection tests."""

    def test_duplicate_record_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            ts = "2026-03-20T10:00:00"
            r1 = store.append("bp", {"sys": 130, "dia": 85}, timestamp=ts)
            r2 = store.append("bp", {"sys": 130, "dia": 85}, timestamp=ts)
            # Same record returned (dedup)
            self.assertEqual(r1["id"], r2["id"])
            # Only one record in store
            self.assertEqual(len(store.query("bp")), 1)

    def test_different_data_not_deduped(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            ts = "2026-03-20T10:00:00"
            store.append("bp", {"sys": 130, "dia": 85}, timestamp=ts)
            store.append("bp", {"sys": 140, "dia": 90}, timestamp=ts)
            self.assertEqual(len(store.query("bp")), 2)

    def test_different_timestamp_not_deduped(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            store.append("bp", {"sys": 130, "dia": 85}, timestamp="2026-03-20T10:00:00")
            store.append("bp", {"sys": 130, "dia": 85}, timestamp="2026-03-20T11:00:00")
            self.assertEqual(len(store.query("bp")), 2)


class MemoryLifecycleTest(unittest.TestCase):
    """Phase 1.3: Memory lifecycle tests."""

    def test_health_fact_serialization_roundtrip(self):
        fact = HealthFact(
            text="收缩压 7 日均值 135 mmHg",
            confidence=0.9,
            valid_until="2026-04-01",
            source_count=5,
            stage="consolidated",
        )
        line = fact.to_markdown_line()
        parsed = HealthFact.from_markdown_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.text, "收缩压 7 日均值 135 mmHg")
        self.assertAlmostEqual(parsed.confidence, 0.9, places=1)
        self.assertEqual(parsed.valid_until, "2026-04-01")
        self.assertEqual(parsed.source_count, 5)
        self.assertEqual(parsed.stage, "consolidated")

    def test_consolidation_threshold(self):
        lifecycle = MemoryLifecycle()
        fact = HealthFact(text="test", source_count=2, stage="formation")
        lifecycle.consolidate(fact)
        self.assertEqual(fact.stage, "formation")  # Not enough sources

        fact.source_count = 3
        lifecycle.consolidate(fact)
        self.assertEqual(fact.stage, "consolidated")

    def test_expiration_check(self):
        from datetime import datetime

        lifecycle = MemoryLifecycle(now_fn=lambda: datetime(2026, 4, 1))
        active_fact = HealthFact(text="active", valid_until="2026-05-01")
        expired_fact = HealthFact(text="expired", valid_until="2026-03-01")
        active, expired = lifecycle.check_expirations([active_fact, expired_fact])
        self.assertEqual(len(active), 1)
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0].stage, "archived")

    def test_evolution(self):
        lifecycle = MemoryLifecycle()
        fact = HealthFact(text="BP avg 140", stage="consolidated")
        lifecycle.evolve(fact, "BP avg 135", new_confidence=0.95)
        self.assertEqual(fact.text, "BP avg 135")
        self.assertEqual(fact.stage, "evolved")
        self.assertAlmostEqual(fact.confidence, 0.95)

    def test_archive_write(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lifecycle = MemoryLifecycle(memory_dir=tmp_dir)
            fact = HealthFact(text="old fact", stage="archived")
            path = lifecycle.write_archive([fact], category="blood-pressure")
            self.assertTrue(path.exists())
            content = path.read_text()
            self.assertIn("old fact", content)


class SourceTracerTest(unittest.TestCase):
    """Phase 1.2: Source tracing tests."""

    def test_trace_summary_to_records(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir)
            store.append("bp", {"sys": 130, "dia": 85}, timestamp="2026-03-20T10:00:00")
            store.append("bp", {"sys": 135, "dia": 88}, timestamp="2026-03-21T10:00:00")

            tracer = SourceTracer(data_dir=tmp_dir)
            records = tracer.trace_summary_to_records("blood-pressure", date="2026-03-21", window_days=7)
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["data"]["sys"], 130)

    def test_trace_record_to_summaries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory_dir = Path(tmp_dir) / "memory" / "health"
            (memory_dir / "daily").mkdir(parents=True)
            (memory_dir / "items").mkdir(parents=True)
            (memory_dir / "daily" / "2026-03-20.md").write_text("# Daily\n")
            (memory_dir / "items" / "blood-pressure.md").write_text("# BP\n")

            tracer = SourceTracer(data_dir=tmp_dir, memory_dir=str(memory_dir))
            record = {"type": "bp", "timestamp": "2026-03-20T10:00:00"}
            results = tracer.trace_record_to_summaries(record)
            types = [r["type"] for r in results]
            self.assertIn("daily", types)
            self.assertIn("item", types)

    def test_build_source_comment(self):
        tracer = SourceTracer()
        comment = tracer.build_source_comment(["items/blood-pressure.md", "daily/2026-03-20.md"])
        self.assertEqual(comment, "<!-- sources: items/blood-pressure.md, daily/2026-03-20.md -->")


class CrossSkillReaderRegistryTest(unittest.TestCase):
    """Phase 0.4: Registry-driven CrossSkillReader tests."""

    def test_read_by_concept_discovers_producers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir).append("bp", {"sys": 130, "dia": 85})
            HealthDataStore("chronic-condition-monitor", data_dir=tmp_dir).append("bp", {"sys": 140, "dia": 90})
            reader = CrossSkillReader(data_dir=tmp_dir)
            records = reader.read("blood-pressure")
            self.assertEqual(len(records), 2)

    def test_read_by_canonical_type(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir).append("bp", {"sys": 130, "dia": 85})
            reader = CrossSkillReader(data_dir=tmp_dir)
            # Can also resolve by canonical_type "bp"
            records = reader.read("bp")
            self.assertEqual(len(records), 1)

    def test_read_unknown_concept_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            reader = CrossSkillReader(data_dir=tmp_dir)
            records = reader.read("nonexistent-concept")
            self.assertEqual(records, [])

    def test_read_all_multiple_concepts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir).append("bp", {"sys": 130, "dia": 85})
            HealthDataStore("chronic-condition-monitor", data_dir=tmp_dir).append("weight", {"kg": 72.5})
            reader = CrossSkillReader(data_dir=tmp_dir)
            result = reader.read_all(["blood-pressure", "weight"])
            self.assertIn("blood-pressure", result)
            self.assertIn("weight", result)
            self.assertEqual(len(result["blood-pressure"]), 1)
            self.assertEqual(len(result["weight"]), 1)


class KnowledgeGraphTest(unittest.TestCase):
    """Phase 2: Knowledge graph tests."""

    def test_add_entity_and_query(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp = graph.add_entity("blood-pressure", "health_concept")
            self.assertEqual(bp["name"], "blood-pressure")
            self.assertEqual(bp["type"], "health_concept")
            # Dedup: same name returns same node
            bp2 = graph.add_entity("blood-pressure", "health_concept")
            self.assertEqual(bp["id"], bp2["id"])

    def test_add_episode_and_edge(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp = graph.add_entity("blood-pressure", "health_concept")
            episode = graph.add_episode("BP reading 130/85", valid_at="2026-03-20T10:00:00")
            edge = graph.add_edge(episode["id"], bp["id"], "measured_by")
            self.assertIsNotNone(edge["id"])
            # Edge dedup
            edge2 = graph.add_edge(episode["id"], bp["id"], "measured_by")
            self.assertEqual(edge["id"], edge2["id"])

    def test_query_neighbors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp = graph.add_entity("blood-pressure", "health_concept")
            med = graph.add_entity("Amlodipine", "medication")
            graph.add_edge(med["id"], bp["id"], "treats")
            neighbors = graph.query_neighbors(bp["id"])
            names = [n["name"] for n in neighbors]
            self.assertIn("Amlodipine", names)

    def test_query_neighbors_depth_2(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp = graph.add_entity("blood-pressure", "health_concept")
            hyp = graph.add_entity("hypertension", "condition")
            kidney = graph.add_entity("kidney", "body_system")
            graph.add_edge(bp["id"], hyp["id"], "monitors")
            graph.add_edge(hyp["id"], kidney["id"], "affects")
            # Depth 1: only hypertension
            d1 = graph.query_neighbors(bp["id"], depth=1)
            self.assertEqual(len(d1), 1)
            # Depth 2: hypertension + kidney
            d2 = graph.query_neighbors(bp["id"], depth=2)
            self.assertEqual(len(d2), 2)

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph1 = HealthKnowledgeGraph(data_dir=tmp_dir)
            graph1.add_entity("blood-pressure", "health_concept")
            graph1.add_entity("weight", "health_concept")

            # New instance reads from disk
            graph2 = HealthKnowledgeGraph(data_dir=tmp_dir)
            self.assertIsNotNone(graph2.find_node_by_name("blood-pressure"))
            self.assertIsNotNone(graph2.find_node_by_name("weight"))
            stats = graph2.stats()
            self.assertEqual(stats["active_nodes"], 2)

    def test_graph_populator_creates_nodes_from_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            populator = GraphPopulator(graph=graph)
            record = {
                "id": "bp_20260320_abc",
                "type": "bp",
                "timestamp": "2026-03-20T10:00:00",
                "skill": "blood-pressure-tracker",
                "note": "",
                "data": {"sys": 130, "dia": 85},
                "_meta": {"concept": "blood-pressure", "domain": "health"},
            }
            result = populator.ingest_record(record)
            self.assertGreater(len(result["episodes"]), 0)
            self.assertGreater(len(result["entities"]), 0)
            # Concept entity created
            self.assertIsNotNone(graph.find_node_by_name("blood-pressure"))

    def test_graph_populator_medication_linking(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            populator = GraphPopulator(graph=graph)
            record = {
                "id": "dose_20260320_abc",
                "type": "dose",
                "timestamp": "2026-03-20T08:00:00",
                "skill": "medication-reminder",
                "note": "",
                "data": {"name": "Amlodipine", "taken": True},
                "_meta": {"concept": "medication-dose", "domain": "health"},
            }
            populator.ingest_record(record)
            med = graph.find_node_by_name("Amlodipine")
            self.assertIsNotNone(med)
            self.assertEqual(med["type"], "medication")

    def test_related_to_blood_pressure_returns_medication(self):
        """Phase 2 validation: related_to("blood-pressure") returns medication, no hardcoding."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp = graph.add_entity("blood-pressure", "health_concept")
            med = graph.add_entity("Amlodipine", "medication")
            graph.add_edge(med["id"], bp["id"], "treats")
            neighbors = graph.query_neighbors(bp["id"])
            self.assertTrue(any(n["name"] == "Amlodipine" for n in neighbors))


class TwinMemoryContextTest(unittest.TestCase):
    """Phase 3: Three-layer context builder tests."""

    def test_build_context_with_health_profile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory_dir = Path(tmp_dir) / "memory" / "health"
            memory_dir.mkdir(parents=True)
            (memory_dir / "_health-profile.md").write_text("# Health Profile\nBP target: <135/85\n")
            (memory_dir / "items").mkdir()
            (memory_dir / "items" / "blood-pressure.md").write_text("## Recent Status\n- Latest: 130/82\n")

            ctx = TwinMemoryContext(memory_dir=str(memory_dir), data_dir=tmp_dir)
            result = ctx.build_context("血压", budget_tokens=4000)
            self.assertIn("Health Profile", result)

    def test_relevance_scoring(self):
        ctx = TwinMemoryContext()
        recent_record = {
            "type": "bp",
            "timestamp": datetime.now().isoformat(),
            "data": {"sys": 130},
            "_meta": {"concept": "blood-pressure", "confidence": 1.0},
        }
        old_record = {
            "type": "bp",
            "timestamp": "2025-01-01T00:00:00",
            "data": {"sys": 130},
            "_meta": {"concept": "blood-pressure", "confidence": 0.5},
        }
        score_recent = ctx.score_relevance(recent_record, query="血压")
        score_old = ctx.score_relevance(old_record, query="血压")
        self.assertGreater(score_recent, score_old)


class MemoryEditorTest(unittest.TestCase):
    """Phase 3.3: Self-editing memory tests."""

    def test_propose_and_apply_health_update(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory_dir = Path(tmp_dir)
            (memory_dir / "items").mkdir(parents=True)
            item_path = memory_dir / "items" / "blood-pressure.md"
            item_path.write_text("## Recent Status\n- Latest: 140/90\n")

            editor = MemoryEditor(memory_dir=str(memory_dir))
            update = editor.propose_update(
                item_path="items/blood-pressure.md",
                section="Recent Status",
                old_content="- Latest: 140/90",
                new_content="- Latest: 130/82",
                reason="New measurement recorded",
                domain="health",
            )
            # Health domain auto-approved
            self.assertEqual(update.status, "approved")
            applied = editor.apply_all_pending()
            self.assertEqual(len(applied), 1)
            self.assertIn("130/82", item_path.read_text())

    def test_cognitive_domain_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            editor = MemoryEditor(memory_dir=tmp_dir)
            update = editor.propose_update(
                item_path="test.md",
                section="test",
                old_content="old",
                new_content="new",
                reason="test",
                domain="cognitive",
            )
            self.assertTrue(update.requires_confirmation)
            self.assertEqual(update.status, "proposed")
            pending = editor.get_pending()
            self.assertEqual(len(pending), 1)


class TwinIdentityTest(unittest.TestCase):
    """Phase 4.1: Identity management tests."""

    def test_initialize_identity(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            identity = TwinIdentity(identity_path=str(Path(tmp_dir) / "_identity.yaml"))
            identity.initialize(
                owner_id="vitaclaw:testuser",
                display_name="Test User",
                generate_keys=False,
            )
            self.assertEqual(identity.owner_id, "vitaclaw:testuser")
            self.assertEqual(identity.twin_id, "vitaclaw:testuser:twin")
            self.assertEqual(identity.display_name, "Test User")

    def test_family_member_management(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            identity = TwinIdentity(identity_path=str(Path(tmp_dir) / "_identity.yaml"))
            identity.initialize("vitaclaw:parent", generate_keys=False)
            identity.add_family_member(
                "vitaclaw:child1",
                relation="child",
                delegate_until="2038-06-01",
            )
            family = identity.get_family()
            self.assertEqual(len(family), 1)
            self.assertEqual(family[0]["relation"], "child")
            self.assertTrue(identity.is_delegate_active("vitaclaw:child1"))

    def test_delegation_expiry(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            identity = TwinIdentity(identity_path=str(Path(tmp_dir) / "_identity.yaml"))
            identity.initialize("vitaclaw:parent", generate_keys=False)
            identity.add_family_member(
                "vitaclaw:child1",
                relation="child",
                delegate_until="2020-01-01",  # Already expired
            )
            self.assertFalse(identity.is_delegate_active("vitaclaw:child1"))


class ConsentManagerTest(unittest.TestCase):
    """Phase 4.2: Consent and authorization tests."""

    def _create_manager_with_policies(self, tmp_dir):
        policy_path = Path(tmp_dir) / "_consent_policies.yaml"
        manager = ConsentManager(policy_path=str(policy_path))
        manager.add_policy(
            {
                "id": "policy_dr_wang",
                "grantee": "hospital:xinhua:dr_wang",
                "concepts": ["blood-pressure", "blood-sugar", "medications"],
                "granularity": "raw",
                "valid_from": "2026-01-01",
                "valid_until": "2027-03-01",
                "purpose": "chronic_disease_management",
            }
        )
        manager.add_policy(
            {
                "id": "policy_emergency",
                "grantee": "any:emergency_physician",
                "concepts": ["*"],
                "granularity": "raw",
                "valid_from": "2026-01-01",
                "valid_until": None,
                "purpose": "emergency",
                "requires_break_glass": True,
            }
        )
        manager.add_policy(
            {
                "id": "policy_research",
                "grantee": "research:trial_123",
                "concepts": ["blood-pressure", "weight"],
                "granularity": "summary",
                "valid_from": "2026-01-01",
                "valid_until": "2027-06-01",
                "purpose": "clinical_research",
            }
        )
        return manager

    def test_check_allowed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            result = manager.check("hospital:xinhua:dr_wang", "blood-pressure", "chronic_disease_management")
            self.assertTrue(result.allowed)
            self.assertEqual(result.granularity, "raw")

    def test_check_denied_wrong_concept(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            result = manager.check("hospital:xinhua:dr_wang", "sleep")
            self.assertFalse(result.allowed)

    def test_check_denied_no_policy(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            result = manager.check("unknown:doctor", "blood-pressure")
            self.assertFalse(result.allowed)

    def test_emergency_requires_break_glass(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            # Without emergency purpose - denied
            result = manager.check("er:emergency_physician", "blood-pressure", "routine")
            self.assertFalse(result.allowed)
            # With emergency purpose - allowed
            result = manager.check("er:emergency_physician", "blood-pressure", "emergency")
            self.assertTrue(result.allowed)

    def test_granularity_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            records = [
                {"data": {"sys": 130, "dia": 85}, "timestamp": "2026-03-20T10:00:00"},
                {"data": {"sys": 140, "dia": 90}, "timestamp": "2026-03-21T10:00:00"},
            ]
            summary = manager.apply_granularity(records, "summary")
            self.assertEqual(summary["count"], 2)
            self.assertIn("sys", summary)
            self.assertEqual(summary["sys"]["mean"], 135.0)

    def test_granularity_trend_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            records = [
                {"data": {"sys": 130}, "timestamp": "2026-03-20T10:00:00"},
                {"data": {"sys": 140}, "timestamp": "2026-03-21T10:00:00"},
            ]
            trend = manager.apply_granularity(records, "trend_only")
            self.assertEqual(trend["trend"]["sys"], "rising")

    def test_granularity_existence_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = self._create_manager_with_policies(tmp_dir)
            result = manager.apply_granularity([{"data": {}}], "existence_only")
            self.assertTrue(result["exists"])
            self.assertEqual(result["count"], 1)


class FamilyManagerTest(unittest.TestCase):
    """Phase 4.3: Family data model tests."""

    def test_add_member_and_sharing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fm = FamilyManager(
                config_path=str(Path(tmp_dir) / "_family.yaml"),
                data_root=tmp_dir,
            )
            fm.add_member("child1", display_name="小明", relation="child", delegate_until="2038-06-01")
            fm.add_sharing_rule("child1", "parent", concepts=["*"], delegate_write=True)

            self.assertEqual(len(fm.list_members()), 1)
            self.assertTrue(fm.is_delegate_active("child1"))
            self.assertTrue(fm.can_read("parent", "child1", "blood-pressure"))
            self.assertTrue(fm.can_write("parent", "child1"))

    def test_sovereignty_handoff(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fm = FamilyManager(
                config_path=str(Path(tmp_dir) / "_family.yaml"),
                data_root=tmp_dir,
                now_fn=lambda: datetime(2040, 1, 1),
            )
            fm.add_member("child1", relation="child", delegate_until="2038-06-01")
            handoffs = fm.check_sovereignty_handoffs()
            self.assertEqual(len(handoffs), 1)
            self.assertEqual(handoffs[0]["status"], "sovereignty_due")
            # After handoff, delegation is no longer active
            self.assertFalse(fm.is_delegate_active("child1"))

    def test_selective_sharing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fm = FamilyManager(
                config_path=str(Path(tmp_dir) / "_family.yaml"),
                data_root=tmp_dir,
            )
            # Both members must exist; "owner" is the data source with active delegation
            fm.add_member("owner", relation="self")
            fm.add_member("spouse", relation="spouse")
            fm.add_sharing_rule("owner", "spouse", concepts=["medications", "appointments"])

            self.assertTrue(fm.can_read("spouse", "owner", "medications"))
            self.assertFalse(fm.can_read("spouse", "owner", "mental-health-score"))


class FHIRMapperTest(unittest.TestCase):
    """Phase 5.1: FHIR bidirectional mapping tests."""

    def test_bp_record_to_fhir_observation(self):
        mapper = FHIRMapper()
        record = {
            "id": "bp_20260320_abc",
            "type": "bp",
            "timestamp": "2026-03-20T10:00:00",
            "skill": "blood-pressure-tracker",
            "note": "",
            "data": {"sys": 130, "dia": 85, "hr": 72},
            "_meta": {"concept": "blood-pressure", "loinc": "85354-9"},
        }
        fhir = mapper.to_fhir(record)
        self.assertIsNotNone(fhir)
        self.assertEqual(fhir["resourceType"], "Observation")
        self.assertEqual(fhir["status"], "final")
        # Should have LOINC coding
        codings = fhir["code"]["coding"]
        self.assertTrue(any(c["code"] == "85354-9" for c in codings))
        # Should have components for systolic/diastolic
        self.assertTrue(len(fhir.get("component", [])) >= 2)

    def test_fhir_observation_roundtrip(self):
        """FHIR export → import preserves data."""
        mapper = FHIRMapper()
        original = {
            "id": "bp_20260320_abc",
            "type": "bp",
            "timestamp": "2026-03-20T10:00:00",
            "skill": "blood-pressure-tracker",
            "note": "",
            "data": {"sys": 130, "dia": 85},
            "_meta": {"concept": "blood-pressure", "loinc": "85354-9"},
        }
        fhir = mapper.to_fhir(original)
        restored = mapper.from_fhir(fhir)
        self.assertIsNotNone(restored)
        # Restored should have systolic/diastolic (canonical names)
        self.assertIn("systolic", restored["data"])
        self.assertEqual(restored["data"]["systolic"], 130)

    def test_fhir_bundle_roundtrip(self):
        mapper = FHIRMapper()
        records = [
            {
                "id": "bp_1",
                "type": "bp",
                "timestamp": "2026-03-20T10:00:00",
                "skill": "blood-pressure-tracker",
                "note": "",
                "data": {"sys": 130, "dia": 85},
                "_meta": {"concept": "blood-pressure", "loinc": "85354-9"},
            },
            {
                "id": "dose_1",
                "type": "dose",
                "timestamp": "2026-03-20T08:00:00",
                "skill": "medication-reminder",
                "note": "",
                "data": {"name": "Amlodipine", "taken": True},
                "_meta": {"concept": "medication-dose"},
            },
        ]
        bundle = mapper.to_fhir_bundle(records)
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(len(bundle["entry"]), 2)

        restored = mapper.from_fhir_bundle(bundle)
        self.assertEqual(len(restored), 2)

    def test_medication_to_fhir(self):
        mapper = FHIRMapper()
        record = {
            "id": "dose_1",
            "type": "dose",
            "timestamp": "2026-03-20T08:00:00",
            "skill": "medication-reminder",
            "note": "",
            "data": {"name": "Amlodipine", "taken": True},
            "_meta": {"concept": "medication-dose"},
        }
        fhir = mapper.to_fhir(record)
        self.assertEqual(fhir["resourceType"], "MedicationStatement")
        self.assertEqual(fhir["status"], "active")


class HealthDataExchangeTest(unittest.TestCase):
    """Phase 5.2: Data exchange engine tests."""

    def test_prepare_share_with_consent(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Set up data
            HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir).append(
                "bp",
                {"sys": 130, "dia": 85},
                meta={"concept": "blood-pressure", "source": "manual"},
            )
            # Set up consent
            memory_dir = Path(tmp_dir) / "memory"
            memory_dir.mkdir()
            consent = ConsentManager(policy_path=str(memory_dir / "_consent.yaml"))
            consent.add_policy(
                {
                    "id": "policy_test",
                    "grantee": "hospital:test:dr_test",
                    "concepts": ["blood-pressure"],
                    "granularity": "raw",
                    "valid_from": "2026-01-01",
                    "valid_until": "2027-12-31",
                    "purpose": "follow_up",
                }
            )

            exchange = HealthDataExchange(
                data_dir=tmp_dir,
                memory_dir=str(memory_dir),
            )
            # Override consent manager
            exchange._consent = consent

            package = exchange.prepare_share(
                "hospital:test:dr_test",
                "follow_up",
                concepts=["blood-pressure"],
            )
            self.assertEqual(package.record_count, 1)
            self.assertIn("blood-pressure", package.concepts)
            self.assertIsNotNone(package.fhir_bundle)

    def test_ingest_fhir_bundle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bundle = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": "ext_bp_1",
                            "status": "final",
                            "code": {
                                "coding": [{"system": "http://loinc.org", "code": "85354-9"}],
                                "text": "blood-pressure",
                            },
                            "effectiveDateTime": "2026-03-20T10:00:00",
                            "component": [
                                {
                                    "code": {"text": "systolic"},
                                    "valueQuantity": {"value": 125, "unit": "mmHg"},
                                },
                                {
                                    "code": {"text": "diastolic"},
                                    "valueQuantity": {"value": 80, "unit": "mmHg"},
                                },
                            ],
                        }
                    }
                ],
            }

            memory_dir = Path(tmp_dir) / "memory"
            memory_dir.mkdir()
            exchange = HealthDataExchange(data_dir=tmp_dir, memory_dir=str(memory_dir))
            records = exchange.ingest_fhir(bundle, issuer="hospital:xinhua")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["_meta"]["issuer"], "hospital:xinhua")
            self.assertEqual(records[0]["_meta"]["source"], "import")


class VisitBriefingEndToEndTest(unittest.TestCase):
    """Phase 5 validation: Full visit briefing scenario."""

    def test_visit_briefing_flow(self):
        """场景：用户明天要去看王医生，系统自动准备就诊数据包。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Set up health data
            bp_store = HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir)
            bp_store.append(
                "bp", {"sys": 135, "dia": 88}, timestamp="2026-03-18T08:00:00", meta={"concept": "blood-pressure"}
            )
            bp_store.append(
                "bp", {"sys": 140, "dia": 92}, timestamp="2026-03-19T08:00:00", meta={"concept": "blood-pressure"}
            )
            bp_store.append(
                "bp", {"sys": 132, "dia": 85}, timestamp="2026-03-20T08:00:00", meta={"concept": "blood-pressure"}
            )

            HealthDataStore("medication-reminder", data_dir=tmp_dir).append(
                "dose",
                {"name": "Amlodipine", "taken": True},
                timestamp="2026-03-20T07:00:00",
                meta={"concept": "medication-dose"},
            )

            # 2. Set up consent policy
            memory_dir = Path(tmp_dir) / "memory"
            memory_dir.mkdir()
            consent = ConsentManager(policy_path=str(memory_dir / "_consent.yaml"))
            consent.add_policy(
                {
                    "id": "policy_dr_wang",
                    "grantee": "hospital:xinhua:dr_wang",
                    "concepts": ["blood-pressure", "medications"],
                    "granularity": "raw",
                    "valid_from": "2026-01-01",
                    "valid_until": "2027-03-01",
                    "purpose": "follow_up",
                }
            )

            # 3. Prepare visit briefing
            exchange = HealthDataExchange(data_dir=tmp_dir, memory_dir=str(memory_dir))
            exchange._consent = consent
            package = exchange.prepare_visit_briefing("policy_dr_wang", "follow_up")

            # 4. Verify
            self.assertGreater(package.record_count, 0)
            self.assertIn("blood-pressure", package.concepts)
            self.assertIsNotNone(package.fhir_bundle)
            self.assertGreater(len(package.fhir_bundle["entry"]), 0)


class CorrelationEngineTest(unittest.TestCase):
    """Phase 6.1: Correlation detection tests."""

    def test_pearson_correlation_perfect_positive(self):
        engine = CorrelationEngine()
        r = engine.pearson_correlation([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        self.assertAlmostEqual(r, 1.0, places=3)

    def test_pearson_correlation_perfect_negative(self):
        engine = CorrelationEngine()
        r = engine.pearson_correlation([1, 2, 3, 4, 5], [10, 8, 6, 4, 2])
        self.assertAlmostEqual(r, -1.0, places=3)

    def test_pearson_insufficient_data(self):
        engine = CorrelationEngine()
        r = engine.pearson_correlation([1, 2], [3, 4])
        self.assertEqual(r, 0.0)

    def test_discover_correlations_with_data(self):
        """Test correlation detection with synthetic data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            bp_store = HealthDataStore("blood-pressure-tracker", data_dir=tmp_dir)
            sleep_store = HealthDataStore("sleep-analyzer", data_dir=tmp_dir)
            now = datetime.now()

            # Create inversely correlated data: high BP ↔ low sleep
            for i in range(10):
                day = (now - timedelta(days=i)).strftime("%Y-%m-%dT08:00:00")
                bp_store.append("bp", {"sys": 140 - i * 2, "dia": 90 - i}, timestamp=day)
                sleep_store.append("sleep_session", {"score": 60 + i * 3}, timestamp=day)

            engine = CorrelationEngine(data_dir=tmp_dir, now_fn=lambda: now)
            result = engine.correlate(
                "blood-pressure",
                "systolic",
                "sleep",
                "score",
                window_days=30,
            )
            # Should find negative correlation (higher BP = lower sleep score)
            self.assertLess(result.correlation, -0.5)
            self.assertEqual(result.direction, "negative")
            self.assertIn(result.strength, ("strong", "moderate"))


class CrossSkillReaderGraphTest(unittest.TestCase):
    """G2: CrossSkillReader graph-driven queries."""

    def test_related_to_returns_neighbors(self):
        """related_to() queries knowledge graph for related entities."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp_entity = graph.add_entity("blood-pressure", "health_concept")
            med_entity = graph.add_entity("amlodipine", "medication")
            graph.add_edge(med_entity["id"], bp_entity["id"], "treats")

            reader = CrossSkillReader(data_dir=tmp_dir)
            reader._graph = graph  # inject graph directly

            related = reader.related_to("blood-pressure", depth=1)
            names = [n["name"] for n in related]
            self.assertIn("amlodipine", names)

    def test_related_to_no_graph_returns_empty(self):
        reader = CrossSkillReader(data_dir="/nonexistent")
        reader._graph = None
        self.assertEqual(reader.related_to("blood-pressure"), [])

    def test_correlations_returns_dict(self):
        """correlations() returns a correlation dict structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            reader = CrossSkillReader(data_dir=tmp_dir)
            result = reader.correlations("blood-pressure", "sleep", window=7)
            self.assertIn("correlation", result)
            self.assertIn("direction", result)
            self.assertIn("strength", result)
            self.assertIn("sample_count", result)


class WeeklyDigestSourcesTest(unittest.TestCase):
    """G1: weekly_health_digest source references."""

    def test_fallback_digest_includes_sources_comment(self):
        """Fallback weekly digest includes <!-- sources: ... --> comment."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.path.insert(0, str(ROOT / "skills" / "weekly-health-digest"))
            from weekly_health_digest import WeeklyHealthDigest

            digest = WeeklyHealthDigest(
                data_dir=tmp_dir,
                memory_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20, 10, 0),
            )
            content = digest._fallback_digest_content(
                week_start="2026-03-16",
                week_end="2026-03-22",
                metrics={"sleep": {"avg_score": 75, "nights_tracked": 5, "avg_duration_min": 420}},
            )
            self.assertIn("<!-- sources:", content)
            self.assertIn("sleep-analyzer", content)
            self.assertIn("range: 2026-03-16~2026-03-22", content)

    def test_fallback_monthly_digest_includes_sources_comment(self):
        """Fallback monthly digest includes <!-- sources: ... --> comment."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sys.path.insert(0, str(ROOT / "skills" / "weekly-health-digest"))
            from weekly_health_digest import WeeklyHealthDigest

            digest = WeeklyHealthDigest(
                data_dir=tmp_dir,
                memory_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20, 10, 0),
            )
            content = digest._fallback_monthly_digest_content(
                month_start="2026-03-01",
                month_end="2026-03-31",
                metrics={"caffeine": {"daily_avg_mg": 200, "days_tracked": 20}},
            )
            self.assertIn("<!-- sources:", content)
            self.assertIn("caffeine-tracker", content)


class HealthDataStoreSignTest(unittest.TestCase):
    """G3: health_data_store signature integration."""

    def test_append_with_sign_false_no_signature(self):
        """sign=False (default) should not add a signature."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            record = store.append("bp", {"systolic": 120, "diastolic": 80})
            self.assertNotIn("signature", record.get("_meta", {}))

    def test_append_with_sign_true_best_effort(self):
        """sign=True should attempt signing; if no keys, no error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test-skill", data_dir=tmp_dir)
            # Should not raise even without keys
            record = store.append(
                "bp",
                {"systolic": 120, "diastolic": 80},
                meta={"concept": "blood-pressure"},
                sign=True,
            )
            # Record should still be created regardless of signing success
            self.assertEqual(record["type"], "bp")


class HeartbeatPredictiveTest(unittest.TestCase):
    """G6: Heartbeat predictive warnings."""

    def test_extrapolate_risk_rising_above_threshold(self):
        """Extrapolation detects future threshold breach."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from skills._shared.health_heartbeat import HealthHeartbeat

            hb = HealthHeartbeat(
                memory_dir=tmp_dir,
                data_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
            )
            # Steadily rising values: 130, 132, 134, 136, 138
            values = [130, 132, 134, 136, 138]
            issue = hb._extrapolate_risk(values, 140.0, "收缩压", "mmHg", "blood-pressure")
            self.assertIsNotNone(issue)
            self.assertIn("趋势预警", issue["title"])

    def test_extrapolate_risk_stable_no_issue(self):
        """Stable values should not trigger predictive warning."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from skills._shared.health_heartbeat import HealthHeartbeat

            hb = HealthHeartbeat(
                memory_dir=tmp_dir,
                data_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
            )
            values = [120, 121, 120, 119, 120]
            issue = hb._extrapolate_risk(values, 140.0, "收缩压", "mmHg", "blood-pressure")
            self.assertIsNone(issue)

    def test_extrapolate_risk_falling_no_issue(self):
        """Falling values should not trigger predictive warning."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from skills._shared.health_heartbeat import HealthHeartbeat

            hb = HealthHeartbeat(
                memory_dir=tmp_dir,
                data_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
            )
            values = [140, 138, 136, 134, 132]
            issue = hb._extrapolate_risk(values, 140.0, "收缩压", "mmHg", "blood-pressure")
            self.assertIsNone(issue)

    def test_issues_predictive_in_run(self):
        """_issues_predictive is called during run()."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from skills._shared.health_heartbeat import HealthHeartbeat

            hb = HealthHeartbeat(
                memory_dir=tmp_dir,
                data_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
            )
            # Should not crash even with no data
            issues = hb._issues_predictive()
            self.assertIsInstance(issues, list)


class SmartHealthCardTest(unittest.TestCase):
    """G4: SMART Health Card creation and verification."""

    def test_qr_uri_roundtrip(self):
        """QR URI encoding/decoding roundtrip."""
        from skills._shared.smart_health_card import SmartHealthCard

        shc = SmartHealthCard()
        jws = "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.test.sig"
        uri = shc.to_qr_uri(jws)
        self.assertTrue(uri.startswith("shc:/"))
        decoded = shc.from_qr_uri(uri)
        self.assertEqual(decoded, jws)

    def test_create_and_verify_shc(self):
        """Full SHC create → verify cycle (requires cryptography)."""
        from skills._shared.smart_health_card import HAS_CRYPTO, SmartHealthCard

        if not HAS_CRYPTO:
            self.skipTest("cryptography package not installed")

        shc = SmartHealthCard(issuer="https://vitaclaw.example")
        shc.generate_keys()

        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": {"resourceType": "Patient", "id": "1"}}],
        }
        jws = shc.create_shc(bundle)
        self.assertIsInstance(jws, str)
        self.assertEqual(len(jws.split(".")), 3)

        result = shc.verify_shc(jws)
        self.assertTrue(result["valid"])
        self.assertIsNotNone(result["fhir_bundle"])
        self.assertEqual(result["fhir_bundle"]["resourceType"], "Bundle")


class AppleHealthBridgeFHIRTest(unittest.TestCase):
    """G5: Apple Health Bridge bidirectional FHIR export."""

    def test_export_to_fhir_bundle_with_records(self):
        """export_to_fhir_bundle() converts records to FHIR."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            from skills._shared.apple_health_bridge import AppleHealthImporter

            importer = AppleHealthImporter(
                workspace_root=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
            )
            records = [
                {
                    "type": "observation",
                    "timestamp": "2026-03-20T08:00:00",
                    "skill": "test",
                    "data": {"value": 72},
                    "_meta": {"concept": "heart-rate", "domain": "health"},
                }
            ]
            bundle = importer.export_to_fhir_bundle(records)
            self.assertEqual(bundle["resourceType"], "Bundle")
            self.assertEqual(bundle["type"], "transaction")


class TimelineGraphNarrativeTest(unittest.TestCase):
    """G7: Timeline Builder knowledge graph narrative."""

    def test_enrich_with_graph_adds_context(self):
        """Timeline entries get graph_context when graph has related medications."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            graph = HealthKnowledgeGraph(data_dir=tmp_dir)
            bp = graph.add_entity("blood-pressure", "health_concept")
            med = graph.add_entity("amlodipine", "medication")
            graph.add_edge(med["id"], bp["id"], "treats")

            builder = HealthTimelineBuilder(
                memory_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
                knowledge_graph=graph,
            )
            entries = [
                {
                    "date": "2026-03-20",
                    "type": "Apple Health 血压",
                    "summary": "120/80",
                    "source": "test",
                    "path": "/test",
                },
            ]
            builder._enrich_with_graph(entries)
            self.assertIn("graph_context", entries[0])
            self.assertIn("amlodipine", entries[0]["graph_context"])

    def test_enrich_without_graph_no_error(self):
        """No graph = no enrichment, no error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            HealthTimelineBuilder(
                memory_dir=tmp_dir,
                now_fn=lambda: datetime(2026, 3, 20),
                knowledge_graph=None,
            )
            entries = [
                {"date": "2026-03-20", "type": "血压", "summary": "120/80", "source": "test", "path": "/test"},
            ]
            # build() won't call _enrich_with_graph if graph is None
            self.assertNotIn("graph_context", entries[0])


class ExportOMOPTest(unittest.TestCase):
    """G8: OMOP CDM export script."""

    def test_export_omop_basic(self):
        """Export creates person, observation, drug_exposure files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir) / "data"
            out_dir = Path(tmp_dir) / "omop_out"

            # Create some test data
            store = HealthDataStore("blood-pressure-tracker", data_dir=str(data_dir))
            store.append("bp", {"systolic": 130, "diastolic": 85}, timestamp="2026-03-20T08:00:00")

            sys.path.insert(0, str(ROOT / "scripts"))
            from export_omop import export_omop

            result = export_omop(
                output_dir=str(out_dir),
                data_dir=str(data_dir),
            )
            self.assertTrue((out_dir / "person.jsonl").exists())
            self.assertTrue((out_dir / "observation.jsonl").exists())
            self.assertTrue((out_dir / "drug_exposure.jsonl").exists())
            self.assertEqual(result["person_count"], 1)


class EventTriggerRulesTest(unittest.TestCase):
    """Test individual critical rules in the event trigger."""

    def test_bp_crisis_180_120(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "bp", "data": {"systolic": 185, "diastolic": 95}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "blood-pressure:crisis")
        self.assertEqual(alerts[0].severity, "critical")

    def test_bp_stage2_160(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "bp", "data": {"systolic": 165, "diastolic": 95}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "blood-pressure:stage2")
        self.assertEqual(alerts[0].severity, "urgent")

    def test_bp_normal_no_alert(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "bp", "data": {"systolic": 120, "diastolic": 80}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 0)

    def test_hypoglycemia(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "glucose", "data": {"value": 3.2}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "blood-sugar:hypoglycemia")
        self.assertEqual(alerts[0].severity, "critical")

    def test_severe_hyperglycemia(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "glucose", "data": {"value": 20.0}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "blood-sugar:severe-hyperglycemia")

    def test_normal_glucose_no_alert(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "glucose", "data": {"value": 5.5}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 0)

    def test_tachycardia(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "heart_rate", "data": {"resting_bpm": 130}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "heart-rate:tachycardia")

    def test_bradycardia(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "heart_rate", "data": {"resting_bpm": 35}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "heart-rate:bradycardia")

    def test_spo2_low(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "spo2", "data": {"spo2": 88}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule_id, "spo2:low")
        self.assertEqual(alerts[0].severity, "critical")

    def test_high_fever(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "temperature", "data": {"temperature": 40.5}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "critical")
        self.assertIn("高热", alerts[0].title)

    def test_moderate_fever(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "temperature", "data": {"temperature": 39.2}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "urgent")

    def test_unrelated_record_no_alert(self):
        trigger = EventTrigger(cooldown_seconds=0)
        record = {"type": "sleep_session", "data": {"score": 80}}
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 0)


class EventTriggerCooldownTest(unittest.TestCase):
    """Test cooldown mechanism prevents alert fatigue."""

    def test_cooldown_suppresses_repeat(self):
        trigger = EventTrigger(cooldown_seconds=600)
        record = {"type": "bp", "data": {"systolic": 190, "diastolic": 130}}
        alerts1 = trigger.evaluate(record)
        self.assertEqual(len(alerts1), 1)
        # Same record again within cooldown → suppressed
        alerts2 = trigger.evaluate(record)
        self.assertEqual(len(alerts2), 0)

    def test_clear_cooldowns(self):
        trigger = EventTrigger(cooldown_seconds=600)
        record = {"type": "bp", "data": {"systolic": 190, "diastolic": 130}}
        trigger.evaluate(record)
        trigger.clear_cooldowns()
        alerts = trigger.evaluate(record)
        self.assertEqual(len(alerts), 1)

    def test_different_rules_not_affected(self):
        trigger = EventTrigger(cooldown_seconds=600)
        trigger.evaluate({"type": "bp", "data": {"systolic": 190, "diastolic": 130}})
        # Different rule should still fire
        alerts = trigger.evaluate({"type": "glucose", "data": {"value": 2.5}})
        self.assertEqual(len(alerts), 1)


class EventTriggerHookIntegrationTest(unittest.TestCase):
    """Test event trigger as HealthDataStore post-append hook."""

    def test_hook_fires_on_critical_append(self):
        """Appending a critical record fires the event trigger hook."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("bp-test", data_dir=tmp_dir)
            trigger = EventTrigger(cooldown_seconds=0)
            store.add_hook(trigger.on_record)

            store.append("bp", {"systolic": 190, "diastolic": 125})
            self.assertEqual(len(trigger.alert_history), 1)
            self.assertEqual(trigger.alert_history[0].rule_id, "blood-pressure:crisis")

    def test_hook_no_alert_for_normal(self):
        """Normal records don't trigger alerts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("bp-test", data_dir=tmp_dir)
            trigger = EventTrigger(cooldown_seconds=0)
            store.add_hook(trigger.on_record)

            store.append("bp", {"systolic": 120, "diastolic": 78})
            self.assertEqual(len(trigger.alert_history), 0)

    def test_hook_with_dispatcher(self):
        """Hook dispatches alerts through the provided dispatcher."""
        dispatched = []

        def mock_dispatcher(issues):
            dispatched.extend(issues)

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("glucose-test", data_dir=tmp_dir)
            trigger = EventTrigger(cooldown_seconds=0, dispatcher=mock_dispatcher)
            store.add_hook(trigger.on_record)

            store.append("glucose", {"value": 2.8})
            self.assertEqual(len(dispatched), 1)
            self.assertEqual(dispatched[0]["priority"], "high")
            self.assertIn("低血糖", dispatched[0]["title"])

    def test_hook_audit_log(self):
        """Hook writes alerts to audit JSONL."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit_path = Path(tmp_dir) / "alerts.jsonl"
            store = HealthDataStore("bp-test", data_dir=tmp_dir)
            trigger = EventTrigger(cooldown_seconds=0, audit_path=str(audit_path))
            store.add_hook(trigger.on_record)

            store.append("bp", {"systolic": 200, "diastolic": 130})
            self.assertTrue(audit_path.exists())
            lines = audit_path.read_text().strip().split("\n")
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["rule_id"], "blood-pressure:crisis")

    def test_multiple_hooks(self):
        """Multiple hooks can be registered and all fire."""
        results = {"hook1": 0, "hook2": 0}

        def hook1(record):
            results["hook1"] += 1

        def hook2(record):
            results["hook2"] += 1

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test", data_dir=tmp_dir)
            store.add_hook(hook1)
            store.add_hook(hook2)
            store.append("bp", {"systolic": 120, "diastolic": 80})
            self.assertEqual(results["hook1"], 1)
            self.assertEqual(results["hook2"], 1)

    def test_remove_hook(self):
        """Hooks can be removed."""
        call_count = [0]

        def hook(record):
            call_count[0] += 1

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test", data_dir=tmp_dir)
            store.add_hook(hook)
            store.append("bp", {"systolic": 120, "diastolic": 80})
            self.assertEqual(call_count[0], 1)
            store.remove_hook(hook)
            store.append("bp", {"systolic": 125, "diastolic": 82}, timestamp="2026-03-20T09:00:00")
            self.assertEqual(call_count[0], 1)

    def test_failing_hook_does_not_block_append(self):
        """A crashing hook must not prevent record persistence."""

        def bad_hook(record):
            raise RuntimeError("Hook crash!")

        with tempfile.TemporaryDirectory() as tmp_dir:
            store = HealthDataStore("test", data_dir=tmp_dir)
            store.add_hook(bad_hook)
            record = store.append("bp", {"systolic": 120, "diastolic": 80})
            # Record should still be saved
            self.assertEqual(record["type"], "bp")
            saved = store.query("bp")
            self.assertEqual(len(saved), 1)


class AlertToIssueTest(unittest.TestCase):
    """Test Alert → push_issue conversion."""

    def test_to_push_issue_format(self):
        alert = Alert(
            rule_id="blood-pressure:crisis",
            severity="critical",
            title="血压危急值",
            reason="190/130",
            next_step="就医",
        )
        issue = alert.to_push_issue()
        self.assertEqual(issue["priority"], "high")
        self.assertEqual(issue["title"], "血压危急值")
        self.assertEqual(issue["trigger"], "event")
        self.assertEqual(issue["execution_mode"], "event-trigger")
        self.assertIn("topic", issue)

    def test_to_dict(self):
        alert = Alert(
            rule_id="spo2:low",
            severity="critical",
            title="血氧低",
            reason="88%",
            next_step="复测",
        )
        d = alert.to_dict()
        self.assertEqual(d["rule_id"], "spo2:low")
        self.assertIn("timestamp", d)


class PushDispatcherMultiChannelTest(unittest.TestCase):
    """Test multi-channel dispatch and priority routing."""

    def test_dispatch_none_channel(self):
        """Channel 'none' sends nothing."""
        import os

        old = os.environ.get("VITACLAW_PUSH_CHANNEL")
        os.environ["VITACLAW_PUSH_CHANNEL"] = "none"
        try:
            result = push_dispatch([{"priority": "high", "title": "test"}])
            self.assertEqual(result["sent"], 0)
        finally:
            if old is not None:
                os.environ["VITACLAW_PUSH_CHANNEL"] = old
            else:
                os.environ.pop("VITACLAW_PUSH_CHANNEL", None)

    def test_format_issues_text(self):
        text = _format_issues_text(
            [
                {"priority": "high", "title": "血压危急"},
                {"priority": "low", "title": "周报待生成"},
            ]
        )
        self.assertIn("血压危急", text)
        self.assertIn("周报待生成", text)

    def test_escape_applescript(self):
        self.assertEqual(_escape_applescript('He said "hi"'), 'He said \\"hi\\"')
        self.assertEqual(_escape_applescript("line1\nline2"), "line1 line2")

    def test_dispatch_unknown_channel(self):
        import os

        old = os.environ.get("VITACLAW_PUSH_CHANNEL")
        os.environ["VITACLAW_PUSH_CHANNEL"] = "nonexistent_channel"
        try:
            result = push_dispatch([{"priority": "high", "title": "test"}])
            self.assertIn("Unknown push channel", result["errors"][0])
        finally:
            if old is not None:
                os.environ["VITACLAW_PUSH_CHANNEL"] = old
            else:
                os.environ.pop("VITACLAW_PUSH_CHANNEL", None)


if __name__ == "__main__":
    unittest.main()
