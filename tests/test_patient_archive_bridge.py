#!/usr/bin/env python3
"""Tests for syncing medical-record-organizer patient archives into a workspace."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from patient_archive_bridge import PatientArchiveBridge  # noqa: E402


class PatientArchiveBridgeTest(unittest.TestCase):
    def test_sync_writes_summary_and_link(self):
        fixed_now = lambda: datetime(2026, 4, 3, 9, 0, 0)

        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as patients_dir:
            patient_dir = Path(patients_dir) / "PT-DEMO001"
            (patient_dir / "10_原始文件" / "未分类").mkdir(parents=True, exist_ok=True)
            (patient_dir / "09_Apple_Health").mkdir(parents=True, exist_ok=True)
            (patient_dir / "INDEX.md").write_text(
                "\n".join(
                    [
                        "# 病历索引 — PT-DEMO001",
                        "",
                        "## 基本信息",
                        "- **诊断**：高血压合并2型糖尿病",
                        "- **核心状况**：近期血压波动",
                        "",
                        "## ★ 当前治疗状态",
                        "- **当前方案**：生活方式管理 + 氨氯地平",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (patient_dir / "timeline.md").write_text(
                "\n".join(
                    [
                        "# 病历时间线 — PT-DEMO001",
                        "",
                        "| 日期 | 文档类型 | 摘要 | 文件路径 |",
                        "|------|----------|------|---------|",
                        "| 2026-04-02 | 门诊复诊 | 调整降压方案，2周后复诊 | 06_治疗决策历史/2026-04-02_followup.md |",
                        "| 2026-03-28 | 化验单 | 空腹血糖 7.4 mmol/L | 05_检验检查/生化肝肾功/2026-03-28_lab.md |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (patient_dir / "10_原始文件" / "未分类" / "new-report.pdf").write_text("pdf placeholder\n", encoding="utf-8")
            (patient_dir / "09_Apple_Health" / "体重变化.md").write_text("# 体重变化\n", encoding="utf-8")

            bridge = PatientArchiveBridge(
                workspace_root=workspace_dir,
                patients_root=patients_dir,
                patient_id="PT-DEMO001",
                now_fn=fixed_now,
            )
            summary = bridge.sync_to_workspace(write=True)

            self.assertTrue(summary["available"])
            summary_path = Path(summary["summary_path"])
            link_path = Path(summary["link_path"])
            self.assertTrue(summary_path.exists())
            self.assertTrue(link_path.exists())

            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn("PT-DEMO001", summary_text)
            self.assertIn("门诊复诊", summary_text)
            self.assertIn("Pending unclassified files: 1", summary_text)
            self.assertIn("体重变化.md", summary_text)

            payload = json.loads(link_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["patient_id"], "PT-DEMO001")

