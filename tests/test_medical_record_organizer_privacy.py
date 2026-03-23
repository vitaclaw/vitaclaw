#!/usr/bin/env python3
"""Tests for medical-record-organizer privacy gate behavior."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "medical-record-organizer" / "scripts" / "copy_patient_document.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("copy_patient_document_module", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


copy_module = _load_module()


class MedicalRecordOrganizerPrivacyTest(unittest.TestCase):
    def _write_stub(self, path: Path, mode: str) -> None:
        if mode == "success":
            body = """#!/usr/bin/env python3
import argparse
import json
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("--output", required=True)
args = parser.parse_args()
shutil.copy2(args.source, args.output)
print(json.dumps({"success": True, "output": args.output, "pii_detected": 1}))
"""
        else:
            body = """#!/usr/bin/env python3
import json
print(json.dumps({"success": False, "error": "runtime not ready"}))
raise SystemExit(2)
"""
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_privacy_mode_blocks_unredacted_image_when_redaction_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            patient_dir = tmp / "PT-TEST"
            source = tmp / "report.jpg"
            source.write_bytes(b"fake-jpg")
            failing_stub = tmp / "redact_fail.py"
            self._write_stub(failing_stub, "fail")

            result = copy_module.copy_patient_document(
                source_path=str(source),
                patient_dir=str(patient_dir),
                target_rel_path="04_影像学/CT/2026-03-23_CT报告_下肢静脉.jpg",
                sequence="0001",
                privacy_mode=True,
                redact_cmd=[sys.executable, str(failing_stub)],
            )

            self.assertFalse(result["success"])
            self.assertTrue(result["blocked"])
            self.assertEqual(result["stage"], "privacy-gate")
            self.assertTrue(Path(result["backup_path"]).exists())
            self.assertFalse(Path(result["target_path"]).exists())

    def test_privacy_mode_copies_redacted_image_when_redaction_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            patient_dir = tmp / "PT-TEST"
            source = tmp / "report.jpg"
            source.write_text("raw image payload", encoding="utf-8")
            success_stub = tmp / "redact_ok.py"
            self._write_stub(success_stub, "success")

            result = copy_module.copy_patient_document(
                source_path=str(source),
                patient_dir=str(patient_dir),
                target_rel_path="04_影像学/CT/2026-03-23_CT报告_下肢静脉.jpg",
                sequence="0001",
                privacy_mode=True,
                redact_cmd=[sys.executable, str(success_stub)],
            )

            self.assertTrue(result["success"])
            self.assertTrue(result["requires_redaction"])
            self.assertTrue(Path(result["backup_path"]).exists())
            target_path = Path(result["target_path"])
            self.assertTrue(target_path.exists())
            self.assertTrue(Path(result["source_used"]).name.endswith("_redacted.jpg"))
            self.assertEqual(target_path.read_text(encoding="utf-8"), "raw image payload")

    def test_privacy_off_allows_original_image_copy(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            patient_dir = tmp / "PT-TEST"
            source = tmp / "report.jpg"
            source.write_text("raw image payload", encoding="utf-8")

            result = copy_module.copy_patient_document(
                source_path=str(source),
                patient_dir=str(patient_dir),
                target_rel_path="04_影像学/CT/2026-03-23_CT报告_下肢静脉.jpg",
                sequence="0001",
                privacy_mode=False,
            )

            self.assertTrue(result["success"])
            self.assertFalse(result["requires_redaction"])
            target_path = Path(result["target_path"])
            self.assertTrue(target_path.exists())
            self.assertEqual(target_path.read_text(encoding="utf-8"), "raw image payload")


if __name__ == "__main__":
    unittest.main()
