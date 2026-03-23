#!/usr/bin/env python3
"""血压趋势分析 - 记录血压并自动分级，支持晨峰检测、血压日记、月度统计和趋势图。"""

import argparse
import json
import math
import os
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore


# ---------------------------------------------------------------------------
# plot_trend - Generate trend line chart PNG
# ---------------------------------------------------------------------------

def plot_trend(values, dates, title, ylabel, ref_lines=None, output_path=None):
    """Generate trend line chart PNG."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, values, marker="o", linewidth=2, markersize=4)
    if ref_lines:
        for ref in ref_lines:
            ax.axhline(y=ref["value"], color=ref.get("color", "red"),
                       linestyle="--", label=ref["label"], alpha=0.7)
    ax.set_title(title, fontsize=14)
    ax.set_ylabel(ylabel)
    if ref_lines:
        ax.legend(loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    path = output_path or f"{title}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# BloodPressureTracker
# ---------------------------------------------------------------------------

class BloodPressureTracker:
    """血压趋势分析：记录、分级、晨峰检测、日记和统计。"""

    # WHO/ISH classification thresholds
    CLASSIFICATIONS = [
        ("normal", "正常", 120, 80),
        ("normal_high", "正常高值", 140, 90),
        ("grade1", "1级高血压", 160, 100),
        ("grade2", "2级高血压", 999, 999),
    ]

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("blood-pressure-tracker", data_dir=data_dir)

    # ----- classify -----

    def classify(self, systolic: int, diastolic: int) -> dict:
        """Classify BP reading per WHO guidelines.

        Returns dict with code, label_cn, and description.
        """
        if systolic < 120 and diastolic < 80:
            return {"code": "normal", "label": "正常", "description": "收缩压<120 且 舒张压<80 mmHg"}
        elif systolic < 140 and diastolic < 90:
            return {"code": "normal_high", "label": "正常高值", "description": "收缩压 120-139 或 舒张压 80-89 mmHg"}
        elif systolic < 160 and diastolic < 100:
            return {"code": "grade1", "label": "1级高血压", "description": "收缩压 140-159 或 舒张压 90-99 mmHg"}
        else:
            return {"code": "grade2", "label": "2级高血压", "description": "收缩压≥160 或 舒张压≥100 mmHg"}

    # ----- flag_urgent -----

    def flag_urgent(self, systolic: int, diastolic: int) -> bool:
        """Returns True if hypertensive crisis (>=180/120)."""
        return systolic >= 180 or diastolic >= 120

    # ----- record -----

    def record(self, systolic: int, diastolic: int, hr: int = None,
               context: str = "", arm: str = "", position: str = "") -> dict:
        """Record a BP reading and auto-classify.

        Args:
            systolic: systolic pressure (mmHg)
            diastolic: diastolic pressure (mmHg)
            hr: heart rate (bpm), optional
            context: e.g. "morning", "evening", "before_med"
            arm: "left" or "right"
            position: "sitting", "standing", "supine"
        """
        grade = self.classify(systolic, diastolic)
        urgent = self.flag_urgent(systolic, diastolic)

        data = {
            "sys": systolic,
            "dia": diastolic,
            "grade": grade["code"],
            "context": context,
            "arm": arm,
            "position": position,
        }
        if hr is not None:
            data["hr"] = hr

        record = self.store.append("bp", data, note=grade["label"])

        print(f"[记录成功] {systolic}/{diastolic} mmHg" + (f" HR:{hr}" if hr else ""))
        print(f"  分级: {grade['label']} ({grade['description']})")
        if context:
            print(f"  时段: {context}")
        if arm:
            print(f"  测量臂: {arm}")
        if urgent:
            print(f"  [!!!紧急!!!] 血压极高 ({systolic}/{diastolic})，疑似高血压危象，请立即就医！")

        return record

    # ----- detect_morning_surge -----

    def detect_morning_surge(self, days: int = 14) -> dict:
        """Compare morning vs evening readings to detect morning surge.

        Morning surge = morning mean - evening mean. >35 mmHg is clinically significant.
        """
        start = (datetime.now() - timedelta(days=days)).isoformat()
        records = self.store.query(record_type="bp", start=start)

        morning = [r for r in records if r["data"].get("context") in ("morning", "晨起", "am")]
        evening = [r for r in records if r["data"].get("context") in ("evening", "晚间", "pm", "bedtime", "睡前")]

        result = {
            "morning_count": len(morning),
            "evening_count": len(evening),
            "morning_surge": None,
            "significant": False,
            "message": "",
        }

        if len(morning) < 2 or len(evening) < 2:
            result["message"] = f"数据不足：晨间 {len(morning)} 条，晚间 {len(evening)} 条，需各至少 2 条"
            print(f"\n=== 晨峰血压检测 (近 {days} 天) ===")
            print(f"  {result['message']}")
            return result

        m_sys_mean = sum(r["data"]["sys"] for r in morning) / len(morning)
        e_sys_mean = sum(r["data"]["sys"] for r in evening) / len(evening)
        surge = m_sys_mean - e_sys_mean

        result["morning_sys_mean"] = round(m_sys_mean, 1)
        result["evening_sys_mean"] = round(e_sys_mean, 1)
        result["morning_surge"] = round(surge, 1)
        result["significant"] = surge > 35

        if result["significant"]:
            result["message"] = f"检测到晨峰血压: 晨间均值 {m_sys_mean:.1f} - 晚间均值 {e_sys_mean:.1f} = 差值 {surge:.1f} mmHg (>35 mmHg，有临床意义)"
        else:
            result["message"] = f"晨峰血压正常: 晨间均值 {m_sys_mean:.1f} - 晚间均值 {e_sys_mean:.1f} = 差值 {surge:.1f} mmHg"

        print(f"\n=== 晨峰血压检测 (近 {days} 天) ===")
        print(f"  {result['message']}")
        return result

    # ----- generate_bp_diary -----

    def generate_bp_diary(self, days: int = 14) -> str:
        """Generate a two-week BP diary table."""
        start = (datetime.now() - timedelta(days=days)).isoformat()
        records = self.store.query(record_type="bp", start=start)

        lines = [
            f"=== 血压日记 (近 {days} 天) ===\n",
            f"{'日期':<12} {'时间':<6} {'收缩压':>6} {'舒张压':>6} {'心率':>4} {'分级':<10} {'时段':<8}",
            "-" * 65,
        ]

        grade_labels = {
            "normal": "正常",
            "normal_high": "正常高值",
            "grade1": "1级",
            "grade2": "2级",
        }

        for r in records:
            ts = r["timestamp"]
            date_str = ts[:10]
            time_str = ts[11:16]
            d = r["data"]
            sys_val = d.get("sys", "")
            dia_val = d.get("dia", "")
            hr_val = d.get("hr", "-")
            grade = grade_labels.get(d.get("grade", ""), d.get("grade", ""))
            ctx = d.get("context", "")
            lines.append(f"{date_str:<12} {time_str:<6} {sys_val:>6} {dia_val:>6} {str(hr_val):>4} {grade:<10} {ctx:<8}")

        if not records:
            lines.append("  暂无记录")

        lines.append(f"\n共 {len(records)} 条记录")
        diary = "\n".join(lines)
        print(diary)
        return diary

    # ----- statistics -----

    def statistics(self, days: int = 30) -> dict:
        """Monthly statistics: mean+-SD, morning surge, grade distribution."""
        start = (datetime.now() - timedelta(days=days)).isoformat()
        records = self.store.query(record_type="bp", start=start)

        if not records:
            print(f"\n最近 {days} 天无血压记录。")
            return {"count": 0}

        sys_vals = [r["data"]["sys"] for r in records if r["data"].get("sys") is not None]
        dia_vals = [r["data"]["dia"] for r in records if r["data"].get("dia") is not None]
        hr_vals = [r["data"]["hr"] for r in records if r["data"].get("hr") is not None]

        def mean_sd(vals):
            if not vals:
                return None, None
            m = sum(vals) / len(vals)
            if len(vals) < 2:
                return round(m, 1), 0
            var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
            return round(m, 1), round(math.sqrt(var), 1)

        sys_mean, sys_sd = mean_sd(sys_vals)
        dia_mean, dia_sd = mean_sd(dia_vals)
        hr_mean, hr_sd = mean_sd(hr_vals)

        # Grade distribution
        grades = [r["data"].get("grade", "unknown") for r in records]
        grade_dist = {}
        for g in grades:
            grade_dist[g] = grade_dist.get(g, 0) + 1

        # Morning surge
        surge_info = self.detect_morning_surge(days=days)

        stats = {
            "count": len(records),
            "sys_mean": sys_mean,
            "sys_sd": sys_sd,
            "dia_mean": dia_mean,
            "dia_sd": dia_sd,
            "hr_mean": hr_mean,
            "hr_sd": hr_sd,
            "grade_distribution": grade_dist,
            "morning_surge": surge_info,
            "sys_max": max(sys_vals) if sys_vals else None,
            "sys_min": min(sys_vals) if sys_vals else None,
            "dia_max": max(dia_vals) if dia_vals else None,
            "dia_min": min(dia_vals) if dia_vals else None,
        }

        grade_labels = {
            "normal": "正常",
            "normal_high": "正常高值",
            "grade1": "1级高血压",
            "grade2": "2级高血压",
        }

        print(f"\n=== 血压统计 (近 {days} 天, 共 {len(records)} 条) ===")
        print(f"  收缩压: {sys_mean}±{sys_sd} mmHg (范围 {stats['sys_min']}-{stats['sys_max']})")
        print(f"  舒张压: {dia_mean}±{dia_sd} mmHg (范围 {stats['dia_min']}-{stats['dia_max']})")
        if hr_mean is not None:
            print(f"  心率:   {hr_mean}±{hr_sd} bpm")
        print(f"\n  分级分布:")
        for code, count in sorted(grade_dist.items()):
            label = grade_labels.get(code, code)
            pct = count / len(records) * 100
            print(f"    {label}: {count} 次 ({pct:.0f}%)")

        return stats

    # ----- generate_chart -----

    def generate_chart(self, days: int = 30) -> str:
        """Dual-line chart (systolic + diastolic) with 140/90 reference lines."""
        start = (datetime.now() - timedelta(days=days)).isoformat()
        records = self.store.query(record_type="bp", start=start)

        if len(records) < 2:
            print("数据不足，至少需要 2 条记录来生成图表。")
            return ""

        dates = [datetime.fromisoformat(r["timestamp"]) for r in records]
        sys_vals = [r["data"]["sys"] for r in records]
        dia_vals = [r["data"]["dia"] for r in records]

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(dates, sys_vals, marker="o", linewidth=2, markersize=4,
                color="#e74c3c", label="收缩压 (SYS)")
        ax.plot(dates, dia_vals, marker="s", linewidth=2, markersize=4,
                color="#3498db", label="舒张压 (DIA)")

        # Reference lines
        ax.axhline(y=140, color="red", linestyle="--", alpha=0.5, label="高血压线 140")
        ax.axhline(y=90, color="orange", linestyle="--", alpha=0.5, label="高血压线 90")
        ax.axhline(y=120, color="green", linestyle="--", alpha=0.3, label="正常上限 120")
        ax.axhline(y=80, color="green", linestyle="--", alpha=0.3, label="正常上限 80")

        ax.set_title(f"血压趋势 (近 {days} 天)", fontsize=14)
        ax.set_ylabel("mmHg")
        ax.legend(loc="upper right", fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()

        chart_path = os.path.join(self.store.charts_dir, f"bp_trend_{days}d.png")
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"血压趋势图已保存: {chart_path}")
        return chart_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="血压趋势分析")
    sub = parser.add_subparsers(dest="command")

    # record
    p_rec = sub.add_parser("record", help="记录血压")
    p_rec.add_argument("systolic", type=int, help="收缩压 (mmHg)")
    p_rec.add_argument("diastolic", type=int, help="舒张压 (mmHg)")
    p_rec.add_argument("hr", type=int, nargs="?", default=None, help="心率 (bpm)")
    p_rec.add_argument("--context", default="", help="时段 (morning/evening)")
    p_rec.add_argument("--arm", default="", help="测量臂 (left/right)")
    p_rec.add_argument("--position", default="", help="体位 (sitting/standing/supine)")
    p_rec.add_argument("--data-dir", default=None, help="数据目录")

    # diary
    p_diary = sub.add_parser("diary", help="血压日记")
    p_diary.add_argument("--days", type=int, default=14, help="天数")
    p_diary.add_argument("--data-dir", default=None, help="数据目录")

    # stats
    p_stats = sub.add_parser("stats", help="月度统计")
    p_stats.add_argument("--days", type=int, default=30, help="天数")
    p_stats.add_argument("--data-dir", default=None, help="数据目录")

    # chart
    p_chart = sub.add_parser("chart", help="生成趋势图")
    p_chart.add_argument("--days", type=int, default=30, help="天数")
    p_chart.add_argument("--data-dir", default=None, help="数据目录")

    # surge
    p_surge = sub.add_parser("surge", help="晨峰血压检测")
    p_surge.add_argument("--days", type=int, default=14, help="天数")
    p_surge.add_argument("--data-dir", default=None, help="数据目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = BloodPressureTracker(data_dir=getattr(args, "data_dir", None))

    if args.command == "record":
        tracker.record(args.systolic, args.diastolic, hr=args.hr,
                       context=args.context, arm=args.arm, position=args.position)
    elif args.command == "diary":
        tracker.generate_bp_diary(days=args.days)
    elif args.command == "stats":
        tracker.statistics(days=args.days)
    elif args.command == "chart":
        tracker.generate_chart(days=args.days)
    elif args.command == "surge":
        tracker.detect_morning_surge(days=args.days)


if __name__ == "__main__":
    main()
