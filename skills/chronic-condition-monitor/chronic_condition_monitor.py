#!/usr/bin/env python3
"""慢病指标监测 - 记录和追踪慢病指标，支持趋势分析、异常告警和就诊摘要生成。"""

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
# Default thresholds
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS = {
    "bp": {
        "sys_max": 140,
        "dia_max": 90,
    },
    "glucose": {
        "fasting_min": 3.9,
        "fasting_max": 6.1,
        "postprandial_max": 7.8,
    },
    "uric_acid": {
        "male_max": 420,
        "female_max": 360,
    },
    "creatinine": {
        "male_min": 57,
        "male_max": 111,
        "female_min": 44,
        "female_max": 97,
    },
    "egfr": {
        "normal_min": 90,
    },
    "weight": {
        "target_kg": None,  # user-configured
    },
}


# ---------------------------------------------------------------------------
# ChronicConditionMonitor
# ---------------------------------------------------------------------------

class ChronicConditionMonitor:
    """慢病指标监测：记录、查询、趋势分析、告警和就诊摘要。"""

    METRIC_TYPES = ("bp", "glucose", "weight", "uric_acid", "creatinine", "egfr", "custom")

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("chronic-condition-monitor", data_dir=data_dir)
        self._init_thresholds()

    def _init_thresholds(self):
        """Load thresholds from config, falling back to defaults."""
        config = self.store.get_config()
        self.thresholds = config.get("thresholds", DEFAULT_THRESHOLDS.copy())
        self.gender = config.get("gender", "male")

    def _save_thresholds(self):
        self.store.set_config("thresholds", self.thresholds)

    # ----- record -----

    def record(self, metric_type: str, values: dict, context: str = "", note: str = "") -> dict:
        """Record a metric reading.

        Args:
            metric_type: bp, glucose, weight, uric_acid, creatinine, egfr, custom
            values: dict of measured values, e.g. {"sys": 138, "dia": 88}
            context: measurement context, e.g. "morning", "fasting", "postprandial"
            note: free-text note
        """
        if metric_type not in self.METRIC_TYPES:
            raise ValueError(f"未知指标类型: {metric_type}，支持: {self.METRIC_TYPES}")
        data = {**values, "context": context}
        record = self.store.append(metric_type, data, note=note)
        print(f"[记录成功] {metric_type} | {values} | 上下文: {context or '无'}")
        return record

    # ----- query -----

    def query(self, metric_type: str = None, days: int = 30) -> list:
        """Query records within the given time window."""
        start = (datetime.now() - timedelta(days=days)).isoformat()
        records = self.store.query(record_type=metric_type, start=start)
        if not records:
            print(f"最近 {days} 天无 {metric_type or '任何'} 记录。")
        else:
            print(f"最近 {days} 天共 {len(records)} 条 {metric_type or '所有'} 记录：")
            for r in records:
                ts = r["timestamp"][:16].replace("T", " ")
                ctx = r["data"].get("context", "")
                print(f"  [{ts}] {r['type']}: {r['data']} {('(' + ctx + ')') if ctx else ''}")
        return records

    # ----- trend -----

    def trend(self, metric_type: str, days: int = 90) -> dict:
        """Trend analysis with PNG chart generation."""
        field_map = {
            "bp": "sys",
            "glucose": "value",
            "weight": "kg",
            "uric_acid": "value",
            "creatinine": "value",
            "egfr": "value",
        }
        field = field_map.get(metric_type, "value")
        trend_data = self.store.trend(metric_type, field, window=days)

        print(f"\n=== {metric_type} 趋势分析 (近 {days} 天) ===")
        print(f"  数据点数: {trend_data['count']}")
        print(f"  均值: {trend_data['mean']}")
        print(f"  斜率: {trend_data['slope']}")
        print(f"  趋势: {trend_data['direction']}")

        # Generate chart if enough data
        if trend_data["count"] >= 2:
            start = (datetime.now() - timedelta(days=days)).isoformat()
            records = [r for r in self.store.query(record_type=metric_type) if r["timestamp"] >= start]
            dates = [datetime.fromisoformat(r["timestamp"]) for r in records if r["data"].get(field) is not None]
            values = [r["data"][field] for r in records if r["data"].get(field) is not None]

            ref_lines = self._get_ref_lines(metric_type)
            label_map = {
                "bp": "收缩压 (mmHg)",
                "glucose": "血糖 (mmol/L)",
                "weight": "体重 (kg)",
                "uric_acid": "尿酸 (μmol/L)",
                "creatinine": "肌酐 (μmol/L)",
                "egfr": "eGFR (mL/min/1.73m^2)",
            }
            ylabel = label_map.get(metric_type, metric_type)
            title = f"{metric_type}_trend_{days}d"
            output_path = os.path.join(self.store.charts_dir, f"{title}.png")
            chart_path = plot_trend(values, dates, title, ylabel, ref_lines=ref_lines, output_path=output_path)
            trend_data["chart"] = chart_path
            print(f"  图表: {chart_path}")

        return trend_data

    def _get_ref_lines(self, metric_type: str) -> list:
        """Get reference lines for a metric type."""
        th = self.thresholds.get(metric_type, {})
        lines = []
        if metric_type == "bp":
            lines.append({"value": th.get("sys_max", 140), "color": "red", "label": "收缩压上限 140"})
        elif metric_type == "glucose":
            lines.append({"value": th.get("fasting_max", 6.1), "color": "red", "label": "空腹上限 6.1"})
            lines.append({"value": th.get("fasting_min", 3.9), "color": "orange", "label": "空腹下限 3.9"})
        elif metric_type == "uric_acid":
            key = "male_max" if self.gender == "male" else "female_max"
            lines.append({"value": th.get(key, 420), "color": "red", "label": f"尿酸上限 {th.get(key, 420)}"})
        elif metric_type == "creatinine":
            prefix = "male" if self.gender == "male" else "female"
            lines.append({"value": th.get(f"{prefix}_max", 111), "color": "red", "label": f"肌酐上限 {th.get(f'{prefix}_max', 111)}"})
            lines.append({"value": th.get(f"{prefix}_min", 57), "color": "orange", "label": f"肌酐下限 {th.get(f'{prefix}_min', 57)}"})
        elif metric_type == "egfr":
            lines.append({"value": th.get("normal_min", 90), "color": "red", "label": "eGFR 正常下限 90"})
        return lines

    # ----- alert_check -----

    def alert_check(self) -> list:
        """Check all metrics against thresholds, return abnormalities."""
        alerts = []
        latest_records = {}
        for mt in self.METRIC_TYPES:
            if mt == "custom":
                continue
            latest = self.store.get_latest(record_type=mt, n=1)
            if latest:
                latest_records[mt] = latest[0]

        th = self.thresholds

        # BP
        if "bp" in latest_records:
            d = latest_records["bp"]["data"]
            sys_val = d.get("sys")
            dia_val = d.get("dia")
            if sys_val and sys_val >= th.get("bp", {}).get("sys_max", 140):
                alerts.append({"metric": "bp", "field": "sys", "value": sys_val, "threshold": th["bp"]["sys_max"], "message": f"收缩压 {sys_val} mmHg 超标 (≥{th['bp']['sys_max']})"})
            if dia_val and dia_val >= th.get("bp", {}).get("dia_max", 90):
                alerts.append({"metric": "bp", "field": "dia", "value": dia_val, "threshold": th["bp"]["dia_max"], "message": f"舒张压 {dia_val} mmHg 超标 (≥{th['bp']['dia_max']})"})

        # Glucose
        if "glucose" in latest_records:
            d = latest_records["glucose"]["data"]
            val = d.get("value")
            ctx = d.get("context", "")
            if val:
                if "fasting" in ctx or "空腹" in ctx:
                    if val > th.get("glucose", {}).get("fasting_max", 6.1):
                        alerts.append({"metric": "glucose", "field": "value", "value": val, "threshold": th["glucose"]["fasting_max"], "message": f"空腹血糖 {val} mmol/L 超标 (>{th['glucose']['fasting_max']})"})
                    elif val < th.get("glucose", {}).get("fasting_min", 3.9):
                        alerts.append({"metric": "glucose", "field": "value", "value": val, "threshold": th["glucose"]["fasting_min"], "message": f"空腹血糖 {val} mmol/L 偏低 (<{th['glucose']['fasting_min']})"})
                elif "postprandial" in ctx or "餐后" in ctx:
                    if val > th.get("glucose", {}).get("postprandial_max", 7.8):
                        alerts.append({"metric": "glucose", "field": "value", "value": val, "threshold": th["glucose"]["postprandial_max"], "message": f"餐后血糖 {val} mmol/L 超标 (>{th['glucose']['postprandial_max']})"})

        # Uric acid
        if "uric_acid" in latest_records:
            d = latest_records["uric_acid"]["data"]
            val = d.get("value")
            key = "male_max" if self.gender == "male" else "female_max"
            limit = th.get("uric_acid", {}).get(key, 420)
            if val and val > limit:
                alerts.append({"metric": "uric_acid", "field": "value", "value": val, "threshold": limit, "message": f"尿酸 {val} μmol/L 超标 (>{limit})"})

        # Creatinine
        if "creatinine" in latest_records:
            d = latest_records["creatinine"]["data"]
            val = d.get("value")
            prefix = "male" if self.gender == "male" else "female"
            low = th.get("creatinine", {}).get(f"{prefix}_min", 57)
            high = th.get("creatinine", {}).get(f"{prefix}_max", 111)
            if val:
                if val > high:
                    alerts.append({"metric": "creatinine", "field": "value", "value": val, "threshold": high, "message": f"肌酐 {val} μmol/L 超标 (>{high})"})
                elif val < low:
                    alerts.append({"metric": "creatinine", "field": "value", "value": val, "threshold": low, "message": f"肌酐 {val} μmol/L 偏低 (<{low})"})

        # eGFR
        if "egfr" in latest_records:
            d = latest_records["egfr"]["data"]
            val = d.get("value")
            limit = th.get("egfr", {}).get("normal_min", 90)
            if val and val < limit:
                alerts.append({"metric": "egfr", "field": "value", "value": val, "threshold": limit, "message": f"eGFR {val} mL/min/1.73m^2 低于正常 (<{limit})"})

        # Print results
        if alerts:
            print(f"\n=== 异常告警 ({len(alerts)} 项) ===")
            for a in alerts:
                print(f"  [!] {a['message']}")
        else:
            print("\n=== 所有指标在正常范围内 ===")

        return alerts

    # ----- consecutive_alert -----

    def consecutive_alert(self, metric_type: str, field: str, count: int = 3) -> bool:
        """Check N consecutive rises or falls."""
        rising = self.store.consecutive_check(metric_type, field, "rising", count)
        falling = self.store.consecutive_check(metric_type, field, "falling", count)
        if rising:
            print(f"[告警] {metric_type}.{field} 连续 {count} 次上升")
        if falling:
            print(f"[告警] {metric_type}.{field} 连续 {count} 次下降")
        if not rising and not falling:
            print(f"{metric_type}.{field} 未出现连续 {count} 次单方向变化。")
        return rising or falling

    # ----- generate_visit_summary -----

    def generate_visit_summary(self, days: int = 30) -> str:
        """Generate a visit preparation summary."""
        start = (datetime.now() - timedelta(days=days)).isoformat()
        summary_parts = [f"=== 就诊摘要 (近 {days} 天) ===\n"]

        field_map = {
            "bp": [("sys", "收缩压"), ("dia", "舒张压")],
            "glucose": [("value", "血糖")],
            "weight": [("kg", "体重")],
            "uric_acid": [("value", "尿酸")],
            "creatinine": [("value", "肌酐")],
            "egfr": [("value", "eGFR")],
        }

        for mt, fields in field_map.items():
            records = self.store.query(record_type=mt, start=start)
            if not records:
                continue
            summary_parts.append(f"\n【{mt.upper()}】共 {len(records)} 条记录")
            for field, label in fields:
                values = [r["data"].get(field) for r in records if r["data"].get(field) is not None]
                if not values:
                    continue
                mean_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                summary_parts.append(f"  {label}: 均值 {mean_val:.1f}, 范围 {min_val}-{max_val}")

                # Trend
                trend_data = self.store.trend(mt, field, window=days)
                summary_parts.append(f"  趋势: {trend_data['direction']} (斜率 {trend_data['slope']})")

        # Abnormal count
        alerts = self.alert_check()
        summary_parts.append(f"\n异常告警: {len(alerts)} 项")
        for a in alerts:
            summary_parts.append(f"  - {a['message']}")

        summary = "\n".join(summary_parts)
        print(summary)
        return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="慢病指标监测")
    sub = parser.add_subparsers(dest="command")

    # record
    p_rec = sub.add_parser("record", help="记录指标")
    p_rec.add_argument("metric_type", choices=ChronicConditionMonitor.METRIC_TYPES, help="指标类型")
    p_rec.add_argument("values", type=str, help="指标值 (JSON)")
    p_rec.add_argument("--context", default="", help="测量上下文")
    p_rec.add_argument("--note", default="", help="备注")
    p_rec.add_argument("--data-dir", default=None, help="数据目录")

    # query
    p_query = sub.add_parser("query", help="查询记录")
    p_query.add_argument("--metric-type", default=None, help="指标类型")
    p_query.add_argument("--days", type=int, default=30, help="时间窗口 (天)")
    p_query.add_argument("--data-dir", default=None, help="数据目录")

    # trend
    p_trend = sub.add_parser("trend", help="趋势分析")
    p_trend.add_argument("metric_type", help="指标类型")
    p_trend.add_argument("--days", type=int, default=90, help="时间窗口 (天)")
    p_trend.add_argument("--data-dir", default=None, help="数据目录")

    # alert
    p_alert = sub.add_parser("alert", help="异常告警检查")
    p_alert.add_argument("--data-dir", default=None, help="数据目录")

    # consecutive
    p_cons = sub.add_parser("consecutive", help="连续变化检查")
    p_cons.add_argument("metric_type", help="指标类型")
    p_cons.add_argument("field", help="字段名")
    p_cons.add_argument("--count", type=int, default=3, help="连续次数")
    p_cons.add_argument("--data-dir", default=None, help="数据目录")

    # summary
    p_sum = sub.add_parser("summary", help="就诊摘要")
    p_sum.add_argument("--days", type=int, default=30, help="时间窗口 (天)")
    p_sum.add_argument("--data-dir", default=None, help="数据目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    monitor = ChronicConditionMonitor(data_dir=getattr(args, "data_dir", None))

    if args.command == "record":
        values = json.loads(args.values)
        monitor.record(args.metric_type, values, context=args.context, note=args.note)
    elif args.command == "query":
        monitor.query(metric_type=args.metric_type, days=args.days)
    elif args.command == "trend":
        monitor.trend(args.metric_type, days=args.days)
    elif args.command == "alert":
        monitor.alert_check()
    elif args.command == "consecutive":
        monitor.consecutive_alert(args.metric_type, args.field, count=args.count)
    elif args.command == "summary":
        monitor.generate_visit_summary(days=args.days)


if __name__ == "__main__":
    main()
