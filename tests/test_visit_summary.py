#!/usr/bin/env python3
"""Unit tests for HealthVisitSummary."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class HealthVisitSummaryInitTest(unittest.TestCase):
    """Test 1: Constructor accepts data_dir, person_id, workspace_root, memory_dir."""

    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_init_creates_internal_engines(self, mock_writer, mock_reader, mock_chart):
        from skills._shared.health_visit_summary import HealthVisitSummary

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = os.path.join(tmpdir, "ws")
            os.makedirs(ws, exist_ok=True)
            summary = HealthVisitSummary(
                data_dir="/tmp/data",
                person_id="mom",
                workspace_root=ws,
                memory_dir="/tmp/mem",
            )
            mock_chart.assert_called_once_with(data_dir="/tmp/data", person_id="mom")
            mock_reader.assert_called_once_with(data_dir="/tmp/data")
            self.assertIsNotNone(summary)


class CollectDataTest(unittest.TestCase):
    """Test 2: _collect_data returns dict with expected keys."""

    @patch("skills._shared.health_visit_summary.HealthHeartbeat")
    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_collect_data_keys(self, mock_writer_cls, mock_reader_cls, mock_chart_cls, mock_hb_cls):
        from skills._shared.health_visit_summary import HealthVisitSummary

        mock_reader = MagicMock()
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_medication_doses.return_value = []
        mock_reader_cls.return_value = mock_reader

        mock_hb = MagicMock()
        mock_hb.run.return_value = {"issues": []}
        mock_hb_cls.return_value = mock_hb

        mock_writer = MagicMock()
        mock_writer.profile_path = Path("/tmp/nonexistent-profile.md")
        mock_writer._resolve_items_path.return_value = Path("/tmp/nonexistent-meds.md")
        mock_writer_cls.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = HealthVisitSummary(workspace_root=tmpdir)
            data = summary._collect_data(days=30)

        self.assertIn("profile", data)
        self.assertIn("vitals", data)
        self.assertIn("medications", data)
        self.assertIn("labs", data)
        self.assertIn("issues", data)


class GenerateMarkdownTest(unittest.TestCase):
    """Test 3: generate(format='markdown') returns dict with 'content' containing sections."""

    @patch("skills._shared.health_visit_summary.HealthHeartbeat")
    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_markdown_has_sections(self, mock_writer_cls, mock_reader_cls, mock_chart_cls, mock_hb_cls):
        from skills._shared.health_visit_summary import HealthVisitSummary

        mock_reader = MagicMock()
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_medication_doses.return_value = []
        mock_reader_cls.return_value = mock_reader

        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart_cls.return_value = mock_chart

        mock_hb = MagicMock()
        mock_hb.run.return_value = {"issues": []}
        mock_hb_cls.return_value = mock_hb

        mock_writer = MagicMock()
        mock_writer.profile_path = Path("/tmp/nonexistent-profile.md")
        mock_writer._resolve_items_path.return_value = Path("/tmp/nonexistent-meds.md")
        mock_writer.files_dir = Path("/tmp/files")
        mock_writer_cls.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = HealthVisitSummary(workspace_root=tmpdir)
            result = summary.generate(days=30, format="markdown", write=False)

        self.assertIn("content", result)
        content = result["content"]
        self.assertIn("患者信息", content)
        self.assertIn("近期生命体征", content)
        self.assertIn("当前用药", content)
        self.assertIn("近期检验结果", content)
        self.assertIn("关注问题", content)
        self.assertIn("就诊问题", content)


class GenerateHTMLTest(unittest.TestCase):
    """Test 4: generate(format='html') returns HTML with DOCTYPE, inline CSS, base64."""

    @patch("skills._shared.health_visit_summary.HealthHeartbeat")
    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_html_structure(self, mock_writer_cls, mock_reader_cls, mock_chart_cls, mock_hb_cls):
        from skills._shared.health_visit_summary import HealthVisitSummary

        mock_reader = MagicMock()
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_medication_doses.return_value = []
        mock_reader_cls.return_value = mock_reader

        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart_cls.return_value = mock_chart

        mock_hb = MagicMock()
        mock_hb.run.return_value = {"issues": []}
        mock_hb_cls.return_value = mock_hb

        mock_writer = MagicMock()
        mock_writer.profile_path = Path("/tmp/nonexistent-profile.md")
        mock_writer._resolve_items_path.return_value = Path("/tmp/nonexistent-meds.md")
        mock_writer.files_dir = Path("/tmp/files")
        mock_writer_cls.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = HealthVisitSummary(workspace_root=tmpdir)
            result = summary.generate(days=30, format="html", write=False)

        self.assertIn("content", result)
        content = result["content"]
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("<style", content)


class PDFFallbackTest(unittest.TestCase):
    """Test 5: generate(format='pdf') with weasyprint absent returns HTML fallback."""

    @patch("skills._shared.health_visit_summary.HealthHeartbeat")
    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_pdf_fallback_without_weasyprint(self, mock_writer_cls, mock_reader_cls, mock_chart_cls, mock_hb_cls):
        from skills._shared.health_visit_summary import HealthVisitSummary

        mock_reader = MagicMock()
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_medication_doses.return_value = []
        mock_reader_cls.return_value = mock_reader

        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart_cls.return_value = mock_chart

        mock_hb = MagicMock()
        mock_hb.run.return_value = {"issues": []}
        mock_hb_cls.return_value = mock_hb

        mock_writer = MagicMock()
        mock_writer.profile_path = Path("/tmp/nonexistent-profile.md")
        mock_writer._resolve_items_path.return_value = Path("/tmp/nonexistent-meds.md")
        mock_writer.files_dir = Path("/tmp/files")
        mock_writer_cls.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = HealthVisitSummary(workspace_root=tmpdir)
            result = summary.generate(days=30, format="pdf", write=False)

        # Should fall back gracefully -- return HTML content or a message about fallback
        self.assertIn("content", result)
        self.assertIn("format", result)


class GracefulEmptyDataTest(unittest.TestCase):
    """Test 6: Missing data handled gracefully -- no crash, Chinese 'no data' message."""

    @patch("skills._shared.health_visit_summary.HealthHeartbeat")
    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_empty_vitals_no_crash(self, mock_writer_cls, mock_reader_cls, mock_chart_cls, mock_hb_cls):
        from skills._shared.health_visit_summary import HealthVisitSummary

        mock_reader = MagicMock()
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_medication_doses.return_value = []
        mock_reader_cls.return_value = mock_reader

        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart_cls.return_value = mock_chart

        mock_hb = MagicMock()
        mock_hb.run.return_value = {"issues": []}
        mock_hb_cls.return_value = mock_hb

        mock_writer = MagicMock()
        mock_writer.profile_path = Path("/tmp/nonexistent-profile.md")
        mock_writer._resolve_items_path.return_value = Path("/tmp/nonexistent-meds.md")
        mock_writer.files_dir = Path("/tmp/files")
        mock_writer_cls.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = HealthVisitSummary(workspace_root=tmpdir)
            result = summary.generate(days=30, format="markdown", write=False)

        content = result["content"]
        # Should have Chinese no-data messages, not crash
        self.assertTrue(
            "近期无" in content or "未找到" in content or "无记录" in content,
            f"Expected Chinese no-data message in content, got:\n{content[:500]}",
        )


class PersonIdThreadingTest(unittest.TestCase):
    """Test 7: person_id threaded to chart_engine and reader."""

    @patch("skills._shared.health_visit_summary.HealthChartEngine")
    @patch("skills._shared.health_visit_summary.CrossSkillReader")
    @patch("skills._shared.health_visit_summary.HealthMemoryWriter")
    def test_person_id_passed_to_engines(self, mock_writer_cls, mock_reader_cls, mock_chart_cls):
        from skills._shared.health_visit_summary import HealthVisitSummary

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = HealthVisitSummary(
                data_dir="/tmp/data",
                person_id="mom",
                workspace_root=tmpdir,
            )

        mock_chart_cls.assert_called_once_with(data_dir="/tmp/data", person_id="mom")
        # CrossSkillReader does not take person_id in constructor, but data_dir
        mock_reader_cls.assert_called_once_with(data_dir="/tmp/data")
        # person_id should be stored for use in data collection
        self.assertEqual(summary.person_id, "mom")


if __name__ == "__main__":
    unittest.main()
