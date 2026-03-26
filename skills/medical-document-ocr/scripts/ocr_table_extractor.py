#!/usr/bin/env python3
"""Table extraction for Chinese medical documents using PPStructureV3.

Handles 体检报告 (physical exam reports) and 检验单 (lab test results)
where data is organized in table layouts.

Uses TableRecognitionPipelineV2 from PaddleOCR 3.x (PPStructureV3).
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


class TableExtractor:
    """Extract structured fields from table-heavy Chinese medical documents.

    Uses PPStructureV3/TableRecognitionPipelineV2 for table detection
    and cell extraction, then applies column role classification to
    associate item names with values, units, and reference ranges.
    """

    # Common column header keywords for role classification
    _COL_ROLE_KEYWORDS = {
        "item": ["项目", "检验项目", "检查项目", "名称", "指标", "项目名称"],
        "value": ["结果", "检验结果", "检查结果", "测定值", "数值"],
        "unit": ["单位", "计量单位"],
        "reference": ["参考值", "参考范围", "正常值", "正常范围", "参考区间"],
    }

    def __init__(self):
        try:
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
            from paddleocr import TableRecognitionPipelineV2
            self._pipeline = TableRecognitionPipelineV2(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
            )
        except ImportError as e:
            print(
                f"[WARN] PaddleOCR not available: {e}. "
                "Install with: pip install paddleocr",
                file=sys.stderr,
            )
            raise

    def extract(self, image_path: str) -> list[dict]:
        """Extract table fields from image.

        Args:
            image_path: Path to image file.

        Returns:
            List of dicts with keys:
                item_name, value, unit, reference_range, confidence, raw_text
        """
        # Resize to max 2048px to prevent OOM (Pitfall 6)
        resized_path = _resize_image(image_path, max_size=2048)
        is_temp = resized_path != image_path

        try:
            results = list(self._pipeline.predict(resized_path))
            return self._parse_table_results(results)
        finally:
            if is_temp:
                try:
                    os.unlink(resized_path)
                except OSError:
                    pass

    def _parse_table_results(self, results: list) -> list[dict]:
        """Parse PPStructureV3 table output into structured fields.

        Applies column role classification (Pitfall 2):
        - First column = item name
        - Second column = result value
        - Third column = unit
        - Fourth column = reference range
        """
        fields: list[dict] = []

        for page_result in results:
            # PPStructureV3 returns table HTML or structured cell data
            html = page_result.get("table_html", "") if isinstance(page_result, dict) else ""
            if html:
                fields.extend(self._parse_html_table(html))
            # Also check for rec_texts-style output
            elif isinstance(page_result, dict) and "rec_texts" in page_result:
                # Fallback: treat as raw text output
                texts = page_result.get("rec_texts", [])
                scores = page_result.get("rec_scores", [])
                raw = " ".join(texts)
                fields.extend(self._extract_from_raw_text(raw, scores))

        return fields

    def _parse_html_table(self, html: str) -> list[dict]:
        """Parse HTML table output from PPStructureV3 into field dicts."""
        fields: list[dict] = []

        # Extract rows from HTML table
        row_pattern = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
        cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL)

        rows = row_pattern.findall(html)
        if not rows:
            return fields

        # Determine column roles from header row
        col_roles = self._classify_columns(rows)

        # Parse data rows (skip header)
        start_row = 1 if col_roles else 0
        for row_html in rows[start_row:]:
            cells = cell_pattern.findall(row_html)
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]

            if not cells:
                continue

            field = self._row_to_field(cells, col_roles)
            if field and field.get("item_name"):
                fields.append(field)

        return fields

    def _classify_columns(self, rows: list[str]) -> list[str]:
        """Classify column roles from header row keywords.

        Returns list of role names: ['item', 'value', 'unit', 'reference', ...]
        Falls back to positional defaults if no keyword match.
        """
        if not rows:
            return ["item", "value", "unit", "reference"]

        cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL)
        header_cells = cell_pattern.findall(rows[0])
        header_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in header_cells]

        if not header_cells:
            return ["item", "value", "unit", "reference"]

        roles: list[str] = []
        for cell_text in header_cells:
            matched = False
            for role, keywords in self._COL_ROLE_KEYWORDS.items():
                if any(kw in cell_text for kw in keywords):
                    roles.append(role)
                    matched = True
                    break
            if not matched:
                roles.append("unknown")

        # If no roles matched, use positional defaults (Pitfall 2)
        if all(r == "unknown" for r in roles):
            n = len(roles)
            defaults = ["item", "value", "unit", "reference"]
            roles = defaults[:n] + ["unknown"] * max(0, n - len(defaults))

        return roles

    def _row_to_field(self, cells: list[str], col_roles: list[str]) -> dict | None:
        """Convert a table row to a field dict using column role mapping."""
        if not cells:
            return None

        field: dict = {
            "item_name": "",
            "value": "",
            "unit": "",
            "reference_range": "",
            "confidence": 0.85,  # Default confidence for table extraction
            "raw_text": " | ".join(cells),
        }

        for i, cell in enumerate(cells):
            if i >= len(col_roles):
                break
            role = col_roles[i]
            if role == "item":
                field["item_name"] = cell
            elif role == "value":
                field["value"] = cell
            elif role == "unit":
                field["unit"] = cell
            elif role == "reference":
                field["reference_range"] = cell

        # Skip rows that look like headers or empty items
        if not field["item_name"] or field["item_name"] in (
            "项目", "检验项目", "检查项目", "名称",
        ):
            return None

        # Per D-16: if confidence < 60%, include raw text for manual identification
        if field["confidence"] < 0.6:
            field["needs_manual_review"] = True

        return field

    def _extract_from_raw_text(self, raw_text: str, scores: list) -> list[dict]:
        """Fallback: extract fields from raw OCR text when table parsing fails."""
        avg_score = sum(scores) / len(scores) if scores else 0.5
        return [{
            "item_name": "",
            "value": "",
            "unit": "",
            "reference_range": "",
            "confidence": avg_score,
            "raw_text": raw_text,
            "needs_manual_review": avg_score < 0.6,
        }]
