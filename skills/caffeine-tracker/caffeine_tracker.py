#!/usr/bin/env python3
"""咖啡因追踪 — 记录摄入、半衰期衰减估算体内残留、计算安全入睡时间。"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore
from health_memory import HealthMemoryWriter


# ---------------------------------------------------------------------------
# CaffeineTracker
# ---------------------------------------------------------------------------

class CaffeineTracker:
    """咖啡因追踪：记录摄入、半衰期衰减估算体内残留、计算安全入睡时间。"""

    DRINKS = {
        "espresso":    {"mg": 63,  "name": "浓缩咖啡"},
        "drip_coffee": {"mg": 96,  "name": "滴滤咖啡"},
        "latte":       {"mg": 150, "name": "拿铁"},
        "americano":   {"mg": 96,  "name": "美式"},
        "green_tea":   {"mg": 28,  "name": "绿茶"},
        "black_tea":   {"mg": 47,  "name": "红茶"},
        "red_bull":    {"mg": 80,  "name": "红牛"},
        "cold_brew":   {"mg": 200, "name": "冷萃"},
        "matcha":      {"mg": 70,  "name": "抹茶"},
        "cola":        {"mg": 34,  "name": "可乐"},
    }

    def __init__(self, data_dir=None):
        self.store = HealthDataStore("caffeine-tracker", data_dir=data_dir)
        self.memory_writer = HealthMemoryWriter()
        self.half_life = 5.0        # hours
        self.sleep_threshold = 50   # mg

    # ----- log -----

    def log(self, drink, mg=None, volume_ml=None, time=None):
        """记录一次咖啡因摄入。

        Args:
            drink: 饮品名称 (英文key或自定义名称)
            mg: 咖啡因含量 (mg)，若饮品在内置数据库中可省略
            volume_ml: 饮品体积 (ml)，可选
            time: 摄入时间 (HH:MM 格式)，默认当前时间
        """
        # Resolve caffeine amount
        drink_info = self.DRINKS.get(drink)
        if mg is None:
            if drink_info:
                mg = drink_info["mg"]
            else:
                print(f"[错误] 未知饮品 '{drink}'，请用 --mg 指定咖啡因含量。")
                print(f"  已知饮品: {', '.join(self.DRINKS.keys())}")
                return

        # Resolve display name
        display_name = drink_info["name"] if drink_info else drink

        # Resolve time
        if time is None:
            time = datetime.now().strftime("%H:%M")

        data = {
            "drink": drink,
            "mg": mg,
            "time": time,
        }
        if volume_ml is not None:
            data["volume_ml"] = volume_ml

        self.store.append("intake", data)
        self._update_memory()

        print(f"[记录成功] {display_name} {mg}mg @ {time}")
        level = self._current_body_level()
        print(f"  当前体内咖啡因: ~{level:.0f}mg")
        safe = self._safe_sleep_time()
        print(f"  安全入睡时间: {safe}")

    # ----- decay calculation -----

    def _calculate_remaining(self, dose_mg, hours_elapsed):
        """计算经过 hours_elapsed 小时后体内残留的咖啡因量。"""
        if hours_elapsed < 0:
            return 0.0
        return dose_mg * (0.5 ** (hours_elapsed / self.half_life))

    # ----- today's intakes -----

    def _get_today_intakes(self):
        """获取今日所有摄入记录。"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_iso = today_start.isoformat()
        return self.store.query(record_type="intake", start=start_iso)

    # ----- current body level -----

    def _current_body_level(self):
        """估算当前体内咖啡因总量 (mg)。"""
        intakes = self._get_today_intakes()
        now = datetime.now()
        total = 0.0

        for rec in intakes:
            intake_time_str = rec["data"].get("time", "00:00")
            # Build full datetime from today's date + intake time
            try:
                h, m = map(int, intake_time_str.split(":"))
                intake_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            except (ValueError, TypeError):
                continue

            hours_elapsed = (now - intake_dt).total_seconds() / 3600.0
            remaining = self._calculate_remaining(rec["data"]["mg"], hours_elapsed)
            total += remaining

        return total

    # ----- safe sleep time -----

    def _safe_sleep_time(self):
        """计算安全入睡时间（体内咖啡因降至阈值以下）。"""
        current = self._current_body_level()
        if current <= self.sleep_threshold:
            return "现在 (已低于阈值)"

        now = datetime.now()
        intakes = self._get_today_intakes()

        # Search from now in 15-minute increments up to 24 hours
        for minutes_ahead in range(0, 24 * 60 + 1, 15):
            check_time = now + timedelta(minutes=minutes_ahead)
            level = 0.0
            for rec in intakes:
                intake_time_str = rec["data"].get("time", "00:00")
                try:
                    h, m = map(int, intake_time_str.split(":"))
                    intake_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                except (ValueError, TypeError):
                    continue
                hours_elapsed = (check_time - intake_dt).total_seconds() / 3600.0
                level += self._calculate_remaining(rec["data"]["mg"], hours_elapsed)

            if level <= self.sleep_threshold:
                return check_time.strftime("%H:%M")

        return ">24h (摄入量过高)"

    # ----- status -----

    def status(self):
        """显示当前咖啡因状态。"""
        intakes = self._get_today_intakes()
        level = self._current_body_level()
        safe = self._safe_sleep_time()
        daily_total = sum(r["data"]["mg"] for r in intakes)

        print(f"\n=== 咖啡因状态 ===")
        print(f"  当前体内残留: ~{level:.0f}mg")
        print(f"  安全入睡时间: {safe}")
        print(f"  今日总摄入:   {daily_total}mg ({len(intakes)} 次)")
        print(f"  半衰期:       {self.half_life}h")
        print(f"  入睡阈值:     {self.sleep_threshold}mg")

        if intakes:
            print(f"\n  今日摄入明细:")
            print(f"  {'时间':<8} {'饮品':<15} {'咖啡因':>6}")
            print(f"  {'-'*32}")
            for rec in intakes:
                d = rec["data"]
                drink_key = d.get("drink", "?")
                drink_info = self.DRINKS.get(drink_key)
                display = drink_info["name"] if drink_info else drink_key
                print(f"  {d.get('time', '?'):<8} {display:<15} {d['mg']:>5}mg")
        else:
            print(f"\n  今日暂无咖啡因摄入记录。")

    # ----- cutoff -----

    def cutoff(self):
        """显示今日咖啡因截止建议。"""
        level = self._current_body_level()
        safe = self._safe_sleep_time()
        intakes = self._get_today_intakes()
        daily_total = sum(r["data"]["mg"] for r in intakes)

        print(f"\n=== 咖啡因截止建议 ===")
        print(f"  当前体内残留: ~{level:.0f}mg")
        print(f"  今日总摄入:   {daily_total}mg")
        print(f"  安全入睡时间: {safe}")

        # Show what happens if user drinks one more espresso now
        if level > 0:
            extra_mg = 96  # americano as reference
            combined = level + extra_mg
            # How long until combined drops to threshold
            if combined > self.sleep_threshold:
                hours_needed = self.half_life * math.log2(combined / self.sleep_threshold)
                new_safe = (datetime.now() + timedelta(hours=hours_needed)).strftime("%H:%M")
                print(f"\n  如果现在再喝一杯美式 (+{extra_mg}mg):")
                print(f"    体内总量将升至 ~{combined:.0f}mg")
                print(f"    安全入睡时间将推迟至 {new_safe}")

        # FDA daily limit warning
        if daily_total > 400:
            print(f"\n  [警告] 今日摄入 {daily_total}mg 已超过 FDA 建议上限 (400mg/天)!")
        elif daily_total > 300:
            print(f"\n  [提醒] 今日摄入 {daily_total}mg，接近 FDA 建议上限 (400mg/天)。")

    # ----- history -----

    def history(self, days=7):
        """显示过去 N 天的咖啡因摄入历史。"""
        start = (datetime.now() - timedelta(days=days)).isoformat()
        records = self.store.query(record_type="intake", start=start)

        print(f"\n=== 咖啡因摄入历史 (近 {days} 天) ===")

        if not records:
            print("  暂无记录。")
            return

        # Group by date
        daily = {}
        for rec in records:
            date_str = rec["timestamp"][:10]
            if date_str not in daily:
                daily[date_str] = []
            daily[date_str].append(rec)

        print(f"  {'日期':<12} {'次数':>4} {'总量':>8} {'饮品明细'}")
        print(f"  {'-'*55}")

        for date_str in sorted(daily.keys()):
            recs = daily[date_str]
            total = sum(r["data"]["mg"] for r in recs)
            drinks = []
            for r in recs:
                drink_key = r["data"].get("drink", "?")
                drink_info = self.DRINKS.get(drink_key)
                display = drink_info["name"] if drink_info else drink_key
                drinks.append(display)
            drink_summary = ", ".join(drinks)
            print(f"  {date_str:<12} {len(recs):>4} {total:>6}mg  {drink_summary}")

        grand_total = sum(r["data"]["mg"] for r in records)
        avg_daily = grand_total / max(len(daily), 1)
        print(f"\n  总计: {grand_total}mg / {len(daily)} 天 (日均 {avg_daily:.0f}mg)")

    # ----- chart -----

    def chart(self, days=14):
        """生成今日 24 小时咖啡因衰减曲线图。"""
        intakes = self._get_today_intakes()

        if not intakes:
            print("今日暂无咖啡因摄入记录，无法生成图表。")
            return ""

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Build time axis: every 5 minutes from 00:00 to 23:59
        time_points = []
        levels = []
        for minute in range(0, 24 * 60, 5):
            t = today_start + timedelta(minutes=minute)
            time_points.append(minute / 60.0)  # hours as float
            level = 0.0
            for rec in intakes:
                intake_time_str = rec["data"].get("time", "00:00")
                try:
                    h, m = map(int, intake_time_str.split(":"))
                    intake_hour = h + m / 60.0
                except (ValueError, TypeError):
                    continue
                hours_elapsed = (minute / 60.0) - intake_hour
                if hours_elapsed >= 0:
                    level += self._calculate_remaining(rec["data"]["mg"], hours_elapsed)
            levels.append(level)

        # Intake markers
        intake_hours = []
        intake_mgs = []
        for rec in intakes:
            intake_time_str = rec["data"].get("time", "00:00")
            try:
                h, m = map(int, intake_time_str.split(":"))
                intake_hours.append(h + m / 60.0)
                intake_mgs.append(rec["data"]["mg"])
            except (ValueError, TypeError):
                continue

        # Plot
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(time_points, levels, linewidth=2, color="#8B4513", label="体内咖啡因 (mg)")
        ax.fill_between(time_points, levels, alpha=0.15, color="#8B4513")

        # Mark each intake
        for ih, img in zip(intake_hours, intake_mgs):
            ax.axvline(x=ih, color="#D2691E", linestyle=":", alpha=0.6)
            # Find the level at intake time for the marker
            idx = int(ih * 60 / 5)
            if 0 <= idx < len(levels):
                ax.plot(ih, levels[idx], "v", color="#D2691E", markersize=10)
                ax.annotate(f"+{img}mg", (ih, levels[idx]),
                            textcoords="offset points", xytext=(5, 10),
                            fontsize=9, color="#D2691E", fontweight="bold")

        # Sleep threshold line
        ax.axhline(y=self.sleep_threshold, color="green", linestyle="--",
                    alpha=0.7, label=f"入睡阈值 ({self.sleep_threshold}mg)")

        # Current time marker
        current_hour = now.hour + now.minute / 60.0
        ax.axvline(x=current_hour, color="blue", linestyle="-.", alpha=0.5,
                    label=f"当前时间 ({now.strftime('%H:%M')})")

        ax.set_title(f"今日咖啡因衰减曲线 ({now.strftime('%Y-%m-%d')})", fontsize=14)
        ax.set_xlabel("时间 (小时)")
        ax.set_ylabel("咖啡因 (mg)")
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)], rotation=45)
        ax.set_ylim(bottom=0)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        chart_path = os.path.join(
            self.store.charts_dir,
            f"caffeine_decay_{now.strftime('%Y%m%d')}.png"
        )
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"咖啡因衰减曲线已保存: {chart_path}")
        return chart_path

    # ----- memory update -----

    def _update_memory(self):
        """更新 health memory 文件。"""
        level = self._current_body_level()
        intakes = self._get_today_intakes()
        safe = self._safe_sleep_time()

        intake_list = []
        for rec in intakes:
            d = rec["data"]
            drink_key = d.get("drink", "?")
            drink_info = self.DRINKS.get(drink_key)
            display = drink_info["name"] if drink_info else drink_key
            intake_list.append({
                "time": d.get("time", "?"),
                "drink": display,
                "mg": d.get("mg", 0),
            })

        self.memory_writer.update_caffeine(level, intake_list, safe)
        self.memory_writer.update_daily_snapshot()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="咖啡因追踪")
    sub = parser.add_subparsers(dest="command")

    # log
    p_log = sub.add_parser("log", help="记录咖啡因摄入")
    p_log.add_argument("--drink", required=True,
                       help=f"饮品名称 ({', '.join(CaffeineTracker.DRINKS.keys())})")
    p_log.add_argument("--mg", type=int, default=None, help="咖啡因含量 (mg)")
    p_log.add_argument("--volume", type=int, default=None, help="饮品体积 (ml)")
    p_log.add_argument("--time", default=None, help="摄入时间 (HH:MM)")
    p_log.add_argument("--data-dir", default=None, help="数据目录")

    # status
    p_status = sub.add_parser("status", help="当前咖啡因状态")
    p_status.add_argument("--data-dir", default=None, help="数据目录")

    # cutoff
    p_cutoff = sub.add_parser("cutoff", help="咖啡因截止建议")
    p_cutoff.add_argument("--data-dir", default=None, help="数据目录")

    # history
    p_history = sub.add_parser("history", help="摄入历史")
    p_history.add_argument("--days", type=int, default=7, help="天数")
    p_history.add_argument("--data-dir", default=None, help="数据目录")

    # chart
    p_chart = sub.add_parser("chart", help="生成衰减曲线图")
    p_chart.add_argument("--days", type=int, default=14, help="天数")
    p_chart.add_argument("--data-dir", default=None, help="数据目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = CaffeineTracker(data_dir=getattr(args, "data_dir", None))

    if args.command == "log":
        tracker.log(args.drink, mg=args.mg, volume_ml=args.volume, time=args.time)
    elif args.command == "status":
        tracker.status()
    elif args.command == "cutoff":
        tracker.cutoff()
    elif args.command == "history":
        tracker.history(days=args.days)
    elif args.command == "chart":
        tracker.chart(days=args.days)


if __name__ == "__main__":
    main()
