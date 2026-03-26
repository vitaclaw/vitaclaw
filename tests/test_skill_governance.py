#!/usr/bin/env python3
"""Tests for Iteration 1 health-core governance metadata."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import skill_catalog  # noqa: E402


class SkillGovernanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = skill_catalog.build_manifest_records()
        cls.summary = skill_catalog.manifest_summary(cls.records)
        cls.health_core = [record for record in cls.records if record["governance_scope"] == "health-core"]
        cls.upstream_new_skills = {
            "allergy-manager",
            "body-composition-analyzer",
            "breathing-exercise-guide",
            "chronic-pain-manager",
            "circadian-rhythm-optimizer",
            "eye-health-advisor",
            "first-aid-guide",
            "google-fit-digest",
            "gut-health-advisor",
            "hormone-health-tracker",
            "hydration-tracker",
            "longevity-advisor",
            "menstrual-cycle-tracker",
            "posture-ergonomics-coach",
            "pregnancy-health-tracker",
            "social-health-tracker",
            "stress-management-coach",
            "vaccination-tracker",
        }

    def test_health_core_scope_matches_manifest_summary(self):
        self.assertEqual(len(self.health_core), self.summary["health_skill_count"])

    def test_health_core_frontmatter_is_fully_valid(self):
        invalid = [record["slug"] for record in self.health_core if not record["frontmatter_valid"]]
        self.assertEqual(invalid, [])

    def test_new_upstream_skills_are_governed_as_health_core(self):
        index = {record["slug"]: record for record in self.records}
        missing = sorted(self.upstream_new_skills - index.keys())
        self.assertEqual(missing, [])

        not_health_core = sorted(
            slug for slug in self.upstream_new_skills if index[slug]["governance_scope"] != "health-core"
        )
        self.assertEqual(not_health_core, [])

    def test_health_core_records_have_governance_metadata(self):
        for record in self.health_core:
            self.assertIn(record["distribution_tier"], {"core", "labs", "restricted"})
            self.assertIsNotNone(record["user_invocable"])
            self.assertTrue(record["allowed_tools"])
            self.assertTrue(record["category"])
            self.assertTrue(record["license_evidence"])

    def test_restricted_records_stay_flagged_for_manual_review(self):
        restricted = [record for record in self.health_core if record["distribution_tier"] == "restricted"]
        self.assertGreaterEqual(len(restricted), 1)
        self.assertTrue(all(record["audit_status"] == "needs-review" for record in restricted))


if __name__ == "__main__":
    unittest.main()
