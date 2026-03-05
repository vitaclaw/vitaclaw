#!/usr/bin/env python3
"""
redact_ocr.py — OCR-based PII redaction for Chinese medical documents.

Uses PaddleOCR for precise text detection + regex/whitelist classification
to redact only PII while preserving all medical data.

Usage:
    python3 redact_ocr.py INPUT [--output OUTPUT] [--debug] [--confidence 0.5]

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
# Medical data whitelist — lines matching these are NEVER redacted
# ---------------------------------------------------------------------------

# Lab units (case-insensitive matching applied separately)
_LAB_UNITS = [
    "mmol/L", "μmol/L", "umol/L", "nmol/L", "pmol/L",
    "U/L", "IU/L", "mU/L", "kU/L",
    "ng/mL", "ng/dL", "μg/L", "ug/L", "mg/L", "mg/dL", "g/L", "g/dL",
    "pg/mL", "μg/dL",
    "×10^9/L", "×10^12/L", "x10^9/L", "x10^12/L",
    "10\\^9/L", "10\\^12/L", "10⁹/L", "10¹²/L",
    "10\\*9/L", "10\\*12/L",
    "cells/μL", "cells/uL",
    "mL/min", "mm/h", "mm/hr",
    "fL", "pg", "g/L", "%",
    "s", "sec", "ratio",
    "copies/mL", "IU/mL",
    "mIU/mL", "uIU/mL", "μIU/mL",
    "kPa", "mmHg", "cm", "mm",
    "MEq/L", "mEq/L", "mOsm/kg",
]

# Lab test names / medical terms — Chinese
_MEDICAL_TERMS_ZH = [
    # Hematology
    "白细胞", "红细胞", "血红蛋白", "血小板", "中性粒细胞", "淋巴细胞",
    "单核细胞", "嗜酸性粒细胞", "嗜碱性粒细胞", "红细胞压积", "红细胞分布宽度",
    "平均红细胞体积", "平均血红蛋白含量", "平均血红蛋白浓度",
    "网织红细胞", "血沉", "凝血酶原时间", "活化部分凝血活酶时间",
    "纤维蛋白原", "D-二聚体", "国际标准化比值",
    # Liver function
    "总蛋白", "白蛋白", "球蛋白", "总胆红素", "直接胆红素", "间接胆红素",
    "谷丙转氨酶", "谷草转氨酶", "碱性磷酸酶", "谷氨酰转肽酶",
    "乳酸脱氢酶", "胆碱酯酶", "前白蛋白", "转铁蛋白",
    # Kidney function
    "肌酐", "尿素氮", "尿素", "尿酸", "胱抑素C", "肾小球滤过率",
    "β2微球蛋白",
    # Electrolytes / metabolic
    "钾", "钠", "氯", "钙", "磷", "镁", "铁", "锌", "铜",
    "血糖", "空腹血糖", "餐后血糖", "糖化血红蛋白",
    "甘油三酯", "总胆固醇", "高密度脂蛋白", "低密度脂蛋白",
    "载脂蛋白", "脂蛋白",
    "同型半胱氨酸", "C反应蛋白", "超敏C反应蛋白", "降钙素原",
    # Tumor markers
    "甲胎蛋白", "癌胚抗原", "糖类抗原", "铁蛋白",
    "前列腺特异性抗原", "游离前列腺特异性抗原",
    "神经元特异性烯醇化酶", "鳞状细胞癌抗原", "细胞角蛋白",
    "人绒毛膜促性腺激素", "乳酸脱氢酶",
    # Thyroid
    "促甲状腺激素", "游离三碘甲状腺原氨酸", "游离甲状腺素",
    "甲状腺球蛋白", "甲状腺过氧化物酶抗体",
    # Immune
    "免疫球蛋白", "补体",
    # Urinalysis
    "尿蛋白", "尿糖", "尿潜血", "尿白细胞", "尿比重", "尿酸碱度",
    # Coagulation
    "凝血", "抗凝血酶",
    # Pathology / molecular
    "免疫组化", "基因检测", "突变", "野生型", "阳性", "阴性",
    "病理", "腺癌", "鳞癌", "分化", "浸润", "转移", "淋巴结",
    # Imaging
    "检查所见", "检查结果", "印象", "诊断", "结论", "建议",
    "影像所见", "超声所见", "X线所见",
    # Report structure
    "参考范围", "参考值", "检验项目", "检测项目", "项目名称",
    "结果", "单位", "提示", "正常", "偏高", "偏低", "异常",
    "标本类型", "标本", "样本", "送检", "采集时间", "检测方法",
    # Hospital structure
    "检验报告", "检查报告", "报告单", "化验单",
]

# Lab test abbreviations — English (case-insensitive)
_MEDICAL_TERMS_EN = [
    "WBC", "RBC", "HGB", "HCT", "PLT", "MCV", "MCH", "MCHC", "RDW",
    "MPV", "PCT", "PDW", "NEUT", "LYMPH", "MONO", "EOS", "BASO",
    "ALT", "AST", "ALP", "GGT", "TBIL", "DBIL", "IBIL", "TP", "ALB", "GLB",
    "BUN", "CRE", "CREA", "UA", "eGFR", "CysC",
    "GLU", "HbA1c", "TG", "TC", "TCHO", "HDL", "LDL", "VLDL",
    "CRP", "hsCRP", "PCT", "ESR", "SAA",
    "PT", "APTT", "INR", "FIB", "TT", "FDP",
    "AFP", "CEA", "CA199", "CA-199", "CA125", "CA-125", "CA153", "CA-153",
    "CA724", "CA-724", "CA242", "CA-242", "CA50", "CA-50",
    "PSA", "fPSA", "tPSA", "NSE", "CYFRA", "SCC", "SCCA",
    "HCG", "β-HCG", "LDH",
    "TSH", "FT3", "FT4", "T3", "T4", "TG", "TPO", "TRAb",
    "IgA", "IgG", "IgM", "IgE",
    "KRAS", "NRAS", "BRAF", "EGFR", "ALK", "ROS1", "HER2", "HER-2",
    "PD-L1", "PDL1", "Ki-67", "Ki67", "TMB", "MSI", "MSS", "dMMR", "pMMR",
    "MLH1", "MSH2", "MSH6", "PMS2", "BRCA", "BRCA1", "BRCA2",
    "PIK3CA", "TP53", "APC", "PTEN", "MET", "RET", "NTRK", "FGFR",
    "NGS", "PCR", "FISH", "IHC", "ICC",
    "DNA", "RNA", "ctDNA", "cfDNA",
    "PET", "CT", "MRI", "PET-CT", "PET/CT",
    "PICC", "CVC", "ECG", "EEG", "EMG",
]

# Report header / table header patterns
_HEADER_PATTERNS = [
    "参考范围", "参考值", "检验项目", "检测项目", "项目名称",
    "结果", "单位", "标本号", "条码号", "样本编号",
    "报告日期", "检测日期", "采样日期", "打印日期", "审核日期",
    "送检日期", "申请日期", "报告时间", "采集时间",
]

# Hospital name patterns
_HOSPITAL_RE = re.compile(
    r"([\u4e00-\u9fff]{2,}(医院|医学中心|卫生院|诊所|检验所|体检中心|医学检验|病理|中心实验室|临床实验室))"
    r"|((人民|中心|第[一二三四五六七八九十]|附属|省|市|区|县|儿童|妇幼|肿瘤|胸科|骨科|口腔|眼科|精神|传染|职业)[\u4e00-\u9fff]*医院)"
)

# Date patterns (these should not be redacted)
_DATE_RE = re.compile(
    r"\d{4}[-/年.]\s*\d{1,2}[-/月.]\s*\d{1,2}[日号]?"
    r"|\d{4}[-/]\d{1,2}[-/]\d{1,2}"
    r"|\d{4}年\d{1,2}月\d{1,2}日"
)

# ---------------------------------------------------------------------------
# PII detection patterns
# ---------------------------------------------------------------------------

# Labels that precede PII values
_PII_LABEL_PATTERNS = [
    (re.compile(r"(姓\s*名|患\s*者|病\s*人)\s*[:：]"), "patient_name"),
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
# Classification logic
# ---------------------------------------------------------------------------


def _build_unit_re():
    """Build a compiled regex that matches any lab unit."""
    escaped = [re.escape(u) for u in _LAB_UNITS]
    return re.compile("|".join(escaped), re.IGNORECASE)


_UNIT_RE = _build_unit_re()

# Build sets for fast lookup
_MEDICAL_ZH_SET = set(_MEDICAL_TERMS_ZH)
_MEDICAL_EN_UPPER = {t.upper() for t in _MEDICAL_TERMS_EN}
_HEADER_SET = set(_HEADER_PATTERNS)


def is_medical_data(text: str) -> bool:
    """Check if text line contains medical/lab data that must NOT be redacted."""
    text_stripped = text.strip()
    if not text_stripped:
        return False

    # Check lab units
    if _UNIT_RE.search(text_stripped):
        return True

    # Check Chinese medical terms
    for term in _MEDICAL_ZH_SET:
        if term in text_stripped:
            return True

    # Check English medical abbreviations (case-insensitive word match)
    words_upper = set(re.findall(r"[A-Za-z][\w-]*", text_stripped))
    words_upper = {w.upper() for w in words_upper}
    if words_upper & _MEDICAL_EN_UPPER:
        return True

    # Check header patterns
    for h in _HEADER_SET:
        if h in text_stripped:
            return True

    # Check hospital name
    if _HOSPITAL_RE.search(text_stripped):
        return True

    # Check date-only lines (report dates)
    if _DATE_RE.search(text_stripped):
        # Only protect if the line is primarily a date (not a PII label with date value)
        # If line also has a PII label, the PII check takes priority
        pass  # Dates alone don't override PII labels; handled in classify_line

    # Numeric-heavy lines (lab values like "5.2" "3.8-10.1")
    # But exclude phone numbers — they are PII, not medical data
    if _PHONE_RE.search(text_stripped) or _LANDLINE_RE.search(text_stripped):
        return False
    digits_and_dots = len(re.findall(r"[\d.↑↓→←▲▼△▽⬆⬇]", text_stripped))
    if len(text_stripped) > 0 and digits_and_dots / len(text_stripped) > 0.4:
        return True

    return False


def classify_line(text: str) -> tuple[str, str | None, float | None]:
    """
    Classify an OCR text line.

    Returns:
        (classification, pii_type, label_ratio)
        classification: "pii", "medical", "unknown"
        pii_type: e.g. "patient_name", "phone", None
        label_ratio: fraction of text that is the label (for label-value separation),
                     None if not applicable
    """
    text_stripped = text.strip()
    if not text_stripped:
        return ("unknown", None, None)

    # 1) Check for PII label patterns — pick the earliest match in the string
    best_match = None
    best_pii_type = None
    for pattern, pii_type in _PII_LABEL_PATTERNS:
        m = pattern.search(text_stripped)
        if m and (best_match is None or m.start() < best_match.start()):
            best_match = m
            best_pii_type = pii_type

    if best_match:
        # If the line ALSO contains medical data after the label, don't redact
        value_part = text_stripped[best_match.end():]
        if value_part.strip() and is_medical_data(value_part):
            return ("medical", None, None)

        # Calculate label ratio for label-value separation
        label_end = best_match.end()
        total_len = len(text_stripped)
        label_ratio = label_end / total_len if total_len > 0 else 0.5
        return ("pii", best_pii_type, label_ratio)

    # 2) Check standalone PII patterns
    if _ID_CARD_RE.search(text_stripped):
        return ("pii", "id_number", None)
    if _PHONE_RE.search(text_stripped):
        return ("pii", "phone", None)
    if _LANDLINE_RE.search(text_stripped):
        return ("pii", "phone", None)

    # 3) Check medical data
    if is_medical_data(text_stripped):
        return ("medical", None, None)

    return ("unknown", None, None)


# ---------------------------------------------------------------------------
# OCR + Redaction pipeline
# ---------------------------------------------------------------------------


def run_ocr(image_path: str, confidence_threshold: float = 0.5):
    """
    Run PaddleOCR on an image and return text lines with bounding boxes.

    Returns list of dicts:
        [{"text": str, "bbox": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], "confidence": float}, ...]
    """
    import os
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_textline_orientation=True, lang="ch")
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


def propagate_pii_to_neighbors(lines_classified, image_height):
    """
    Multi-line PII propagation: if a line is PII (especially address),
    adjacent unknown lines are also marked as PII — unless they match
    the medical whitelist.

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

        # Check next line(s) below
        for next_pos in range(idx_pos + 1, min(idx_pos + 3, len(sorted_indices))):
            next_idx = sorted_indices[next_pos]
            next_item = lines_classified[next_idx]

            if next_item["classification"] == "medical":
                break  # Stop propagation at medical data

            next_y1 = next_item["rect"][1]
            gap = next_y1 - y2

            # If next line is close (within 1.5x line height) and not medical
            if gap < line_height * 1.5 and next_item["classification"] == "unknown":
                next_item["classification"] = "pii"
                next_item["pii_type"] = "address_cont"
                next_item["label_ratio"] = None
                y2 = next_item["rect"][3]  # Extend for next check

    return lines_classified


def redact_image_ocr(
    input_path: str,
    output_path: str,
    confidence_threshold: float = 0.5,
    debug: bool = False,
    debug_path: str | None = None,
) -> dict:
    """
    Main pipeline: OCR → classify → redact PII only.

    Returns result dict for JSON output.
    """
    from PIL import Image, ImageDraw, ImageFont

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

    img = Image.open(input_path).convert("RGB")
    width, height = img.size

    # 2) Classify each line
    lines_classified = []
    for line in ocr_lines:
        text = line["text"]
        rect = bbox_to_rect(line["bbox"])
        classification, pii_type, label_ratio = classify_line(text)

        lines_classified.append({
            "text": text,
            "bbox": line["bbox"],
            "rect": rect,
            "confidence": line["confidence"],
            "classification": classification,
            "pii_type": pii_type,
            "label_ratio": label_ratio,
        })

    # 3) Multi-line PII propagation
    lines_classified = propagate_pii_to_neighbors(lines_classified, height)

    # 4) Build redaction regions (only PII lines)
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

    # 5) Apply redaction
    draw = ImageDraw.Draw(img)
    for region in pii_regions:
        q = region["quad_px"]
        draw.polygon([tuple(p) for p in q], fill="black")

    img.save(output_path)

    # 6) Debug image (optional)
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

    # 7) Build result
    result = {
        "success": True,
        "output": output_path,
        "pii_detected": len(pii_regions),
        "total_lines": len(lines_classified),
        "medical_lines": sum(1 for x in lines_classified if x["classification"] == "medical"),
        "unknown_lines": sum(1 for x in lines_classified if x["classification"] == "unknown"),
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
        )
        print(json.dumps(result, ensure_ascii=False))
    except ImportError as e:
        missing = str(e)
        print(json.dumps({
            "success": False,
            "error": f"Missing dependency: {missing}. Run: pip install paddlepaddle paddleocr",
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
