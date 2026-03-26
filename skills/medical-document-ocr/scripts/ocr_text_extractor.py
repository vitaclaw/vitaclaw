#!/usr/bin/env python3
"""Text extraction for Chinese medical documents using PaddleOCR PP-OCRv5.

Handles 门诊病历 (outpatient records) and 处方单 (prescriptions)
where data is organized as flowing text rather than tables.

Uses PaddleOCR (lang="ch") with the .predict() API (PaddleOCR 3.x).
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path


def _resize_image(image_path: str, max_size: int = 2048) -> str:
    """Resize image so longest side <= max_size pixels.

    Per Pitfall 6: prevents OOM on large phone camera images.
    Returns path to resized image (may be a temp file).
    """
    from PIL import Image

    with Image.open(image_path) as img:
        w, h = img.size
        if max(w, h) <= max_size:
            return image_path
        scale = max_size / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp_path = tmp.name
        tmp.close()
        if resized.mode == "RGBA":
            resized = resized.convert("RGB")
        resized.save(tmp_path, "JPEG", quality=95)
        return tmp_path


class TextExtractor:
    """Extract structured fields from text-heavy Chinese medical documents.

    Handles prescriptions (处方单) and outpatient records (门诊病历)
    using PaddleOCR PP-OCRv5 for Chinese text recognition.
    """

    # Medication pattern: drug name + dosage + frequency
    _MED_PATTERNS = [
        # "阿莫西林胶囊 0.5g 每日3次" or "氨氯地平片 5mg bid"
        re.compile(
            r"([^\d\s]{2,15}(?:片|胶囊|颗粒|注射液|口服液|滴眼液|软膏|乳膏|丸)?)"
            r"\s*"
            r"([\d.]+\s*(?:mg|g|ml|mL|IU|万单位|ug|mcg|μg))"
            r"\s*"
            r"((?:每日|一日|每天|日)\s*\d+\s*次|[Bb]id|[Tt]id|[Qq]d|[Qq]id|prn|[Qq]n|[Qq]od)?"
        ),
    ]

    # Diagnosis pattern
    _DIAGNOSIS_PATTERNS = [
        re.compile(r"(?:诊断|初步诊断|出院诊断|临床诊断)\s*[:：]\s*(.+)"),
        re.compile(r"(?:西医诊断|中医诊断)\s*[:：]\s*(.+)"),
    ]

    # Chief complaint / history patterns
    _COMPLAINT_PATTERNS = [
        re.compile(r"(?:主诉|主\s*诉)\s*[:：]\s*(.+)"),
        re.compile(r"(?:现病史|病史)\s*[:：]\s*(.+)"),
        re.compile(r"(?:既往史)\s*[:：]\s*(.+)"),
    ]

    def __init__(self):
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(lang="ch")
        except ImportError as e:
            print(
                f"[WARN] PaddleOCR not available: {e}. "
                "Install with: pip install paddleocr",
                file=sys.stderr,
            )
            raise

    def extract(self, image_path: str) -> list[dict]:
        """Extract text fields from image.

        Args:
            image_path: Path to image file.

        Returns:
            List of dicts with keys:
                item_name, value, unit, confidence, record_type, raw_text
        """
        # Resize to max 2048px to prevent OOM (Pitfall 6)
        resized_path = _resize_image(image_path, max_size=2048)
        is_temp = resized_path != image_path

        try:
            results = list(self._ocr.predict(resized_path))
            return self._parse_text_results(results)
        finally:
            if is_temp:
                try:
                    os.unlink(resized_path)
                except OSError:
                    pass

    def _parse_text_results(self, results: list) -> list[dict]:
        """Parse PaddleOCR text output into structured fields."""
        all_texts: list[str] = []
        all_scores: list[float] = []

        for page in results:
            if not isinstance(page, dict):
                continue
            texts = page.get("rec_texts", [])
            scores = page.get("rec_scores", [])
            all_texts.extend(texts)
            all_scores.extend(scores)

        if not all_texts:
            return []

        raw_text = "\n".join(all_texts)
        avg_confidence = sum(all_scores) / len(all_scores) if all_scores else 0.5

        fields: list[dict] = []

        # Extract medications
        fields.extend(self._extract_medications(raw_text, avg_confidence))

        # Extract diagnoses
        fields.extend(self._extract_diagnoses(raw_text, avg_confidence))

        # Extract chief complaints and history
        fields.extend(self._extract_complaints(raw_text, avg_confidence))

        # Per D-16: if overall confidence < 60%, include raw text
        if avg_confidence < 0.6:
            fields.append({
                "item_name": "raw_ocr_text",
                "value": raw_text,
                "unit": "",
                "confidence": avg_confidence,
                "record_type": "raw_text",
                "raw_text": raw_text,
                "needs_manual_review": True,
            })

        # Attach raw_text to all fields for reference
        for f in fields:
            if "raw_text" not in f:
                f["raw_text"] = raw_text

        return fields

    def _extract_medications(self, text: str, base_confidence: float) -> list[dict]:
        """Extract medication records from text."""
        fields: list[dict] = []

        for pattern in self._MED_PATTERNS:
            for match in pattern.finditer(text):
                drug_name = match.group(1).strip()
                dosage = match.group(2).strip()
                frequency = match.group(3).strip() if match.group(3) else ""

                # Parse unit from dosage
                unit_match = re.search(r"(mg|g|ml|mL|IU|万单位|ug|mcg|μg)", dosage)
                unit = unit_match.group(1) if unit_match else ""
                value = re.sub(r"(mg|g|ml|mL|IU|万单位|ug|mcg|μg)", "", dosage).strip()

                fields.append({
                    "item_name": drug_name,
                    "value": value,
                    "unit": unit,
                    "frequency": frequency,
                    "confidence": base_confidence,
                    "record_type": "medication",
                    "needs_manual_review": base_confidence < 0.6,
                })

        return fields

    def _extract_diagnoses(self, text: str, base_confidence: float) -> list[dict]:
        """Extract diagnosis records from text."""
        fields: list[dict] = []

        for pattern in self._DIAGNOSIS_PATTERNS:
            match = pattern.search(text)
            if match:
                diagnosis_text = match.group(1).strip()
                # Split multiple diagnoses separated by common delimiters
                diagnoses = re.split(r"[;；\d+[.、）)]", diagnosis_text)
                for diag in diagnoses:
                    diag = diag.strip()
                    if diag and len(diag) >= 2:
                        fields.append({
                            "item_name": "diagnosis",
                            "value": diag,
                            "unit": "",
                            "confidence": base_confidence,
                            "record_type": "diagnosis",
                            "needs_manual_review": base_confidence < 0.6,
                        })

        return fields

    def _extract_complaints(self, text: str, base_confidence: float) -> list[dict]:
        """Extract chief complaint and history from text."""
        fields: list[dict] = []

        for pattern in self._COMPLAINT_PATTERNS:
            match = pattern.search(text)
            if match:
                complaint_text = match.group(1).strip()
                # Determine the type from the pattern
                pattern_str = pattern.pattern
                if "主诉" in pattern_str:
                    item_name = "chief_complaint"
                elif "现病史" in pattern_str or "病史" in pattern_str:
                    item_name = "present_illness"
                elif "既往史" in pattern_str:
                    item_name = "past_history"
                else:
                    item_name = "clinical_note"

                fields.append({
                    "item_name": item_name,
                    "value": complaint_text,
                    "unit": "",
                    "confidence": base_confidence,
                    "record_type": "clinical_note",
                    "needs_manual_review": base_confidence < 0.6,
                })

        return fields
