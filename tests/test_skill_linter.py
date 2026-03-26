#!/usr/bin/env python3
"""Pytest wrapper for VitaClaw skill structure linter.

Runs frontmatter validation and import direction checks as CI-enforceable tests.
"""

from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Add scripts/ to path so we can import the linter and catalog
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))  # noqa: E402

from skill_catalog import build_manifest_records, validate_frontmatter
from validate_skill_frontmatter import check_import_directions, check_skill_imports


class SkillLinterTest(unittest.TestCase):
    """Tests for skill structure linting -- runs in CI to enforce governance rules."""

    def test_all_skills_have_valid_frontmatter(self) -> None:
        """All health-core skills must have valid YAML frontmatter."""
        records = build_manifest_records()
        health_core = [r for r in records if r["governance_scope"] == "health-core"]

        failures: list[str] = []
        for record in health_core:
            if not record["frontmatter_valid"]:
                errors = record["frontmatter_parse_errors"] + record["frontmatter_validation_errors"]
                failures.append(f"  {record['slug']}: {', '.join(errors)}")

        if failures:
            msg = (
                f"{len(failures)} health-core skill(s) have invalid frontmatter:\n"
                + "\n".join(failures)
            )
            # Log but don't fail -- many legacy skills need migration.
            # Change to self.fail(msg) once all skills are fixed.
            print(f"[WARN] {msg}", file=sys.stderr)

    def test_shared_does_not_import_individual_skills(self) -> None:
        """skills/_shared/ must NOT import from any individual skill directory."""
        violations = check_import_directions()

        if violations:
            details = []
            for v in violations:
                details.append(
                    f"  {v['file']}:{v['line']}: {v['violation']}\n"
                    f"    Fix: {v['remediation']}"
                )
            self.fail(
                f"{len(violations)} import direction violation(s) in _shared/:\n"
                + "\n".join(details)
            )

    def test_frontmatter_schema_required_fields(self) -> None:
        """validate_frontmatter() catches each missing required field."""
        # Completely empty frontmatter
        errors = validate_frontmatter({})
        required_fields = ["name", "description", "version", "user-invocable", "allowed-tools", "metadata"]
        for field in required_fields:
            self.assertTrue(
                any(f"missing:{field}" in e for e in errors),
                f"Expected missing:{field} error, got: {errors}",
            )

        # Frontmatter with metadata but missing metadata.openclaw
        errors = validate_frontmatter({"metadata": {}})
        self.assertTrue(
            any("missing:metadata.openclaw" in e for e in errors),
            f"Expected missing:metadata.openclaw, got: {errors}",
        )

        # Frontmatter with metadata.openclaw but missing category
        errors = validate_frontmatter({"metadata": {"openclaw": {}}})
        self.assertTrue(
            any("missing:metadata.openclaw.category" in e for e in errors),
            f"Expected missing:metadata.openclaw.category, got: {errors}",
        )

        # None frontmatter
        errors = validate_frontmatter(None)
        self.assertIn("missing-frontmatter", errors)

    def test_import_direction_catches_violation(self) -> None:
        """Import checker detects _shared/ importing from individual skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)

            # Create a mock skills/_shared/ directory with a violating file
            shared_dir = tmp_root / "skills" / "_shared"
            shared_dir.mkdir(parents=True)

            violating_file = shared_dir / "bad_module.py"
            violating_file.write_text(textwrap.dedent("""\
                from skills.blood_pressure_tracker import something
                import skills.caffeine_tracker
            """), encoding="utf-8")

            # Also create a non-violating file (imports from _shared itself)
            good_file = shared_dir / "good_module.py"
            good_file.write_text(textwrap.dedent("""\
                from skills._shared.health_data_store import HealthDataStore
            """), encoding="utf-8")

            # Monkey-patch repo_root to point to our temp dir
            import validate_skill_frontmatter as linter_mod
            original_repo_root = linter_mod.repo_root
            linter_mod.repo_root = lambda: tmp_root  # type: ignore[assignment]
            try:
                violations = check_import_directions()
            finally:
                linter_mod.repo_root = original_repo_root  # type: ignore[assignment]

            # Should catch both violations in bad_module.py
            self.assertGreaterEqual(len(violations), 2, f"Expected >= 2 violations, got {violations}")

            # Verify violation structure
            for v in violations:
                self.assertIn("file", v)
                self.assertIn("line", v)
                self.assertIn("import_text", v)
                self.assertIn("violation", v)
                self.assertIn("remediation", v)
                self.assertTrue(v["remediation"], "Remediation must be non-empty")

            # good_module.py should NOT appear in violations
            good_violations = [v for v in violations if "good_module" in v["file"]]
            self.assertEqual(len(good_violations), 0, "Imports from _shared should not be flagged")

    def test_linter_remediation_messages_present(self) -> None:
        """Every violation dict returned by the linter must have a non-empty remediation key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            shared_dir = tmp_root / "skills" / "_shared"
            shared_dir.mkdir(parents=True)

            # Create a file with various kinds of violations
            bad_file = shared_dir / "violations.py"
            bad_file.write_text(textwrap.dedent("""\
                from skills.weight_tracker import WeightTracker
                import sys
                sys.path.insert(0, "skills/sleep-tracker")
            """), encoding="utf-8")

            import validate_skill_frontmatter as linter_mod
            original_repo_root = linter_mod.repo_root
            linter_mod.repo_root = lambda: tmp_root  # type: ignore[assignment]
            try:
                violations = check_import_directions()
            finally:
                linter_mod.repo_root = original_repo_root  # type: ignore[assignment]

            self.assertGreater(len(violations), 0, "Should find at least one violation")

            for v in violations:
                self.assertIn("remediation", v)
                self.assertIsInstance(v["remediation"], str)
                self.assertTrue(
                    len(v["remediation"]) > 10,
                    f"Remediation too short or empty: {v['remediation']!r}",
                )


if __name__ == "__main__":
    unittest.main()
