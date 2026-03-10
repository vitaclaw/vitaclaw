#!/usr/bin/env python3
"""术后康复追踪 - 记录引流量、伤口、疼痛等恢复指标，支持里程碑检查和复查提醒。"""

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
# Recovery milestones template
# ---------------------------------------------------------------------------
MILESTONES = [
    {"day_range": (1, 1), "label": "术后第1天", "items": ["可翻身", "拔尿管"]},
    {"day_range": (2, 3), "label": "术后第2-3天", "items": ["可下床活动", "排气"]},
    {"day_range": (3, 5), "label": "术后第3-5天", "items": ["拔引流管（引流量<50mL/天）"]},
    {"day_range": (5, 7), "label": "术后第5-7天", "items": ["恢复半流质饮食"]},
    {"day_range": (7, 14), "label": "术后第7-14天", "items": ["拆线/伤口愈合"]},
    {"day_range": (14, 30), "label": "术后第14-30天", "items": ["恢复日常活动"]},
]

RECHECK_SCHEDULE = [
    {"day": 7, "label": "术后1周", "items": ["伤口检查", "拆线评估"]},
    {"day": 14, "label": "术后2周", "items": ["血常规", "肝肾功能", "伤口复查"]},
    {"day": 30, "label": "术后1月", "items": ["影像学复查", "肿瘤标志物", "全面体检"]},
    {"day": 90, "label": "术后3月", "items": ["CT/MRI复查", "肿瘤标志物", "营养评估"]},
    {"day": 180, "label": "术后6月", "items": ["全面影像学", "肿瘤标志物", "心肺功能"]},
    {"day": 365, "label": "术后1年", "items": ["年度全面复查", "影像学", "肿瘤标志物", "生活质量评估"]},
]


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
# PostSurgeryRecovery
# ---------------------------------------------------------------------------
class PostSurgeryRecovery:
    """术后康复追踪器。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("post-surgery-recovery", data_dir=data_dir)

    # ----- configure -----
    def configure(self, surgery_type: str, surgery_date: str,
                  hospital: str = "", surgeon: str = "", note: str = "") -> dict:
        """配置手术信息。

        Args:
            surgery_type: 手术类型，如 肺叶切除术
            surgery_date: 手术日期 YYYY-MM-DD
            hospital: 医院名称
            surgeon: 主刀医生
            note: 备注
        """
        config = {
            "surgery_type": surgery_type,
            "surgery_date": surgery_date,
            "hospital": hospital,
            "surgeon": surgeon,
            "note": note,
            "configured_at": datetime.now().isoformat(),
        }
        for k, v in config.items():
            self.store.set_config(k, v)

        print(f"✅ 手术信息已配置")
        print(f"   手术类型: {surgery_type}")
        print(f"   手术日期: {surgery_date}")
        if hospital:
            print(f"   医    院: {hospital}")
        if surgeon:
            print(f"   主刀医生: {surgeon}")

        return config

    # ----- record -----
    def record(self, drainage: float = None, wound: str = None, pain_score: int = None,
               activity: str = None, diet: str = None, temp: float = None, note: str = "") -> dict:
        """记录每日康复数据，至少提供一项。

        Args:
            drainage: 引流量 mL
            wound: 伤口状况描述
            pain_score: 疼痛评分 0-10 (NRS)
            activity: 活动水平描述
            diet: 饮食状况
            temp: 体温 (°C)
            note: 备注
        """
        data = {}
        if drainage is not None:
            data["drainage"] = drainage
        if wound is not None:
            data["wound"] = wound
        if pain_score is not None:
            if not (0 <= pain_score <= 10):
                print("⚠ 疼痛评分应在0-10范围内")
            data["pain_score"] = pain_score
        if activity is not None:
            data["activity"] = activity
        if diet is not None:
            data["diet"] = diet
        if temp is not None:
            data["temp"] = temp

        if not data:
            print("❌ 请至少提供一项记录数据")
            return {}

        days = self.days_since_surgery()
        data["post_op_day"] = days

        rec = self.store.append("recovery", data, note=note)

        print(f"✅ 术后第{days}天 康复记录已保存")
        if drainage is not None:
            drain_status = "⚠ 引流量偏多" if drainage > 100 else ("✅ 接近拔管标准" if drainage < 50 else "")
            print(f"   引流量: {drainage} mL {drain_status}")
        if wound is not None:
            print(f"   伤  口: {wound}")
        if pain_score is not None:
            pain_level = "轻度" if pain_score <= 3 else ("中度" if pain_score <= 6 else "重度")
            print(f"   疼  痛: {pain_score}/10 ({pain_level})")
        if activity is not None:
            print(f"   活  动: {activity}")
        if diet is not None:
            print(f"   饮  食: {diet}")
        if temp is not None:
            temp_status = "⚠ 发热" if temp >= 38.0 else "正常"
            print(f"   体  温: {temp}°C ({temp_status})")

        return rec

    # ----- days_since_surgery -----
    def days_since_surgery(self) -> int:
        """计算术后天数。"""
        config = self.store.get_config()
        surgery_date_str = config.get("surgery_date")
        if not surgery_date_str:
            return -1
        surgery_date = datetime.strptime(surgery_date_str, "%Y-%m-%d")
        return (datetime.now() - surgery_date).days

    # ----- generate_progress_report -----
    def generate_progress_report(self) -> str:
        """生成综合康复进度报告。"""
        config = self.store.get_config()
        records = self.store.query(record_type="recovery")

        days = self.days_since_surgery()
        surgery_type = config.get("surgery_type", "未配置")
        surgery_date = config.get("surgery_date", "未配置")
        hospital = config.get("hospital", "")

        lines = []
        lines.append(f"═══ 术后康复进度报告 ═══")
        lines.append(f"手术类型: {surgery_type}")
        lines.append(f"手术日期: {surgery_date}")
        if hospital:
            lines.append(f"医    院: {hospital}")
        lines.append(f"术后天数: 第{days}天")
        lines.append(f"记录总数: {len(records)}")
        lines.append("")

        if not records:
            lines.append("📭 暂无康复记录")
            report = "\n".join(lines)
            print(report)
            return report

        # Latest vitals
        latest = records[-1]["data"]
        lines.append("── 最新状态 ──")
        if "drainage" in latest:
            lines.append(f"  引流量: {latest['drainage']} mL")
        if "wound" in latest:
            lines.append(f"  伤  口: {latest['wound']}")
        if "pain_score" in latest:
            pain_level = "轻度" if latest["pain_score"] <= 3 else ("中度" if latest["pain_score"] <= 6 else "重度")
            lines.append(f"  疼  痛: {latest['pain_score']}/10 ({pain_level})")
        if "activity" in latest:
            lines.append(f"  活  动: {latest['activity']}")
        if "diet" in latest:
            lines.append(f"  饮  食: {latest['diet']}")
        if "temp" in latest:
            lines.append(f"  体  温: {latest['temp']}°C")
        lines.append("")

        # Drainage trend
        drainage_values = [r["data"]["drainage"] for r in records if "drainage" in r["data"]]
        if len(drainage_values) >= 2:
            lines.append("── 引流量趋势 ──")
            if drainage_values[-1] < drainage_values[0]:
                lines.append(f"  趋势: ↓下降 ({drainage_values[0]} → {drainage_values[-1]} mL)")
            elif drainage_values[-1] > drainage_values[0]:
                lines.append(f"  趋势: ↑上升 ({drainage_values[0]} → {drainage_values[-1]} mL)")
            else:
                lines.append(f"  趋势: →稳定 ({drainage_values[-1]} mL)")
            if drainage_values[-1] < 50:
                lines.append(f"  ✅ 引流量<50mL/天，可考虑拔管")
            lines.append("")

        # Pain trend
        pain_values = [r["data"]["pain_score"] for r in records if "pain_score" in r["data"]]
        if len(pain_values) >= 2:
            lines.append("── 疼痛趋势 ──")
            if pain_values[-1] < pain_values[0]:
                lines.append(f"  趋势: ↓减轻 ({pain_values[0]} → {pain_values[-1]})")
            elif pain_values[-1] > pain_values[0]:
                lines.append(f"  趋势: ↑加重 ({pain_values[0]} → {pain_values[-1]})")
            else:
                lines.append(f"  趋势: →稳定 ({pain_values[-1]})")
            lines.append("")

        # Diet progression
        diet_records = [(r["data"].get("post_op_day", "?"), r["data"]["diet"]) for r in records if "diet" in r["data"]]
        if diet_records:
            lines.append("── 饮食恢复 ──")
            for pod, diet in diet_records:
                lines.append(f"  第{pod}天: {diet}")
            lines.append("")

        # Activity progression
        activity_records = [(r["data"].get("post_op_day", "?"), r["data"]["activity"]) for r in records if "activity" in r["data"]]
        if activity_records:
            lines.append("── 活动恢复 ──")
            for pod, act in activity_records:
                lines.append(f"  第{pod}天: {act}")
            lines.append("")

        # Temperature alerts
        temp_values = [(r["data"].get("post_op_day", "?"), r["data"]["temp"]) for r in records if "temp" in r["data"]]
        fever_records = [(pod, t) for pod, t in temp_values if t >= 38.0]
        if fever_records:
            lines.append("── 发热记录 ──")
            for pod, t in fever_records:
                lines.append(f"  ⚠ 第{pod}天: {t}°C")
            lines.append("")

        report = "\n".join(lines)
        print(report)
        return report

    # ----- recovery_milestones -----
    def recovery_milestones(self) -> list:
        """检查术后康复里程碑达成情况。"""
        days = self.days_since_surgery()
        records = self.store.query(record_type="recovery")

        if days < 0:
            print("❌ 请先配置手术信息 (configure)")
            return []

        # Analyze recorded data for milestone checking
        has_activity = any("activity" in r["data"] for r in records)
        drainage_values = [r["data"]["drainage"] for r in records if "drainage" in r["data"]]
        min_drainage = min(drainage_values) if drainage_values else None
        diet_records = [r["data"]["diet"] for r in records if "diet" in r["data"]]
        wound_records = [r["data"]["wound"] for r in records if "wound" in r["data"]]

        print(f"\n🏥 术后康复里程碑 - 第{days}天")
        print("-" * 50)

        result = []
        for ms in MILESTONES:
            day_start, day_end = ms["day_range"]
            label = ms["label"]

            if days < day_start:
                status = "⏳ 未到时间"
                achieved = False
            elif days >= day_start:
                # Determine if milestone is likely achieved based on data
                achieved = False
                if day_end <= 1:
                    # Day 1 milestones
                    if has_activity:
                        achieved = True
                elif day_end <= 3:
                    # Day 2-3: activity
                    activity_texts = [r["data"].get("activity", "") for r in records if "activity" in r["data"]]
                    if any("下床" in a or "活动" in a or "行走" in a for a in activity_texts):
                        achieved = True
                elif day_end <= 5:
                    # Day 3-5: drainage < 50
                    if min_drainage is not None and min_drainage < 50:
                        achieved = True
                elif day_end <= 7:
                    # Day 5-7: semi-liquid diet
                    if any("半流" in d or "流质" in d or "粥" in d or "汤" in d for d in diet_records):
                        achieved = True
                elif day_end <= 14:
                    # Day 7-14: wound healing
                    if any("愈合" in w or "良好" in w or "甲级" in w for w in wound_records):
                        achieved = True
                elif day_end <= 30:
                    # Day 14-30: resume daily activities
                    activity_texts = [r["data"].get("activity", "") for r in records if "activity" in r["data"]]
                    if any("日常" in a or "自理" in a or "正常" in a for a in activity_texts):
                        achieved = True

                if days > day_end and not achieved:
                    status = "⚠ 已过预期时间，未确认达成"
                elif achieved:
                    status = "✅ 已达成"
                else:
                    status = "🔄 进行中" if days <= day_end else "⚠ 未确认"
            else:
                status = "⏳ 未到时间"
                achieved = False

            items_str = "、".join(ms["items"])
            print(f"  {status} {label}: {items_str}")
            result.append({"label": label, "items": ms["items"], "achieved": achieved, "status": status})

        return result

    # ----- remind_recheck -----
    def remind_recheck(self) -> list:
        """根据术后天数生成复查提醒。"""
        days = self.days_since_surgery()
        config = self.store.get_config()
        surgery_date_str = config.get("surgery_date")

        if days < 0 or not surgery_date_str:
            print("❌ 请先配置手术信息 (configure)")
            return []

        surgery_date = datetime.strptime(surgery_date_str, "%Y-%m-%d")

        print(f"\n📅 术后复查提醒 - 第{days}天")
        print("-" * 50)

        result = []
        for sched in RECHECK_SCHEDULE:
            target_date = surgery_date + timedelta(days=sched["day"])
            days_until = (target_date - datetime.now()).days

            if days_until < -7:
                status = "⏰ 已过期"
            elif days_until < 0:
                status = "🔴 已过期(近期)"
            elif days_until == 0:
                status = "🔴 今天！"
            elif days_until <= 7:
                status = f"🟡 {days_until}天后"
            else:
                status = f"🟢 {days_until}天后"

            items_str = "、".join(sched["items"])
            target_str = target_date.strftime("%Y-%m-%d")

            # Only show upcoming or recently past
            if days_until >= -30:
                print(f"  {status} {sched['label']} ({target_str})")
                print(f"         检查项目: {items_str}")
                result.append({
                    "label": sched["label"],
                    "target_date": target_str,
                    "days_until": days_until,
                    "items": sched["items"],
                    "status": status,
                })

        if not result:
            print("  ✅ 暂无近期复查提醒")

        return result

    # ----- generate_chart -----
    def generate_chart(self) -> str:
        """生成双轴图表：引流量 + 疼痛评分。"""
        records = self.store.query(record_type="recovery")
        if not records:
            print("📭 暂无数据，无法生成图表")
            return ""

        # Extract drainage and pain data
        drainage_data = [(r["data"].get("post_op_day", 0), r["data"]["drainage"])
                         for r in records if "drainage" in r["data"]]
        pain_data = [(r["data"].get("post_op_day", 0), r["data"]["pain_score"])
                     for r in records if "pain_score" in r["data"]]

        if not drainage_data and not pain_data:
            print("📭 无引流量或疼痛数据，无法生成图表")
            return ""

        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Drainage on left axis
        if drainage_data:
            days_d, vals_d = zip(*sorted(drainage_data))
            color1 = "#2196F3"
            ax1.plot(days_d, vals_d, marker="o", color=color1, linewidth=2, markersize=5, label="引流量 (mL)")
            ax1.set_ylabel("引流量 (mL)", color=color1, fontsize=12)
            ax1.tick_params(axis="y", labelcolor=color1)
            ax1.axhline(y=50, color=color1, linestyle="--", alpha=0.4, label="拔管参考线 (50mL)")

        ax1.set_xlabel("术后天数", fontsize=12)

        # Pain on right axis
        if pain_data:
            ax2 = ax1.twinx()
            days_p, vals_p = zip(*sorted(pain_data))
            color2 = "#FF5722"
            ax2.plot(days_p, vals_p, marker="s", color=color2, linewidth=2, markersize=5, label="疼痛评分")
            ax2.set_ylabel("疼痛评分 (NRS 0-10)", color=color2, fontsize=12)
            ax2.tick_params(axis="y", labelcolor=color2)
            ax2.set_ylim(0, 10)

        config = self.store.get_config()
        surgery_type = config.get("surgery_type", "")
        title = f"术后康复趋势 - {surgery_type}" if surgery_type else "术后康复趋势"
        ax1.set_title(title, fontsize=14)
        ax1.grid(True, alpha=0.3)

        # Combined legend
        handles1, labels1 = ax1.get_legend_handles_labels()
        if pain_data:
            handles2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper right", fontsize=9)
        else:
            ax1.legend(loc="upper right", fontsize=9)

        fig.tight_layout()
        path = os.path.join(self.store.charts_dir, "recovery_trend.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"📈 图表已保存: {path}")
        return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="术后康复追踪")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # configure
    p_conf = sub.add_parser("configure", help="配置手术信息")
    p_conf.add_argument("--type", required=True, help="手术类型")
    p_conf.add_argument("--date", required=True, help="手术日期 YYYY-MM-DD")
    p_conf.add_argument("--hospital", default="", help="医院名称")
    p_conf.add_argument("--surgeon", default="", help="主刀医生")
    p_conf.add_argument("--note", default="", help="备注")

    # record
    p_rec = sub.add_parser("record", help="记录康复数据")
    p_rec.add_argument("--drainage", type=float, default=None, help="引流量 mL")
    p_rec.add_argument("--wound", default=None, help="伤口状况")
    p_rec.add_argument("--pain", type=int, default=None, help="疼痛评分 0-10")
    p_rec.add_argument("--activity", default=None, help="活动水平")
    p_rec.add_argument("--diet", default=None, help="饮食状况")
    p_rec.add_argument("--temp", type=float, default=None, help="体温")
    p_rec.add_argument("--note", default="", help="备注")

    # progress
    sub.add_parser("progress", help="康复进度报告")

    # milestones
    sub.add_parser("milestones", help="里程碑检查")

    # recheck
    sub.add_parser("recheck", help="复查提醒")

    # chart
    sub.add_parser("chart", help="生成趋势图表")

    args = parser.parse_args()
    tracker = PostSurgeryRecovery()

    if args.command == "configure":
        tracker.configure(
            surgery_type=args.type,
            surgery_date=args.date,
            hospital=args.hospital,
            surgeon=args.surgeon,
            note=args.note,
        )
    elif args.command == "record":
        tracker.record(
            drainage=args.drainage,
            wound=args.wound,
            pain_score=args.pain,
            activity=args.activity,
            diet=args.diet,
            temp=args.temp,
            note=args.note,
        )
    elif args.command == "progress":
        tracker.generate_progress_report()
    elif args.command == "milestones":
        tracker.recovery_milestones()
    elif args.command == "recheck":
        tracker.remind_recheck()
    elif args.command == "chart":
        tracker.generate_chart()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
