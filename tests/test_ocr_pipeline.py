#!/usr/bin/env python3
"""Tests for the OCR extraction pipeline.

All PaddleOCR model inference is mocked -- these are unit tests
that validate pipeline logic, not OCR accuracy.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
SCRIPTS_DIR = ROOT / "skills" / "medical-document-ocr" / "scripts"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from ocr_pipeline import OCRPipeline  # noqa: E402


def _make_pipeline(**resolver_kwargs):
    """Create pipeline with mocked dependencies, bypassing __init__."""
    pipeline = OCRPipeline.__new__(OCRPipeline)
    mock_resolver = MagicMock()
    if resolver_kwargs:
        for k, v in resolver_kwargs.items():
            setattr(mock_resolver, k, v)
    pipeline._concept_resolver = mock_resolver
    pipeline._table_extractor = None
    pipeline._text_extractor = None
    return pipeline


class PrepareInputTest(unittest.TestCase):
    """Test OCRPipeline._prepare_input handles various file types."""

    def test_jpg_passthrough(self):
        """JPG files should be returned as-is without conversion."""
        pipeline = _make_pipeline()
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(b"\xff\xd8\xff\xe0")
        tmp.close()
        try:
            result = pipeline._prepare_input(tmp.name)
            self.assertEqual(result, [tmp.name])
        finally:
            os.unlink(tmp.name)

    def test_png_passthrough(self):
        """PNG files should be returned as-is."""
        pipeline = _make_pipeline()
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(b"\x89PNG")
        tmp.close()
        try:
            result = pipeline._prepare_input(tmp.name)
            self.assertEqual(result, [tmp.name])
        finally:
            os.unlink(tmp.name)

    def test_unsupported_format_raises(self):
        """Unsupported file formats should raise ValueError."""
        pipeline = _make_pipeline()
        with self.assertRaises(ValueError):
            pipeline._prepare_input("/fake/file.xyz")


class ClassifyDocumentTest(unittest.TestCase):
    """Test OCRPipeline._classify_document with mocked OCR output."""

    @patch("paddleocr.PaddleOCR")
    def test_classify_physical_exam(self, mock_ocr_class):
        """Document with '体检' keyword should be classified as physical_exam."""
        pipeline = _make_pipeline()
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.predict.return_value = iter([
            {"rec_texts": ["某某医院", "健康体检报告", "姓名"], "rec_scores": [0.9, 0.95, 0.88]}
        ])
        result = pipeline._classify_document("/fake/image.jpg")
        self.assertEqual(result, "physical_exam")

    @patch("paddleocr.PaddleOCR")
    def test_classify_lab_test(self, mock_ocr_class):
        """Document with '检验' keyword should be classified as lab_test."""
        pipeline = _make_pipeline()
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.predict.return_value = iter([
            {"rec_texts": ["检验报告单", "血常规"], "rec_scores": [0.9, 0.85]}
        ])
        result = pipeline._classify_document("/fake/image.jpg")
        self.assertEqual(result, "lab_test")

    @patch("paddleocr.PaddleOCR")
    def test_classify_outpatient(self, mock_ocr_class):
        """Document with '门诊' keyword should be classified as outpatient."""
        pipeline = _make_pipeline()
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.predict.return_value = iter([
            {"rec_texts": ["门诊病历", "主诉"], "rec_scores": [0.9, 0.85]}
        ])
        result = pipeline._classify_document("/fake/image.jpg")
        self.assertEqual(result, "outpatient")

    @patch("paddleocr.PaddleOCR")
    def test_classify_prescription(self, mock_ocr_class):
        """Document with '处方' keyword should be classified as prescription."""
        pipeline = _make_pipeline()
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.predict.return_value = iter([
            {"rec_texts": ["处方笺", "Rx"], "rec_scores": [0.9, 0.85]}
        ])
        result = pipeline._classify_document("/fake/image.jpg")
        self.assertEqual(result, "prescription")

    @patch("paddleocr.PaddleOCR")
    def test_classify_default_lab_test(self, mock_ocr_class):
        """Unknown document type should default to lab_test."""
        pipeline = _make_pipeline()
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.predict.return_value = iter([
            {"rec_texts": ["some random text"], "rec_scores": [0.5]}
        ])
        result = pipeline._classify_document("/fake/image.jpg")
        self.assertEqual(result, "lab_test")


class MapToConceptsTest(unittest.TestCase):
    """Test OCRPipeline._map_to_concepts maps Chinese lab terms to concept IDs."""

    def test_map_known_chinese_term(self):
        """Known Chinese lab items should map to concept IDs."""
        mock_resolve = MagicMock(return_value=("blood-sugar", {"canonical_type": "glucose"}))
        pipeline = _make_pipeline()
        pipeline._concept_resolver.resolve_concept = mock_resolve
        fields = [
            {"item_name": "血糖", "value": "5.6", "unit": "mmol/L", "confidence": 0.9},
        ]
        result = pipeline._map_to_concepts(fields)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["concept_id"], "blood-sugar")

    def test_map_unknown_term(self):
        """Unknown terms should get empty concept_id."""
        pipeline = _make_pipeline()
        fields = [
            {"item_name": "未知项目", "value": "123", "unit": "", "confidence": 0.8},
        ]
        result = pipeline._map_to_concepts(fields)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["concept_id"], "")

    def test_map_partial_match(self):
        """Partial Chinese name matches should work."""
        mock_resolve = MagicMock(return_value=("blood-sugar", {"canonical_type": "glucose"}))
        pipeline = _make_pipeline()
        pipeline._concept_resolver.resolve_concept = mock_resolve
        fields = [
            {"item_name": "空腹血糖(GLU)", "value": "5.1", "unit": "mmol/L", "confidence": 0.88},
        ]
        result = pipeline._map_to_concepts(fields)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["concept_id"], "blood-sugar")

    def test_preserves_existing_record_type(self):
        """TextExtractor record_type (e.g. 'medication') should be preserved."""
        pipeline = _make_pipeline()
        fields = [
            {
                "item_name": "阿莫西林",
                "value": "0.5",
                "unit": "g",
                "confidence": 0.85,
                "record_type": "medication",
            },
        ]
        result = pipeline._map_to_concepts(fields)
        self.assertEqual(result[0]["record_type"], "medication")


class ArchiveOriginalTest(unittest.TestCase):
    """Test OCRPipeline._archive_original copies file and creates metadata."""

    def test_archive_copies_file(self):
        """Original file should be copied to files_dir."""
        pipeline = _make_pipeline()

        # Create temp source file
        src = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        src.write(b"fake image data")
        src.close()

        # Create temp files_dir
        files_dir = tempfile.mkdtemp()

        try:
            with patch("ocr_pipeline.HealthMemoryWriter") as mock_writer_class:
                mock_writer = MagicMock()
                mock_writer.files_dir = Path(files_dir)
                mock_writer_class.return_value = mock_writer

                result = pipeline._archive_original(src.name)

            # Verify file was copied
            self.assertTrue(os.path.exists(result))
            # Verify metadata JSON was created
            meta_path = result + ".meta.json"
            self.assertTrue(os.path.exists(meta_path))
            with open(meta_path) as f:
                meta = json.load(f)
            self.assertEqual(meta["source"], "ocr_pipeline")
            self.assertIn("file_hash", meta)
        finally:
            os.unlink(src.name)
            shutil.rmtree(files_dir)


class ProcessOutputFormatTest(unittest.TestCase):
    """Test that OCRPipeline.process returns correct staging dict format."""

    def test_staging_dict_keys(self):
        """Process output should have all required staging dict keys."""
        pipeline = _make_pipeline()
        pipeline._concept_resolver.resolve_concept.return_value = (
            "blood-sugar", {"canonical_type": "glucose"}
        )

        # Mock all pipeline stages
        pipeline._prepare_input = MagicMock(return_value=["/fake/image.jpg"])
        pipeline._classify_document = MagicMock(return_value="lab_test")
        pipeline._archive_original = MagicMock(return_value="memory/health/files/2026-03-26_ocr_abc.jpg")

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = [
            {
                "item_name": "血糖",
                "value": "5.6",
                "unit": "mmol/L",
                "reference_range": "3.9-6.1",
                "confidence": 0.92,
                "raw_text": "血糖 5.6 mmol/L 3.9-6.1",
            }
        ]
        pipeline._get_table_extractor = MagicMock(return_value=mock_extractor)

        # Create a real temp file for process to find
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(b"\xff\xd8\xff\xe0")
        tmp.close()

        try:
            result = pipeline.process(tmp.name)

            # Verify all required keys
            self.assertIn("document_type", result)
            self.assertIn("source_file", result)
            self.assertIn("archived_path", result)
            self.assertIn("confidence", result)
            self.assertIn("extracted_fields", result)
            self.assertIn("raw_text", result)

            # Verify extracted_fields have concept mapping
            self.assertGreater(len(result["extracted_fields"]), 0)
            field = result["extracted_fields"][0]
            self.assertIn("concept_id", field)
            self.assertIn("record_type", field)
        finally:
            os.unlink(tmp.name)

    def test_no_healthdatastore_import(self):
        """OCR pipeline should NOT import HealthDataStore (staging only)."""
        pipeline_path = SCRIPTS_DIR / "ocr_pipeline.py"
        content = pipeline_path.read_text()
        import re
        # No import statement for health_data_store
        self.assertIsNone(
            re.search(r"^(?:from|import)\s+.*health_data_store", content, re.MULTILINE),
            "OCR pipeline must not import health_data_store",
        )
        # No HealthDataStore class usage
        self.assertIsNone(
            re.search(r"HealthDataStore\s*\(", content),
            "OCR pipeline must not instantiate HealthDataStore",
        )


class TableExtractorParsingTest(unittest.TestCase):
    """Test TableExtractor HTML table parsing."""

    def test_parse_html_table_with_headers(self):
        """Table with header keywords should classify columns correctly."""
        from ocr_table_extractor import TableExtractor

        extractor = TableExtractor.__new__(TableExtractor)
        extractor._pipeline = None

        html = (
            "<table>"
            "<tr><th>检验项目</th><th>结果</th><th>单位</th><th>参考范围</th></tr>"
            "<tr><td>血红蛋白</td><td>135</td><td>g/L</td><td>130-175</td></tr>"
            "<tr><td>白细胞</td><td>5.3</td><td>10^9/L</td><td>3.5-9.5</td></tr>"
            "</table>"
        )

        fields = extractor._parse_html_table(html)
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0]["item_name"], "血红蛋白")
        self.assertEqual(fields[0]["value"], "135")
        self.assertEqual(fields[0]["unit"], "g/L")
        self.assertEqual(fields[0]["reference_range"], "130-175")

    def test_parse_html_table_positional_defaults(self):
        """Table without header keywords should use positional defaults."""
        from ocr_table_extractor import TableExtractor

        extractor = TableExtractor.__new__(TableExtractor)
        extractor._pipeline = None

        html = (
            "<table>"
            "<tr><th>A</th><th>B</th><th>C</th><th>D</th></tr>"
            "<tr><td>血糖</td><td>5.6</td><td>mmol/L</td><td>3.9-6.1</td></tr>"
            "</table>"
        )

        fields = extractor._parse_html_table(html)
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["item_name"], "血糖")
        self.assertEqual(fields[0]["value"], "5.6")


class TextExtractorParsingTest(unittest.TestCase):
    """Test TextExtractor pattern matching."""

    def test_extract_medications(self):
        """Medication patterns should be extracted correctly."""
        from ocr_text_extractor import TextExtractor

        extractor = TextExtractor.__new__(TextExtractor)
        extractor._ocr = None

        text = "阿莫西林胶囊 0.5g 每日3次 饭后服用"
        fields = extractor._extract_medications(text, 0.9)
        self.assertGreater(len(fields), 0)
        self.assertEqual(fields[0]["record_type"], "medication")

    def test_extract_diagnoses(self):
        """Diagnosis patterns should be extracted correctly."""
        from ocr_text_extractor import TextExtractor

        extractor = TextExtractor.__new__(TextExtractor)
        extractor._ocr = None

        text = "诊断：高血压2级 高危"
        fields = extractor._extract_diagnoses(text, 0.85)
        self.assertGreater(len(fields), 0)
        self.assertEqual(fields[0]["record_type"], "diagnosis")

    def test_extract_chief_complaint(self):
        """Chief complaint patterns should be extracted."""
        from ocr_text_extractor import TextExtractor

        extractor = TextExtractor.__new__(TextExtractor)
        extractor._ocr = None

        text = "主诉：头晕头痛3天"
        fields = extractor._extract_complaints(text, 0.9)
        self.assertGreater(len(fields), 0)
        self.assertEqual(fields[0]["item_name"], "chief_complaint")


if __name__ == "__main__":
    unittest.main()
