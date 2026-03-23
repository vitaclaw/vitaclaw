#!/usr/bin/env python3
"""Tests for manifest-driven README rendering."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import render_readme_catalog  # noqa: E402


class ReadmeRenderTest(unittest.TestCase):
    def test_render_is_idempotent_on_temp_copies(self):
        manifest = render_readme_catalog.load_manifest(ROOT / "skills-manifest.json")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            readme_en = tmp / "README.md"
            readme_zh = tmp / "README.zh.md"
            shutil.copy2(ROOT / "README.md", readme_en)
            shutil.copy2(ROOT / "README.zh.md", readme_zh)

            first_en = render_readme_catalog.render_readme(readme_en, manifest, zh=False)
            first_zh = render_readme_catalog.render_readme(readme_zh, manifest, zh=True)
            second_en = render_readme_catalog.render_readme(readme_en, manifest, zh=False)
            second_zh = render_readme_catalog.render_readme(readme_zh, manifest, zh=True)

            self.assertFalse(first_en)
            self.assertFalse(first_zh)
            self.assertFalse(second_en)
            self.assertFalse(second_zh)

    def test_repository_readmes_reference_manifest_counts(self):
        manifest = render_readme_catalog.load_manifest(ROOT / "skills-manifest.json")
        expected_skill_count = str(manifest["summary"]["skill_count"])
        expected_health_core = str(manifest["summary"]["health_skill_count"])

        readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh.md").read_text(encoding="utf-8")

        self.assertIn(f"| Total skills (excluding `_shared`) | {expected_skill_count} |", readme_en)
        self.assertIn(f"| Health-core skills | {expected_health_core} |", readme_en)
        self.assertIn(f"| 总 skill 数（不含 `_shared`） | {expected_skill_count} |", readme_zh)
        self.assertIn(f"| 健康核心 skill | {expected_health_core} |", readme_zh)


if __name__ == "__main__":
    unittest.main()
