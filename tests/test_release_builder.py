#!/usr/bin/env python3
"""Tests for layered VitaClaw release building."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import build_vitaclaw_release  # noqa: E402


class ReleaseBuilderTest(unittest.TestCase):
    def test_available_packages_are_exposed(self):
        self.assertEqual(
            set(build_vitaclaw_release.available_packages()),
            {
                "vitaclaw-core",
                "vitaclaw-family-care",
                "vitaclaw-oncology",
                "vitaclaw-labs",
            },
        )

    def test_core_package_builds_manifest_and_readme(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dist_dir = Path(tmp_dir)
            built = build_vitaclaw_release.build_package("vitaclaw-core", dist_dir=dist_dir, clean=True)

            self.assertTrue((built / "package-manifest.json").exists())
            self.assertTrue((built / "README.md").exists())
            self.assertTrue((built / "scripts" / "run_health_chief_of_staff.py").exists())
            self.assertTrue((built / "skills" / "_shared" / "health_team_runtime.py").exists())

    def test_all_packages_build(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dist_dir = Path(tmp_dir)
            for package in build_vitaclaw_release.available_packages():
                built = build_vitaclaw_release.build_package(package, dist_dir=dist_dir, clean=True)
                self.assertTrue(built.exists())
                self.assertTrue((built / "package-manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
