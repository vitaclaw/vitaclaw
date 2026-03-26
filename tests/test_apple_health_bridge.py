#!/usr/bin/env python3
"""Tests for importing Apple Health export into patient archives."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from skills._shared.apple_health_bridge import AppleHealthImporter

XML_SAMPLE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<HealthData>\n"
    '  <Record type="HKQuantityTypeIdentifierHeartRate"'
    ' startDate="2026-03-02 08:00:00 +0800"'
    ' endDate="2026-03-02 08:00:00 +0800" value="72" unit="count/min"/>\n'
    '  <Record type="HKQuantityTypeIdentifierHeartRate"'
    ' startDate="2026-03-10 08:00:00 +0800"'
    ' endDate="2026-03-10 08:00:00 +0800" value="78" unit="count/min"/>\n'
    '  <Record type="HKQuantityTypeIdentifierBodyMass"'
    ' startDate="2026-03-03 07:00:00 +0800"'
    ' endDate="2026-03-03 07:00:00 +0800" value="70.5" unit="kg"/>\n'
    '  <Record type="HKQuantityTypeIdentifierBodyMass"'
    ' startDate="2026-03-20 07:00:00 +0800"'
    ' endDate="2026-03-20 07:00:00 +0800" value="69.8" unit="kg"/>\n'
    '  <Record type="HKQuantityTypeIdentifierStepCount"'
    ' startDate="2026-03-05 20:00:00 +0800"'
    ' endDate="2026-03-05 20:00:00 +0800" value="8200" unit="count"/>\n'
    '  <Record type="HKQuantityTypeIdentifierStepCount"'
    ' startDate="2026-03-18 20:00:00 +0800"'
    ' endDate="2026-03-18 20:00:00 +0800" value="6100" unit="count"/>\n'
    '  <Record type="HKCategoryTypeIdentifierSleepAnalysis"'
    ' startDate="2026-03-06 23:00:00 +0800"'
    ' endDate="2026-03-07 06:30:00 +0800"'
    ' value="HKCategoryValueSleepAnalysisAsleep"/>\n'
    '  <Record type="HKQuantityTypeIdentifierBloodPressureSystolic"'
    ' startDate="2026-03-12 08:10:00 +0800"'
    ' endDate="2026-03-12 08:10:00 +0800" value="128" unit="mmHg"/>\n'
    '  <Record type="HKQuantityTypeIdentifierBloodPressureDiastolic"'
    ' startDate="2026-03-12 08:10:20 +0800"'
    ' endDate="2026-03-12 08:10:20 +0800" value="82" unit="mmHg"/>\n'
    "</HealthData>\n"
)


class AppleHealthBridgeTest(unittest.TestCase):
    def test_import_export_generates_reports_updates_timeline_and_syncs(self):
        def fixed_now():
            return datetime(2026, 4, 3, 12, 0, 0)

        with (
            tempfile.TemporaryDirectory() as workspace_dir,
            tempfile.TemporaryDirectory() as patients_dir,
            tempfile.TemporaryDirectory() as input_dir,
        ):
            patient_dir = Path(patients_dir) / "PT-APPLE01"
            (patient_dir / "06_治疗决策历史").mkdir(parents=True, exist_ok=True)
            (patient_dir / "INDEX.md").write_text("# 病历索引 — PT-APPLE01\n", encoding="utf-8")
            (patient_dir / "timeline.md").write_text(
                "# 病历时间线 — PT-APPLE01\n\n"
                "| 日期 | 文档类型 | 摘要 | 文件路径 |\n"
                "|------|----------|------|---------|\n",
                encoding="utf-8",
            )
            (patient_dir / "06_治疗决策历史" / "治疗决策总表.md").write_text(
                "\n".join(
                    [
                        "# 治疗决策历史总表",
                        "",
                        "| 线数 | 时间段 | 方案 | 疗效 |"
                        " 副反应 | 影像趋势 | 标志物趋势 | 决策思路 |",
                        "|------|--------|------|------|"
                        "--------|----------|-----------|--------|",
                        "| 一线 | 2026-03-01 ~ 2026-03-31 |"
                        " 生活方式 + 降压药 | SD | 轻度乏力 | 稳定 | 稳定 | 继续观察 |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            xml_path = Path(input_dir) / "export.xml"
            xml_path.write_text(XML_SAMPLE, encoding="utf-8")

            result = AppleHealthImporter(
                workspace_root=workspace_dir,
                patients_root=patients_dir,
                patient_id="PT-APPLE01",
                now_fn=fixed_now,
            ).import_export(str(xml_path))

            self.assertTrue(result["success"])
            apple_dir = patient_dir / "09_Apple_Health"
            self.assertTrue((apple_dir / "心率趋势.md").exists())
            self.assertTrue((apple_dir / "体重变化.md").exists())
            self.assertTrue((apple_dir / "治疗相关性分析.md").exists())

            correlation = (apple_dir / "治疗相关性分析.md").read_text(encoding="utf-8")
            self.assertIn("一线 — 生活方式 + 降压药", correlation)
            self.assertIn("体重变化", correlation)

            timeline_text = (patient_dir / "timeline.md").read_text(encoding="utf-8")
            self.assertIn("Apple Health 导入", timeline_text)

            workspace_summary = Path(workspace_dir) / "memory" / "health" / "files" / "patient-archive-summary.md"
            self.assertTrue(workspace_summary.exists())
            self.assertIn("Apple Health reports", workspace_summary.read_text(encoding="utf-8"))
