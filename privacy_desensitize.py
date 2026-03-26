#!/usr/bin/env python3
"""
医疗报告隐私信息脱敏脚本
策略：PaddleOCR 文字检测 + 条码检测 + LLM 隐私识别

支持格式: JPG/PNG/BMP/WEBP/HEIC/HEIF/PDF

用法:
  python privacy_desensitize.py image.jpg                 # 处理单张图片
  python privacy_desensitize.py image.jpg output.jpg      # 指定输出路径
  python privacy_desensitize.py report.pdf                # 处理 PDF
  python privacy_desensitize.py /path/to/dir              # 批量处理目录（含子目录）
"""

import json
import os
import re
import sys
import tempfile
import requests
from PIL import Image

# ============ LLM 配置 ============
API_BASE = os.environ.get("LLM_API_BASE", "http://localhost:8000/v1")
API_KEY = os.environ.get("LLM_API_KEY", "199604")
MODEL = os.environ.get("LLM_MODEL", "Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit")

# 代理设置：本地模型不走代理
_NO_PROXY_SESSION = None


def _get_session():
    """获取不走代理的 requests session（用于本地模型）"""
    global _NO_PROXY_SESSION
    if _NO_PROXY_SESSION is None:
        _NO_PROXY_SESSION = requests.Session()
        _NO_PROXY_SESSION.trust_env = False  # 忽略系统代理
    return _NO_PROXY_SESSION


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".heic", ".heif"}
PDF_EXTS = {".pdf"}
ALL_SUPPORTED_EXTS = IMAGE_EXTS | PDF_EXTS


# ============ OCR ============
_ocr_instance = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(lang="ch")
    return _ocr_instance


def ocr_recognize(image_path: str) -> list:
    """PaddleOCR 识别，返回 [{"idx": 0, "text": "...", "bbox": [x1,y1,x2,y2]}, ...]"""
    print("[OCR] 正在识别文字...")
    ocr = _get_ocr()
    raw = ocr.ocr(image_path)

    items = []
    if not raw or not raw[0]:
        return items

    result = raw[0]

    if hasattr(result, "keys") or isinstance(result, dict):
        dt_polys = result.get("dt_polys", []) if isinstance(result, dict) else getattr(result, "dt_polys", [])
        rec_texts = result.get("rec_texts", []) if isinstance(result, dict) else getattr(result, "rec_texts", [])
        for i, poly in enumerate(dt_polys):
            text = rec_texts[i] if i < len(rec_texts) else ""
            pts = poly.tolist() if hasattr(poly, "tolist") else poly
            x1 = int(min(p[0] for p in pts))
            y1 = int(min(p[1] for p in pts))
            x2 = int(max(p[0] for p in pts))
            y2 = int(max(p[1] for p in pts))
            items.append({"idx": i, "text": text.strip(), "bbox": [x1, y1, x2, y2]})
    elif isinstance(result, list):
        for i, line in enumerate(result):
            if isinstance(line, (list, tuple)) and len(line) == 2:
                box, (text, _score) = line
                pts = box
                x1 = int(min(p[0] for p in pts))
                y1 = int(min(p[1] for p in pts))
                x2 = int(max(p[0] for p in pts))
                y2 = int(max(p[1] for p in pts))
                items.append({"idx": i, "text": text.strip(), "bbox": [x1, y1, x2, y2]})

    print(f"[OCR] 识别到 {len(items)} 个文本区域")
    for it in items:
        print(f"  [{it['idx']:3d}] \"{it['text']}\"  @ {it['bbox']}")

    return items


# ============ 条码/二维码检测 ============
def detect_barcodes(image_path: str) -> list:
    """检测图片中的条码和二维码，返回 bbox 列表"""
    try:
        import cv2
    except ImportError:
        return []

    img = cv2.imread(image_path)
    if img is None:
        return []

    bboxes = []

    # 方法 1: pyzbar（支持一维码+二维码，需要 zbar 库）
    try:
        from pyzbar.pyzbar import decode
        barcodes = decode(img)
        for bc in barcodes:
            x, y, w, h = bc.rect
            bboxes.append([x, y, x + w, y + h])
            print(f"[条码] pyzbar 检测到 {bc.type}: {bc.data.decode('utf-8', errors='replace')[:30]}... @ [{x},{y},{x+w},{y+h}]")
    except ImportError:
        pass

    # 方法 2: OpenCV QR 检测（不需要 zbar，但只检测 QR 码）
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
                print(f"[条码] OpenCV 检测到 QR Code @ [{x1},{y1},{x2},{y2}]")

    # 方法 3: OpenCV 一维条形码检测
    if not bboxes:
        try:
            bd = cv2.barcode.BarcodeDetector()
            result = bd.detectAndDecode(img)
            # API 返回值可能是 (ok, decoded, points) 或 (ok, decoded, type, points)
            if len(result) == 4:
                ok, decoded, _det_type, points = result
            elif len(result) == 3:
                ok, decoded, points = result
            else:
                ok, decoded, points = False, [], None
            if ok and points is not None:
                for i, pts in enumerate(points):
                    x1 = int(min(p[0] for p in pts))
                    y1 = int(min(p[1] for p in pts))
                    x2 = int(max(p[0] for p in pts))
                    y2 = int(max(p[1] for p in pts))
                    bboxes.append([x1, y1, x2, y2])
                    info = decoded[i][:30] if decoded and i < len(decoded) else ""
                    print(f"[条码] OpenCV 检测到条形码: {info}... @ [{x1},{y1},{x2},{y2}]")
        except (AttributeError, cv2.error, Exception):
            pass  # OpenCV 版本不支持 barcode 模块

    if bboxes:
        print(f"[条码] 共检测到 {len(bboxes)} 个条码/二维码")
    return bboxes


# ============ LLM 隐私识别 ============
LLM_SYSTEM_PROMPT = """你是一个医疗报告隐私信息识别专家。你的任务是从OCR识别出的文本列表中，找出所有包含隐私信息的文本。

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


def llm_detect(ocr_items: list) -> dict:
    """调用 LLM 识别隐私信息，返回 {index: "隐私类型"}"""
    if not ocr_items:
        return {}

    # 构建 OCR 文本列表给 LLM
    text_list = []
    for item in ocr_items:
        text_list.append(f"[{item['idx']}] \"{item['text']}\"")
    ocr_text = "\n".join(text_list)

    user_prompt = f"以下是从一份医疗报告中OCR识别出的文本列表，请识别其中的隐私信息：\n\n{ocr_text}"

    print(f"[LLM] 正在调用模型识别隐私（{len(ocr_items)} 个文本区域）...")

    try:
        session = _get_session()
        resp = session.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 2048,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        print(f"[LLM] 原始返回: {content[:500]}")

        # 解析 JSON 数组 — 兼容模型在 <think>...</think> 后输出的情况
        # 先尝试去掉 think 标签
        clean_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        # 提取 JSON 数组 — 找包含至少2个数字（或空数组）的最长匹配
        # 优先取最后出现的完整数组（模型常在分析后才给最终答案）
        indices = None
        all_arrays = re.findall(r"\[[\d\s,]+\]", clean_content)
        if all_arrays:
            # 取最后一个且包含最多数字的数组
            best = max(all_arrays, key=lambda x: x.count(","))
            indices = json.loads(best)
        elif clean_content == "[]" or re.search(r"\[\s*\]", clean_content):
            indices = []
        else:
            # 最后尝试：提取所有散落的数字（如模型返回 "6, 8, 9, 11, 15"）
            nums = re.findall(r"\b(\d+)\b", clean_content)
            if nums:
                indices = [int(n) for n in nums]
                # 过滤掉明显不是 idx 的大数字
                max_idx = max(item["idx"] for item in ocr_items)
                indices = [n for n in indices if n <= max_idx]
            else:
                indices = []

        # 构建结果字典
        idx_set = set(item["idx"] for item in ocr_items)
        privacy = {}
        for idx in indices:
            if idx in idx_set:
                privacy[idx] = "LLM检测"

        return privacy

    except requests.exceptions.ConnectionError:
        print(f"[LLM] 错误：无法连接到 {API_BASE}，请确认模型服务已启动")
        return {}
    except requests.exceptions.Timeout:
        print("[LLM] 错误：请求超时（120s）")
        return {}
    except Exception as e:
        print(f"[LLM] 错误: {e}")
        return {}


# ============ 打码（原地操作） ============
def apply_mosaic_inplace(image: Image.Image, bboxes: list, mosaic_size: int = 15):
    """对多个 bbox 区域原地打马赛克"""
    padding = 8
    for bbox in bboxes:
        x1 = max(0, bbox[0] - padding)
        y1 = max(0, bbox[1] - padding)
        x2 = min(image.width, bbox[2] + padding)
        y2 = min(image.height, bbox[3] + padding)
        if x2 <= x1 or y2 <= y1:
            continue

        region = image.crop((x1, y1, x2, y2))
        w, h = region.size
        small_w = max(1, w // mosaic_size)
        small_h = max(1, h // mosaic_size)
        small = region.resize((small_w, small_h), Image.BILINEAR)
        mosaic = small.resize((w, h), Image.NEAREST)
        image.paste(mosaic, (x1, y1))


# ============ HEIC 转换 ============
def _ensure_jpg(image_path: str) -> str:
    """HEIC/HEIF → 临时 JPG（PaddleOCR 不支持 HEIC）"""
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in (".heic", ".heif"):
        return image_path
    import subprocess
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp_path = tmp.name
    tmp.close()
    r = subprocess.run(["sips", "-s", "format", "jpeg", image_path, "--out", tmp_path],
                       capture_output=True, timeout=30)
    if r.returncode == 0:
        print("[HEIC] 转换完成")
        return tmp_path
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        with Image.open(image_path) as img:
            img.convert("RGB").save(tmp_path, "JPEG", quality=95)
        return tmp_path
    except Exception as e:
        print(f"[HEIC] 转换失败: {e}")
        return image_path


# ============ PDF 处理 ============
def pdf_to_images(pdf_path: str, dpi: int = 200) -> list:
    """
    将 PDF 每一页渲染为临时 JPG 图片。
    返回 [(page_num, tmp_image_path), ...]
    """
    import fitz  # PyMuPDF

    print(f"[PDF] 正在转换 PDF → 图片 (DPI={dpi})...")
    doc = fitz.open(pdf_path)
    page_images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # 计算缩放倍率: dpi / 72 (PDF 默认 72dpi)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, prefix=f"pdf_p{page_num+1}_")
        tmp_path = tmp.name
        tmp.close()

        # 保存为 JPEG
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img.save(tmp_path, "JPEG", quality=95)

        page_images.append((page_num + 1, tmp_path))
        print(f"  第 {page_num + 1}/{len(doc)} 页 → {pix.width}x{pix.height}")

    doc.close()
    print(f"[PDF] 共转换 {len(page_images)} 页")
    return page_images


def _cleanup_tmp(path: str, original: str):
    if path != original and os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass


# ============ 处理单张图片 ============
def process_image(image_path: str, output_path: str):
    """处理单张图片"""
    print(f"\n{'='*60}")
    print(f"处理: {os.path.basename(image_path)}")
    print(f"{'='*60}")

    ocr_path = _ensure_jpg(image_path)

    # Step 1: 条码/二维码检测
    barcode_bboxes = detect_barcodes(ocr_path)

    # Step 2: OCR
    ocr_items = ocr_recognize(ocr_path)

    if not ocr_items and not barcode_bboxes:
        print("未识别到文字和条码，跳过")
        _cleanup_tmp(ocr_path, image_path)
        return

    # Step 3: LLM 隐私识别
    llm_result = {}
    if ocr_items:
        print(f"\n[LLM] 检测中...")
        llm_result = llm_detect(ocr_items)
        print(f"[LLM] 检测到 {len(llm_result)} 项隐私:")
        for idx in sorted(llm_result):
            print(f"  [{idx:3d}] \"{ocr_items[idx]['text']}\" → {llm_result[idx]}")

    if not llm_result and not barcode_bboxes:
        print("未检测到隐私信息，跳过")
        _cleanup_tmp(ocr_path, image_path)
        return

    # Step 4: 合并所有需要打码的 bbox
    all_bboxes = barcode_bboxes.copy()
    for idx in sorted(llm_result):
        all_bboxes.append(ocr_items[idx]["bbox"])

    # Step 5: 打码
    print(f"\n[打码] 正在处理 {len(all_bboxes)} 个区域...")
    with Image.open(ocr_path) as img:
        if img.mode == "RGBA":
            img = img.convert("RGB")

        apply_mosaic_inplace(img, all_bboxes)

        ext = os.path.splitext(output_path)[1].lower()
        if ext in (".jpg", ".jpeg"):
            img.save(output_path, "JPEG", quality=95)
        elif ext == ".png":
            img.save(output_path, "PNG")
        else:
            img.save(output_path, quality=95)

    _cleanup_tmp(ocr_path, image_path)
    print(f"[完成] → {output_path}")


# ============ 处理 PDF ============
def process_pdf(pdf_path: str, output_path: str):
    """处理 PDF 文件：逐页渲染→检测→打码→重新合成 PDF"""
    import fitz

    print(f"\n{'='*60}")
    print(f"处理 PDF: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    page_images = pdf_to_images(pdf_path)
    if not page_images:
        print("PDF 无页面，跳过")
        return

    processed_images = []
    tmp_files = []

    for page_num, tmp_img_path in page_images:
        tmp_files.append(tmp_img_path)
        print(f"\n--- 第 {page_num} 页 ---")

        # 条码检测
        barcode_bboxes = detect_barcodes(tmp_img_path)

        # OCR
        ocr_items = ocr_recognize(tmp_img_path)

        # LLM
        llm_result = {}
        if ocr_items:
            llm_result = llm_detect(ocr_items)
            print(f"[LLM] 第 {page_num} 页检测到 {len(llm_result)} 项隐私")
            for idx in sorted(llm_result):
                print(f"  [{idx:3d}] \"{ocr_items[idx]['text']}\" → {llm_result[idx]}")

        # 合并 bbox
        all_bboxes = barcode_bboxes.copy()
        for idx in sorted(llm_result):
            all_bboxes.append(ocr_items[idx]["bbox"])

        # 打码
        if all_bboxes:
            print(f"[打码] 第 {page_num} 页处理 {len(all_bboxes)} 个区域")
            with Image.open(tmp_img_path) as img:
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                apply_mosaic_inplace(img, all_bboxes)
                img.save(tmp_img_path, "JPEG", quality=95)

        processed_images.append(tmp_img_path)

    # 合成 PDF
    print(f"\n[PDF] 正在合成输出 PDF...")
    doc = fitz.open()
    for img_path in processed_images:
        img = fitz.open(img_path)
        # 从图片创建单页 PDF
        pdfbytes = img.convert_to_pdf()
        img.close()
        imgpdf = fitz.open("pdf", pdfbytes)
        doc.insert_pdf(imgpdf)
        imgpdf.close()
    doc.save(output_path)
    doc.close()

    # 清理临时文件
    for tmp_path in tmp_files:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    print(f"[完成] → {output_path}")


# ============ 批量处理目录 ============
def process_directory(dir_path: str, recursive: bool = True):
    """批量处理目录下所有图片和 PDF"""
    all_files = []

    if recursive:
        for root, _dirs, files in os.walk(dir_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ALL_SUPPORTED_EXTS and "_desensitized" not in f:
                    all_files.append(os.path.join(root, f))
    else:
        for f in os.listdir(dir_path):
            ext = os.path.splitext(f)[1].lower()
            if ext in ALL_SUPPORTED_EXTS and "_desensitized" not in f:
                all_files.append(os.path.join(dir_path, f))

    if not all_files:
        print(f"目录 {dir_path} 中未找到支持的文件")
        return

    all_files.sort()
    print(f"找到 {len(all_files)} 个文件待处理\n")

    for i, input_path in enumerate(all_files, 1):
        print(f"\n[{i}/{len(all_files)}]", end="")
        base, ext = os.path.splitext(input_path)
        ext_lower = ext.lower()

        if ext_lower in PDF_EXTS:
            output_path = f"{base}_desensitized.pdf"
            process_pdf(input_path, output_path)
        else:
            out_ext = ".jpg" if ext_lower in (".heic", ".heif") else ext
            output_path = f"{base}_desensitized{out_ext}"
            process_image(input_path, output_path)


# ============ 入口 ============
def main():
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        print("用法: python privacy_desensitize.py <图片/PDF/目录路径> [输出路径]")
        print()
        print("支持格式: JPG, PNG, BMP, WEBP, HEIC, HEIF, PDF")
        print()
        print("环境变量配置:")
        print("  LLM_API_BASE  - LLM API 地址 (默认: http://localhost:8000/v1)")
        print("  LLM_API_KEY   - API Key")
        print("  LLM_MODEL     - 模型名称 (默认: qwen3.5-27b)")
        sys.exit(1)

    if os.path.isdir(input_path):
        process_directory(input_path)
    else:
        ext = os.path.splitext(input_path)[1].lower()

        if len(sys.argv) > 2:
            output_path = sys.argv[2]
        else:
            base = os.path.splitext(input_path)[0]
            if ext in PDF_EXTS:
                output_path = f"{base}_desensitized.pdf"
            else:
                out_ext = ".jpg" if ext in (".heic", ".heif") else os.path.splitext(input_path)[1]
                output_path = f"{base}_desensitized{out_ext}"

        if ext in PDF_EXTS:
            process_pdf(input_path, output_path)
        else:
            process_image(input_path, output_path)


if __name__ == "__main__":
    main()
