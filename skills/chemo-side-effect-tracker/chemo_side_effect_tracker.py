#!/usr/bin/env python3
"""化疗副作用追踪 - 按CTCAE v5.0标准记录化疗副作用分级，支持周期对比和毒性报告。"""

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
# CTCAE v5.0 常见化疗毒性分级表
# ---------------------------------------------------------------------------
CTCAE_GRADES = {
    "恶心": {1: "食欲下降，不影响进食", 2: "摄入量减少，不影响脱水", 3: "摄入不足，需静脉补液", 4: "危及生命", 5: "死亡"},
    "呕吐": {1: "1-2次/24h", 2: "3-5次/24h", 3: "≥6次/24h，需静脉补液", 4: "危及生命", 5: "死亡"},
    "腹泻": {1: "较基线增加<4次/天", 2: "较基线增加4-6次/天", 3: "较基线增加≥7次/天，需住院", 4: "危及生命", 5: "死亡"},
    "骨髓抑制": {1: "轻度", 2: "中度", 3: "重度", 4: "危及生命", 5: "死亡"},
    "中性粒细胞减少": {1: "ANC 1.5-2.0×10⁹/L", 2: "ANC 1.0-1.5×10⁹/L", 3: "ANC 0.5-1.0×10⁹/L", 4: "ANC<0.5×10⁹/L", 5: "死亡"},
    "血小板减少": {1: "PLT 75-150×10⁹/L", 2: "PLT 50-75×10⁹/L", 3: "PLT 25-50×10⁹/L", 4: "PLT<25×10⁹/L", 5: "死亡"},
    "贫血": {1: "Hb 100-LLN g/L", 2: "Hb 80-100 g/L", 3: "Hb<80 g/L,需输血", 4: "危及生命", 5: "死亡"},
    "手足综合征": {1: "轻微皮肤改变", 2: "疼痛性皮肤改变，影响功能", 3: "严重皮肤改变，影响自理", 4: "-", 5: "-"},
    "周围神经病变": {1: "感觉异常", 2: "中度症状，影响功能", 3: "重度症状，影响自理", 4: "危及生命", 5: "死亡"},
    "口腔黏膜炎": {1: "无症状或轻微症状", 2: "中度疼痛，不影响进食", 3: "严重疼痛，影响进食", 4: "危及生命", 5: "死亡"},
    "脱发": {1: "脱发<50%", 2: "脱发≥50%", 3: "-", 4: "-", 5: "-"},
    "疲劳": {1: "轻度疲劳", 2: "中度疲劳，影响日常活动", 3: "重度疲劳，影响自理", 4: "-", 5: "-"},
    "皮疹": {1: "丘疹/脓疱<10%体表", 2: "10-30%体表", 3: ">30%体表", 4: "危及生命", 5: "死亡"},
    "肝功能异常": {1: "ALT/AST 1-3×ULN", 2: "ALT/AST 3-5×ULN", 3: "ALT/AST 5-20×ULN", 4: "ALT/AST>20×ULN", 5: "死亡"},
    "肾功能异常": {1: "Cr 1-1.5×ULN", 2: "Cr 1.5-3×ULN", 3: "Cr 3-6×ULN", 4: "Cr>6×ULN", 5: "死亡"},
    "发热": {1: "38.0-39.0°C", 2: "39.1-40.0°C", 3: ">40.0°C ≤24h", 4: ">40.0°C >24h", 5: "死亡"},
    "便秘": {1: "偶发或间歇性", 2: "持续性，需用泻药", 3: "需手动排便", 4: "危及生命", 5: "死亡"},
    "食欲减退": {1: "食欲下降", 2: "摄入量显著减少", 3: "需胃管/TPN", 4: "危及生命", 5: "死亡"},
    "高血压": {1: "SBP 120-139 或 DBP 80-89", 2: "SBP 140-159 或 DBP 90-99", 3: "SBP≥160 或 DBP≥100", 4: "危及生命", 5: "死亡"},
    "蛋白尿": {1: "1+ 或 0.15-1.0 g/24h", 2: "2+ 或 1.0-3.5 g/24h", 3: ">3.5 g/24h", 4: "肾病综合征", 5: "死亡"},
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
# ChemoSideEffectTracker
# ---------------------------------------------------------------------------
class ChemoSideEffectTracker:
    """化疗副作用追踪器，按CTCAE v5.0标准记录和分析毒性。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("chemo-side-effect-tracker", data_dir=data_dir)

    # ----- record -----
    def record(self, regimen: str, cycle: int, side_effects: list, note: str = "") -> dict:
        """记录一次化疗周期的副作用。

        Args:
            regimen: 化疗方案名称，如 FOLFOX
            cycle: 周期编号
            side_effects: 副作用列表，每项 {"name": "恶心", "grade": 2}
            note: 备注
        Returns:
            保存的记录
        """
        validated = []
        warnings = []
        for se in side_effects:
            name = se.get("name", "")
            grade = se.get("grade", 0)
            if name not in CTCAE_GRADES:
                warnings.append(f"⚠ '{name}' 不在CTCAE标准表中，仍予记录")
            if not (1 <= grade <= 5):
                warnings.append(f"⚠ '{name}' 分级 {grade} 超出1-5范围，已跳过")
                continue
            desc = ""
            if name in CTCAE_GRADES:
                desc = CTCAE_GRADES[name].get(grade, "")
            validated.append({"name": name, "grade": grade, "description": desc})

        data = {
            "regimen": regimen,
            "cycle": cycle,
            "side_effects": validated,
        }
        rec = self.store.append("side_effect", data, note=note)

        if warnings:
            for w in warnings:
                print(w)

        print(f"✅ 已记录 {regimen} 第{cycle}周期副作用 ({len(validated)}项)")
        for v in validated:
            grade_marker = "🔴" if v["grade"] >= 3 else ("🟡" if v["grade"] == 2 else "🟢")
            print(f"   {grade_marker} {v['name']}: {v['grade']}级 - {v['description']}")
        return rec

    # ----- trend_across_cycles -----
    def trend_across_cycles(self, regimen: str = None) -> dict:
        """分析副作用跨周期变化趋势。"""
        records = self.store.query(record_type="side_effect")
        if regimen:
            records = [r for r in records if r["data"].get("regimen") == regimen]
        if not records:
            print("📭 暂无副作用记录")
            return {"cycles": [], "trends": {}}

        # Organize by cycle
        cycle_data = {}
        for r in records:
            c = r["data"]["cycle"]
            for se in r["data"].get("side_effects", []):
                cycle_data.setdefault(se["name"], {})[c] = se["grade"]

        # Sort cycles
        all_cycles = sorted(set(c for mapping in cycle_data.values() for c in mapping))

        regime_label = regimen or "所有方案"
        print(f"\n📊 副作用趋势分析 - {regime_label}")
        print(f"{'副作用':<12} " + " ".join(f"C{c:<3}" for c in all_cycles) + "  趋势")
        print("-" * (14 + 5 * len(all_cycles) + 8))

        trends = {}
        for name in sorted(cycle_data.keys()):
            grades_by_cycle = cycle_data[name]
            row_values = [grades_by_cycle.get(c, None) for c in all_cycles]
            present_values = [v for v in row_values if v is not None]

            if len(present_values) >= 2:
                if present_values[-1] > present_values[0]:
                    direction = "↑加重"
                elif present_values[-1] < present_values[0]:
                    direction = "↓减轻"
                else:
                    direction = "→稳定"
            else:
                direction = "-"

            trends[name] = {"values": row_values, "cycles": all_cycles, "direction": direction}

            row_str = ""
            for v in row_values:
                if v is None:
                    row_str += " -   "
                else:
                    row_str += f" {v}   "
            print(f"{name:<12} {row_str} {direction}")

        return {"cycles": all_cycles, "trends": trends}

    # ----- worst_toxicity -----
    def worst_toxicity(self, regimen: str = None) -> list:
        """列出所有≥3级的严重毒性。"""
        records = self.store.query(record_type="side_effect")
        if regimen:
            records = [r for r in records if r["data"].get("regimen") == regimen]

        severe = []
        for r in records:
            for se in r["data"].get("side_effects", []):
                if se["grade"] >= 3:
                    severe.append({
                        "regimen": r["data"]["regimen"],
                        "cycle": r["data"]["cycle"],
                        "name": se["name"],
                        "grade": se["grade"],
                        "description": se.get("description", ""),
                        "date": r["timestamp"][:10],
                    })

        if not severe:
            print("✅ 未记录到≥3级严重毒性")
            return []

        severe.sort(key=lambda x: x["grade"], reverse=True)

        regime_label = regimen or "所有方案"
        print(f"\n🔴 严重毒性记录 (≥3级) - {regime_label}")
        print(f"{'方案':<10} {'周期':<6} {'副作用':<12} {'分级':<6} {'描述':<30} {'日期':<12}")
        print("-" * 80)
        for s in severe:
            print(f"{s['regimen']:<10} C{s['cycle']:<5} {s['name']:<12} {s['grade']}级    {s['description']:<30} {s['date']}")

        return severe

    # ----- generate_toxicity_report -----
    def generate_toxicity_report(self, regimen: str = None) -> str:
        """生成综合毒性报告。"""
        records = self.store.query(record_type="side_effect")
        if regimen:
            records = [r for r in records if r["data"].get("regimen") == regimen]

        if not records:
            msg = "📭 暂无副作用记录，无法生成报告"
            print(msg)
            return msg

        regime_label = regimen or "所有方案"

        # Summary stats
        total_cycles = len(set((r["data"]["regimen"], r["data"]["cycle"]) for r in records))
        all_effects = []
        for r in records:
            for se in r["data"].get("side_effects", []):
                all_effects.append({**se, "regimen": r["data"]["regimen"], "cycle": r["data"]["cycle"]})

        # By side effect type
        by_type = {}
        for e in all_effects:
            by_type.setdefault(e["name"], []).append(e["grade"])

        # Max grade per type
        max_grades = {name: max(grades) for name, grades in by_type.items()}
        avg_grades = {name: round(sum(grades) / len(grades), 1) for name, grades in by_type.items()}

        lines = []
        lines.append(f"═══ 化疗毒性综合报告 - {regime_label} ═══")
        lines.append(f"记录周期数: {total_cycles}")
        lines.append(f"副作用种类: {len(by_type)}")
        lines.append(f"≥3级毒性种类: {sum(1 for g in max_grades.values() if g >= 3)}")
        lines.append("")

        lines.append("── 各副作用汇总 ──")
        lines.append(f"{'副作用':<14} {'出现次数':<10} {'最高分级':<10} {'平均分级':<10} {'最高级描述'}")
        lines.append("-" * 80)
        for name in sorted(by_type.keys(), key=lambda n: max_grades[n], reverse=True):
            max_g = max_grades[name]
            desc = CTCAE_GRADES.get(name, {}).get(max_g, "")
            lines.append(f"{name:<14} {len(by_type[name]):<10} {max_g}级{'':>6} {avg_grades[name]:<10} {desc}")

        lines.append("")

        # By cycle
        cycle_map = {}
        for r in records:
            key = (r["data"]["regimen"], r["data"]["cycle"])
            for se in r["data"].get("side_effects", []):
                cycle_map.setdefault(key, []).append(se)

        lines.append("── 各周期毒性概览 ──")
        for (reg, cyc) in sorted(cycle_map.keys(), key=lambda x: (x[0], x[1])):
            effects = cycle_map[(reg, cyc)]
            max_g = max(e["grade"] for e in effects)
            marker = "🔴" if max_g >= 3 else ("🟡" if max_g == 2 else "🟢")
            effect_strs = [f"{e['name']}({e['grade']}级)" for e in effects]
            lines.append(f"  {marker} {reg} C{cyc}: {', '.join(effect_strs)}")

        # Alerts
        lines.append("")
        lines.append("── 警示 ──")
        has_alert = False
        for name, grades in by_type.items():
            if max(grades) >= 3:
                lines.append(f"  🔴 {name}: 出现过{max(grades)}级毒性，需密切关注")
                has_alert = True
            if len(grades) >= 3 and all(grades[i] <= grades[i + 1] for i in range(len(grades) - 1)) and grades[-1] > grades[0]:
                lines.append(f"  ⚠ {name}: 毒性呈持续加重趋势 ({' → '.join(str(g) for g in grades)})")
                has_alert = True
        if not has_alert:
            lines.append("  ✅ 暂无特殊警示")

        report = "\n".join(lines)
        print(report)
        return report

    # ----- generate_chart -----
    def generate_chart(self, regimen: str = None) -> str:
        """生成分组柱状图：X=周期, Y=分级, 按副作用类型分组。"""
        records = self.store.query(record_type="side_effect")
        if regimen:
            records = [r for r in records if r["data"].get("regimen") == regimen]

        if not records:
            print("📭 暂无数据，无法生成图表")
            return ""

        # Organize data
        cycle_effects = {}
        all_effect_names = set()
        for r in records:
            cyc = r["data"]["cycle"]
            for se in r["data"].get("side_effects", []):
                cycle_effects.setdefault(cyc, {})[se["name"]] = se["grade"]
                all_effect_names.add(se["name"])

        cycles = sorted(cycle_effects.keys())
        effect_names = sorted(all_effect_names)

        if not cycles or not effect_names:
            print("📭 数据不足，无法生成图表")
            return ""

        fig, ax = plt.subplots(figsize=(max(8, len(cycles) * 2), 5))

        n_effects = len(effect_names)
        bar_width = 0.8 / n_effects
        x_positions = list(range(len(cycles)))

        colors = plt.cm.Set3(range(n_effects))

        for i, ename in enumerate(effect_names):
            values = [cycle_effects.get(c, {}).get(ename, 0) for c in cycles]
            positions = [x + i * bar_width for x in x_positions]
            ax.bar(positions, values, bar_width, label=ename, color=colors[i], edgecolor="white")

        ax.set_xlabel("化疗周期")
        ax.set_ylabel("CTCAE分级")
        ax.set_title(f"化疗副作用分级趋势 - {regimen or '所有方案'}", fontsize=14)
        ax.set_xticks([x + bar_width * (n_effects - 1) / 2 for x in x_positions])
        ax.set_xticklabels([f"C{c}" for c in cycles])
        ax.set_ylim(0, 5.5)
        ax.set_yticks([0, 1, 2, 3, 4, 5])
        ax.axhline(y=3, color="red", linestyle="--", alpha=0.5, label="≥3级警戒线")
        ax.legend(loc="upper right", fontsize=8, ncol=2)
        ax.grid(True, axis="y", alpha=0.3)
        fig.tight_layout()

        path = os.path.join(self.store.charts_dir, f"toxicity_{regimen or 'all'}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"📈 图表已保存: {path}")
        return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_effects(effects_str: str) -> list:
    """Parse '恶心:2,手足综合征:1' into list of dicts."""
    result = []
    for item in effects_str.split(","):
        item = item.strip()
        if ":" not in item:
            continue
        name, grade_str = item.rsplit(":", 1)
        try:
            grade = int(grade_str.strip())
        except ValueError:
            continue
        result.append({"name": name.strip(), "grade": grade})
    return result


def main():
    parser = argparse.ArgumentParser(description="化疗副作用追踪 (CTCAE v5.0)")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # record
    p_rec = sub.add_parser("record", help="记录副作用")
    p_rec.add_argument("--regimen", required=True, help="化疗方案名称")
    p_rec.add_argument("--cycle", type=int, required=True, help="周期编号")
    p_rec.add_argument("--effects", required=True, help="副作用列表，格式: 恶心:2,手足综合征:1")
    p_rec.add_argument("--note", default="", help="备注")

    # trend
    p_trend = sub.add_parser("trend", help="副作用趋势分析")
    p_trend.add_argument("--regimen", default=None, help="化疗方案名称")

    # worst
    sub.add_parser("worst", help="列出严重毒性(≥3级)")

    # report
    p_report = sub.add_parser("report", help="生成综合毒性报告")
    p_report.add_argument("--regimen", default=None, help="化疗方案名称")

    # chart
    p_chart = sub.add_parser("chart", help="生成毒性图表")
    p_chart.add_argument("--regimen", default=None, help="化疗方案名称")

    args = parser.parse_args()
    tracker = ChemoSideEffectTracker()

    if args.command == "record":
        effects = parse_effects(args.effects)
        if not effects:
            print("❌ 无法解析副作用列表，请使用格式: 恶心:2,手足综合征:1")
            return
        tracker.record(args.regimen, args.cycle, effects, note=args.note)
    elif args.command == "trend":
        tracker.trend_across_cycles(regimen=args.regimen)
    elif args.command == "worst":
        tracker.worst_toxicity()
    elif args.command == "report":
        tracker.generate_toxicity_report(regimen=args.regimen)
    elif args.command == "chart":
        tracker.generate_chart(regimen=args.regimen)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
