#!/usr/bin/env python3
"""
redact_ocr.py — OCR-based PII redaction for Chinese medical documents.

Uses PaddleOCR for text detection + PaddleNLP UIE NER for PII classification.
Only PII fields are redacted; everything else is left untouched.

Usage:
    python3 redact_ocr.py INPUT [--output OUTPUT] [--debug] [--confidence 0.5] [--no-ner]

Output JSON to stdout:
    {"success": true, "output": "...", "pii_detected": N, "regions": [...]}

Debug mode (--debug):
    Saves annotated image with green boxes (kept) and red boxes (redacted).
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# PII detection — regex-first, NER only for names
# ---------------------------------------------------------------------------

# Labels that precede PII values
_PII_LABEL_PATTERNS = [
    (re.compile(r"(姓?\s*名|患\s*者|病\s*人)\s*[:：]"), "patient_name"),
    (re.compile(r"(身份证|身份证号|证件号码?|ID)\s*[:：]"), "id_number"),
    (re.compile(r"(电\s*话|联系电话|手\s*机|联系方式|Tel|TEL)\s*[:：]"), "phone"),
    (re.compile(r"(地\s*址|住\s*址|通讯地址|联系地址)\s*[:：]"), "address"),
    (re.compile(r"(住院号|住院病历号|病历号|门诊号|就诊号|就诊卡号|病案号|ID号)\s*[:：]"), "admission_id"),
    (re.compile(r"(床\s*号|病\s*床|床\s*位)\s*[:：]"), "bed_number"),
    (re.compile(r"(检验者|检验医师|检验人员|检测者)\s*[:：]"), "examiner"),
    (re.compile(r"(审核者|审核医师|审核人员|审核人)\s*[:：]"), "reviewer"),
    (re.compile(r"(报告医师|报告者|报告人|报告医生)\s*[:：]"), "reporter"),
    (re.compile(r"(核对者|核对人|复核者|复核人)\s*[:：]"), "verifier"),
    (re.compile(r"(送检医[师生]|开单医[师生]|临床医[师生]|主治医[师生]|申请医[师生])\s*[:：]"), "ordering_doctor"),
]

# Standalone PII patterns (no label needed)
_ID_CARD_RE = re.compile(r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b")
_PHONE_RE = re.compile(r"\b1[3-9]\d{9}\b")
_LANDLINE_RE = re.compile(r"\b0\d{2,3}[-\s]?\d{7,8}\b")


def _classify_by_patterns(text: str) -> tuple[str | None, float | None]:
    """Label patterns + standalone patterns. Returns (pii_type, label_ratio) or (None, None)."""
    text_stripped = text.strip()
    if not text_stripped:
        return (None, None)

    # 1) Label patterns — pick earliest match
    best_match = None
    best_pii_type = None
    for pattern, pii_type in _PII_LABEL_PATTERNS:
        m = pattern.search(text_stripped)
        if m and (best_match is None or m.start() < best_match.start()):
            best_match = m
            best_pii_type = pii_type
    if best_match:
        label_ratio = best_match.end() / len(text_stripped) if len(text_stripped) > 0 else 0.5
        return (best_pii_type, label_ratio)

    # 2) Standalone patterns
    if _ID_CARD_RE.search(text_stripped):
        return ("id_number", None)
    if _PHONE_RE.search(text_stripped):
        return ("phone", None)
    if _LANDLINE_RE.search(text_stripped):
        return ("phone", None)

    return (None, None)


_ner_engine = None
_ner_available = None  # None = not checked, True/False = result


def _init_ner_engine():
    global _ner_engine, _ner_available
    if _ner_available is False:
        return None
    if _ner_engine is not None:
        return _ner_engine
    try:
        from paddlenlp import Taskflow
        _ner_engine = Taskflow(
            "information_extraction",
            schema=["人名"],
            model="uie-micro",
        )
        _ner_available = True
        return _ner_engine
    except Exception:
        _ner_available = False
        return None

# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------


def classify_line(text: str) -> tuple[str, str | None, float | None]:
    """
    Classify an OCR text line — regex first, NER fallback for names only.

    Returns:
        (classification, pii_type, label_ratio)
        classification: "pii" or "keep"
        pii_type: e.g. "patient_name", "phone", None
        label_ratio: fraction of text that is the label (for label-value separation),
                     None if not applicable
    """
    text_stripped = text.strip()
    if not text_stripped or len(text_stripped) < 2:
        return ("keep", None, None)

    # Regex first
    pii_type, label_ratio = _classify_by_patterns(text_stripped)
    if pii_type:
        return ("pii", pii_type, label_ratio)

    # NER fallback (names only)
    engine = _init_ner_engine()
    if engine is None:
        return ("keep", None, None)
    try:
        results = engine(text_stripped)
    except Exception:
        return ("keep", None, None)
    if not results:
        return ("keep", None, None)
    result = results[0] if isinstance(results, list) else results
    for ent in result.get("人名", []):
        if ent.get("probability", 0) >= 0.75:
            start = ent["start"]
            total = len(text_stripped)
            lr = start / total if start > 0 and total > 0 else None
            return ("pii", "patient_name", lr)
    return ("keep", None, None)


def _run_ner_batch(lines_classified: list):
    """Regex-first, then NER for names only."""
    # Phase 1: regex — instant
    ner_candidates = []
    for i, item in enumerate(lines_classified):
        pii_type, label_ratio = _classify_by_patterns(item["text"])
        if pii_type:
            item["classification"] = "pii"
            item["pii_type"] = pii_type
            item["label_ratio"] = label_ratio
        else:
            ner_candidates.append(i)

    # Phase 2: NER for remaining lines — only detect names
    engine = _init_ner_engine()
    if engine is None or not ner_candidates:
        return
    texts = [(i, lines_classified[i]["text"].strip()) for i in ner_candidates]
    valid = [(i, t) for i, t in texts if len(t) >= 2]
    if not valid:
        return
    try:
        results = engine([t for _, t in valid])
    except Exception:
        return
    for (idx, txt), result in zip(valid, results):
        if not result:
            continue
        for ent in result.get("人名", []):
            if ent.get("probability", 0) >= 0.75:
                start = ent["start"]
                total = len(txt)
                lines_classified[idx]["classification"] = "pii"
                lines_classified[idx]["pii_type"] = "patient_name"
                lines_classified[idx]["label_ratio"] = start / total if start > 0 and total > 0 else None
                break


# ---------------------------------------------------------------------------
# OCR merge — fix split labels like "姓" + "名：王某某"
# ---------------------------------------------------------------------------


def _merge_split_labels(lines):
    """
    Merge single-character OCR fragments with the nearest right neighbor
    on the same row when the horizontal gap is smaller than the text line
    height (≈ one character width).  Handles "姓"+"名：…", "床"+"号：…", etc.
    """
    if len(lines) < 2:
        return lines

    def _center_y(bbox):
        return sum(p[1] for p in bbox) / 4

    def _right_edge(bbox):
        return max(p[0] for p in bbox)

    def _left_edge(bbox):
        return min(p[0] for p in bbox)

    def _line_height(bbox):
        ys = [p[1] for p in bbox]
        return max(ys) - min(ys)

    consumed = set()
    merged = []

    for i, line in enumerate(lines):
        if i in consumed:
            continue
        text = line["text"]
        # Only try to merge single-character fragments
        if len(text.strip()) != 1:
            merged.append(line)
            continue

        bbox_i = line["bbox"]
        cy_i = _center_y(bbox_i)
        right_i = _right_edge(bbox_i)
        lh_i = _line_height(bbox_i)

        # Find the nearest right neighbor on the same row
        best_j = None
        best_gap = float("inf")
        for j, other in enumerate(lines):
            if j == i or j in consumed:
                continue
            bbox_j = other["bbox"]
            cy_j = _center_y(bbox_j)
            left_j = _left_edge(bbox_j)
            lh_j = _line_height(bbox_j)
            avg_lh = (lh_i + lh_j) / 2

            # Same row: center-Y difference < half the average line height
            if abs(cy_j - cy_i) > avg_lh * 0.5:
                continue
            # Must be to the right
            gap = left_j - right_i
            if gap < 0:
                continue
            # Gap must be less than one line height (≈ one character width)
            if gap < avg_lh * 2 and gap < best_gap:
                best_gap = gap
                best_j = j

        if best_j is not None:
            other = lines[best_j]
            # Merge: concatenate text, combine bounding boxes
            new_text = text + other["text"]
            # Build a spanning quad: leftmost of i, rightmost of j
            bi = bbox_i
            bj = other["bbox"]
            new_bbox = [
                bi[0],  # top-left from first
                bj[1],  # top-right from second
                bj[2],  # bottom-right from second
                bi[3],  # bottom-left from first
            ]
            new_conf = min(line["confidence"], other["confidence"])
            consumed.add(best_j)
            merged.append({
                "text": new_text,
                "bbox": new_bbox,
                "confidence": new_conf,
            })
        else:
            merged.append(line)

    return merged


# ---------------------------------------------------------------------------
# OCR + Redaction pipeline
# ---------------------------------------------------------------------------


def run_ocr(image_path: str, confidence_threshold: float = 0.5):
    """
    Run PaddleOCR on an image and return text lines with bounding boxes.

    Returns:
        lines: [{"text": str, "bbox": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], "confidence": float}, ...]
    """
    import os
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        use_textline_orientation=True,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        lang="ch",
    )
    result = list(ocr.predict(image_path))

    lines = []
    if not result:
        return lines

    for page in result:
        texts = page["rec_texts"]
        scores = page["rec_scores"]
        polys = page["dt_polys"]
        for text, conf, poly in zip(texts, scores, polys):
            if conf >= confidence_threshold:
                bbox = poly.tolist()  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                lines.append({
                    "text": text,
                    "bbox": bbox,
                    "confidence": conf,
                })
    return lines


def bbox_to_rect(bbox):
    """Convert PaddleOCR quad bbox to (x1, y1, x2, y2) rectangle."""
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]
    return (min(xs), min(ys), max(xs), max(ys))


def split_label_value_quad(bbox, label_ratio):
    """
    Split a quadrilateral bbox into label part and value part along text direction.

    bbox: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
          PaddleOCR convention: top-left, top-right, bottom-right, bottom-left
    label_ratio: fraction along text direction that is the label

    Returns: value_quad — list of 4 points for the value part only
    """
    tl, tr, br, bl = bbox[0], bbox[1], bbox[2], bbox[3]
    r = label_ratio
    split_top = [tl[0] + (tr[0] - tl[0]) * r, tl[1] + (tr[1] - tl[1]) * r]
    split_bot = [bl[0] + (br[0] - bl[0]) * r, bl[1] + (br[1] - bl[1]) * r]
    return [split_top, list(tr), list(br), split_bot]


def pad_quad(quad, pad, img_width, img_height):
    """Expand a quad outward from its centroid by pad pixels."""
    cx = sum(p[0] for p in quad) / 4
    cy = sum(p[1] for p in quad) / 4
    result = []
    for p in quad:
        dx = p[0] - cx
        dy = p[1] - cy
        length = (dx**2 + dy**2) ** 0.5 or 1
        result.append([
            max(0, min(img_width, p[0] + dx / length * pad)),
            max(0, min(img_height, p[1] + dy / length * pad)),
        ])
    return result


def _propagate_label_to_value(lines_classified):
    """When a PII box is label-only (label_ratio >= 0.85), propagate to right-adjacent boxes on same row."""
    if not lines_classified:
        return

    def _cy(bbox):
        return sum(p[1] for p in bbox) / 4

    def _lh(bbox):
        ys = [p[1] for p in bbox]
        return max(ys) - min(ys)

    for i, item in enumerate(lines_classified):
        if item["classification"] != "pii":
            continue
        if item["label_ratio"] is None or item["label_ratio"] < 0.85:
            continue

        bbox_i = item["bbox"]
        cy_i = _cy(bbox_i)
        right_i = max(p[0] for p in bbox_i)
        lh_i = _lh(bbox_i)

        candidates = []
        for j, other in enumerate(lines_classified):
            if j == i:
                continue
            bbox_j = other["bbox"]
            cy_j = _cy(bbox_j)
            left_j = min(p[0] for p in bbox_j)
            lh_j = _lh(bbox_j)
            avg_lh = (lh_i + lh_j) / 2

            if abs(cy_j - cy_i) > avg_lh * 0.5:
                continue
            gap = left_j - right_i
            if gap < -avg_lh * 0.5:
                continue
            if gap > avg_lh * 3:
                continue
            candidates.append((gap, j))

        candidates.sort()
        for _, j in candidates:
            other = lines_classified[j]
            if other["classification"] == "pii":
                other["label_ratio"] = None
                break
            other["classification"] = "pii"
            other["pii_type"] = item["pii_type"]
            other["label_ratio"] = None


def propagate_pii_to_neighbors(lines_classified):
    """
    Multi-line PII propagation: if a line is PII (especially address),
    adjacent non-PII lines within proximity are also marked as PII.

    This handles addresses that span multiple OCR lines.
    """
    if not lines_classified:
        return lines_classified

    # Sort by vertical position
    sorted_indices = sorted(
        range(len(lines_classified)),
        key=lambda i: lines_classified[i]["rect"][1]
    )

    # For each PII line of type "address", check neighbors
    for idx_pos, idx in enumerate(sorted_indices):
        item = lines_classified[idx]
        if item["classification"] != "pii" or item["pii_type"] != "address":
            continue

        _, y1, _, y2 = item["rect"]
        line_height = y2 - y1

        # Check next line(s) below (up to 3 lines, within 1.5x line height)
        for next_pos in range(idx_pos + 1, min(idx_pos + 3, len(sorted_indices))):
            next_idx = sorted_indices[next_pos]
            next_item = lines_classified[next_idx]

            if next_item["classification"] == "pii":
                break  # Already PII, stop

            next_y1 = next_item["rect"][1]
            gap = next_y1 - y2

            if gap < line_height * 1.5 and next_item["classification"] == "keep":
                next_item["classification"] = "pii"
                next_item["pii_type"] = "address_cont"
                next_item["label_ratio"] = None
                y2 = next_item["rect"][3]  # Extend for next check
            else:
                break

    return lines_classified


def redact_image_ocr(
    input_path: str,
    output_path: str,
    confidence_threshold: float = 0.5,
    debug: bool = False,
    debug_path: str | None = None,
    no_ner: bool = False,
) -> dict:
    """
    Main pipeline: OCR → classify → redact PII only.

    Returns result dict for JSON output.
    """
    from PIL import Image, ImageDraw

    # 1) Run OCR
    ocr_lines = run_ocr(input_path, confidence_threshold)
    if not ocr_lines:
        # No text detected — just copy the file as-is
        img = Image.open(input_path)
        img.save(output_path)
        return {
            "success": True,
            "output": output_path,
            "pii_detected": 0,
            "total_lines": 0,
            "regions": [],
            "note": "No text detected by OCR",
        }

    # Use original image (doc preprocessor is disabled so OCR coords match)
    img = Image.open(input_path).convert("RGB")
    width, height = img.size

    # 2) Merge split labels (e.g. "姓" + "名：王某某" → "姓名：王某某")
    ocr_lines = _merge_split_labels(ocr_lines)

    # 3) Classify — NER batch
    lines_classified = []
    for line in ocr_lines:
        lines_classified.append({
            "text": line["text"],
            "bbox": line["bbox"],
            "rect": bbox_to_rect(line["bbox"]),
            "confidence": line["confidence"],
            "classification": "keep",
            "pii_type": None,
            "label_ratio": None,
        })
    if not no_ner:
        _run_ner_batch(lines_classified)

    # 3.5) Label-only → value propagation (横向)
    _propagate_label_to_value(lines_classified)

    # 4) Multi-line PII propagation
    lines_classified = propagate_pii_to_neighbors(lines_classified)

    # 5) Build redaction regions (only PII lines)
    pii_regions = []
    for item in lines_classified:
        if item["classification"] != "pii":
            continue

        bbox = item["bbox"]
        if item["label_ratio"] is not None and item["label_ratio"] < 0.9:
            redact_quad = split_label_value_quad(bbox, item["label_ratio"])
        else:
            redact_quad = [list(p) for p in bbox]

        padded = pad_quad(redact_quad, 2, width, height)

        pii_regions.append({
            "pii_type": item["pii_type"],
            "text_preview": item["text"][:6] + "..." if len(item["text"]) > 6 else item["text"],
            "quad_px": [[int(v) for v in p] for p in padded],
        })

    # 6) Apply redaction
    draw = ImageDraw.Draw(img)
    for region in pii_regions:
        q = region["quad_px"]
        draw.polygon([tuple(p) for p in q], fill="black")

    img.save(output_path)

    # 7) Debug image (optional)
    if debug:
        debug_img = Image.open(input_path).convert("RGB")
        debug_draw = ImageDraw.Draw(debug_img)

        for item in lines_classified:
            if item["classification"] != "pii":
                continue
            quad_points = [tuple(p) for p in item["bbox"]]

            for i in range(4):
                debug_draw.line(
                    [quad_points[i], quad_points[(i + 1) % 4]],
                    fill="red", width=2
                )

            label_text = item["pii_type"] or "pii"
            rect = item["rect"]
            try:
                debug_draw.text((rect[0], rect[1] - 12), label_text, fill="red")
            except Exception:
                pass

        if not debug_path:
            p = Path(output_path)
            debug_path = str(p.parent / f"{p.stem}_debug{p.suffix}")
        debug_img.save(debug_path)

    # 8) Build result
    result = {
        "success": True,
        "output": output_path,
        "pii_detected": len(pii_regions),
        "total_lines": len(lines_classified),
        "kept_lines": sum(1 for x in lines_classified if x["classification"] == "keep"),
        "regions": pii_regions,
    }
    if debug and debug_path:
        result["debug_image"] = debug_path

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="OCR-based PII redaction for Chinese medical documents."
    )
    parser.add_argument("input", help="Path to input image file")
    parser.add_argument("--output", help="Output file path (default: [name]_redacted.[ext])")
    parser.add_argument("--debug", action="store_true",
                        help="Save annotated debug image showing PII regions (red boxes)")
    parser.add_argument("--confidence", type=float, default=0.5,
                        help="OCR confidence threshold (default: 0.5)")
    parser.add_argument("--no-ner", action="store_true",
                        help="Skip NER classification; all lines kept (debug/fallback)")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(json.dumps({"success": False, "error": f"Input file not found: {input_path}"}))
        sys.exit(1)

    suffix = input_path.suffix.lower()
    supported = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    if suffix not in supported:
        print(json.dumps({
            "success": False,
            "error": f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(supported))}",
        }))
        sys.exit(1)

    if args.output:
        output_path = str(Path(args.output).expanduser().resolve())
    else:
        output_path = str(input_path.parent / f"{input_path.stem}_redacted{input_path.suffix}")

    try:
        result = redact_image_ocr(
            input_path=str(input_path),
            output_path=output_path,
            confidence_threshold=args.confidence,
            debug=args.debug,
            no_ner=args.no_ner,
        )
        print(json.dumps(result, ensure_ascii=False))
    except ImportError as e:
        missing = str(e)
        print(json.dumps({
            "success": False,
            "error": f"Missing dependency: {missing}. Run: pip install paddlepaddle paddleocr paddlenlp",
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
