#!/usr/bin/env python3
"""
redact_ocr.py — OCR-based PII redaction for Chinese medical documents.

Uses PaddleOCR for text detection + PaddleNLP UIE NER for PII classification.
Optionally uses LLM as a complementary PII identifier for higher recall.
Supports barcode/QR code detection and redaction.

Supports: JPG/PNG/BMP/WEBP/HEIC/HEIF images and scanned PDFs.

Usage:
    python3 redact_ocr.py INPUT [--output OUTPUT] [--debug] [--confidence 0.5] [--no-ner] [--no-llm]
    python3 redact_ocr.py --check-runtime

Output JSON to stdout:
    {"success": true, "output": "...", "pii_detected": N, "regions": [...]}

Debug mode (--debug):
    Saves annotated image with green boxes (kept) and red boxes (redacted).
"""

import argparse
import json
import os
import re
import sys
import tempfile
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


# ---------------------------------------------------------------------------
# Barcode / QR code detection
# ---------------------------------------------------------------------------

def detect_barcodes(image_path: str) -> list:
    """Detect barcodes and QR codes, return list of [x1, y1, x2, y2] rects."""
    try:
        import cv2
    except ImportError:
        return []

    img = cv2.imread(image_path)
    if img is None:
        return []

    bboxes = []

    # Method 1: pyzbar (1D + 2D barcodes)
    try:
        from pyzbar.pyzbar import decode
        for bc in decode(img):
            x, y, w, h = bc.rect
            bboxes.append([x, y, x + w, y + h])
    except ImportError:
        pass

    # Method 2: OpenCV QR detector (fallback, QR only)
    if not bboxes:
        detector = cv2.QRCodeDetector()
        retval, points = detector.detect(img)
        if retval and points is not None:
            for pts in points:
                x1 = int(min(p[0] for p in pts))
                y1 = int(min(p[1] for p in pts))
                x2 = int(max(p[0] for p in pts))
                y2 = int(max(p[1] for p in pts))
                bboxes.append([x1, y1, x2, y2])

    # Method 3: OpenCV barcode detector (1D barcodes)
    if not bboxes:
        try:
            bd = cv2.barcode.BarcodeDetector()
            result = bd.detectAndDecode(img)
            if len(result) == 4:
                ok, _decoded, _det_type, points = result
            elif len(result) == 3:
                ok, _decoded, points = result
            else:
                ok, points = False, None
            if ok and points is not None:
                for pts in points:
                    x1 = int(min(p[0] for p in pts))
                    y1 = int(min(p[1] for p in pts))
                    x2 = int(max(p[0] for p in pts))
                    y2 = int(max(p[1] for p in pts))
                    bboxes.append([x1, y1, x2, y2])
        except (AttributeError, Exception):
            pass

    return bboxes


# ---------------------------------------------------------------------------
# LLM-based PII complement (higher recall for items regex/NER miss)
# ---------------------------------------------------------------------------

_LLM_SYSTEM_PROMPT = """你是一个医疗报告隐私信息识别专家。你的任务是从OCR识别出的文本列表中，找出所有包含隐私信息的文本。

## 隐私信息类型
1. **患者姓名** - 包含中文姓名、以及"姓名：XXX"格式
2. **各类编号** - 病历号、住院号、门诊号、报告单号、标本编号、超声号、检查号、条码号、检验号等
3. **证件号码** - 身份证号、护照号等
4. **联系方式** - 手机号、电话号码
5. **地址信息** - 家庭住址、工作单位地址、籍贯、出生地等（但不包含医院名称/地址）
6. **日期时间** - 报告时间、检查时间、采样时间、入院/出院日期等与患者就诊相关的时间（但不包含参考值中的时间）
7. **年龄/出生日期** - 具体年龄（如"43岁"）、出生日期
8. **性别年龄组合** - 如"男 65岁"、"女43岁"
9. **医护人员姓名** - 检查医师、报告医师、审核医师、录入员、主治医师、申请医生、检验者、审核者等的姓名
10. **科室/床号/病区** - 具体科室名称、床号、病区信息
11. **处方号/医嘱号** - 处方编号等
12. **体检编号** - 体检报告中的编号
13. **手术相关人员** - 术者、助手、麻醉师的姓名
14. **病理号** - 病理报告编号

## 不应标记为隐私的内容
- 医院名称（如"西北妇女儿童医院"）
- 医学诊断内容、检查所见、检查结论
- 化验项目名称和结果数值（如"白细胞 5.3"、"血红蛋白 120"）
- 参考值、单位
- 报告标题（如"检验报告单"、"超声检查报告单"）
- 药品名称、剂量
- 检查仪器、设备名称
- 表单选项文本（如"1.男2.女"、"1.未婚2.已婚"）
- 医学术语和描述性文字

## 输出格式
你必须只输出一个 JSON 数组，包含所有隐私文本的序号（idx字段值）。
不要输出分析过程、表格、解释或任何其他文字，只输出 JSON 数组。
示例: [0, 3, 5, 12]
如果没有隐私信息，返回: []"""


def _llm_detect_pii(ocr_items: list) -> set:
    """
    Call local LLM to identify PII indices from OCR text list.
    Returns set of indices flagged as PII, or empty set if LLM unavailable.
    """
    if not ocr_items:
        return set()

    api_base = os.environ.get("LLM_API_BASE", "http://localhost:8000/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")

    if not model:
        return set()

    try:
        import requests
    except ImportError:
        return set()

    text_list = [f'[{i}] "{item["text"]}"' for i, item in enumerate(ocr_items)]
    user_prompt = f"以下是从一份医疗报告中OCR识别出的文本列表，请识别其中的隐私信息：\n\n" + "\n".join(text_list)

    try:
        session = requests.Session()
        session.trust_env = False  # skip system proxies for local models
        resp = session.post(
            f"{api_base}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 2048,
            },
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip <think> tags
        clean = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        # Extract JSON array
        all_arrays = re.findall(r"\[[\d\s,]+\]", clean)
        if all_arrays:
            best = max(all_arrays, key=lambda x: x.count(","))
            indices = json.loads(best)
        elif re.search(r"\[\s*\]", clean):
            indices = []
        else:
            nums = re.findall(r"\b(\d+)\b", clean)
            max_idx = len(ocr_items) - 1
            indices = [int(n) for n in nums if int(n) <= max_idx]

        return set(idx for idx in indices if 0 <= idx < len(ocr_items))

    except Exception:
        return set()


# ---------------------------------------------------------------------------
# HEIC / HEIF format conversion
# ---------------------------------------------------------------------------

def _ensure_processable(image_path: str) -> tuple:
    """Convert HEIC/HEIF to temporary JPG. Returns (processable_path, is_temp)."""
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


# ---------------------------------------------------------------------------
# PII detection — regex-first, NER only for names
# ---------------------------------------------------------------------------


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


def runtime_check() -> dict:
    issues = []
    checks = {
        "paddleocr_import": False,
        "paddleocr_engine": False,
        "paddlenlp_import": False,
        "paddlenlp_engine": False,
    }

    try:
        from paddleocr import PaddleOCR

        checks["paddleocr_import"] = True
        try:
            PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                lang="ch",
                show_log=False,
            )
            checks["paddleocr_engine"] = True
        except Exception as exc:  # pragma: no cover - depends on local runtime
            issues.append(f"PaddleOCR runtime not ready: {exc}")
    except Exception as exc:  # pragma: no cover - depends on local runtime
        issues.append(f"Missing PaddleOCR dependency: {exc}")

    try:
        from paddlenlp import Taskflow

        checks["paddlenlp_import"] = True
        try:
            Taskflow(
                "information_extraction",
                schema=["人名"],
                model="uie-micro",
            )
            checks["paddlenlp_engine"] = True
        except Exception as exc:  # pragma: no cover - depends on local runtime
            issues.append(f"PaddleNLP runtime not ready: {exc}")
    except Exception as exc:  # pragma: no cover - depends on local runtime
        issues.append(f"Missing PaddleNLP dependency: {exc}")

    return {
        "success": all(checks.values()),
        "checks": checks,
        "issues": issues,
    }


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
    no_llm: bool = False,
) -> dict:
    """
    Main pipeline: OCR → classify (regex+NER+LLM) → barcode detect → redact PII.

    Returns result dict for JSON output.
    """
    from PIL import Image, ImageDraw

    # 0) Handle HEIC/HEIF conversion
    proc_path, is_tmp = _ensure_processable(input_path)

    # 1) Run OCR
    ocr_lines = run_ocr(proc_path, confidence_threshold)

    # 1b) Detect barcodes/QR codes
    barcode_bboxes = detect_barcodes(proc_path)

    if not ocr_lines and not barcode_bboxes:
        # No text or barcodes detected — just copy the file as-is
        img = Image.open(proc_path)
        img.save(output_path)
        if is_tmp:
            try: os.unlink(proc_path)
            except OSError: pass
        return {
            "success": True,
            "output": output_path,
            "pii_detected": 0,
            "total_lines": 0,
            "barcodes_detected": 0,
            "regions": [],
            "note": "No text or barcodes detected",
        }

    # Use original image (doc preprocessor is disabled so OCR coords match)
    img = Image.open(proc_path).convert("RGB")
    width, height = img.size

    # 2) Merge split labels (e.g. "姓" + "名：王某某" → "姓名：王某某")
    ocr_lines = _merge_split_labels(ocr_lines)

    # 3) Classify — regex + NER batch
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

    # 3.6) LLM complement — catch PII that regex/NER missed
    llm_flagged = set()
    if not no_llm and lines_classified:
        keep_items = [
            {"idx": i, "text": item["text"]}
            for i, item in enumerate(lines_classified)
            if item["classification"] == "keep" and item["text"].strip()
        ]
        if keep_items:
            llm_flagged = _llm_detect_pii(keep_items)
            # Map back: llm_detect_pii returns indices into keep_items
            keep_to_orig = {ki: keep_items[ki]["idx"] for ki in range(len(keep_items))}
            for ki in llm_flagged:
                orig_idx = keep_to_orig.get(ki)
                if orig_idx is not None and lines_classified[orig_idx]["classification"] == "keep":
                    lines_classified[orig_idx]["classification"] = "pii"
                    lines_classified[orig_idx]["pii_type"] = "llm_detected"

    # 4) Multi-line PII propagation
    lines_classified = propagate_pii_to_neighbors(lines_classified)

    # 5) Build redaction regions (PII text lines)
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

    # 5b) Add barcode regions
    barcode_regions = []
    pad = 8
    for bb in barcode_bboxes:
        x1 = max(0, bb[0] - pad)
        y1 = max(0, bb[1] - pad)
        x2 = min(width, bb[2] + pad)
        y2 = min(height, bb[3] + pad)
        quad = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        barcode_regions.append({
            "pii_type": "barcode",
            "text_preview": "[barcode/QR]",
            "quad_px": quad,
        })

    all_regions = pii_regions + barcode_regions

    # 6) Apply redaction
    draw = ImageDraw.Draw(img)
    for region in all_regions:
        q = region["quad_px"]
        draw.polygon([tuple(p) for p in q], fill="black")

    img.save(output_path)

    if is_tmp:
        try: os.unlink(proc_path)
        except OSError: pass

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

        # Draw barcode regions in blue
        for br in barcode_regions:
            q = br["quad_px"]
            for i in range(4):
                debug_draw.line([tuple(q[i]), tuple(q[(i + 1) % 4])], fill="blue", width=2)

        if not debug_path:
            p = Path(output_path)
            debug_path = str(p.parent / f"{p.stem}_debug{p.suffix}")
        debug_img.save(debug_path)

    # 8) Build result
    result = {
        "success": True,
        "output": output_path,
        "pii_detected": len(pii_regions),
        "barcodes_detected": len(barcode_regions),
        "total_lines": len(lines_classified),
        "kept_lines": sum(1 for x in lines_classified if x["classification"] == "keep"),
        "llm_complement_hits": len(llm_flagged),
        "regions": all_regions,
    }
    if debug and debug_path:
        result["debug_image"] = debug_path

    return result


# ---------------------------------------------------------------------------
# PDF processing — render pages → redact each → reassemble
# ---------------------------------------------------------------------------

def redact_pdf(
    input_path: str,
    output_path: str,
    dpi: int = 200,
    confidence_threshold: float = 0.5,
    debug: bool = False,
    no_ner: bool = False,
    no_llm: bool = False,
) -> dict:
    """
    Process a scanned PDF: render each page to image, redact PII, reassemble PDF.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {"success": False, "error": "PyMuPDF (fitz) required for PDF processing. Run: pip install PyMuPDF"}

    from PIL import Image

    doc = fitz.open(input_path)
    if len(doc) == 0:
        doc.close()
        return {"success": False, "error": "PDF has no pages"}

    tmp_files = []
    page_results = []
    total_pii = 0
    total_barcodes = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Render page to temp image
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, prefix=f"pdf_p{page_num+1}_")
        tmp_path = tmp.name
        tmp.close()
        tmp_files.append(tmp_path)

        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img.save(tmp_path, "JPEG", quality=95)

        # Redact the page image
        redacted_path = tmp_path.replace(".jpg", "_redacted.jpg")
        tmp_files.append(redacted_path)

        page_result = redact_image_ocr(
            input_path=tmp_path,
            output_path=redacted_path,
            confidence_threshold=confidence_threshold,
            debug=debug,
            no_ner=no_ner,
            no_llm=no_llm,
        )
        page_results.append(page_result)
        total_pii += page_result.get("pii_detected", 0)
        total_barcodes += page_result.get("barcodes_detected", 0)

    doc.close()

    # Reassemble into PDF
    out_doc = fitz.open()
    for tmp_path in tmp_files:
        if not tmp_path.endswith("_redacted.jpg"):
            continue
        if not os.path.exists(tmp_path):
            continue
        img_doc = fitz.open(tmp_path)
        pdfbytes = img_doc.convert_to_pdf()
        img_doc.close()
        imgpdf = fitz.open("pdf", pdfbytes)
        out_doc.insert_pdf(imgpdf)
        imgpdf.close()
    out_doc.save(output_path)
    out_doc.close()

    # Cleanup temp files
    for tmp_path in tmp_files:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return {
        "success": True,
        "output": output_path,
        "pages": len(page_results),
        "pii_detected": total_pii,
        "barcodes_detected": total_barcodes,
        "page_results": page_results,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="OCR-based PII redaction for Chinese medical documents."
    )
    parser.add_argument("input", nargs="?", help="Path to input image or scanned PDF")
    parser.add_argument("--output", help="Output file path (default: [name]_redacted.[ext])")
    parser.add_argument("--debug", action="store_true",
                        help="Save annotated debug image showing PII regions (red boxes)")
    parser.add_argument("--confidence", type=float, default=0.5,
                        help="OCR confidence threshold (default: 0.5)")
    parser.add_argument("--no-ner", action="store_true",
                        help="Skip NER classification (debug/fallback)")
    parser.add_argument("--no-llm", action="store_true",
                        help="Skip LLM complement PII detection")
    parser.add_argument("--dpi", type=int, default=200,
                        help="DPI for PDF page rendering (default: 200)")
    parser.add_argument(
        "--check-runtime",
        action="store_true",
        help="Check whether PaddleOCR and PaddleNLP are ready for mandatory redaction.",
    )
    args = parser.parse_args()

    if args.check_runtime:
        result = runtime_check()
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if result.get("success") else 2)

    if not args.input:
        print(json.dumps({"success": False, "error": "input is required unless --check-runtime is used"}))
        sys.exit(1)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(json.dumps({"success": False, "error": f"Input file not found: {input_path}"}))
        sys.exit(1)

    suffix = input_path.suffix.lower()
    image_types = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".heif"}
    pdf_types = {".pdf"}
    supported = image_types | pdf_types

    if suffix not in supported:
        print(json.dumps({
            "success": False,
            "error": f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(supported))}",
        }))
        sys.exit(1)

    if args.output:
        output_path = str(Path(args.output).expanduser().resolve())
    else:
        if suffix in pdf_types:
            output_path = str(input_path.parent / f"{input_path.stem}_redacted.pdf")
        elif suffix in (".heic", ".heif"):
            output_path = str(input_path.parent / f"{input_path.stem}_redacted.jpg")
        else:
            output_path = str(input_path.parent / f"{input_path.stem}_redacted{input_path.suffix}")

    try:
        if suffix in pdf_types:
            result = redact_pdf(
                input_path=str(input_path),
                output_path=output_path,
                dpi=args.dpi,
                confidence_threshold=args.confidence,
                debug=args.debug,
                no_ner=args.no_ner,
                no_llm=args.no_llm,
            )
        else:
            result = redact_image_ocr(
                input_path=str(input_path),
                output_path=output_path,
                confidence_threshold=args.confidence,
                debug=args.debug,
                no_ner=args.no_ner,
                no_llm=args.no_llm,
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
