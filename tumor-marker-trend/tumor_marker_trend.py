#!/usr/bin/env python3
"""肿瘤标志物趋势 - 记录CEA/CA199/AFP等肿瘤标志物，支持趋势分析和突增检测。"""

import argparse
import json
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
# Reference ranges
# ---------------------------------------------------------------------------
MARKER_REFERENCES = {
    "CEA": {"upper": 5.0, "unit": "ng/mL", "name": "癌胚抗原"},
    "CA199": {"upper": 37.0, "unit": "U/mL", "name": "糖类抗原199"},
    "CA125": {"upper": 35.0, "unit": "U/mL", "name": "糖类抗原125"},
    "AFP": {"upper": 7.0, "unit": "ng/mL", "name": "甲胎蛋白"},
    "PSA": {"upper": 4.0, "unit": "ng/mL", "name": "前列腺特异性抗原"},
    "CA153": {"upper": 25.0, "unit": "U/mL", "name": "糖类抗原153"},
    "CA724": {"upper": 6.9, "unit": "U/mL", "name": "糖类抗原724"},
    "NSE": {"upper": 16.3, "unit": "ng/mL", "name": "神经元特异性烯醇化酶"},
    "CYFRA211": {"upper": 3.3, "unit": "ng/mL", "name": "细胞角蛋白19片段"},
    "SCC": {"upper": 1.5, "unit": "ng/mL", "name": "鳞状细胞癌抗原"},
    "HE4": {"upper": 140.0, "unit": "pmol/L", "name": "人附睾蛋白4"},
    "TPSA": {"upper": 4.0, "unit": "ng/mL", "name": "总前列腺特异抗原"},
    "ferritin": {"upper": 400.0, "unit": "ng/mL", "name": "铁蛋白"},
}


# ---------------------------------------------------------------------------
# Plot helper
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
# TumorMarkerTrend
# ---------------------------------------------------------------------------
class TumorMarkerTrend:
    """肿瘤标志物趋势追踪器。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("tumor-marker-trend", data_dir=data_dir)

    # ----- record -----
    def record(self, marker: str, value: float, unit: str = None,
               lab_date: str = None, treatment_context: str = "", note: str = "") -> dict:
        """记录一次肿瘤标志物检测值。

        Args:
            marker: 标志物名称，如 CEA, CA199
            value: 检测值
            unit: 单位（不提供则从参考范围自动获取）
            lab_date: 检验日期 YYYY-MM-DD（不提供则用当前时间）
            treatment_context: 治疗背景，如"奥沙利铂第4周期"
            note: 备注
        """
        marker_upper = marker.upper() if marker.upper() in MARKER_REFERENCES else marker
        ref = MARKER_REFERENCES.get(marker_upper)

        if unit is None and ref:
            unit = ref["unit"]

        data = {
            "marker": marker_upper,
            "value": value,
            "unit": unit or "",
            "lab_date": lab_date or datetime.now().strftime("%Y-%m-%d"),
            "treatment_context": treatment_context,
        }
        rec = self.store.append("marker", data, note=note)

        # Status vs reference
        status = ""
        if ref:
            if value > ref["upper"]:
                ratio = value / ref["upper"]
                status = f"↑ 超参考上限 ({ratio:.1f}x)"
            else:
                status = "✅ 正常范围内"

        marker_name = ref["name"] if ref else marker_upper
        print(f"✅ 已记录 {marker_name} ({marker_upper}): {value} {unit or ''}")
        if status:
            print(f"   {status}  (参考上限: {ref['upper']} {ref['unit']})")
        if treatment_context:
            print(f"   治疗背景: {treatment_context}")

        return rec

    # ----- trend -----
    def trend(self, marker: str, months: int = 6) -> dict:
        """分析特定标志物的趋势。"""
        marker_upper = marker.upper() if marker.upper() in MARKER_REFERENCES else marker
        records = self.store.query(record_type="marker")
        records = [r for r in records if r["data"].get("marker") == marker_upper]

        cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
        records = [r for r in records if r["timestamp"] >= cutoff]

        if not records:
            print(f"📭 无 {marker_upper} 在近{months}个月的记录")
            return {"marker": marker_upper, "values": [], "direction": "no_data"}

        values = [r["data"]["value"] for r in records]
        dates = [r["data"].get("lab_date", r["timestamp"][:10]) for r in records]
        ref = MARKER_REFERENCES.get(marker_upper)

        # Trend calculation
        if len(values) >= 2:
            mean_val = sum(values) / len(values)
            n = len(values)
            x_mean = (n - 1) / 2
            numerator = sum((i - x_mean) * (v - mean_val) for i, v in enumerate(values))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator else 0
            direction = "rising" if slope > 0.01 else ("falling" if slope < -0.01 else "stable")
        else:
            mean_val = values[0]
            slope = 0
            direction = "insufficient_data"

        direction_cn = {"rising": "↑上升", "falling": "↓下降", "stable": "→稳定", "insufficient_data": "数据不足"}.get(direction, direction)
        marker_name = ref["name"] if ref else marker_upper

        print(f"\n📊 {marker_name} ({marker_upper}) 趋势分析 - 近{months}个月")
        print(f"   数据点: {len(values)}")
        print(f"   最新值: {values[-1]} {ref['unit'] if ref else ''}")
        print(f"   均  值: {round(mean_val, 2)}")
        print(f"   趋  势: {direction_cn} (斜率: {round(slope, 4)})")
        if ref:
            print(f"   参考上限: {ref['upper']} {ref['unit']}")
            above_count = sum(1 for v in values if v > ref["upper"])
            print(f"   超标次数: {above_count}/{len(values)}")

        print(f"\n   {'日期':<14} {'数值':<12} {'状态'}")
        print("   " + "-" * 40)
        for d, v in zip(dates, values):
            if ref and v > ref["upper"]:
                st = f"↑ {v / ref['upper']:.1f}x"
            else:
                st = "正常"
            print(f"   {d:<14} {v:<12} {st}")

        # Generate chart
        chart_path = self.generate_chart(marker_upper, months)

        return {
            "marker": marker_upper,
            "values": values,
            "dates": dates,
            "mean": round(mean_val, 2),
            "slope": round(slope, 4),
            "direction": direction,
            "chart": chart_path,
        }

    # ----- detect_surge -----
    def detect_surge(self, marker: str = None, threshold_pct: float = 20) -> list:
        """检测标志物是否突增（最新值较前一次升高超过阈值百分比）。"""
        records = self.store.query(record_type="marker")
        if not records:
            print("📭 暂无标志物记录")
            return []

        # Group by marker
        by_marker = {}
        for r in records:
            m = r["data"]["marker"]
            by_marker.setdefault(m, []).append(r)

        if marker:
            marker_upper = marker.upper() if marker.upper() in MARKER_REFERENCES else marker
            by_marker = {k: v for k, v in by_marker.items() if k == marker_upper}

        surges = []
        print(f"\n🔍 突增检测 (阈值: {threshold_pct}%)")
        print(f"{'标志物':<12} {'前一次':<12} {'最新值':<12} {'变化率':<12} {'状态'}")
        print("-" * 60)

        for m_name, recs in sorted(by_marker.items()):
            values = [r["data"]["value"] for r in recs]
            if len(values) < 2:
                print(f"{m_name:<12} {'--':<12} {values[-1]:<12} {'--':<12} 数据不足")
                continue

            prev = values[-2]
            latest = values[-1]
            if prev == 0:
                pct_change = float("inf") if latest > 0 else 0
            else:
                pct_change = ((latest - prev) / prev) * 100

            is_surge = pct_change > threshold_pct
            status = f"⚠ 突增 +{pct_change:.1f}%" if is_surge else f"✅ {pct_change:+.1f}%"

            ref = MARKER_REFERENCES.get(m_name)
            unit = ref["unit"] if ref else ""

            print(f"{m_name:<12} {prev:<12} {latest:<12} {pct_change:+.1f}%{'':>5} {status}")

            if is_surge:
                surges.append({
                    "marker": m_name,
                    "previous": prev,
                    "latest": latest,
                    "pct_change": round(pct_change, 1),
                    "unit": unit,
                })

        if not surges:
            print("\n✅ 未检测到标志物突增")
        else:
            print(f"\n⚠ 检测到 {len(surges)} 个标志物突增，建议关注")

        return surges

    # ----- compare_markers -----
    def compare_markers(self) -> list:
        """对比所有已记录标志物的最新值和趋势。"""
        records = self.store.query(record_type="marker")
        if not records:
            print("📭 暂无标志物记录")
            return []

        by_marker = {}
        for r in records:
            m = r["data"]["marker"]
            by_marker.setdefault(m, []).append(r)

        print(f"\n📋 肿瘤标志物对比总览")
        print(f"{'标志物':<12} {'中文名':<14} {'最新值':<12} {'单位':<10} {'参考上限':<10} {'vs参考':<10} {'趋势':<10} {'数据点'}")
        print("-" * 95)

        result = []
        for m_name in sorted(by_marker.keys()):
            recs = by_marker[m_name]
            values = [r["data"]["value"] for r in recs]
            latest = values[-1]
            ref = MARKER_REFERENCES.get(m_name, {})
            upper = ref.get("upper")
            unit = ref.get("unit", recs[-1]["data"].get("unit", ""))
            cn_name = ref.get("name", m_name)

            # vs reference
            if upper:
                if latest > upper:
                    vs_ref = f"↑ {latest / upper:.1f}x"
                else:
                    vs_ref = "正常"
            else:
                vs_ref = "无参考"

            # direction
            if len(values) >= 2:
                n = len(values)
                mean_val = sum(values) / n
                x_mean = (n - 1) / 2
                numerator = sum((i - x_mean) * (v - mean_val) for i, v in enumerate(values))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                slope = numerator / denominator if denominator else 0
                direction = "↑上升" if slope > 0.01 else ("↓下降" if slope < -0.01 else "→稳定")
            else:
                direction = "-"

            print(f"{m_name:<12} {cn_name:<14} {latest:<12} {unit:<10} {upper or '--':<10} {vs_ref:<10} {direction:<10} {len(values)}")

            result.append({
                "marker": m_name,
                "name": cn_name,
                "latest": latest,
                "unit": unit,
                "upper": upper,
                "vs_ref": vs_ref,
                "direction": direction,
                "count": len(values),
            })

        return result

    # ----- generate_chart -----
    def generate_chart(self, marker: str, months: int = 12) -> str:
        """生成趋势图，带参考上限线。"""
        marker_upper = marker.upper() if marker.upper() in MARKER_REFERENCES else marker
        records = self.store.query(record_type="marker")
        records = [r for r in records if r["data"].get("marker") == marker_upper]

        cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
        records = [r for r in records if r["timestamp"] >= cutoff]

        if len(records) < 2:
            print(f"📭 {marker_upper} 数据点不足（需至少2个），无法生成图表")
            return ""

        values = [r["data"]["value"] for r in records]
        date_strs = [r["data"].get("lab_date", r["timestamp"][:10]) for r in records]
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in date_strs]

        ref = MARKER_REFERENCES.get(marker_upper)
        ref_lines = []
        if ref:
            ref_lines.append({"value": ref["upper"], "color": "red", "label": f"参考上限 {ref['upper']} {ref['unit']}"})

        marker_name = ref["name"] if ref else marker_upper
        unit = ref["unit"] if ref else ""

        path = os.path.join(self.store.charts_dir, f"trend_{marker_upper}.png")
        plot_trend(
            values=values,
            dates=dates,
            title=f"{marker_name} ({marker_upper}) 趋势",
            ylabel=f"{marker_upper} ({unit})",
            ref_lines=ref_lines,
            output_path=path,
        )
        print(f"📈 图表已保存: {path}")
        return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="肿瘤标志物趋势追踪")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # record
    p_rec = sub.add_parser("record", help="记录标志物值")
    p_rec.add_argument("marker", help="标志物名称，如 CEA, CA199")
    p_rec.add_argument("value", type=float, help="检测值")
    p_rec.add_argument("--unit", default=None, help="单位（可自动检测）")
    p_rec.add_argument("--date", default=None, help="检验日期 YYYY-MM-DD")
    p_rec.add_argument("--treatment", default="", help="治疗背景")
    p_rec.add_argument("--note", default="", help="备注")

    # trend
    p_trend = sub.add_parser("trend", help="趋势分析")
    p_trend.add_argument("marker", help="标志物名称")
    p_trend.add_argument("--months", type=int, default=6, help="查看近N个月")

    # surge
    p_surge = sub.add_parser("surge", help="突增检测")
    p_surge.add_argument("--marker", default=None, help="指定标志物（默认检查全部）")
    p_surge.add_argument("--threshold", type=float, default=20, help="突增阈值百分比")

    # compare
    sub.add_parser("compare", help="多标志物对比")

    args = parser.parse_args()
    tracker = TumorMarkerTrend()

    if args.command == "record":
        tracker.record(
            marker=args.marker,
            value=args.value,
            unit=args.unit,
            lab_date=args.date,
            treatment_context=args.treatment,
            note=args.note,
        )
    elif args.command == "trend":
        tracker.trend(args.marker, months=args.months)
    elif args.command == "surge":
        tracker.detect_surge(marker=args.marker, threshold_pct=args.threshold)
    elif args.command == "compare":
        tracker.compare_markers()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
