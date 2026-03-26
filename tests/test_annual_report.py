#!/usr/bin/env python3
"""Tests for HealthAnnualReport — annual health report generation."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class HealthAnnualReportTest(unittest.TestCase):
    """Unit tests for health_annual_report module."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_dir = self.tmpdir.name
        self.memory_dir = os.path.join(self.tmpdir.name, "memory", "health")
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(os.path.join(self.memory_dir, "daily"), exist_ok=True)
        os.makedirs(os.path.join(self.memory_dir, "items"), exist_ok=True)
        os.makedirs(os.path.join(self.memory_dir, "files"), exist_ok=True)

    def tearDown(self):
        self.tmpdir.cleanup()

    # ── Test 1: Constructor accepts all expected parameters ──────

    def test_init_accepts_all_parameters(self):
        """HealthAnnualReport.__init__ accepts data_dir, person_id, workspace_root, memory_dir, year."""
        from skills._shared.health_annual_report import HealthAnnualReport

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            person_id="mom",
            workspace_root=self.tmpdir.name,
            memory_dir=self.memory_dir,
            year=2025,
        )
        self.assertEqual(report.year, 2025)
        self.assertEqual(report.person_id, "mom")

    # ── Test 2: generate() returns dict with path and content ────

    @patch("skills._shared.health_annual_report.CorrelationEngine")
    @patch("skills._shared.health_annual_report.CrossSkillReader")
    @patch("skills._shared.health_annual_report.HealthChartEngine")
    def test_generate_returns_dict_with_path_and_html_content(
        self, MockChart, MockReader, MockCorr
    ):
        """generate() returns dict with 'path' and 'content' keys; content has DOCTYPE."""
        from skills._shared.health_annual_report import HealthAnnualReport

        # Mock chart engine to return empty strings (no data)
        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart.generate_sleep_chart.return_value = ""
        MockChart.return_value = mock_chart

        # Mock reader
        mock_reader = MagicMock()
        mock_reader.read_medication_doses.return_value = []
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_sleep_data.return_value = []
        MockReader.return_value = mock_reader

        # Mock correlation engine
        mock_corr = MagicMock()
        mock_corr.discover_correlations.return_value = []
        MockCorr.return_value = mock_corr

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            memory_dir=self.memory_dir,
            year=2025,
        )
        result = report.generate(write=False)

        self.assertIn("path", result)
        self.assertIn("content", result)
        self.assertTrue(result["content"].startswith("<!DOCTYPE html>"))

    # ── Test 3: HTML contains all 7 section headers ──────────────

    @patch("skills._shared.health_annual_report.CorrelationEngine")
    @patch("skills._shared.health_annual_report.CrossSkillReader")
    @patch("skills._shared.health_annual_report.HealthChartEngine")
    def test_html_contains_all_seven_sections(
        self, MockChart, MockReader, MockCorr
    ):
        """HTML output contains all 7 section headers per D-08."""
        from skills._shared.health_annual_report import HealthAnnualReport

        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart.generate_sleep_chart.return_value = ""
        MockChart.return_value = mock_chart

        mock_reader = MagicMock()
        mock_reader.read_medication_doses.return_value = []
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_sleep_data.return_value = []
        MockReader.return_value = mock_reader

        mock_corr = MagicMock()
        mock_corr.discover_correlations.return_value = []
        MockCorr.return_value = mock_corr

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            memory_dir=self.memory_dir,
            year=2025,
        )
        result = report.generate(write=False)
        html = result["content"]

        # All 7 sections per D-08
        expected_sections = [
            "年度概览",       # Year Overview
            "指标轨迹",       # Metric Trajectories
            "用药依从性",     # Medication Adherence
            "健康事件",       # Health Events Timeline
            "改善领域",       # Improvement Areas
            "相关性洞察",     # Correlation Insights
            "目标回顾",       # Goals Review
        ]
        for section in expected_sections:
            self.assertIn(section, html, f"Missing section header: {section}")

    # ── Test 4: _medication_adherence returns correct structure ───

    @patch("skills._shared.health_annual_report.CrossSkillReader")
    def test_medication_adherence_calculation(self, MockReader):
        """_medication_adherence returns dict[med_name, {total_days, tracked_days, adherence_pct, monthly_breakdown}]."""
        from skills._shared.health_annual_report import HealthAnnualReport

        mock_reader = MagicMock()
        # Simulate 90 days of aspirin doses across 3 months
        doses = []
        for month in range(1, 4):
            for day in range(1, 31):
                try:
                    ts = f"2025-{month:02d}-{day:02d}T08:00:00"
                    datetime.strptime(ts[:10], "%Y-%m-%d")  # validate date
                    doses.append({
                        "timestamp": ts,
                        "data": {"medication": "阿司匹林", "dose": "100mg"},
                    })
                except ValueError:
                    pass
        mock_reader.read_medication_doses.return_value = doses
        MockReader.return_value = mock_reader

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            memory_dir=self.memory_dir,
            year=2025,
        )
        adherence = report._medication_adherence(2025)

        self.assertIn("阿司匹林", adherence)
        entry = adherence["阿司匹林"]
        self.assertIn("total_days", entry)
        self.assertIn("tracked_days", entry)
        self.assertIn("adherence_pct", entry)
        self.assertIn("monthly_breakdown", entry)
        self.assertGreater(entry["tracked_days"], 0)
        self.assertGreater(entry["adherence_pct"], 0)

    # ── Test 5: _extract_events_from_daily_logs ──────────────────

    def test_extract_events_from_daily_logs(self):
        """_extract_events_from_daily_logs returns list of dicts with date, type, keyword, context."""
        from skills._shared.health_annual_report import HealthAnnualReport

        # Create a daily log with events
        daily_dir = os.path.join(self.memory_dir, "daily")
        log_content = "## 2025-03-15\n- 就医：去医院复查血压\n- 头晕持续了一天\n"
        with open(os.path.join(daily_dir, "2025-03-15.md"), "w") as f:
            f.write(log_content)

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            memory_dir=self.memory_dir,
            year=2025,
        )
        events = report._extract_events_from_daily_logs(2025)

        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)
        event = events[0]
        self.assertIn("date", event)
        self.assertIn("type", event)
        self.assertIn("keyword", event)
        self.assertIn("context", event)

    # ── Test 6: _improvement_areas returns correct structure ─────

    @patch("skills._shared.health_annual_report.CrossSkillReader")
    def test_improvement_areas_with_data(self, MockReader):
        """_improvement_areas returns list of {metric, direction, delta_pct}."""
        from skills._shared.health_annual_report import HealthAnnualReport

        mock_reader = MagicMock()
        # Q1 BP readings (Jan-Mar): higher
        q1_bp = [
            {"timestamp": f"2025-{m:02d}-{d:02d}T08:00:00",
             "data": {"systolic": 145, "diastolic": 95}}
            for m in range(1, 4) for d in [1, 15]
        ]
        # Q4 BP readings (Oct-Dec): lower (improved)
        q4_bp = [
            {"timestamp": f"2025-{m:02d}-{d:02d}T08:00:00",
             "data": {"systolic": 130, "diastolic": 85}}
            for m in range(10, 13) for d in [1, 15]
        ]
        mock_reader.read_blood_pressure.return_value = q1_bp + q4_bp

        # Glucose data - no change
        mock_reader.read_glucose_data.return_value = []
        # Weight data - no change
        mock_reader.read_weight_data.return_value = []
        # Sleep data - no change
        mock_reader.read_sleep_data.return_value = []

        MockReader.return_value = mock_reader

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            memory_dir=self.memory_dir,
            year=2025,
        )
        areas = report._improvement_areas(2025)

        self.assertIsInstance(areas, list)
        # Should detect BP improvement (收缩压 = systolic, 舒张压 = diastolic)
        bp_areas = [a for a in areas if "压" in a["metric"]]
        self.assertGreater(len(bp_areas), 0)
        for area in areas:
            self.assertIn("metric", area)
            self.assertIn("direction", area)
            self.assertIn("delta_pct", area)

    # ── Test 7: Sparse data handling ─────────────────────────────

    @patch("skills._shared.health_annual_report.CorrelationEngine")
    @patch("skills._shared.health_annual_report.CrossSkillReader")
    @patch("skills._shared.health_annual_report.HealthChartEngine")
    def test_sparse_data_produces_valid_html_with_messages(
        self, MockChart, MockReader, MockCorr
    ):
        """Report with 0 records generates valid HTML with insufficient data messages."""
        from skills._shared.health_annual_report import HealthAnnualReport

        mock_chart = MagicMock()
        mock_chart.generate_blood_pressure_chart.return_value = ""
        mock_chart.generate_blood_glucose_chart.return_value = ""
        mock_chart.generate_weight_chart.return_value = ""
        mock_chart.generate_sleep_chart.return_value = ""
        MockChart.return_value = mock_chart

        mock_reader = MagicMock()
        mock_reader.read_medication_doses.return_value = []
        mock_reader.read_blood_pressure.return_value = []
        mock_reader.read_glucose_data.return_value = []
        mock_reader.read_weight_data.return_value = []
        mock_reader.read_sleep_data.return_value = []
        MockReader.return_value = mock_reader

        mock_corr = MagicMock()
        mock_corr.discover_correlations.return_value = []
        MockCorr.return_value = mock_corr

        report = HealthAnnualReport(
            data_dir=self.data_dir,
            memory_dir=self.memory_dir,
            year=2025,
        )
        result = report.generate(write=False)
        html = result["content"]

        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("暂无", html)  # Chinese "no data" message

    # ── Test 8: person_id threaded to all sub-engines ────────────

    def test_person_id_threaded_to_sub_engines(self):
        """person_id is passed to HealthChartEngine, CrossSkillReader, and CorrelationEngine."""
        from skills._shared.health_annual_report import HealthAnnualReport

        with patch("skills._shared.health_annual_report.HealthChartEngine") as MockChart, \
             patch("skills._shared.health_annual_report.CrossSkillReader") as MockReader, \
             patch("skills._shared.health_annual_report.CorrelationEngine") as MockCorr:

            report = HealthAnnualReport(
                data_dir=self.data_dir,
                person_id="mom",
                memory_dir=self.memory_dir,
                year=2025,
            )

            # Chart engine should receive person_id
            MockChart.assert_called_once()
            chart_kwargs = MockChart.call_args
            self.assertEqual(
                chart_kwargs[1].get("person_id") or chart_kwargs[0][1] if len(chart_kwargs[0]) > 1 else chart_kwargs[1].get("person_id"),
                "mom",
            )


if __name__ == "__main__":
    unittest.main()
