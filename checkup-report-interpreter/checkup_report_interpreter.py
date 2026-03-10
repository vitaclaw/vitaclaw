#!/usr/bin/env python3
"""体检报告智能解读 - PDF解析 + LLM异常识别与健康建议生成。

完全独立的工具，不依赖 MTB 项目的 src/ 或 config/。
"""

import argparse
import json
import os
import re
import sys
from typing import Any


# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")


# ---------------------------------------------------------------------------
# Reference Ranges for Common Checkup Items
# ---------------------------------------------------------------------------

REFERENCE_RANGES: dict[str, dict[str, Any]] = {
    # Blood routine (血常规)
    "白细胞": {"low": 3.5, "high": 9.5, "unit": "×10⁹/L"},
    "红细胞": {
        "low": 4.3, "high": 5.8, "unit": "×10¹²/L",
        "gender": {
            "male": {"low": 4.3, "high": 5.8},
            "female": {"low": 3.8, "high": 5.1},
        },
    },
    "血红蛋白": {
        "low": 130, "high": 175, "unit": "g/L",
        "gender": {
            "male": {"low": 130, "high": 175},
            "female": {"low": 115, "high": 150},
        },
    },
    "血小板": {"low": 125, "high": 350, "unit": "×10⁹/L"},
    "中性粒细胞百分比": {"low": 40, "high": 75, "unit": "%"},
    "淋巴细胞百分比": {"low": 20, "high": 50, "unit": "%"},
    # Liver function (肝功能)
    "ALT": {"low": 0, "high": 40, "unit": "U/L"},
    "AST": {"low": 0, "high": 40, "unit": "U/L"},
    "总胆红素": {"low": 0, "high": 21, "unit": "μmol/L"},
    "直接胆红素": {"low": 0, "high": 8, "unit": "μmol/L"},
    "白蛋白": {"low": 40, "high": 55, "unit": "g/L"},
    "GGT": {"low": 0, "high": 60, "unit": "U/L"},
    "ALP": {"low": 45, "high": 125, "unit": "U/L"},
    # Kidney function (肾功能)
    "肌酐": {"low": 57, "high": 111, "unit": "μmol/L"},
    "尿素氮": {"low": 3.1, "high": 8.0, "unit": "mmol/L"},
    "尿酸": {"low": 208, "high": 428, "unit": "μmol/L"},
    "eGFR": {"low": 90, "high": 999, "unit": "mL/min/1.73m²"},
    # Blood lipids (血脂)
    "总胆固醇": {"low": 0, "high": 5.2, "unit": "mmol/L"},
    "甘油三酯": {"low": 0, "high": 1.7, "unit": "mmol/L"},
    "HDL-C": {"low": 1.0, "high": 999, "unit": "mmol/L"},
    "LDL-C": {"low": 0, "high": 3.4, "unit": "mmol/L"},
    # Blood sugar (血糖)
    "空腹血糖": {"low": 3.9, "high": 6.1, "unit": "mmol/L"},
    "糖化血红蛋白": {"low": 0, "high": 6.0, "unit": "%"},
    # Thyroid (甲状腺)
    "TSH": {"low": 0.27, "high": 4.2, "unit": "mIU/L"},
    "FT3": {"low": 3.1, "high": 6.8, "unit": "pmol/L"},
    "FT4": {"low": 12, "high": 22, "unit": "pmol/L"},
    # Tumor markers (肿瘤标志物)
    "CEA": {"low": 0, "high": 5.0, "unit": "ng/mL"},
    "AFP": {"low": 0, "high": 7.0, "unit": "ng/mL"},
    "CA199": {"low": 0, "high": 37.0, "unit": "U/mL"},
    "CA125": {"low": 0, "high": 35.0, "unit": "U/mL"},
    "PSA": {"low": 0, "high": 4.0, "unit": "ng/mL"},
}


# ---------------------------------------------------------------------------
# Priority Levels
# ---------------------------------------------------------------------------

PRIORITY_LEVELS = {
    "critical": "紧急异常（需立即就医）",
    "high": "重要异常（建议尽快复查）",
    "moderate": "中等异常（建议定期复查）",
    "low": "轻微异常（注意观察）",
    "normal": "正常",
}

# Special critical thresholds for specific items
CRITICAL_THRESHOLDS: dict[str, list[dict[str, Any]]] = {
    "空腹血糖": [
        {"condition": "gte", "value": 11.1, "priority": "critical"},
        {"condition": "gte", "value": 7.0, "priority": "high"},
    ],
    "AFP": [
        {"condition": "gte", "value": 400, "priority": "critical"},
        {"condition": "gte", "value": 20, "priority": "high"},
    ],
    "PSA": [
        {"condition": "gte", "value": 10, "priority": "high"},
    ],
    "CEA": [
        {"condition": "gte", "value": 20, "priority": "high"},
    ],
    "CA199": [
        {"condition": "gte", "value": 100, "priority": "high"},
    ],
    "CA125": [
        {"condition": "gte", "value": 100, "priority": "high"},
    ],
    "血红蛋白": [
        {"condition": "lte", "value": 60, "priority": "critical"},
        {"condition": "lte", "value": 90, "priority": "high"},
    ],
    "血小板": [
        {"condition": "lte", "value": 50, "priority": "critical"},
        {"condition": "gte", "value": 600, "priority": "high"},
    ],
    "白细胞": [
        {"condition": "lte", "value": 1.5, "priority": "critical"},
        {"condition": "gte", "value": 20, "priority": "critical"},
    ],
    "肌酐": [
        {"condition": "gte", "value": 400, "priority": "critical"},
        {"condition": "gte", "value": 200, "priority": "high"},
    ],
    "eGFR": [
        {"condition": "lte", "value": 15, "priority": "critical"},
        {"condition": "lte", "value": 30, "priority": "high"},
    ],
    "糖化血红蛋白": [
        {"condition": "gte", "value": 9.0, "priority": "high"},
    ],
}


# ---------------------------------------------------------------------------
# LLM Call
# ---------------------------------------------------------------------------

def _llm_call(system_prompt: str, user_prompt: str, max_tokens: int = 8192) -> str:
    """Call LLM via OpenRouter API."""
    import requests

    if not OPENROUTER_API_KEY:
        return "[错误] 未设置 OPENROUTER_API_KEY 环境变量"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        resp = requests.post(
            OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"[LLM调用失败] {e}"


# ---------------------------------------------------------------------------
# PDF Parsing
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text with page markers.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        RuntimeError: If PDF parsing fails.
    """
    import fitz  # PyMuPDF

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"无法打开 PDF 文件: {e}") from e

    text_parts: list[str] = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            text_parts.append(f"[Page {page_num + 1}]\n{text}")
    doc.close()

    if not text_parts:
        raise RuntimeError("PDF 文件中未提取到任何文本内容，可能是扫描件或图片型 PDF")

    return "\n\n".join(text_parts)


# ---------------------------------------------------------------------------
# JSON Parsing Helpers
# ---------------------------------------------------------------------------

def _parse_llm_json(raw: str) -> Any:
    """Parse JSON from LLM response, handling markdown code blocks.

    LLM responses often wrap JSON in ```json ... ``` blocks.
    This function strips those markers before parsing.
    """
    if not raw or raw.startswith("[错误]") or raw.startswith("[LLM调用失败]"):
        return None

    # Strip markdown code block markers
    text = raw.strip()
    # Match ```json ... ``` or ``` ... ```
    pattern = r"```(?:json)?\s*\n?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON array or object in the text
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start_idx = text.find(start_char)
            end_idx = text.rfind(end_char)
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    return json.loads(text[start_idx : end_idx + 1])
                except json.JSONDecodeError:
                    continue
        return None


# ---------------------------------------------------------------------------
# CheckupReportInterpreter
# ---------------------------------------------------------------------------

class CheckupReportInterpreter:
    """体检报告智能解读：PDF解析、结构化提取、异常分级、临床解读、健康建议。"""

    def __init__(self):
        self.reference_ranges = REFERENCE_RANGES
        self.priority_levels = PRIORITY_LEVELS
        self.critical_thresholds = CRITICAL_THRESHOLDS

    # ----- extract_items -----

    def extract_items(self, text: str) -> list[dict[str, Any]]:
        """Use LLM to extract structured checkup items from raw text.

        Args:
            text: Raw text extracted from a checkup report PDF.

        Returns:
            List of dicts, each with keys: category, item, value, unit,
            reference_range, status.
        """
        system_prompt = """你是一位专业的体检报告数据提取专家。你的任务是从体检报告文本中识别并提取所有检查项目。

要求：
1. 识别所有检查项目，包括：实验室检验（血常规、生化、免疫等）、影像学发现（B超、CT、X光等）、体格检查结果（身高、体重、血压等）
2. 对于每个检查项目，提取以下信息：
   - category: 检查类别（如"血常规"、"肝功能"、"肾功能"、"血脂"、"血糖"、"甲状腺功能"、"肿瘤标志物"、"尿常规"、"心电图"、"腹部B超"、"胸部X光"、"体格检查"等）
   - item: 检查项目名称（如"白细胞"、"ALT"、"空腹血糖"等）
   - value: 检测数值（纯数字，如果是定性结果则填写结果文字如"阴性"、"阳性"）
   - unit: 单位（如"×10⁹/L"、"U/L"、"mmol/L"等）
   - reference_range: 报告上标注的参考范围（如"3.5-9.5"）
   - status: 状态判断（"正常"、"偏高"、"偏低"、"异常"中的一个）
3. 对于影像学和体格检查等非数值结果，value 填写发现描述，status 根据是否有异常发现判断
4. 务必提取报告中的所有项目，不要遗漏

请严格以 JSON 数组格式返回，不要包含任何其他文字说明。示例格式：
[
  {"category": "血常规", "item": "白细胞", "value": "6.5", "unit": "×10⁹/L", "reference_range": "3.5-9.5", "status": "正常"},
  {"category": "腹部B超", "item": "肝脏", "value": "肝内稍强回声，考虑血管瘤可能", "unit": "", "reference_range": "", "status": "异常"}
]"""

        user_prompt = f"请从以下体检报告文本中提取所有检查项目：\n\n{text}"

        raw_response = _llm_call(system_prompt, user_prompt, max_tokens=8192)
        items = _parse_llm_json(raw_response)

        if items is None:
            print("[警告] LLM 返回的数据无法解析为 JSON，尝试使用原始文本")
            return []

        if not isinstance(items, list):
            print("[警告] LLM 返回的数据不是数组格式")
            return []

        # Validate and enrich items against built-in reference ranges
        validated_items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            # Ensure required fields exist
            item.setdefault("category", "未分类")
            item.setdefault("item", "未知项目")
            item.setdefault("value", "")
            item.setdefault("unit", "")
            item.setdefault("reference_range", "")
            item.setdefault("status", "正常")

            # Cross-check with built-in reference ranges
            item_name = item["item"]
            value_str = str(item["value"]).strip()
            if item_name in self.reference_ranges and _is_numeric(value_str):
                ref = self.reference_ranges[item_name]
                value_num = float(value_str)
                low = ref["low"]
                high = ref["high"]
                if value_num < low:
                    item["status"] = "偏低"
                elif value_num > high:
                    item["status"] = "偏高"
                # Fill in unit from reference if missing
                if not item["unit"] and ref.get("unit"):
                    item["unit"] = ref["unit"]

            validated_items.append(item)

        return validated_items

    # ----- interpret -----

    def interpret(self, items: list[dict[str, Any]]) -> str:
        """Use LLM to interpret the extracted checkup items.

        Args:
            items: List of structured checkup items from extract_items().

        Returns:
            Interpretation text in Chinese.
        """
        if not items:
            return "未提取到检查项目，无法进行解读。"

        # Separate abnormal vs normal items for focused analysis
        abnormal_items = [i for i in items if i.get("status") != "正常"]
        normal_items = [i for i in items if i.get("status") == "正常"]

        system_prompt = """你是一位经验丰富的全科医生，擅长解读体检报告。请对提取出的检查项目进行临床解读。

要求：
1. 按器官系统分组解读（如血液系统、肝胆系统、肾脏系统、代谢系统、甲状腺、肿瘤标志物、影像学等）
2. 重点分析异常项目的临床意义
3. 考虑异常指标之间的关联性（如 ALT+AST 同时升高提示肝损伤）
4. 用通俗易懂的中文解释，避免过多专业术语，必要时加括号解释
5. 对于每个异常项目，说明：
   - 该指标的含义
   - 偏高/偏低的可能原因
   - 临床意义和风险程度
6. 最后给出需要重点关注的问题列表

请用清晰的分段格式输出，使用中文标题和编号。"""

        items_json = json.dumps(items, ensure_ascii=False, indent=2)
        user_prompt = f"""以下是从体检报告中提取的检查项目：

异常项目 ({len(abnormal_items)} 项)：
{json.dumps(abnormal_items, ensure_ascii=False, indent=2)}

正常项目 ({len(normal_items)} 项)：
{json.dumps(normal_items, ensure_ascii=False, indent=2)}

请进行系统性的临床解读。"""

        return _llm_call(system_prompt, user_prompt, max_tokens=8192)

    # ----- prioritize -----

    def prioritize(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Classify abnormalities by priority level.

        Priority rules:
        - critical: value >3x upper or <0.3x lower reference, or specific thresholds
        - high: value >2x upper or <0.5x lower
        - moderate: value >1.5x upper or <0.7x lower
        - low: mild elevations/decreases
        - normal: within reference range

        Args:
            items: List of structured checkup items.

        Returns:
            Items list with added 'priority' and 'priority_label' fields,
            sorted by priority (critical first).
        """
        priority_order = {"critical": 0, "high": 1, "moderate": 2, "low": 3, "normal": 4}

        for item in items:
            item_name = item.get("item", "")
            value_str = str(item.get("value", "")).strip()
            status = item.get("status", "正常")

            # Default to normal
            priority = "normal"

            if status == "正常":
                item["priority"] = "normal"
                item["priority_label"] = self.priority_levels["normal"]
                continue

            # Check special critical thresholds first
            if item_name in self.critical_thresholds and _is_numeric(value_str):
                value_num = float(value_str)
                for threshold in self.critical_thresholds[item_name]:
                    cond = threshold["condition"]
                    thr_val = threshold["value"]
                    if cond == "gte" and value_num >= thr_val:
                        priority = threshold["priority"]
                        break
                    elif cond == "lte" and value_num <= thr_val:
                        priority = threshold["priority"]
                        break
                if priority != "normal":
                    item["priority"] = priority
                    item["priority_label"] = self.priority_levels[priority]
                    continue

            # General ratio-based prioritization
            if item_name in self.reference_ranges and _is_numeric(value_str):
                ref = self.reference_ranges[item_name]
                value_num = float(value_str)
                low = ref["low"]
                high = ref["high"]

                if value_num > high and high > 0:
                    ratio = value_num / high
                    if ratio > 3.0:
                        priority = "critical"
                    elif ratio > 2.0:
                        priority = "high"
                    elif ratio > 1.5:
                        priority = "moderate"
                    else:
                        priority = "low"
                elif value_num < low and low > 0:
                    ratio = value_num / low
                    if ratio < 0.3:
                        priority = "critical"
                    elif ratio < 0.5:
                        priority = "high"
                    elif ratio < 0.7:
                        priority = "moderate"
                    else:
                        priority = "low"
                else:
                    # Abnormal status from LLM but within our reference range
                    priority = "low"
            elif status in ("偏高", "偏低", "异常"):
                # Non-numeric or not in reference ranges - try to parse from report range
                priority = self._prioritize_by_report_range(item)
            else:
                priority = "normal"

            item["priority"] = priority
            item["priority_label"] = self.priority_levels[priority]

        # Sort by priority (critical first)
        items.sort(key=lambda x: priority_order.get(x.get("priority", "normal"), 4))
        return items

    def _prioritize_by_report_range(self, item: dict[str, Any]) -> str:
        """Attempt prioritization using the report's own reference range.

        Falls back to 'low' if parsing fails.
        """
        ref_range = item.get("reference_range", "")
        value_str = str(item.get("value", "")).strip()

        if not ref_range or not _is_numeric(value_str):
            # Non-numeric abnormalities (imaging, qualitative) default to moderate
            status = item.get("status", "")
            if status == "异常":
                return "moderate"
            return "low"

        value_num = float(value_str)

        # Try to parse reference range like "3.5-9.5" or "0-40"
        range_match = re.match(
            r"[<>≤≥]?\s*(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)", ref_range
        )
        if not range_match:
            return "low"

        try:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
        except ValueError:
            return "low"

        if value_num > high and high > 0:
            ratio = value_num / high
            if ratio > 3.0:
                return "critical"
            elif ratio > 2.0:
                return "high"
            elif ratio > 1.5:
                return "moderate"
            return "low"
        elif value_num < low and low > 0:
            ratio = value_num / low
            if ratio < 0.3:
                return "critical"
            elif ratio < 0.5:
                return "high"
            elif ratio < 0.7:
                return "moderate"
            return "low"

        return "low"

    # ----- compare_years -----

    def compare_years(
        self,
        items_current: list[dict[str, Any]],
        items_previous: list[dict[str, Any]],
    ) -> str:
        """Compare two years' checkup results.

        Highlights new abnormalities, worsening trends, and improvements.

        Args:
            items_current: Current year's extracted items.
            items_previous: Previous year's extracted items.

        Returns:
            Comparison report text in Chinese.
        """
        if not items_current:
            return "当前年份报告未提取到检查项目，无法进行对比。"
        if not items_previous:
            return "往年报告未提取到检查项目，无法进行对比。"

        system_prompt = """你是一位经验丰富的全科医生，正在对比患者两年的体检报告。

请从以下几个角度进行分析：
1. **新增异常**：今年出现但去年没有的异常项目
2. **恶化趋势**：今年数值比去年明显恶化的项目（偏离参考范围更远）
3. **改善项目**：今年数值比去年改善的项目（更接近参考范围）
4. **持续异常**：两年都异常的项目，关注是否稳定
5. **关键趋势总结**：整体健康趋势评估

对比要求：
- 用通俗中文解释变化的临床意义
- 对恶化项目给出具体的关注建议
- 对改善项目给予肯定并建议继续保持
- 用表格形式展示关键指标的变化（项目 | 去年值 | 今年值 | 变化 | 临床意义）

请用清晰的分段格式输出。"""

        user_prompt = f"""今年的体检数据：
{json.dumps(items_current, ensure_ascii=False, indent=2)}

去年的体检数据：
{json.dumps(items_previous, ensure_ascii=False, indent=2)}

请进行详细对比分析。"""

        return _llm_call(system_prompt, user_prompt, max_tokens=8192)

    # ----- generate_report -----

    def generate_report(
        self,
        pdf_path: str,
        previous_items: list[dict[str, Any]] | None = None,
    ) -> str:
        """Full pipeline: parse → extract → interpret → prioritize → report.

        Args:
            pdf_path: Path to the checkup report PDF.
            previous_items: Optional previous year's items for comparison.

        Returns:
            Complete interpretation report as a formatted string.
        """
        # Step 1: Parse PDF
        print("=" * 60)
        print("  体检报告智能解读")
        print("=" * 60)
        print(f"\n[1/5] 正在解析 PDF 文件: {pdf_path}")

        try:
            raw_text = parse_pdf(pdf_path)
        except (FileNotFoundError, RuntimeError) as e:
            return f"[错误] {e}"

        print(f"  提取文本长度: {len(raw_text)} 字符")

        # Step 2: Extract structured items
        print("\n[2/5] 正在提取检查项目（LLM 结构化提取）...")
        items = self.extract_items(raw_text)

        if not items:
            return "[错误] 未能从报告中提取到任何检查项目。请确认 PDF 是文本型报告（非扫描件）。"

        abnormal_count = sum(1 for i in items if i.get("status") != "正常")
        print(f"  提取到 {len(items)} 个检查项目，其中 {abnormal_count} 项异常")

        # Step 3: Prioritize abnormalities
        print("\n[3/5] 正在进行异常分级...")
        items = self.prioritize(items)

        priority_counts: dict[str, int] = {}
        for item in items:
            p = item.get("priority", "normal")
            priority_counts[p] = priority_counts.get(p, 0) + 1
        for level in ["critical", "high", "moderate", "low"]:
            count = priority_counts.get(level, 0)
            if count > 0:
                print(f"  {self.priority_levels[level]}: {count} 项")

        # Step 4: LLM interpretation
        print("\n[4/5] 正在进行临床解读（LLM 分析）...")
        interpretation = self.interpret(items)

        # Step 5: Generate comprehensive report
        print("\n[5/5] 正在生成完整报告...")

        report_parts: list[str] = []

        # Section 1: Overview
        report_parts.append(self._format_overview(items, pdf_path))

        # Section 2: Abnormal findings summary
        report_parts.append(self._format_abnormal_summary(items))

        # Section 3: System-by-system interpretation
        report_parts.append(self._format_interpretation(interpretation))

        # Section 4: Health recommendations
        recommendations = self._generate_recommendations(items)
        report_parts.append(self._format_recommendations(recommendations))

        # Section 5: Follow-up tests
        follow_ups = self._generate_follow_up_tests(items)
        report_parts.append(self._format_follow_up_tests(follow_ups))

        # Optional: Year-over-year comparison
        if previous_items:
            print("\n[附加] 正在进行年度对比分析...")
            comparison = self.compare_years(items, previous_items)
            report_parts.append(self._format_comparison(comparison))

        # Disclaimer
        report_parts.append(self._format_disclaimer())

        full_report = "\n".join(report_parts)

        print("\n" + "=" * 60)
        print("  报告生成完成")
        print("=" * 60)
        print(full_report)

        return full_report

    # ----- Internal formatting helpers -----

    def _format_overview(self, items: list[dict[str, Any]], pdf_path: str) -> str:
        """Format the overview section."""
        total = len(items)
        abnormal = sum(1 for i in items if i.get("status") != "正常")
        normal = total - abnormal

        categories: dict[str, int] = {}
        for item in items:
            cat = item.get("category", "未分类")
            categories[cat] = categories.get(cat, 0) + 1

        lines = [
            "",
            "━" * 50,
            "一、体检概览",
            "━" * 50,
            f"  报告文件: {os.path.basename(pdf_path)}",
            f"  检查项目总数: {total}",
            f"  正常项目: {normal}",
            f"  异常项目: {abnormal}",
            "",
            "  检查类别分布:",
        ]
        for cat, count in sorted(categories.items()):
            lines.append(f"    - {cat}: {count} 项")

        return "\n".join(lines)

    def _format_abnormal_summary(self, items: list[dict[str, Any]]) -> str:
        """Format the abnormal findings summary, sorted by priority."""
        abnormal = [i for i in items if i.get("priority", "normal") != "normal"]

        lines = [
            "",
            "━" * 50,
            "二、异常项目汇总（按优先级排序）",
            "━" * 50,
        ]

        if not abnormal:
            lines.append("  恭喜！所有检查项目均在正常范围内。")
            return "\n".join(lines)

        current_priority = ""
        for item in abnormal:
            priority = item.get("priority", "low")
            priority_label = item.get("priority_label", "")

            if priority != current_priority:
                current_priority = priority
                marker = _priority_marker(priority)
                lines.append(f"\n  {marker} {priority_label}")
                lines.append("  " + "-" * 40)

            value_str = str(item.get("value", ""))
            unit = item.get("unit", "")
            status = item.get("status", "")
            ref = item.get("reference_range", "")

            detail = f"    [{item.get('category', '')}] {item.get('item', '')}: {value_str}"
            if unit:
                detail += f" {unit}"
            detail += f" ({status})"
            if ref:
                detail += f"  [参考: {ref}]"
            lines.append(detail)

        return "\n".join(lines)

    def _format_interpretation(self, interpretation: str) -> str:
        """Format the LLM interpretation section."""
        lines = [
            "",
            "━" * 50,
            "三、各系统解读",
            "━" * 50,
            "",
            interpretation,
        ]
        return "\n".join(lines)

    def _generate_recommendations(self, items: list[dict[str, Any]]) -> str:
        """Use LLM to generate health recommendations based on findings."""
        abnormal = [i for i in items if i.get("status") != "正常"]
        if not abnormal:
            return "各项指标均正常，建议继续保持健康的生活方式，定期体检。"

        system_prompt = """你是一位资深全科医生，请根据体检异常项目给出具体、实用的健康建议。

要求：
1. 按重要程度排序给出建议
2. 包含饮食、运动、生活习惯、用药提醒等方面
3. 建议要具体可操作，避免笼统的套话
4. 对紧急和重要异常，明确建议就医科室和时间
5. 用通俗中文，条理清晰"""

        user_prompt = f"""以下是体检中发现的异常项目：
{json.dumps(abnormal, ensure_ascii=False, indent=2)}

请给出个性化的健康建议。"""

        return _llm_call(system_prompt, user_prompt, max_tokens=4096)

    def _format_recommendations(self, recommendations: str) -> str:
        """Format the health recommendations section."""
        lines = [
            "",
            "━" * 50,
            "四、健康建议",
            "━" * 50,
            "",
            recommendations,
        ]
        return "\n".join(lines)

    def _generate_follow_up_tests(self, items: list[dict[str, Any]]) -> str:
        """Use LLM to suggest follow-up tests based on abnormal findings."""
        abnormal = [i for i in items if i.get("status") != "正常"]
        if not abnormal:
            return "无特殊复查项目，建议每年常规体检。"

        system_prompt = """你是一位资深全科医生，请根据体检异常项目建议需要复查的项目。

要求：
1. 列出建议复查的具体检查项目
2. 说明建议复查的时间（如1个月、3个月、6个月）
3. 说明建议就诊的科室
4. 区分紧急复查和常规随访
5. 用通俗中文，列表形式输出"""

        user_prompt = f"""以下是体检中发现的异常项目：
{json.dumps(abnormal, ensure_ascii=False, indent=2)}

请建议需要复查的项目和时间安排。"""

        return _llm_call(system_prompt, user_prompt, max_tokens=4096)

    def _format_follow_up_tests(self, follow_ups: str) -> str:
        """Format the follow-up tests section."""
        lines = [
            "",
            "━" * 50,
            "五、建议复查项目",
            "━" * 50,
            "",
            follow_ups,
        ]
        return "\n".join(lines)

    def _format_comparison(self, comparison: str) -> str:
        """Format the year-over-year comparison section."""
        lines = [
            "",
            "━" * 50,
            "六、年度对比分析",
            "━" * 50,
            "",
            comparison,
        ]
        return "\n".join(lines)

    def _format_disclaimer(self) -> str:
        """Format the disclaimer."""
        return "\n".join([
            "",
            "━" * 50,
            "免责声明",
            "━" * 50,
            "",
            "本报告由 AI 辅助生成，仅供参考，不构成医疗诊断或治疗建议。",
            "如有异常发现，请及时咨询专业医生进行进一步检查和诊断。",
            "紧急异常项目请立即前往医院就诊。",
            "",
        ])


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def _is_numeric(value: str) -> bool:
    """Check if a string can be parsed as a float."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _priority_marker(priority: str) -> str:
    """Return a text marker for priority level."""
    markers = {
        "critical": "[!!!]",
        "high": "[!!]",
        "moderate": "[!]",
        "low": "[i]",
        "normal": "[OK]",
    }
    return markers.get(priority, "[?]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="体检报告智能解读（PDF解析 + LLM异常识别与健康建议）"
    )
    sub = parser.add_subparsers(dest="command")

    # report - full interpretation pipeline
    p_report = sub.add_parser("report", help="完整解读体检报告")
    p_report.add_argument("pdf", help="体检报告 PDF 文件路径")

    # parse - extract raw text only
    p_parse = sub.add_parser("parse", help="仅解析 PDF 提取文本")
    p_parse.add_argument("pdf", help="体检报告 PDF 文件路径")

    # extract - extract structured items
    p_extract = sub.add_parser("extract", help="提取结构化检查项目")
    p_extract.add_argument("pdf", help="体检报告 PDF 文件路径")

    # compare - compare two years
    p_compare = sub.add_parser("compare", help="对比两年体检报告")
    p_compare.add_argument("current_pdf", help="今年体检报告 PDF 文件路径")
    p_compare.add_argument("previous_pdf", help="往年体检报告 PDF 文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    interpreter = CheckupReportInterpreter()

    if args.command == "parse":
        try:
            text = parse_pdf(args.pdf)
            print(text)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"[错误] {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "extract":
        try:
            text = parse_pdf(args.pdf)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"[错误] {e}", file=sys.stderr)
            sys.exit(1)

        print("正在提取检查项目...")
        items = interpreter.extract_items(text)

        if not items:
            print("[警告] 未能提取到检查项目")
            sys.exit(1)

        # Prioritize and display
        items = interpreter.prioritize(items)
        print(f"\n提取到 {len(items)} 个检查项目:\n")
        print(json.dumps(items, ensure_ascii=False, indent=2))

    elif args.command == "report":
        interpreter.generate_report(args.pdf)

    elif args.command == "compare":
        # Parse and extract from both PDFs
        try:
            print("正在解析今年报告...")
            text_current = parse_pdf(args.current_pdf)
            print("正在解析往年报告...")
            text_previous = parse_pdf(args.previous_pdf)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"[错误] {e}", file=sys.stderr)
            sys.exit(1)

        print("正在提取今年检查项目...")
        items_current = interpreter.extract_items(text_current)
        print("正在提取往年检查项目...")
        items_previous = interpreter.extract_items(text_previous)

        if not items_current:
            print("[错误] 今年报告未提取到检查项目", file=sys.stderr)
            sys.exit(1)

        # Generate full report with comparison
        interpreter.generate_report(args.current_pdf, previous_items=items_previous)


if __name__ == "__main__":
    main()
