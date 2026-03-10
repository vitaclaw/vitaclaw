#!/usr/bin/env python3
"""每周健康周报 -- 聚合多源健康数据，生成叙事性周报并写入 Health Memory。"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import requests

# ---------------------------------------------------------------------------
# Shared modules
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from health_data_store import HealthDataStore  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402
from cross_skill_reader import CrossSkillReader  # noqa: E402


# ---------------------------------------------------------------------------
# LLM helper (same pattern as tumor-journey-summary)
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
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"[LLM调用失败] {e}"


# ---------------------------------------------------------------------------
# WeeklyHealthDigest
# ---------------------------------------------------------------------------
class WeeklyHealthDigest:
    """聚合多源健康数据，生成叙事性周报并写入 Health Memory。

    数据来源（通过 CrossSkillReader）：
    - caffeine-tracker: 每日咖啡因摄入
    - sleep-analyzer: 睡眠会话记录
    - supplement-manager: 补剂服用日志
    - blood-pressure-tracker: 血压记录（如有）
    - medication-reminder: 用药记录（如有）
    """

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("weekly-health-digest", data_dir=data_dir)
        self.memory_writer = HealthMemoryWriter()
        self.reader = CrossSkillReader(data_dir=data_dir)

    # ------------------------------------------------------------------
    # Week range helper
    # ------------------------------------------------------------------

    def _get_week_range(self, week_of: str = None) -> tuple:
        """Return (week_start_iso, week_end_iso) for the Monday-Sunday week.

        Args:
            week_of: Optional date string YYYY-MM-DD. Defaults to the current
                     or most recent Monday.

        Returns:
            Tuple of (start_date_str, end_date_str) in YYYY-MM-DD format.
        """
        if week_of:
            try:
                ref = datetime.strptime(week_of, "%Y-%m-%d")
            except ValueError:
                print(f"[错误] 日期格式不正确: {week_of}，请使用 YYYY-MM-DD 格式")
                ref = datetime.now()
        else:
            ref = datetime.now()

        # Monday of that week (weekday 0 = Monday)
        monday = ref - timedelta(days=ref.weekday())
        sunday = monday + timedelta(days=6)

        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Aggregate metrics for a given week
    # ------------------------------------------------------------------

    def _compute_weekly_metrics(self, start: str, end: str) -> dict:
        """Read all data sources and compute aggregate metrics for [start, end].

        Args:
            start: Week start date YYYY-MM-DD (inclusive).
            end: Week end date YYYY-MM-DD (inclusive).

        Returns:
            Dict with keys: caffeine, sleep, supplements, blood_pressure,
            medication. Each sub-dict contains aggregate statistics.
        """
        # Timestamps for JSONL queries (start of start day, end of end day)
        ts_start = f"{start}T00:00:00"
        ts_end = f"{end}T23:59:59"

        metrics = {}

        # --- Caffeine ---
        caffeine_records = self.reader.read_caffeine_intakes(
            start=ts_start, end=ts_end
        )
        if caffeine_records:
            daily_totals = {}
            for rec in caffeine_records:
                data = rec.get("data", {})
                ts = rec.get("timestamp", "")[:10]
                mg = data.get("mg") or data.get("caffeine_mg") or 0
                try:
                    mg = float(mg)
                except (TypeError, ValueError):
                    mg = 0
                daily_totals[ts] = daily_totals.get(ts, 0) + mg

            daily_values = list(daily_totals.values())
            max_day_date = max(daily_totals, key=daily_totals.get) if daily_totals else None
            metrics["caffeine"] = {
                "daily_avg_mg": round(sum(daily_values) / len(daily_values), 1) if daily_values else 0,
                "max_day_mg": round(max(daily_values), 1) if daily_values else 0,
                "max_day_date": max_day_date,
                "total_intakes": len(caffeine_records),
                "days_tracked": len(daily_totals),
            }
        else:
            metrics["caffeine"] = None

        # --- Sleep ---
        sleep_records = self.reader.read_sleep_data(start=ts_start, end=ts_end)
        if sleep_records:
            scores = []
            durations = []
            efficiencies = []
            daily_sleep = {}
            for rec in sleep_records:
                data = rec.get("data", {})
                date_key = data.get("date") or rec.get("timestamp", "")[:10]

                score = data.get("score")
                if score is not None:
                    try:
                        score = float(score)
                        scores.append(score)
                        daily_sleep[date_key] = {"score": score}
                    except (TypeError, ValueError):
                        pass

                dur = data.get("total_min") or data.get("duration_min")
                if dur is not None:
                    try:
                        durations.append(float(dur))
                    except (TypeError, ValueError):
                        pass

                eff = data.get("efficiency_pct") or data.get("efficiency")
                if eff is not None:
                    try:
                        efficiencies.append(float(eff))
                    except (TypeError, ValueError):
                        pass

            best_night = max(daily_sleep, key=lambda d: daily_sleep[d]["score"]) if daily_sleep else None
            worst_night = min(daily_sleep, key=lambda d: daily_sleep[d]["score"]) if daily_sleep else None

            metrics["sleep"] = {
                "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
                "avg_duration_min": round(sum(durations) / len(durations), 1) if durations else None,
                "avg_efficiency": round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else None,
                "best_night": best_night,
                "worst_night": worst_night,
                "nights_tracked": len(sleep_records),
            }
        else:
            metrics["sleep"] = None

        # --- Supplements ---
        supplement_records = self.reader.read_supplement_doses(
            start=ts_start, end=ts_end
        )
        if supplement_records:
            per_supplement = {}
            for rec in supplement_records:
                data = rec.get("data", {})
                name = data.get("supplement") or data.get("name") or "unknown"
                taken = data.get("taken", True)
                if name not in per_supplement:
                    per_supplement[name] = {"taken": 0, "expected": 0}
                per_supplement[name]["expected"] += 1
                if taken:
                    per_supplement[name]["taken"] += 1

            total_taken = sum(s["taken"] for s in per_supplement.values())
            total_expected = sum(s["expected"] for s in per_supplement.values())
            overall_pct = round(100 * total_taken / total_expected, 1) if total_expected > 0 else 0

            per_supp_pct = {}
            for name, counts in per_supplement.items():
                pct = round(100 * counts["taken"] / counts["expected"], 1) if counts["expected"] > 0 else 0
                per_supp_pct[name] = {
                    "adherence_pct": pct,
                    "taken": counts["taken"],
                    "expected": counts["expected"],
                }

            metrics["supplements"] = {
                "overall_adherence_pct": overall_pct,
                "per_supplement": per_supp_pct,
                "total_doses": len(supplement_records),
            }
        else:
            metrics["supplements"] = None

        # --- Blood Pressure ---
        bp_records = self.reader.read_blood_pressure(start=ts_start, end=ts_end)
        if bp_records:
            systolics = []
            diastolics = []
            for rec in bp_records:
                data = rec.get("data", {})
                sys_val = data.get("systolic") or data.get("sys")
                dia_val = data.get("diastolic") or data.get("dia")
                if sys_val is not None:
                    try:
                        systolics.append(float(sys_val))
                    except (TypeError, ValueError):
                        pass
                if dia_val is not None:
                    try:
                        diastolics.append(float(dia_val))
                    except (TypeError, ValueError):
                        pass

            # Simple trend: compare first half vs second half averages
            trend_dir = "stable"
            if len(systolics) >= 4:
                mid = len(systolics) // 2
                first_half = sum(systolics[:mid]) / mid
                second_half = sum(systolics[mid:]) / (len(systolics) - mid)
                diff = second_half - first_half
                if diff > 3:
                    trend_dir = "rising"
                elif diff < -3:
                    trend_dir = "falling"

            metrics["blood_pressure"] = {
                "avg_systolic": round(sum(systolics) / len(systolics), 1) if systolics else None,
                "avg_diastolic": round(sum(diastolics) / len(diastolics), 1) if diastolics else None,
                "readings": len(bp_records),
                "trend": trend_dir,
            }
        else:
            metrics["blood_pressure"] = None

        # --- Medication ---
        med_records = self.reader.read_medication_doses(start=ts_start, end=ts_end)
        if med_records:
            total = len(med_records)
            taken = sum(
                1 for r in med_records if r.get("data", {}).get("taken", True)
            )
            metrics["medication"] = {
                "adherence_pct": round(100 * taken / total, 1) if total > 0 else 0,
                "doses_taken": taken,
                "doses_expected": total,
            }
        else:
            metrics["medication"] = None

        return metrics

    # ------------------------------------------------------------------
    # Format metrics for LLM consumption
    # ------------------------------------------------------------------

    def _format_metrics_for_llm(self, metrics: dict, prev_metrics: dict = None) -> str:
        """Format current and previous week metrics into readable text for the LLM.

        Args:
            metrics: Current week's metrics dict.
            prev_metrics: Previous week's metrics dict (optional).

        Returns:
            Formatted string describing the metrics and trends.
        """
        lines = []

        def _trend_arrow(current, previous):
            """Return trend indicator comparing current vs previous value."""
            if current is None or previous is None:
                return ""
            try:
                diff = float(current) - float(previous)
            except (TypeError, ValueError):
                return ""
            if abs(diff) < 0.5:
                return " (-> stable)"
            return f" ({'↑' if diff > 0 else '↓'} vs last week: {previous})"

        # Caffeine
        lines.append("## 咖啡因摄入")
        caff = metrics.get("caffeine")
        prev_caff = (prev_metrics or {}).get("caffeine")
        if caff:
            lines.append(f"- 日均摄入: {caff['daily_avg_mg']}mg"
                         + _trend_arrow(caff['daily_avg_mg'],
                                        prev_caff.get('daily_avg_mg') if prev_caff else None))
            lines.append(f"- 单日最高: {caff['max_day_mg']}mg ({caff.get('max_day_date', '?')})")
            lines.append(f"- 总摄入次数: {caff['total_intakes']}")
            lines.append(f"- 追踪天数: {caff['days_tracked']}")
        else:
            lines.append("- 本周无咖啡因数据")

        # Sleep
        lines.append("\n## 睡眠数据")
        slp = metrics.get("sleep")
        prev_slp = (prev_metrics or {}).get("sleep")
        if slp:
            if slp.get("avg_score") is not None:
                lines.append(f"- 平均睡眠评分: {slp['avg_score']}/100"
                             + _trend_arrow(slp['avg_score'],
                                            prev_slp.get('avg_score') if prev_slp else None))
            if slp.get("avg_duration_min") is not None:
                h, m = divmod(int(slp["avg_duration_min"]), 60)
                lines.append(f"- 平均睡眠时长: {h}h{m}m")
            if slp.get("avg_efficiency") is not None:
                lines.append(f"- 平均睡眠效率: {slp['avg_efficiency']}%"
                             + _trend_arrow(slp['avg_efficiency'],
                                            prev_slp.get('avg_efficiency') if prev_slp else None))
            if slp.get("best_night"):
                lines.append(f"- 最佳睡眠夜: {slp['best_night']}")
            if slp.get("worst_night"):
                lines.append(f"- 最差睡眠夜: {slp['worst_night']}")
            lines.append(f"- 追踪夜数: {slp['nights_tracked']}")
        else:
            lines.append("- 本周无睡眠数据")

        # Supplements
        lines.append("\n## 补剂服用")
        supp = metrics.get("supplements")
        prev_supp = (prev_metrics or {}).get("supplements")
        if supp:
            lines.append(f"- 整体依从率: {supp['overall_adherence_pct']}%"
                         + _trend_arrow(supp['overall_adherence_pct'],
                                        prev_supp.get('overall_adherence_pct') if prev_supp else None))
            per_s = supp.get("per_supplement", {})
            if per_s:
                lines.append("- 分项:")
                for name, info in per_s.items():
                    lines.append(f"  - {name}: {info['adherence_pct']}% "
                                 f"({info['taken']}/{info['expected']})")
        else:
            lines.append("- 本周无补剂数据")

        # Blood pressure
        bp = metrics.get("blood_pressure")
        prev_bp = (prev_metrics or {}).get("blood_pressure")
        if bp:
            lines.append("\n## 血压")
            if bp.get("avg_systolic") is not None:
                lines.append(f"- 平均: {bp['avg_systolic']}/{bp.get('avg_diastolic', '?')} mmHg"
                             + _trend_arrow(bp['avg_systolic'],
                                            prev_bp.get('avg_systolic') if prev_bp else None))
            lines.append(f"- 测量次数: {bp['readings']}")
            lines.append(f"- 趋势: {bp['trend']}")

        # Medication
        med = metrics.get("medication")
        prev_med = (prev_metrics or {}).get("medication")
        if med:
            lines.append("\n## 用药")
            lines.append(f"- 依从率: {med['adherence_pct']}%"
                         + _trend_arrow(med['adherence_pct'],
                                        prev_med.get('adherence_pct') if prev_med else None))
            lines.append(f"- 服药/应服: {med['doses_taken']}/{med['doses_expected']}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # generate
    # ------------------------------------------------------------------

    def generate(self, week_of: str = None):
        """Generate the weekly health digest for the specified week.

        Args:
            week_of: Optional date string YYYY-MM-DD (any day in the target
                     week). Defaults to current/most-recent Monday.
        """
        week_start, week_end = self._get_week_range(week_of)
        print(f"生成周报: {week_start} ~ {week_end}")

        # Compute current week metrics
        metrics = self._compute_weekly_metrics(week_start, week_end)

        # Check if there is any data at all
        has_data = any(v is not None for v in metrics.values())
        if not has_data:
            print(f"\n本周 ({week_start} ~ {week_end}) 无任何健康数据。")
            print("请先使用以下技能记录数据:")
            print("  - caffeine-tracker: 咖啡因摄入")
            print("  - sleep-analyzer: 睡眠数据")
            print("  - supplement-manager: 补剂服用")
            print("  - blood-pressure-tracker: 血压记录")
            print("  - medication-reminder: 用药记录")
            return

        # Compute previous week metrics for comparison
        prev_start_dt = datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=7)
        prev_end_dt = datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=1)
        prev_start = prev_start_dt.strftime("%Y-%m-%d")
        prev_end = prev_end_dt.strftime("%Y-%m-%d")

        # Try loading previous digest from store first
        prev_metrics = None
        prev_digests = self.store.query(record_type="digest")
        for d in reversed(prev_digests):
            if d.get("data", {}).get("week_start") == prev_start:
                prev_metrics = d["data"].get("metrics")
                break

        # If no stored previous digest, recompute
        if prev_metrics is None:
            prev_metrics = self._compute_weekly_metrics(prev_start, prev_end)
            prev_has_data = any(v is not None for v in prev_metrics.values())
            if not prev_has_data:
                prev_metrics = None

        # Format for LLM
        metrics_text = self._format_metrics_for_llm(metrics, prev_metrics)

        # LLM system prompt
        system_prompt = (
            "你是一位健康数据分析师。根据用户本周的健康数据生成一份简洁的中文周报。\n\n"
            "请严格使用以下格式输出：\n\n"
            f"# 健康周报 -- {week_start} ~ {week_end}\n\n"
            "## 本周亮点\n"
            "- (列出 2-4 条值得关注的健康行为亮点或成就)\n\n"
            "## 数据概览\n"
            "| 指标 | 本周 | 上周 | 趋势 |\n"
            "|------|------|------|------|\n"
            "(填入关键指标的对比表格，趋势用箭头表示)\n\n"
            "## 预警\n"
            "- (列出需要注意的健康风险或异常数据，如无则写 '本周无预警')\n\n"
            "## 建议\n"
            "- (给出 2-4 条具体可执行的改善建议)\n\n"
            "注意事项：\n"
            "- 如果某项数据缺失，在表格中标注 '无数据'\n"
            "- 趋势箭头: 改善用 ↑，下降用 ↓，稳定用 →\n"
            "- 建议要具体、可执行，不要泛泛而谈\n"
            "- 预警需要有数据支撑，不要凭空猜测\n"
            "- 保持简洁，总字数控制在 500 字以内"
        )

        user_prompt = f"以下是我本周的健康数据统计：\n\n{metrics_text}"

        print("正在使用 LLM 生成周报...")
        digest_content = _llm_call(system_prompt, user_prompt)

        if digest_content.startswith("[错误]") or digest_content.startswith("[LLM调用失败]"):
            print(f"  {digest_content}")
            return

        # Print the generated digest
        print("\n" + "=" * 60)
        print(digest_content)
        print("=" * 60)

        # Store digest in JSONL
        self.store.append(
            "digest",
            {
                "week_start": week_start,
                "week_end": week_end,
                "metrics": metrics,
                "content": digest_content,
                "generated_at": datetime.now().isoformat(),
            },
            note=f"周报 {week_start} ~ {week_end}",
        )

        # Write to memory
        self.memory_writer.update_weekly_digest(digest_content)
        print(f"\n已保存周报并更新 Health Memory (memory/health/weekly-digest.md)")

    # ------------------------------------------------------------------
    # view
    # ------------------------------------------------------------------

    def view(self, week_of: str = None):
        """Display a previously generated digest.

        Args:
            week_of: Optional date string YYYY-MM-DD. If not specified,
                     shows the most recent digest.
        """
        digests = self.store.query(record_type="digest")
        if not digests:
            print("尚无已生成的周报。")
            print("  请先运行: python weekly_health_digest.py generate")
            return

        if week_of:
            week_start, week_end = self._get_week_range(week_of)
            target = None
            for d in digests:
                if d.get("data", {}).get("week_start") == week_start:
                    target = d
                    break
            if not target:
                print(f"未找到 {week_start} ~ {week_end} 的周报。")
                print("已有周报:")
                for d in digests:
                    ws = d.get("data", {}).get("week_start", "?")
                    we = d.get("data", {}).get("week_end", "?")
                    print(f"  - {ws} ~ {we}")
                print(f"\n可运行: python weekly_health_digest.py generate --week-of {week_start}")
                return
        else:
            target = digests[-1]

        content = target.get("data", {}).get("content", "")
        ws = target.get("data", {}).get("week_start", "?")
        we = target.get("data", {}).get("week_end", "?")
        gen_at = target.get("data", {}).get("generated_at", "?")

        print(f"周报: {ws} ~ {we} (生成于 {gen_at[:16] if len(gen_at) > 16 else gen_at})")
        print("=" * 60)
        print(content)
        print("=" * 60)

    # ------------------------------------------------------------------
    # trend
    # ------------------------------------------------------------------

    def trend(self, weeks: int = 4):
        """Show multi-week trend comparison table.

        Args:
            weeks: Number of weeks to compare (default: 4).
        """
        today = datetime.now()
        # Start from the most recent Monday
        current_monday = today - timedelta(days=today.weekday())

        weekly_data = []
        for i in range(weeks):
            monday = current_monday - timedelta(weeks=i)
            sunday = monday + timedelta(days=6)
            start = monday.strftime("%Y-%m-%d")
            end = sunday.strftime("%Y-%m-%d")

            metrics = self._compute_weekly_metrics(start, end)
            has_data = any(v is not None for v in metrics.values())

            weekly_data.append({
                "week": f"{start}",
                "start": start,
                "end": end,
                "metrics": metrics,
                "has_data": has_data,
            })

        # Reverse so oldest is first
        weekly_data.reverse()

        # Check if any week has data
        if not any(w["has_data"] for w in weekly_data):
            print(f"最近 {weeks} 周无任何健康数据。")
            return

        # Print trend table
        print(f"\n健康趋势对比 (最近 {weeks} 周)")
        print("=" * 80)

        # Header
        header = f"{'指标':<24}"
        for w in weekly_data:
            header += f" {w['week']:>12}"
        print(header)
        print("-" * 80)

        # Caffeine - daily avg
        row = f"{'咖啡因 日均(mg)':<24}"
        for w in weekly_data:
            caff = w["metrics"].get("caffeine")
            val = f"{caff['daily_avg_mg']}" if caff else "-"
            row += f" {val:>12}"
        print(row)

        # Sleep - avg score
        row = f"{'睡眠评分 均值':<24}"
        for w in weekly_data:
            slp = w["metrics"].get("sleep")
            val = f"{slp['avg_score']}" if slp and slp.get("avg_score") is not None else "-"
            row += f" {val:>12}"
        print(row)

        # Sleep - avg duration
        row = f"{'睡眠时长 均值(min)':<24}"
        for w in weekly_data:
            slp = w["metrics"].get("sleep")
            val = f"{slp['avg_duration_min']}" if slp and slp.get("avg_duration_min") is not None else "-"
            row += f" {val:>12}"
        print(row)

        # Supplement adherence
        row = f"{'补剂依从率(%)':<24}"
        for w in weekly_data:
            supp = w["metrics"].get("supplements")
            val = f"{supp['overall_adherence_pct']}" if supp else "-"
            row += f" {val:>12}"
        print(row)

        # Blood pressure (if any week has it)
        has_bp = any(w["metrics"].get("blood_pressure") is not None for w in weekly_data)
        if has_bp:
            row = f"{'血压 收缩压均值':<24}"
            for w in weekly_data:
                bp = w["metrics"].get("blood_pressure")
                val = f"{bp['avg_systolic']}" if bp and bp.get("avg_systolic") is not None else "-"
                row += f" {val:>12}"
            print(row)

        # Medication adherence (if any week has it)
        has_med = any(w["metrics"].get("medication") is not None for w in weekly_data)
        if has_med:
            row = f"{'用药依从率(%)':<24}"
            for w in weekly_data:
                med = w["metrics"].get("medication")
                val = f"{med['adherence_pct']}" if med else "-"
                row += f" {val:>12}"
            print(row)

        print("=" * 80)

        # Compute simple trend indicators for the most recent two weeks with data
        data_weeks = [w for w in weekly_data if w["has_data"]]
        if len(data_weeks) >= 2:
            latest = data_weeks[-1]["metrics"]
            prev = data_weeks[-2]["metrics"]
            print("\n趋势摘要:")
            indicators = []

            # Caffeine trend
            if latest.get("caffeine") and prev.get("caffeine"):
                curr_val = latest["caffeine"]["daily_avg_mg"]
                prev_val = prev["caffeine"]["daily_avg_mg"]
                diff = curr_val - prev_val
                if abs(diff) < 5:
                    indicators.append(f"  咖啡因摄入 → 稳定 ({curr_val}mg/日)")
                elif diff > 0:
                    indicators.append(f"  咖啡因摄入 ↑ 增加 ({prev_val} -> {curr_val}mg/日)")
                else:
                    indicators.append(f"  咖啡因摄入 ↓ 减少 ({prev_val} -> {curr_val}mg/日)")

            # Sleep trend
            if (latest.get("sleep") and latest["sleep"].get("avg_score") is not None
                    and prev.get("sleep") and prev["sleep"].get("avg_score") is not None):
                curr_val = latest["sleep"]["avg_score"]
                prev_val = prev["sleep"]["avg_score"]
                diff = curr_val - prev_val
                if abs(diff) < 2:
                    indicators.append(f"  睡眠质量 → 稳定 (评分 {curr_val})")
                elif diff > 0:
                    indicators.append(f"  睡眠质量 ↑ 改善 ({prev_val} -> {curr_val})")
                else:
                    indicators.append(f"  睡眠质量 ↓ 下降 ({prev_val} -> {curr_val})")

            # Supplement trend
            if latest.get("supplements") and prev.get("supplements"):
                curr_val = latest["supplements"]["overall_adherence_pct"]
                prev_val = prev["supplements"]["overall_adherence_pct"]
                diff = curr_val - prev_val
                if abs(diff) < 3:
                    indicators.append(f"  补剂依从 → 稳定 ({curr_val}%)")
                elif diff > 0:
                    indicators.append(f"  补剂依从 ↑ 提升 ({prev_val}% -> {curr_val}%)")
                else:
                    indicators.append(f"  补剂依从 ↓ 下降 ({prev_val}% -> {curr_val}%)")

            if indicators:
                for ind in indicators:
                    print(ind)
            else:
                print("  数据不足，无法计算趋势")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="每周健康周报 - 聚合多源健康数据，生成叙事性周报"
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # generate
    p_gen = sub.add_parser("generate", help="生成本周周报")
    p_gen.add_argument(
        "--week-of",
        default=None,
        help="目标周内任意日期 (YYYY-MM-DD)，默认为本周",
    )

    # view
    p_view = sub.add_parser("view", help="查看已生成的周报")
    p_view.add_argument(
        "--week-of",
        default=None,
        help="目标周内任意日期 (YYYY-MM-DD)，默认为最近一期",
    )

    # trend
    p_trend = sub.add_parser("trend", help="显示多周趋势对比")
    p_trend.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="对比周数 (默认: 4)",
    )

    args = parser.parse_args()
    digest = WeeklyHealthDigest()

    if args.command == "generate":
        digest.generate(week_of=args.week_of)
    elif args.command == "view":
        digest.view(week_of=args.week_of)
    elif args.command == "trend":
        digest.trend(weeks=args.weeks)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
