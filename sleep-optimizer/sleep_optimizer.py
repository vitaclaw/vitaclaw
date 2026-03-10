#!/usr/bin/env python3
"""睡眠优化建议 — 基于多源健康数据，LLM 生成个性化睡眠改善方案。"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_memory import HealthMemoryWriter
from cross_skill_reader import CrossSkillReader


# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")


def _llm_call(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call LLM via OpenRouter API."""
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
# Data formatting helpers
# ---------------------------------------------------------------------------

def _format_sleep_data(records: list) -> str:
    """Format sleep records into readable text for the LLM.

    Expected record shape (from sleep-analyzer via CrossSkillReader):
        {"data": {"date": "2026-03-08", "bedtime": "23:15", "wake_time": "07:00",
                  "score": 78, "efficiency_pct": 92, "deep_min": 85,
                  "rem_min": 55, "total_min": 465, ...}}
    """
    if not records:
        return "睡眠数据：无记录\n"

    lines = [f"睡眠数据（最近 {len(records)} 晚）："]
    for r in sorted(records, key=lambda x: x.get("data", {}).get("date", ""), reverse=True):
        d = r.get("data", {})
        date = d.get("date", "?")
        bedtime = d.get("bedtime", "?")
        wake = d.get("wake_time", "?")
        score = d.get("score", "?")
        eff = d.get("efficiency_pct", "?")
        deep = d.get("deep_min", "?")
        rem = d.get("rem_min", "?")
        total = d.get("total_min")
        duration_str = ""
        if total is not None:
            h, m = divmod(int(total), 60)
            duration_str = f", 总时长 {h}h{m}m"
        lines.append(
            f"- {date}: 入睡 {bedtime} → 起床 {wake}{duration_str}, "
            f"评分 {score}/100, 效率 {eff}%, 深睡 {deep}min, REM {rem}min"
        )
    return "\n".join(lines) + "\n"


def _format_caffeine_data(records: list) -> str:
    """Format caffeine intake records into readable text for the LLM.

    Expected record shape (from caffeine-tracker via CrossSkillReader):
        {"data": {"drink": "美式咖啡", "mg": 95, "time": "08:30", ...},
         "timestamp": "2026-03-08T08:30:00"}
    """
    if not records:
        return "咖啡因数据：无记录\n"

    # Group by date
    by_date: dict = {}
    for r in records:
        d = r.get("data", {})
        ts = r.get("timestamp", "")
        date = ts[:10] if len(ts) >= 10 else d.get("date", "?")
        by_date.setdefault(date, []).append(d)

    lines = [f"咖啡因摄入数据（最近 {len(by_date)} 天）："]
    for date in sorted(by_date.keys(), reverse=True):
        intakes = by_date[date]
        total_mg = sum(i.get("mg", 0) for i in intakes)
        times = [i.get("time", "?") for i in intakes]
        last_time = max(times) if times else "?"
        drinks = [f"{i.get('drink', '?')}({i.get('mg', '?')}mg)" for i in intakes]
        lines.append(
            f"- {date}: {len(intakes)} 杯, 共 {total_mg}mg, "
            f"最后一杯 {last_time} [{', '.join(drinks)}]"
        )
    return "\n".join(lines) + "\n"


def _format_supplement_data(records: list) -> str:
    """Format active supplement regimen into readable text for the LLM.

    Expected record shape (from supplement-manager via CrossSkillReader):
        {"data": {"name": "VD3", "dose": "5000IU", "frequency": "daily",
                  "timing": "morning with food", "status": "active", ...}}
    """
    if not records:
        return "补剂方案：无记录\n"

    lines = ["当前补剂方案："]
    for r in records:
        d = r.get("data", {})
        name = d.get("name", "?")
        dose = d.get("dose", "?")
        freq = d.get("frequency", "?")
        timing = d.get("timing", "?")
        lines.append(f"- {name} {dose} {freq} ({timing})")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# SleepOptimizer
# ---------------------------------------------------------------------------

class SleepOptimizer:
    """基于多源健康数据的个性化睡眠优化建议器。

    纯读取 + LLM 推理技能：读取 sleep-analyzer、caffeine-tracker、
    supplement-manager 的数据以及 health memory 上下文，交由 LLM 分析
    并生成个性化睡眠改善方案。本技能不写入任何数据。
    """

    def __init__(self):
        self.memory = HealthMemoryWriter()
        self.reader = CrossSkillReader()

    # ---- helpers ----

    def _collect_data(self, days: int = 14) -> dict:
        """Collect sleep, caffeine, and supplement data for the given window.

        Returns a dict with keys: sleep_records, caffeine_records,
        supplement_records, health_context, and their formatted strings.
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        sleep_records = self.reader.read_sleep_data(start=cutoff)
        caffeine_records = self.reader.read_caffeine_intakes(start=cutoff)
        supplement_records = self.reader.read_supplement_regimen()
        health_context = self.memory.read_health_context()

        return {
            "sleep_records": sleep_records,
            "caffeine_records": caffeine_records,
            "supplement_records": supplement_records,
            "health_context": health_context,
            "sleep_text": _format_sleep_data(sleep_records),
            "caffeine_text": _format_caffeine_data(caffeine_records),
            "supplement_text": _format_supplement_data(supplement_records),
        }

    def _has_any_data(self, collected: dict) -> bool:
        """Return True if at least one data source has records."""
        return bool(
            collected["sleep_records"]
            or collected["caffeine_records"]
            or collected["supplement_records"]
        )

    def _no_data_message(self):
        """Print a helpful message when no data is available."""
        print("暂无可用的健康数据。")
        print("")
        print("睡眠优化建议需要至少一种数据来源：")
        print("  - 睡眠数据：使用 sleep-analyzer 技能记录睡眠")
        print("  - 咖啡因数据：使用 caffeine-tracker 技能记录咖啡因摄入")
        print("  - 补剂数据：使用 supplement-manager 技能管理补剂方案")
        print("")
        print("请先使用上述技能记录数据后，再运行睡眠优化建议。")

    # ---- recommend ----

    def recommend(self):
        """生成完整的个性化睡眠优化建议。

        读取过去 14 天的睡眠、咖啡因和补剂数据，结合 health memory
        上下文，通过 LLM 生成全面的睡眠改善方案。
        """
        collected = self._collect_data(days=14)

        if not self._has_any_data(collected):
            self._no_data_message()
            return

        # Build data summary for LLM
        data_summary = (
            f"{collected['sleep_text']}\n"
            f"{collected['caffeine_text']}\n"
            f"{collected['supplement_text']}\n"
        )

        health_ctx = collected["health_context"]
        if health_ctx:
            data_summary += f"\n健康档案上下文：\n{health_ctx}\n"

        system_prompt = (
            "你是一位睡眠医学专家，精通咖啡因药代动力学和营养补剂。"
            "基于用户的睡眠数据、咖啡因摄入记录和补剂方案，给出个性化睡眠优化建议。\n\n"
            "请按以下结构输出建议：\n\n"
            "## 睡眠模式分析\n"
            "简要分析用户当前的睡眠模式、规律性和质量趋势。\n\n"
            "## 最佳入睡/起床时间建议\n"
            "基于观测到的用户睡眠模式，推荐最佳的入睡和起床时间窗口。\n\n"
            "## 个人化咖啡因截止时间\n"
            "基于咖啡因半衰期（约5-6小时）和用户的个人睡眠影响推断，"
            "给出每日咖啡因摄入的最晚时间建议。\n\n"
            "## 补剂服用时间优化\n"
            "如有相关补剂（如褪黑素、镁、GABA等），建议最佳服用时间以辅助睡眠。\n\n"
            "## 蓝光/屏幕截止时间\n"
            "根据建议的入睡时间，给出屏幕使用截止时间。\n\n"
            "## 睡前 routine 建议\n"
            "个性化的睡前放松流程建议。\n\n"
            "## 优先行动建议\n"
            "按优先级排序的具体行动建议（最多5条），标注预期影响程度。\n\n"
            "请用中文回答，保持专业但易懂。引用具体数据来支撑建议。"
        )

        user_prompt = f"以下是我的健康数据，请给出个性化睡眠优化建议：\n\n{data_summary}"

        print("正在分析睡眠数据并生成个性化建议...\n")
        result = _llm_call(system_prompt, user_prompt)
        print(result)

    # ---- bedtime ----

    def bedtime(self):
        """分析最佳入睡时间。

        简化版本：仅聚焦于最佳入睡时间分析，找出睡眠评分
        最高的夜晚的入睡时间模式。
        """
        collected = self._collect_data(days=14)

        if not collected["sleep_records"]:
            self._no_data_message()
            return

        data_summary = (
            f"{collected['sleep_text']}\n"
            f"{collected['caffeine_text']}\n"
        )

        system_prompt = (
            "你是一位睡眠医学专家。请仅聚焦于分析用户的最佳入睡时间。\n\n"
            "分析要求：\n"
            "1. 找出睡眠评分最高的那几晚的入睡时间模式\n"
            "2. 考虑咖啡因摄入对入睡时间的影响\n"
            "3. 给出一个具体的「最佳入睡时间窗口」（如 22:30-23:00）\n"
            "4. 解释推荐理由，引用具体数据\n\n"
            "请简洁回答，控制在 300 字以内。用中文回答。"
        )

        user_prompt = f"请分析我的最佳入睡时间：\n\n{data_summary}"

        print("正在分析最佳入睡时间...\n")
        result = _llm_call(system_prompt, user_prompt, max_tokens=1024)
        print(result)

    # ---- review ----

    def review(self, days: int = 30):
        """生成综合睡眠健康评估报告。

        读取指定天数的睡眠、咖啡因和补剂数据，通过 LLM 生成
        包含趋势分析、模式识别和月度对比（如有数据）的综合评估。

        Args:
            days: 回顾天数，默认 30 天。
        """
        collected = self._collect_data(days=days)

        if not self._has_any_data(collected):
            self._no_data_message()
            return

        data_summary = (
            f"{collected['sleep_text']}\n"
            f"{collected['caffeine_text']}\n"
            f"{collected['supplement_text']}\n"
        )

        health_ctx = collected["health_context"]
        if health_ctx:
            data_summary += f"\n健康档案上下文：\n{health_ctx}\n"

        system_prompt = (
            "你是一位睡眠医学专家。请基于用户提供的健康数据，"
            f"生成一份过去 {days} 天的综合睡眠健康评估报告。\n\n"
            "报告应包含以下部分：\n\n"
            "## 睡眠质量总览\n"
            "平均评分、总时长、效率等核心指标汇总。\n\n"
            "## 趋势分析\n"
            "睡眠质量是在改善、稳定还是下降？用数据说明。\n\n"
            "## 模式识别\n"
            "识别有价值的模式，如：\n"
            "- 工作日 vs 周末的睡眠差异\n"
            "- 咖啡因摄入量与睡眠质量的关联\n"
            "- 补剂使用与睡眠指标的关联\n"
            "- 入睡时间波动性\n\n"
            "## 关键发现\n"
            "最值得关注的 2-3 个发现。\n\n"
            "## 改善建议\n"
            "基于数据的具体改善建议（最多 3 条）。\n\n"
            "请用中文回答，保持专业但易懂。所有结论必须基于实际数据。"
        )

        user_prompt = (
            f"以下是我过去 {days} 天的健康数据，"
            f"请生成综合睡眠健康评估报告：\n\n{data_summary}"
        )

        print(f"正在生成过去 {days} 天的睡眠健康评估报告...\n")
        result = _llm_call(system_prompt, user_prompt)
        print(result)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="睡眠优化建议 - 基于多源健康数据生成个性化睡眠改善方案"
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # recommend
    sub.add_parser(
        "recommend",
        help="生成完整的个性化睡眠优化建议（睡眠+咖啡因+补剂综合分析）",
    )

    # bedtime
    sub.add_parser(
        "bedtime",
        help="分析最佳入睡时间",
    )

    # review
    p_review = sub.add_parser(
        "review",
        help="生成综合睡眠健康评估报告",
    )
    p_review.add_argument(
        "--days",
        type=int,
        default=30,
        help="回顾天数（默认 30）",
    )

    args = parser.parse_args()
    optimizer = SleepOptimizer()

    if args.command == "recommend":
        optimizer.recommend()
    elif args.command == "bedtime":
        optimizer.bedtime()
    elif args.command == "review":
        optimizer.review(days=args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
