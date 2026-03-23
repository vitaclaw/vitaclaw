#!/usr/bin/env python3
"""Tests for the Iteration 1 health-core smoke command map."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import smoke_test_skills  # noqa: E402


class SmokeTestSkillsTest(unittest.TestCase):
    def test_health_core_smoke_commands_include_compile_and_help(self):
        command_map = smoke_test_skills.health_core_smoke_commands()

        self.assertIn("blood-pressure-tracker::py_compile", command_map)
        self.assertIn("blood-pressure-tracker::help", command_map)
        self.assertIn("medical-record-organizer::py_compile", command_map)

        help_cmd = command_map["blood-pressure-tracker::help"]
        self.assertEqual(help_cmd[-1], "--help")
        self.assertIn("skills/blood-pressure-tracker/blood_pressure_tracker.py", help_cmd)


if __name__ == "__main__":
    unittest.main()
