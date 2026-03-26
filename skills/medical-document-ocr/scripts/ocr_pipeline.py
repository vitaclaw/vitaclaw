#!/usr/bin/env python3
"""OCR extraction pipeline for Chinese medical documents.

Orchestrates: input handling -> document classification -> extraction
dispatch (table vs text) -> concept mapping -> document archiving.

CRITICAL: This pipeline NEVER auto-stores to HealthDataStore.
It returns staging JSON for user confirmation only.

Supported document types:
  - 体检报告 (physical exam report) -- table extraction
  - 检验单 (lab test results) -- table extraction
  - 门诊病历 (outpatient records) -- text extraction
  - 处方单 (prescriptions) -- text extraction

Supported input formats: JPG, PNG, HEIC, PDF (per D-17).

Usage:
  python ocr_pipeline.py <path> --format json
  python ocr_pipeline.py <path> --format markdown
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _setup_imports():
    """Add shared modules to path."""
    shared = str(_repo_root() / "skills" / "_shared")
    if shared not in sys.path:
        sys.path.insert(0, shared)


_setup_imports()

from concept_resolver import ConceptResolver  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402


class OCRPipeline:
    """Orchestrate OCR extraction for Chinese medical documents.

    Pipeline stages (per D-11): classify -> extract -> map -> stage.
    Does NOT write to HealthDataStore -- staging only.
    """

    DOC_TYPES = {
        "体检报告": "physical_exam",
        "检验单": "lab_test",
        "门诊病历": "outpatient",
        "处方单": "prescription",
    }

    TABLE_TYPES = {"physical_exam", "lab_test"}
    TEXT_TYPES = {"outpatient", "prescription"}

    # Chinese lab item name -> health concept ID mapping
    _CHINESE_CONCEPT_MAP = {
        "血红蛋白": "hemoglobin",
        "红细胞": "rbc",
        "白细胞": "wbc",
        "血小板": "platelet",
        "血糖": "blood-sugar",
        "空腹血糖": "blood-sugar",
        "葡萄糖": "blood-sugar",
        "收缩压": "blood-pressure",
        "舒张压": "blood-pressure",
        "血压": "blood-pressure",
        "总胆固醇": "blood-lipids",
        "甘油三酯": "blood-lipids",
        "高密度脂蛋白": "blood-lipids",
        "低密度脂蛋白": "blood-lipids",
        "谷丙转氨酶": "liver-function",
        "谷草转氨酶": "liver-function",
        "总胆红素": "liver-function",
        "白蛋白": "liver-function",
        "ALT": "liver-function",
        "AST": "liver-function",
        "肌酐": "kidney-function",
        "尿素氮": "kidney-function",
        "尿酸": "kidney-function",
        "肾小球滤过率": "kidney-function",
        "eGFR": "kidney-function",
        "体温": "temperature",
        "心率": "heart-rate",
        "脉搏": "heart-rate",
        "血氧": "spo2",
        "血氧饱和度": "spo2",
        "体重": "weight",
        "AFP": "tumor-markers",
        "CEA": "tumor-markers",
        "CA199": "tumor-markers",
        "PSA": "tumor-markers",
        "甲胎蛋白": "tumor-markers",
        "癌胚抗原": "tumor-markers",
    }

    def __init__(self, concept_resolver=None):
        self._concept_resolver = concept_resolver or ConceptResolver()
        self._table_extractor = None  # Lazy init
        self._text_extractor = None   # Lazy init

    def process(self, file_path: str, person_id: str | None = None) -> dict:
        """Process a medical document image/PDF.

        Args:
            file_path: Path to image or PDF file.
            person_id: Optional person identifier for multi-person support.

        Returns:
            Staging dict with document_type, source_file, archived_path,
            confidence, extracted_fields, and raw_text.
            DOES NOT write to HealthDataStore -- staging only per D-11.
        """
        file_path = str(Path(file_path).expanduser().resolve())
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")

        # Stage 1: Prepare input (HEIC->JPG, PDF->images)
        image_paths = self._prepare_input(file_path)

        if not image_paths:
            raise ValueError(f"No processable images from: {file_path}")

        # Stage 2: Classify document type (from first image)
        doc_type = self._classify_document(image_paths[0])

        # Stage 3: Extract fields
        all_fields: list[dict] = []
        all_raw_texts: list[str] = []

        for img_path in image_paths:
            if doc_type in self.TABLE_TYPES:
                extractor = self._get_table_extractor()
                fields = extractor.extract(img_path)
            else:
                extractor = self._get_text_extractor()
                fields = extractor.extract(img_path)

            all_fields.extend(fields)
            # Collect raw text from fields
            for f in fields:
                raw = f.get("raw_text", "")
                if raw:
                    all_raw_texts.append(raw)

        # Stage 4: Map to health concepts
        mapped_fields = self._map_to_concepts(all_fields)

        # Stage 5: Archive original document
        archived_path = self._archive_original(file_path, person_id=person_id)

        # Cleanup temp image files from PDF conversion
        for img_path in image_paths:
            if img_path != file_path and os.path.exists(img_path):
                try:
                    os.unlink(img_path)
                except OSError:
                    pass

        # Calculate overall confidence
        confidences = [f.get("confidence", 0) for f in mapped_fields]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Find display name for document type
        doc_type_zh = ""
        for zh, en in self.DOC_TYPES.items():
            if en == doc_type:
                doc_type_zh = zh
                break

        return {
            "document_type": doc_type_zh or doc_type,
            "document_type_key": doc_type,
            "source_file": file_path,
            "archived_path": archived_path,
            "confidence": round(avg_confidence, 2),
            "extracted_fields": mapped_fields,
            "raw_text": "\n".join(all_raw_texts),
            "person_id": person_id,
        }

    def _prepare_input(self, file_path: str) -> list[str]:
        """Handle input: HEIC -> JPG, PDF -> images.

        Per D-17: accepts JPG, PNG, HEIC, PDF.
        Returns list of image paths ready for OCR.
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".heic", ".heif"):
            # Convert HEIC to JPG using pattern from redact_ocr.py
            converted, is_temp = self._ensure_processable(file_path)
            return [converted]

        if ext == ".pdf":
            # Convert PDF pages to images using PyMuPDF
            return self._pdf_to_images(file_path)

        # JPG, PNG, etc. -- use directly
        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"):
            return [file_path]

        raise ValueError(f"Unsupported file format: {ext}")

    def _ensure_processable(self, image_path: str) -> tuple[str, bool]:
        """Convert HEIC/HEIF to temporary JPG.

        Reuses pattern from redact_ocr.py.
        Returns (processable_path, is_temp).
        """
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in (".heic", ".heif"):
            return (image_path, False)

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp_path = tmp.name
        tmp.close()

        # Try macOS sips first
        try:
            import subprocess
            r = subprocess.run(
                ["sips", "-s", "format", "jpeg", image_path, "--out", tmp_path],
                capture_output=True, timeout=30,
            )
            if r.returncode == 0:
                return (tmp_path, True)
        except Exception:
            pass

        # Fallback: pillow-heif
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            from PIL import Image
            with Image.open(image_path) as img:
                img.convert("RGB").save(tmp_path, "JPEG", quality=95)
            return (tmp_path, True)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            return (image_path, False)

    def _pdf_to_images(self, pdf_path: str, dpi: int = 200) -> list[str]:
        """Convert PDF pages to temporary JPG images.

        Reuses pattern from privacy_desensitize.py.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF required for PDF processing. Run: pip install PyMuPDF")

        from PIL import Image

        doc = fitz.open(pdf_path)
        image_paths: list[str] = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            tmp = tempfile.NamedTemporaryFile(
                suffix=".jpg", delete=False, prefix=f"ocr_p{page_num + 1}_"
            )
            tmp_path = tmp.name
            tmp.close()

            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img.save(tmp_path, "JPEG", quality=95)
            image_paths.append(tmp_path)

        doc.close()
        return image_paths

    def _classify_document(self, image_path: str) -> str:
        """Auto-detect document type from layout and keywords.

        Per D-12: system auto-detects, does not require user to specify.
        Uses quick text OCR on first image and looks for keywords.
        Returns one of DOC_TYPES values.
        """
        try:
            from paddleocr import PaddleOCR  # noqa: E402
            ocr = PaddleOCR(lang="ch")
            results = list(ocr.predict(image_path))

            all_text = ""
            for page in results:
                if isinstance(page, dict):
                    texts = page.get("rec_texts", [])
                    all_text += " ".join(texts) + " "

            all_text = all_text.lower()

            # Check keywords in priority order
            if "体检" in all_text or "健康体检" in all_text:
                return "physical_exam"
            if "检验" in all_text or "化验" in all_text or "生化" in all_text:
                return "lab_test"
            if "门诊" in all_text or "病历" in all_text:
                return "outpatient"
            if "处方" in all_text or "rx" in all_text:
                return "prescription"

        except Exception as e:
            print(f"[WARN] Document classification failed: {e}", file=sys.stderr)

        # Default: lab_test (most common per D-12)
        return "lab_test"

    def _map_to_concepts(self, extracted_fields: list[dict]) -> list[dict]:
        """Map extracted item names to health concepts via ConceptResolver.

        Adds concept_id and record_type to each field.
        """
        mapped: list[dict] = []

        for field in extracted_fields:
            item_name = field.get("item_name", "")
            concept_id = None
            record_type = "lab_result"

            # Try Chinese name lookup first
            if item_name in self._CHINESE_CONCEPT_MAP:
                concept_id = self._CHINESE_CONCEPT_MAP[item_name]
            else:
                # Try partial match
                for zh_name, cid in self._CHINESE_CONCEPT_MAP.items():
                    if zh_name in item_name or item_name in zh_name:
                        concept_id = cid
                        break

            # If we found a concept, look up record_type
            if concept_id:
                try:
                    _, defn = self._concept_resolver.resolve_concept(concept_id)
                    record_type = defn.get("canonical_type", "lab_result")
                except Exception:
                    pass

            # Use record_type from field if already set (e.g., from TextExtractor)
            if field.get("record_type") and field["record_type"] != "lab_result":
                record_type = field["record_type"]

            mapped_field = dict(field)
            mapped_field["concept_id"] = concept_id or ""
            mapped_field["record_type"] = record_type
            mapped.append(mapped_field)

        return mapped

    def _archive_original(self, file_path: str, person_id: str | None = None) -> str:
        """Copy original document to memory/health/files/ with metadata.

        Per OCR-05: archive original for reference.
        Returns archived path.
        """
        writer = HealthMemoryWriter(person_id=person_id)
        files_dir = writer.files_dir
        files_dir.mkdir(parents=True, exist_ok=True)

        # Generate archived filename: YYYY-MM-DD_{doc_hash}.{ext}
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_hash = self._file_hash(file_path)[:8]
        ext = os.path.splitext(file_path)[1]
        archived_name = f"{date_str}_ocr_{file_hash}{ext}"
        archived_path = files_dir / archived_name

        # Copy original file
        shutil.copy2(file_path, archived_path)

        # Write metadata JSON alongside
        meta_path = files_dir / f"{archived_name}.meta.json"
        meta = {
            "original_path": file_path,
            "archived_at": datetime.now().isoformat(timespec="seconds"),
            "file_hash": file_hash,
            "person_id": person_id,
            "source": "ocr_pipeline",
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return str(archived_path)

    def _file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _get_table_extractor(self):
        """Lazy-initialize table extractor."""
        if self._table_extractor is None:
            from ocr_table_extractor import TableExtractor
            self._table_extractor = TableExtractor()
        return self._table_extractor

    def _get_text_extractor(self):
        """Lazy-initialize text extractor."""
        if self._text_extractor is None:
            from ocr_text_extractor import TextExtractor
            self._text_extractor = TextExtractor()
        return self._text_extractor


def main():
    """CLI entry point for OCR pipeline."""
    parser = argparse.ArgumentParser(
        description="OCR extraction pipeline for Chinese medical documents."
    )
    parser.add_argument("input", help="Path to image or PDF file")
    parser.add_argument(
        "--format", choices=["json", "markdown"], default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--person-id", default=None,
        help="Person ID for multi-person support"
    )
    args = parser.parse_args()

    try:
        pipeline = OCRPipeline()
        result = pipeline.process(args.input, person_id=args.person_id)

        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_markdown(result)

    except ImportError as e:
        print(json.dumps({
            "success": False,
            "error": f"Missing dependency: {e}. Run: pip install paddleocr",
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


def _print_markdown(result: dict):
    """Print extraction result in human-readable markdown."""
    print(f"# OCR Extraction Result\n")
    print(f"**Document type:** {result['document_type']}")
    print(f"**Source:** {result['source_file']}")
    print(f"**Archived:** {result['archived_path']}")
    print(f"**Confidence:** {result['confidence']:.0%}\n")

    fields = result.get("extracted_fields", [])
    if fields:
        print("## Extracted Fields\n")
        print("| Item | Value | Unit | Reference | Concept | Confidence |")
        print("|------|-------|------|-----------|---------|------------|")
        for f in fields:
            conf_str = f"{f.get('confidence', 0):.0%}"
            flag = " *" if f.get("needs_manual_review") else ""
            print(
                f"| {f.get('item_name', '')} "
                f"| {f.get('value', '')} "
                f"| {f.get('unit', '')} "
                f"| {f.get('reference_range', '')} "
                f"| {f.get('concept_id', '')} "
                f"| {conf_str}{flag} |"
            )
    else:
        print("No structured fields extracted.\n")

    if result.get("raw_text"):
        print(f"\n## Raw OCR Text\n")
        print(f"```\n{result['raw_text'][:2000]}\n```")


if __name__ == "__main__":
    main()
