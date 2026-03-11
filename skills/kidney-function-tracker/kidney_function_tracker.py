#!/usr/bin/env python3
"""肾功能追踪 - 记录肌酐、eGFR、尿蛋白等指标，支持CKD分期、恶化检测和综合报告。"""

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
# CKD Staging
# ---------------------------------------------------------------------------

CKD_STAGES = [
    ("G1", "正常或高", 90, None, "肾功能正常，但存在肾脏损害证据"),
    ("G2", "轻度下降", 60, 89, "轻度肾功能下降"),
    ("G3a", "轻中度下降", 45, 59, "轻中度肾功能下降，需加强监测"),
    ("G3b", "中重度下降", 30, 44, "中重度肾功能下降，需肾内科随诊"),
    ("G4", "重度下降", 15, 29, "重度肾功能下降，需准备肾替代治疗"),
    ("G5", "肾衰竭", 0, 14, "肾衰竭，需透析或移植"),
]


# ---------------------------------------------------------------------------
# KidneyFunctionTracker
# ---------------------------------------------------------------------------

class KidneyFunctionTracker:
    """肾功能追踪：记录、CKD分期、恶化检测和综合报告。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("kidney-function-tracker", data_dir=data_dir)

    # ----- record -----

    def record(self, creatinine: float = None, egfr: float = None,
               urine_protein: str = None, microalbumin: float = None,
               lab_date: str = None, note: str = "") -> dict:
        """Record kidney function indicators.

        Args:
            creatinine: serum creatinine (mg/dL or umol/L based on config)
            egfr: estimated GFR (mL/min/1.73m2)
            urine_protein: qualitative result (-, +/-, +, ++, +++)
            microalbumin: urine microalbumin (mg/L)
            lab_date: lab date (ISO format), defaults to now
            note: free-text note
        """
        data = {}
        if creatinine is not None:
            data["creatinine"] = creatinine
        if egfr is not None:
            data["egfr"] = egfr
        if urine_protein is not None:
            data["urine_protein"] = urine_protein
        if microalbumin is not None:
            data["microalbumin"] = microalbumin
        if lab_date:
            data["lab_date"] = lab_date

        if not data:
            print("错误：至少需要提供一项肾功能指标。")
            return {}

        record = self.store.append("kidney", data, note=note)

        print(f"[记录成功] 肾功能指标:")
        if creatinine is not None:
            print(f"  肌酐: {creatinine}")
        if egfr is not None:
            stage = self.stage_ckd(egfr)
            print(f"  eGFR: {egfr} mL/min/1.73m^2 → {stage['stage']} ({stage['label']})")
        if urine_protein is not None:
            print(f"  尿蛋白: {urine_protein}")
        if microalbumin is not None:
            print(f"  微量白蛋白: {microalbumin} mg/L")

        return record

    # ----- stage_ckd -----

    def stage_ckd(self, egfr: float) -> dict:
        """CKD staging based on eGFR value.

        Returns dict with stage, label, range, and description.
        """
        for stage, label, low, high, desc in CKD_STAGES:
            if high is None:
                # G1: >= 90
                if egfr >= low:
                    return {"stage": stage, "label": label, "range": f"≥{low}", "description": desc}
            else:
                if low <= egfr <= high:
                    return {"stage": stage, "label": label, "range": f"{low}-{high}", "description": desc}

        # Fallback for negative or unusual values
        return {"stage": "G5", "label": "肾衰竭", "range": "<15", "description": "肾衰竭，需透析或移植"}

    # ----- detect_deterioration -----

    def detect_deterioration(self, months: int = 6) -> dict:
        """Detect eGFR decline rate over given months.

        Rapid decline: >5 mL/min/year. Significant decline: >3 mL/min/year.
        """
        start = (datetime.now() - timedelta(days=months * 30)).isoformat()
        records = [r for r in self.store.query(record_type="kidney") if r["timestamp"] >= start]
        egfr_records = [(r["timestamp"], r["data"]["egfr"]) for r in records if r["data"].get("egfr") is not None]

        result = {
            "data_points": len(egfr_records),
            "decline_rate": None,
            "decline_rate_per_year": None,
            "alert_level": "insufficient_data",
            "message": "",
        }

        if len(egfr_records) < 2:
            result["message"] = f"数据不足：仅 {len(egfr_records)} 个 eGFR 数据点，需至少 2 个"
            print(f"\n=== eGFR 恶化检测 (近 {months} 个月) ===")
            print(f"  {result['message']}")
            return result

        # Sort by timestamp
        egfr_records.sort(key=lambda x: x[0])
        first_ts, first_val = egfr_records[0]
        last_ts, last_val = egfr_records[-1]

        first_dt = datetime.fromisoformat(first_ts)
        last_dt = datetime.fromisoformat(last_ts)
        days_diff = (last_dt - first_dt).days

        if days_diff < 1:
            result["message"] = "所有记录在同一天，无法计算变化率"
            print(f"\n=== eGFR 恶化检测 (近 {months} 个月) ===")
            print(f"  {result['message']}")
            return result

        total_change = last_val - first_val
        annual_rate = total_change / days_diff * 365

        result["first_egfr"] = first_val
        result["last_egfr"] = last_val
        result["total_change"] = round(total_change, 2)
        result["decline_rate_per_year"] = round(annual_rate, 2)

        if annual_rate < -5:
            result["alert_level"] = "rapid_decline"
            result["message"] = f"[严重] eGFR 快速下降: {annual_rate:.1f} mL/min/年 (从 {first_val} 到 {last_val})，建议尽快肾内科就诊"
        elif annual_rate < -3:
            result["alert_level"] = "significant_decline"
            result["message"] = f"[警告] eGFR 显著下降: {annual_rate:.1f} mL/min/年 (从 {first_val} 到 {last_val})，建议加强监测"
        elif annual_rate < 0:
            result["alert_level"] = "mild_decline"
            result["message"] = f"eGFR 轻度下降: {annual_rate:.1f} mL/min/年 (从 {first_val} 到 {last_val})，属于正常范围"
        else:
            result["alert_level"] = "stable_or_improving"
            result["message"] = f"eGFR 稳定或改善: {annual_rate:+.1f} mL/min/年 (从 {first_val} 到 {last_val})"

        print(f"\n=== eGFR 恶化检测 (近 {months} 个月) ===")
        print(f"  数据点: {len(egfr_records)}, 时间跨度: {days_diff} 天")
        print(f"  {result['message']}")

        return result

    # ----- remind_recheck -----

    def remind_recheck(self) -> dict:
        """Suggest recheck intervals based on current CKD stage."""
        latest = self.store.get_latest(record_type="kidney", n=1)

        if not latest or latest[0]["data"].get("egfr") is None:
            msg = "无 eGFR 记录，建议尽快进行肾功能检查。"
            print(f"\n=== 复查提醒 ===\n  {msg}")
            return {"message": msg, "interval": None}

        egfr = latest[0]["data"]["egfr"]
        stage_info = self.stage_ckd(egfr)
        stage = stage_info["stage"]

        intervals = {
            "G1": {"months": 12, "desc": "每年复查一次"},
            "G2": {"months": 6, "desc": "每 6 个月复查一次"},
            "G3a": {"months": 3, "desc": "每 3 个月复查一次"},
            "G3b": {"months": 3, "desc": "每 3 个月复查一次，需肾内科随诊"},
            "G4": {"months": 1, "desc": "每月复查，准备肾替代治疗评估"},
            "G5": {"months": 1, "desc": "每月或更频繁复查，需透析或移植评估"},
        }

        interval = intervals.get(stage, intervals["G1"])
        last_ts = latest[0]["timestamp"][:10]

        # Calculate next recheck date
        last_date = datetime.fromisoformat(latest[0]["timestamp"])
        next_date = last_date + timedelta(days=interval["months"] * 30)
        days_until = (next_date - datetime.now()).days

        result = {
            "current_stage": stage,
            "current_egfr": egfr,
            "interval_months": interval["months"],
            "interval_desc": interval["desc"],
            "last_check": last_ts,
            "next_check": next_date.strftime("%Y-%m-%d"),
            "days_until": max(0, days_until),
            "overdue": days_until < 0,
        }

        print(f"\n=== 复查提醒 ===")
        print(f"  当前 CKD 分期: {stage} ({stage_info['label']})")
        print(f"  最近 eGFR: {egfr} mL/min/1.73m^2 (检查日期: {last_ts})")
        print(f"  建议复查间隔: {interval['desc']}")
        print(f"  下次复查日期: {result['next_check']}")
        if result["overdue"]:
            print(f"  [提醒] 已超过建议复查时间 {abs(days_until)} 天，请尽快安排复查！")
        else:
            print(f"  距下次复查还有 {days_until} 天")

        return result

    # ----- generate_report -----

    def generate_report(self) -> str:
        """Comprehensive kidney function report."""
        lines = ["=" * 50, "       肾功能综合报告", "=" * 50, ""]

        # Latest values
        latest = self.store.get_latest(record_type="kidney", n=1)
        if not latest:
            msg = "暂无肾功能记录。请先使用 record 命令记录数据。"
            print(msg)
            return msg

        last = latest[0]
        d = last["data"]
        ts = last["timestamp"][:16].replace("T", " ")

        lines.append(f"最近检查时间: {ts}")
        lines.append("")

        # Current values
        lines.append("【当前指标】")
        if d.get("creatinine") is not None:
            lines.append(f"  肌酐: {d['creatinine']}")
        if d.get("egfr") is not None:
            stage = self.stage_ckd(d["egfr"])
            lines.append(f"  eGFR: {d['egfr']} mL/min/1.73m^2")
            lines.append(f"  CKD 分期: {stage['stage']} - {stage['label']}")
            lines.append(f"    → {stage['description']}")
        if d.get("urine_protein") is not None:
            lines.append(f"  尿蛋白: {d['urine_protein']}")
        if d.get("microalbumin") is not None:
            lines.append(f"  微量白蛋白: {d['microalbumin']} mg/L")
        lines.append("")

        # Trend (6 months)
        lines.append("【eGFR 趋势 (近 6 个月)】")
        trend_data = self.store.trend("kidney", "egfr", window=180)
        if trend_data["count"] >= 2:
            lines.append(f"  数据点: {trend_data['count']}")
            lines.append(f"  均值: {trend_data['mean']} mL/min/1.73m^2")
            lines.append(f"  趋势: {trend_data['direction']} (斜率 {trend_data['slope']})")
        else:
            lines.append(f"  数据不足 (仅 {trend_data['count']} 个数据点)")
        lines.append("")

        # Deterioration
        lines.append("【恶化评估】")
        det = self.detect_deterioration(months=6)
        lines.append(f"  {det['message']}")
        lines.append("")

        # Recheck
        lines.append("【复查建议】")
        recheck = self.remind_recheck()
        lines.append(f"  {recheck.get('interval_desc', '请先记录 eGFR 数据')}")
        if recheck.get("next_check"):
            lines.append(f"  下次复查: {recheck['next_check']}")
            if recheck.get("overdue"):
                lines.append(f"  [!] 已超期，请尽快复查！")
        lines.append("")

        # Creatinine trend
        lines.append("【肌酐趋势 (近 6 个月)】")
        cr_trend = self.store.trend("kidney", "creatinine", window=180)
        if cr_trend["count"] >= 2:
            lines.append(f"  数据点: {cr_trend['count']}")
            lines.append(f"  均值: {cr_trend['mean']}")
            lines.append(f"  趋势: {cr_trend['direction']} (斜率 {cr_trend['slope']})")
            if cr_trend["direction"] == "rising":
                lines.append(f"  [注意] 肌酐持续上升，提示肾功能可能恶化")
        else:
            lines.append(f"  数据不足 (仅 {cr_trend['count']} 个数据点)")
        lines.append("")

        # Urine protein history
        records = self.store.query(record_type="kidney")
        up_records = [r for r in records if r["data"].get("urine_protein") is not None]
        if up_records:
            lines.append("【尿蛋白记录】")
            for r in up_records[-5:]:
                ts = r["timestamp"][:10]
                lines.append(f"  {ts}: {r['data']['urine_protein']}")
            positive = [r for r in up_records if r["data"]["urine_protein"] not in ("-", "阴性")]
            if positive:
                lines.append(f"  阳性次数: {len(positive)}/{len(up_records)}")
            lines.append("")

        lines.append("=" * 50)

        report = "\n".join(lines)
        print(report)
        return report

    # ----- generate_chart -----

    def generate_chart(self, months: int = 12) -> str:
        """eGFR trend chart with CKD stage boundary lines."""
        start = (datetime.now() - timedelta(days=months * 30)).isoformat()
        records = [r for r in self.store.query(record_type="kidney") if r["timestamp"] >= start]
        egfr_records = [(r["timestamp"], r["data"]["egfr"]) for r in records if r["data"].get("egfr") is not None]

        if len(egfr_records) < 2:
            print("数据不足，至少需要 2 个 eGFR 数据点来生成图表。")
            return ""

        egfr_records.sort(key=lambda x: x[0])
        dates = [datetime.fromisoformat(ts) for ts, _ in egfr_records]
        values = [v for _, v in egfr_records]

        ref_lines = [
            {"value": 90, "color": "green", "label": "G1/G2 界限 (90)"},
            {"value": 60, "color": "#f39c12", "label": "G2/G3a 界限 (60)"},
            {"value": 45, "color": "orange", "label": "G3a/G3b 界限 (45)"},
            {"value": 30, "color": "#e74c3c", "label": "G3b/G4 界限 (30)"},
            {"value": 15, "color": "darkred", "label": "G4/G5 界限 (15)"},
        ]

        chart_path = os.path.join(self.store.charts_dir, f"egfr_trend_{months}m.png")
        plot_trend(
            values, dates,
            title=f"eGFR 趋势 (近 {months} 个月)",
            ylabel="eGFR (mL/min/1.73m^2)",
            ref_lines=ref_lines,
            output_path=chart_path,
        )

        print(f"eGFR 趋势图已保存: {chart_path}")

        # Also generate creatinine chart if data available
        cr_records = [(r["timestamp"], r["data"]["creatinine"]) for r in records if r["data"].get("creatinine") is not None]
        if len(cr_records) >= 2:
            cr_records.sort(key=lambda x: x[0])
            cr_dates = [datetime.fromisoformat(ts) for ts, _ in cr_records]
            cr_values = [v for _, v in cr_records]
            cr_path = os.path.join(self.store.charts_dir, f"creatinine_trend_{months}m.png")
            plot_trend(
                cr_values, cr_dates,
                title=f"肌酐趋势 (近 {months} 个月)",
                ylabel="肌酐",
                output_path=cr_path,
            )
            print(f"肌酐趋势图已保存: {cr_path}")

        return chart_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="肾功能追踪")
    sub = parser.add_subparsers(dest="command")

    # record
    p_rec = sub.add_parser("record", help="记录肾功能指标")
    p_rec.add_argument("--creatinine", type=float, default=None, help="血清肌酐")
    p_rec.add_argument("--egfr", type=float, default=None, help="eGFR (mL/min/1.73m^2)")
    p_rec.add_argument("--urine-protein", default=None, help="尿蛋白 (-, +/-, +, ++, +++)")
    p_rec.add_argument("--microalbumin", type=float, default=None, help="微量白蛋白 (mg/L)")
    p_rec.add_argument("--lab-date", default=None, help="检验日期 (YYYY-MM-DD)")
    p_rec.add_argument("--note", default="", help="备注")
    p_rec.add_argument("--data-dir", default=None, help="数据目录")

    # report
    p_report = sub.add_parser("report", help="生成综合报告")
    p_report.add_argument("--data-dir", default=None, help="数据目录")

    # chart
    p_chart = sub.add_parser("chart", help="生成趋势图")
    p_chart.add_argument("--months", type=int, default=12, help="月数")
    p_chart.add_argument("--data-dir", default=None, help="数据目录")

    # stage
    p_stage = sub.add_parser("stage", help="查看 CKD 分期")
    p_stage.add_argument("egfr", type=float, help="eGFR 值")

    # deterioration
    p_det = sub.add_parser("deterioration", help="恶化检测")
    p_det.add_argument("--months", type=int, default=6, help="月数")
    p_det.add_argument("--data-dir", default=None, help="数据目录")

    # recheck
    p_recheck = sub.add_parser("recheck", help="复查提醒")
    p_recheck.add_argument("--data-dir", default=None, help="数据目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "stage":
        tracker = KidneyFunctionTracker()
        stage = tracker.stage_ckd(args.egfr)
        print(f"eGFR {args.egfr} → CKD {stage['stage']} ({stage['label']})")
        print(f"  范围: {stage['range']} mL/min/1.73m^2")
        print(f"  说明: {stage['description']}")
        return

    tracker = KidneyFunctionTracker(data_dir=getattr(args, "data_dir", None))

    if args.command == "record":
        tracker.record(
            creatinine=args.creatinine,
            egfr=args.egfr,
            urine_protein=args.urine_protein,
            microalbumin=args.microalbumin,
            lab_date=args.lab_date,
            note=args.note,
        )
    elif args.command == "report":
        tracker.generate_report()
    elif args.command == "chart":
        tracker.generate_chart(months=args.months)
    elif args.command == "deterioration":
        tracker.detect_deterioration(months=args.months)
    elif args.command == "recheck":
        tracker.remind_recheck()


if __name__ == "__main__":
    main()
