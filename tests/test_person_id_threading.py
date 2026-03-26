#!/usr/bin/env python3
"""Tests for person_id threading through the VitaClaw data layer.

Covers HealthDataStore, HealthMemoryWriter, CrossSkillReader, and FamilyManager
integration with person_id parameter.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skills._shared.health_data_store import HealthDataStore


class HealthDataStorePersonIdAppendTest(unittest.TestCase):
    """Test person_id behavior in HealthDataStore.append()."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name
        self.store = HealthDataStore("blood-pressure-tracker", data_dir=self.data_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_append_without_person_id_creates_record_without_field(self):
        """Backward compat: append with no person_id should NOT include person_id in record."""
        record = self.store.append("bp", {"systolic": 120, "diastolic": 80})
        self.assertNotIn("person_id", record)

    def test_append_with_person_id_none_creates_record_without_field(self):
        """person_id=None should NOT include person_id in record."""
        record = self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id=None)
        self.assertNotIn("person_id", record)

    def test_append_with_person_id_self_creates_record_without_field(self):
        """person_id='self' is implicit -- should NOT include person_id field."""
        record = self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id="self")
        self.assertNotIn("person_id", record)

    def test_append_with_person_id_mom_creates_record_with_field(self):
        """person_id='mom' should be stored in the record."""
        record = self.store.append("bp", {"systolic": 130, "diastolic": 85}, person_id="mom")
        self.assertEqual(record["person_id"], "mom")

    def test_append_person_id_persists_to_jsonl(self):
        """Verify person_id is actually written to the JSONL file."""
        self.store.append("bp", {"systolic": 130, "diastolic": 85}, person_id="mom")
        data_file = Path(self.data_dir) / "blood-pressure-tracker" / "records.jsonl"
        lines = data_file.read_text().strip().split("\n")
        record = json.loads(lines[0])
        self.assertEqual(record["person_id"], "mom")

    def test_append_no_person_id_not_in_jsonl(self):
        """Verify person_id field is absent from JSONL when not specified."""
        self.store.append("bp", {"systolic": 120, "diastolic": 80})
        data_file = Path(self.data_dir) / "blood-pressure-tracker" / "records.jsonl"
        lines = data_file.read_text().strip().split("\n")
        record = json.loads(lines[0])
        self.assertNotIn("person_id", record)


class HealthDataStorePersonIdQueryTest(unittest.TestCase):
    """Test person_id behavior in HealthDataStore.query()."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name
        self.store = HealthDataStore("blood-pressure-tracker", data_dir=self.data_dir)
        # Create records for different persons
        self.store.append("bp", {"systolic": 120, "diastolic": 80}, timestamp="2025-01-01T10:00:00")
        self.store.append("bp", {"systolic": 130, "diastolic": 85}, timestamp="2025-01-02T10:00:00", person_id="mom")
        self.store.append("bp", {"systolic": 110, "diastolic": 70}, timestamp="2025-01-03T10:00:00", person_id="self")
        self.store.append("bp", {"systolic": 140, "diastolic": 90}, timestamp="2025-01-04T10:00:00", person_id="dad")

    def tearDown(self):
        self._tmp.cleanup()

    def test_query_without_person_id_returns_all(self):
        """Backward compat: query without person_id returns ALL records."""
        records = self.store.query("bp")
        self.assertEqual(len(records), 4)

    def test_query_with_person_id_none_returns_all(self):
        """person_id=None returns ALL records (no filter)."""
        records = self.store.query("bp", person_id=None)
        self.assertEqual(len(records), 4)

    def test_query_with_person_id_self_returns_self_records(self):
        """person_id='self' returns records with absent or 'self' person_id."""
        records = self.store.query("bp", person_id="self")
        # Should get the record without person_id AND the one with person_id="self"
        self.assertEqual(len(records), 2)
        for r in records:
            pid = r.get("person_id")
            self.assertTrue(pid is None or pid == "self", f"Unexpected person_id: {pid}")

    def test_query_with_person_id_mom_returns_only_mom(self):
        """person_id='mom' returns ONLY records with person_id='mom'."""
        records = self.store.query("bp", person_id="mom")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["person_id"], "mom")
        self.assertEqual(records[0]["data"]["systolic"], 130)

    def test_query_with_person_id_dad_returns_only_dad(self):
        """person_id='dad' returns ONLY records with person_id='dad'."""
        records = self.store.query("bp", person_id="dad")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["person_id"], "dad")

    def test_query_with_unknown_person_returns_empty(self):
        """Querying for a person with no records returns empty list."""
        records = self.store.query("bp", person_id="uncle")
        self.assertEqual(len(records), 0)


class HealthDataStorePersonIdDedupTest(unittest.TestCase):
    """Test that dedup includes person_id in its comparison key."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name
        self.store = HealthDataStore("blood-pressure-tracker", data_dir=self.data_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_dedup_different_persons_not_deduped(self):
        """Same data for different persons should NOT be deduplicated."""
        r1 = self.store.append("bp", {"systolic": 120, "diastolic": 80}, timestamp="2025-01-01T10:00:00")
        bp_data = {"systolic": 120, "diastolic": 80}
        r2 = self.store.append(
            "bp", bp_data, timestamp="2025-01-01T10:00:00", person_id="mom",
        )
        # They should be different records (not deduped)
        self.assertNotEqual(r1["id"], r2["id"])

    def test_dedup_same_person_is_deduped(self):
        """Same data for same person should be deduplicated."""
        bp_data = {"systolic": 120, "diastolic": 80}
        r1 = self.store.append(
            "bp", bp_data, timestamp="2025-01-01T10:00:00", person_id="mom",
        )
        r2 = self.store.append(
            "bp", bp_data, timestamp="2025-01-01T10:00:00", person_id="mom",
        )
        # Should return the existing record (deduped)
        self.assertEqual(r1["id"], r2["id"])

    def test_dedup_self_explicit_and_implicit_are_same(self):
        """person_id=None and person_id='self' should be deduped against each other."""
        bp_data = {"systolic": 120, "diastolic": 80}
        r1 = self.store.append("bp", bp_data, timestamp="2025-01-01T10:00:00")
        r2 = self.store.append(
            "bp", bp_data, timestamp="2025-01-01T10:00:00", person_id="self",
        )
        self.assertEqual(r1["id"], r2["id"])


class HealthDataStorePersonIdValidationTest(unittest.TestCase):
    """Test person_id slug validation."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name
        self.store = HealthDataStore("blood-pressure-tracker", data_dir=self.data_dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_valid_slugs_accepted(self):
        """Valid kebab-case slugs should be accepted."""
        for slug in ["mom", "dad", "child-1", "grand-ma", "a", "abc123"]:
            record = self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id=slug)
            self.assertEqual(record.get("person_id"), slug)

    def test_uppercase_rejected(self):
        """Uppercase slugs should be rejected."""
        with self.assertRaises(ValueError):
            self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id="Mom")

    def test_spaces_rejected(self):
        """Slugs with spaces should be rejected."""
        with self.assertRaises(ValueError):
            self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id="my mom")

    def test_too_long_rejected(self):
        """Slugs longer than 32 chars should be rejected."""
        with self.assertRaises(ValueError):
            self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id="a" * 33)

    def test_starts_with_hyphen_rejected(self):
        """Slugs starting with hyphen should be rejected."""
        with self.assertRaises(ValueError):
            self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id="-mom")

    def test_self_is_valid(self):
        """'self' is a valid slug (treated as implicit)."""
        record = self.store.append("bp", {"systolic": 120, "diastolic": 80}, person_id="self")
        # Should succeed without error, person_id omitted from record
        self.assertNotIn("person_id", record)


class HealthMemoryWriterPersonIdTest(unittest.TestCase):
    """Test person_id-aware path resolution in HealthMemoryWriter."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.memory_root = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _resolved_root(self):
        """Return the resolved memory root (handles macOS /var -> /private/var)."""
        return Path(self.memory_root).resolve()

    def test_items_path_without_person_id_is_flat(self):
        """No person_id: items path should be flat (backward compat)."""
        from skills._shared.health_memory import HealthMemoryWriter

        writer = HealthMemoryWriter(memory_root=self.memory_root)
        path = writer._resolve_items_path("blood-pressure")
        expected = self._resolved_root() / "items" / "blood-pressure.md"
        self.assertEqual(path, expected)

    def test_items_path_with_person_id_self_is_flat(self):
        """person_id='self': items path should be flat (same as None)."""
        from skills._shared.health_memory import HealthMemoryWriter

        writer = HealthMemoryWriter(memory_root=self.memory_root, person_id="self")
        path = writer._resolve_items_path("blood-pressure")
        expected = self._resolved_root() / "items" / "blood-pressure.md"
        self.assertEqual(path, expected)

    def test_items_path_with_person_id_mom_uses_subdirectory(self):
        """person_id='mom': items path should include mom subdirectory."""
        from skills._shared.health_memory import HealthMemoryWriter

        writer = HealthMemoryWriter(memory_root=self.memory_root, person_id="mom")
        path = writer._resolve_items_path("blood-pressure")
        expected = self._resolved_root() / "items" / "mom" / "blood-pressure.md"
        self.assertEqual(path, expected)

    def test_person_subdirectory_created(self):
        """Calling _resolve_items_path with person_id should create the subdirectory."""
        from skills._shared.health_memory import HealthMemoryWriter

        writer = HealthMemoryWriter(memory_root=self.memory_root, person_id="mom")
        path = writer._resolve_items_path("blood-pressure")
        # _resolve_items_path should ensure the parent directory exists
        self.assertTrue(path.parent.exists())
        self.assertTrue(path.parent.name == "mom")


class CrossSkillReaderPersonIdTest(unittest.TestCase):
    """Test person_id passthrough in CrossSkillReader."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_read_with_person_id_passes_through(self):
        """CrossSkillReader.read() with person_id should pass it to HealthDataStore.query()."""
        from unittest.mock import MagicMock

        from skills._shared.cross_skill_reader import CrossSkillReader

        reader = CrossSkillReader(data_dir=self.data_dir)

        # Mock the resolver to return a concept with a producer
        mock_resolver = MagicMock()
        mock_resolver.resolve_concept.return_value = (
            "blood-pressure",
            {"producers": [{"skill": "blood-pressure-tracker", "record_type": "bp"}]},
        )
        reader._resolver = mock_resolver

        # Mock the store to track the query call
        mock_store = MagicMock()
        mock_store.query.return_value = []
        reader._stores["blood-pressure-tracker"] = mock_store

        reader.read("blood-pressure", person_id="mom")
        mock_store.query.assert_called_once_with("bp", start=None, end=None, person_id="mom")

    def test_read_without_person_id_backward_compat(self):
        """CrossSkillReader.read() without person_id should pass person_id=None."""
        from unittest.mock import MagicMock

        from skills._shared.cross_skill_reader import CrossSkillReader

        reader = CrossSkillReader(data_dir=self.data_dir)

        mock_resolver = MagicMock()
        mock_resolver.resolve_concept.return_value = (
            "blood-pressure",
            {"producers": [{"skill": "blood-pressure-tracker", "record_type": "bp"}]},
        )
        reader._resolver = mock_resolver

        mock_store = MagicMock()
        mock_store.query.return_value = []
        reader._stores["blood-pressure-tracker"] = mock_store

        reader.read("blood-pressure")
        mock_store.query.assert_called_once_with("bp", start=None, end=None, person_id=None)

    def test_read_all_with_person_id(self):
        """CrossSkillReader.read_all() should pass person_id through."""
        from unittest.mock import MagicMock

        from skills._shared.cross_skill_reader import CrossSkillReader

        reader = CrossSkillReader(data_dir=self.data_dir)

        mock_resolver = MagicMock()
        mock_resolver.resolve_concept.return_value = (
            "blood-pressure",
            {"producers": [{"skill": "blood-pressure-tracker", "record_type": "bp"}]},
        )
        reader._resolver = mock_resolver

        mock_store = MagicMock()
        mock_store.query.return_value = []
        reader._stores["blood-pressure-tracker"] = mock_store

        reader.read_all(["blood-pressure"], person_id="mom")
        mock_store.query.assert_called_once_with("bp", start=None, end=None, person_id="mom")


class FamilyManagerBasicTest(unittest.TestCase):
    """Test FamilyManager add_member and get_member."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_and_get_member(self):
        """FamilyManager can add a member and retrieve their profile."""
        from skills._shared.family_manager import FamilyManager

        fm = FamilyManager(
            config_path=str(Path(self.tmp_dir) / "_family.yaml"),
            data_root=str(Path(self.tmp_dir) / "data"),
        )
        member = fm.add_member("mom", display_name="Mom", relation="mother")
        self.assertEqual(member["id"], "mom")
        self.assertEqual(member["display_name"], "Mom")

        retrieved = fm.get_member("mom")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], "mom")

    def test_list_members(self):
        """FamilyManager can list all members."""
        from skills._shared.family_manager import FamilyManager

        fm = FamilyManager(
            config_path=str(Path(self.tmp_dir) / "_family.yaml"),
            data_root=str(Path(self.tmp_dir) / "data"),
        )
        fm.add_member("mom", display_name="Mom", relation="mother")
        fm.add_member("dad", display_name="Dad", relation="father")
        members = fm.list_members()
        self.assertEqual(len(members), 2)


class FullIntegrationTest(unittest.TestCase):
    """Full integration test: FamilyManager + HealthDataStore + HealthMemoryWriter + CrossSkillReader."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = self._tmp.name
        self.data_dir = str(Path(self.tmp_dir) / "data")
        self.memory_root = str(Path(self.tmp_dir) / "memory" / "health")
        Path(self.data_dir).mkdir(parents=True)
        Path(self.memory_root).mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_full_person_id_integration(self):
        """End-to-end: add member, store data, query filtered, verify memory paths."""
        from skills._shared.family_manager import FamilyManager
        from skills._shared.health_memory import HealthMemoryWriter

        # 1. Create FamilyManager, add "mom"
        fm = FamilyManager(
            config_path=str(Path(self.tmp_dir) / "_family.yaml"),
            data_root=self.data_dir,
        )
        member = fm.add_member("mom", display_name="Mom", relation="mother")
        self.assertEqual(member["id"], "mom")

        # 2. Create HealthDataStore, append record with person_id="mom"
        store = HealthDataStore("blood-pressure-tracker", data_dir=self.data_dir)
        store.append("bp", {"systolic": 140, "diastolic": 90}, person_id="mom", timestamp="2025-01-01T10:00:00")
        store.append("bp", {"systolic": 120, "diastolic": 80}, timestamp="2025-01-01T11:00:00")

        # 3. Query with person_id="mom" -- gets the record
        mom_records = store.query("bp", person_id="mom")
        self.assertEqual(len(mom_records), 1)
        self.assertEqual(mom_records[0]["data"]["systolic"], 140)

        # 4. Query with person_id="self" -- does NOT get mom's record
        self_records = store.query("bp", person_id="self")
        self.assertEqual(len(self_records), 1)
        self.assertEqual(self_records[0]["data"]["systolic"], 120)

        # 5. Create HealthMemoryWriter with person_id="mom"
        writer = HealthMemoryWriter(memory_root=self.memory_root, person_id="mom")

        # 6. Verify item path includes "mom" subdirectory
        mom_item_path = writer._resolve_items_path("blood-pressure")
        self.assertIn("mom", str(mom_item_path))
        self.assertTrue(str(mom_item_path).endswith("items/mom/blood-pressure.md"))

        # 7. Verify self writer uses flat path
        self_writer = HealthMemoryWriter(memory_root=self.memory_root)
        self_item_path = self_writer._resolve_items_path("blood-pressure")
        self.assertTrue(str(self_item_path).endswith("items/blood-pressure.md"))
        self.assertNotIn("/mom/", str(self_item_path))


if __name__ == "__main__":
    unittest.main()
