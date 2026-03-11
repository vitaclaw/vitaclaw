#!/usr/bin/env python3
"""睡眠分析 — 记录睡眠数据，计算效率与评分，关联咖啡因数据分析。"""

import argparse
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore
from health_memory import HealthMemoryWriter
from cross_skill_reader import CrossSkillReader


# ---------------------------------------------------------------------------
# SleepAnalyzer
# ---------------------------------------------------------------------------

class SleepAnalyzer:
    """睡眠分析：记录睡眠数据，计算效率与评分，支持Apple Health导入，关联咖啡因数据分析。"""

    def __init__(self, data_dir=None):
        self.store = HealthDataStore("sleep-analyzer", data_dir=data_dir)
        self.memory_writer = HealthMemoryWriter()
        self.cross_reader = CrossSkillReader(data_dir=data_dir)

    # ----- log -----

    def log(self, bedtime, wake_time, deep_min=None, light_min=None,
            rem_min=None, awake_min=None, date=None, source="manual"):
        """记录一次睡眠。

        Args:
            bedtime: 就寝时间 (HH:MM 格式)
            wake_time: 起床时间 (HH:MM 格式)
            deep_min: 深睡时长 (分钟)，可选
            light_min: 浅睡时长 (分钟)，可选
            rem_min: REM睡眠时长 (分钟)，可选
            awake_min: 夜间清醒时长 (分钟)，可选
            date: 日期 (YYYY-MM-DD 格式)，默认自动推断
            source: 数据来源，默认 "manual"
        """
        # Parse bedtime and wake_time
        bed_h, bed_m = map(int, bedtime.split(":"))
        wake_h, wake_m = map(int, wake_time.split(":"))

        # Determine date: if bedtime > wake_time (overnight), date is yesterday
        if date is None:
            today = datetime.now().date()
            if bed_h > wake_h or (bed_h == wake_h and bed_m > wake_m):
                # Overnight sleep — date is yesterday (when you went to bed)
                date = (today - timedelta(days=1)).isoformat()
            else:
                date = today.isoformat()

        # Calculate total time in bed (minutes)
        bed_dt = datetime(2000, 1, 1, bed_h, bed_m)
        wake_dt = datetime(2000, 1, 1, wake_h, wake_m)
        if wake_dt <= bed_dt:
            # Overnight: add 24 hours to wake time
            wake_dt += timedelta(days=1)
        total_min = int((wake_dt - bed_dt).total_seconds() / 60)

        # Sleep efficiency: (time_in_bed - awake_time) / time_in_bed * 100
        aw = awake_min or 0
        sleep_min = total_min - aw
        efficiency_pct = round(sleep_min / total_min * 100, 1) if total_min > 0 else 0.0

        # Calculate score
        score = self._calculate_score(total_min, deep_min, light_min,
                                      rem_min, awake_min, efficiency_pct)

        data = {
            "date": date,
            "bedtime": bedtime,
            "wake_time": wake_time,
            "total_min": total_min,
            "deep_min": deep_min,
            "light_min": light_min,
            "rem_min": rem_min,
            "awake_min": aw,
            "efficiency_pct": efficiency_pct,
            "score": score,
            "source": source,
        }

        self.store.append("sleep_session", data)

        # Print summary
        hours, mins = divmod(total_min, 60)
        sleep_hours, sleep_mins = divmod(sleep_min, 60)
        print(f"\n[记录成功] {date} 睡眠")
        print(f"  就寝: {bedtime}  起床: {wake_time}")
        print(f"  在床时间: {hours}h{mins}m  实际睡眠: {sleep_hours}h{sleep_mins}m")
        print(f"  睡眠效率: {efficiency_pct}%")
        if deep_min is not None:
            print(f"  深睡: {deep_min}min  浅睡: {light_min or '?'}min  "
                  f"REM: {rem_min or '?'}min  清醒: {aw}min")
        print(f"  睡眠评分: {score}/100")

        self._update_memory()

    # ----- _calculate_score -----

    def _calculate_score(self, total_min, deep_min, light_min, rem_min,
                         awake_min, efficiency_pct):
        """计算睡眠评分 (0-100)。

        有阶段数据时:
          - 效率 40%  + 深睡占比 25% + REM占比 20% + 时长 15%
        无阶段数据时:
          - 效率 60%  + 时长 40%
        """
        has_stages = deep_min is not None or rem_min is not None

        # Duration component: ideal 420-540 min (7-9 hours)
        if 420 <= total_min <= 540:
            duration_score = 1.0
        else:
            duration_score = max(0.0, 1.0 - abs(total_min - 480) / 180)

        if has_stages:
            # Efficiency component (weight 0.4)
            efficiency_component = efficiency_pct * 0.4

            # Deep sleep component (weight 0.25): ideal ~20% of total
            if deep_min is not None and total_min > 0:
                deep_pct = (deep_min / total_min) * 100
                deep_component = min(deep_pct, 25.0) * 0.25
            else:
                deep_component = 0.0

            # REM component (weight 0.20): ideal ~25% of total
            if rem_min is not None and total_min > 0:
                rem_pct = (rem_min / total_min) * 100
                rem_component = min(rem_pct, 25.0) * 0.20
            else:
                rem_component = 0.0

            # Duration component (weight 0.15)
            duration_component = duration_score * 15.0

            score = efficiency_component + deep_component + rem_component + duration_component
        else:
            # Without stage data: efficiency 60% + duration 40%
            efficiency_component = efficiency_pct * 0.6
            duration_component = duration_score * 40.0
            score = efficiency_component + duration_component

        return min(round(score), 100)

    # ----- import_apple_health -----

    def import_apple_health(self, filepath):
        """从 Apple Health 导出 XML 文件导入睡眠数据。

        Args:
            filepath: Apple Health export.xml 文件路径
        """
        if not os.path.exists(filepath):
            print(f"[错误] 文件不存在: {filepath}")
            return

        print(f"正在解析 Apple Health 数据: {filepath}")
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Apple Health sleep analysis type identifier
        sleep_type = "HKCategoryTypeIdentifierSleepAnalysis"

        # Collect all sleep records
        sleep_records = []
        for record in root.iter("Record"):
            if record.get("type") == sleep_type:
                sleep_records.append(record)

        if not sleep_records:
            print("[提示] 未找到睡眠分析数据。")
            return

        # Apple sleep value mapping
        # HKCategoryValueSleepAnalysis values:
        #   InBed = 0, Asleep = 1 (legacy)
        #   AsleepUnspecified = 1, AsleepCore = 3, AsleepDeep = 4, AsleepREM = 5
        #   Awake = 2
        STAGE_MAP = {
            "HKCategoryValueSleepAnalysisInBed": "inbed",
            "HKCategoryValueSleepAnalysisAsleepUnspecified": "light",
            "HKCategoryValueSleepAnalysisAsleep": "light",
            "HKCategoryValueSleepAnalysisAsleepCore": "light",
            "HKCategoryValueSleepAnalysisAsleepDeep": "deep",
            "HKCategoryValueSleepAnalysisAsleepREM": "rem",
            "HKCategoryValueSleepAnalysisAwake": "awake",
        }

        # Group entries by night (use the date of the start time)
        # For overnight sleep, group by the evening date
        nights = {}
        for rec in sleep_records:
            value = rec.get("value", "")
            stage = STAGE_MAP.get(value)
            if stage is None:
                continue

            start_str = rec.get("startDate", "")
            end_str = rec.get("endDate", "")
            if not start_str or not end_str:
                continue

            try:
                # Apple Health format: 2026-01-15 22:30:00 +0800
                start_dt = datetime.strptime(start_str[:19], "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_str[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            duration_min = (end_dt - start_dt).total_seconds() / 60.0

            # Determine night date: if start is before 18:00, it belongs to
            # previous night; otherwise it's tonight
            if start_dt.hour < 18:
                night_date = (start_dt.date() - timedelta(days=1)).isoformat()
            else:
                night_date = start_dt.date().isoformat()

            if night_date not in nights:
                nights[night_date] = {
                    "entries": [],
                    "earliest_start": start_dt,
                    "latest_end": end_dt,
                }

            nights[night_date]["entries"].append({
                "stage": stage,
                "start": start_dt,
                "end": end_dt,
                "duration_min": duration_min,
            })

            if start_dt < nights[night_date]["earliest_start"]:
                nights[night_date]["earliest_start"] = start_dt
            if end_dt > nights[night_date]["latest_end"]:
                nights[night_date]["latest_end"] = end_dt

        # Process each night
        imported = 0
        for night_date in sorted(nights.keys()):
            night = nights[night_date]
            entries = night["entries"]
            earliest = night["earliest_start"]
            latest = night["latest_end"]

            bedtime = earliest.strftime("%H:%M")
            wake_time = latest.strftime("%H:%M")
            total_min = int((latest - earliest).total_seconds() / 60)

            # Sum up stage durations
            deep_total = sum(e["duration_min"] for e in entries if e["stage"] == "deep")
            light_total = sum(e["duration_min"] for e in entries if e["stage"] == "light")
            rem_total = sum(e["duration_min"] for e in entries if e["stage"] == "rem")
            awake_total = sum(e["duration_min"] for e in entries if e["stage"] == "awake")

            deep_min = round(deep_total) if deep_total > 0 else None
            light_min = round(light_total) if light_total > 0 else None
            rem_min = round(rem_total) if rem_total > 0 else None
            awake_min = round(awake_total) if awake_total > 0 else 0

            efficiency_pct = round((total_min - awake_min) / total_min * 100, 1) if total_min > 0 else 0.0
            score = self._calculate_score(total_min, deep_min, light_min,
                                          rem_min, awake_min, efficiency_pct)

            data = {
                "date": night_date,
                "bedtime": bedtime,
                "wake_time": wake_time,
                "total_min": total_min,
                "deep_min": deep_min,
                "light_min": light_min,
                "rem_min": rem_min,
                "awake_min": awake_min,
                "efficiency_pct": efficiency_pct,
                "score": score,
                "source": "apple_health",
            }

            self.store.append("sleep_session", data)
            imported += 1

        print(f"\n[导入完成] 共导入 {imported} 晚睡眠数据 (来源: Apple Health)")
        if imported > 0:
            print(f"  日期范围: {sorted(nights.keys())[0]} ~ {sorted(nights.keys())[-1]}")
            self._update_memory()

    # ----- score -----

    def score(self, n=1):
        """显示最近 N 晚的睡眠评分详情。

        Args:
            n: 查看最近几晚，默认 1
        """
        sessions = self.store.get_latest(record_type="sleep_session", n=n)

        if not sessions:
            print("暂无睡眠记录。")
            return

        for rec in sessions:
            d = rec["data"]
            date = d.get("date", "?")
            total_min = d.get("total_min", 0)
            deep_min = d.get("deep_min")
            rem_min = d.get("rem_min")
            awake_min = d.get("awake_min", 0)
            efficiency = d.get("efficiency_pct", 0)
            score_val = d.get("score", 0)

            hours, mins = divmod(total_min, 60)
            has_stages = deep_min is not None or rem_min is not None

            print(f"\n=== 睡眠评分 {date} ===")
            print(f"  总分: {score_val}/100")
            print(f"  就寝: {d.get('bedtime', '?')}  起床: {d.get('wake_time', '?')}")
            print(f"  在床时间: {hours}h{mins}m")
            print(f"  睡眠效率: {efficiency}%")

            print(f"\n  评分分解:")
            if has_stages:
                eff_component = round(efficiency * 0.4, 1)
                print(f"    效率分 (40%):  {eff_component:.1f}")

                if deep_min is not None and total_min > 0:
                    deep_pct = (deep_min / total_min) * 100
                    deep_component = round(min(deep_pct, 25.0) * 0.25, 1)
                    print(f"    深睡分 (25%):  {deep_component:.1f}  "
                          f"(深睡 {deep_min}min, 占比 {deep_pct:.1f}%)")
                else:
                    print(f"    深睡分 (25%):  0.0  (无数据)")

                if rem_min is not None and total_min > 0:
                    rem_pct = (rem_min / total_min) * 100
                    rem_component = round(min(rem_pct, 25.0) * 0.20, 1)
                    print(f"    REM分 (20%):   {rem_component:.1f}  "
                          f"(REM {rem_min}min, 占比 {rem_pct:.1f}%)")
                else:
                    print(f"    REM分 (20%):   0.0  (无数据)")

                if 420 <= total_min <= 540:
                    dur_component = 15.0
                else:
                    dur_component = round(15.0 * max(0.0, 1.0 - abs(total_min - 480) / 180), 1)
                print(f"    时长分 (15%):  {dur_component:.1f}  ({hours}h{mins}m)")
            else:
                eff_component = round(efficiency * 0.6, 1)
                print(f"    效率分 (60%):  {eff_component:.1f}")
                if 420 <= total_min <= 540:
                    dur_component = 40.0
                else:
                    dur_component = round(40.0 * max(0.0, 1.0 - abs(total_min - 480) / 180), 1)
                print(f"    时长分 (40%):  {dur_component:.1f}  ({hours}h{mins}m)")

            if awake_min > 0:
                print(f"    夜间清醒: {awake_min}min")

    # ----- trend -----

    def trend(self, days=14):
        """显示最近 N 天的睡眠趋势。

        Args:
            days: 查看天数，默认 14
        """
        start = (datetime.now() - timedelta(days=days)).isoformat()
        sessions = self.store.query(record_type="sleep_session", start=start)

        print(f"\n=== 睡眠趋势 (近 {days} 天) ===")

        if not sessions:
            print("  暂无睡眠记录。")
            return

        scores = [r["data"].get("score", 0) for r in sessions]
        efficiencies = [r["data"].get("efficiency_pct", 0) for r in sessions]
        totals = [r["data"].get("total_min", 0) for r in sessions]

        avg_score = sum(scores) / len(scores)
        avg_efficiency = sum(efficiencies) / len(efficiencies)
        avg_total = sum(totals) / len(totals)

        # Trend direction via simple linear slope
        trend_info = self.store.trend("sleep_session", "score", window=days)
        direction = trend_info.get("direction", "stable")
        direction_cn = {"rising": "上升", "falling": "下降", "stable": "稳定",
                        "insufficient_data": "数据不足"}.get(direction, direction)

        avg_h, avg_m = divmod(int(avg_total), 60)
        print(f"  记录数: {len(sessions)} 晚")
        print(f"  平均评分:   {avg_score:.1f}/100")
        print(f"  平均时长:   {avg_h}h{avg_m}m")
        print(f"  平均效率:   {avg_efficiency:.1f}%")
        print(f"  趋势方向:   {direction_cn}")

        # Per-night table
        print(f"\n  {'日期':<12} {'就寝':<6} {'起床':<6} {'时长':>6} {'效率':>6} {'评分':>4}")
        print(f"  {'-'*48}")
        for rec in sessions:
            d = rec["data"]
            total = d.get("total_min", 0)
            h, m = divmod(total, 60)
            print(f"  {d.get('date', '?'):<12} "
                  f"{d.get('bedtime', '?'):<6} "
                  f"{d.get('wake_time', '?'):<6} "
                  f"{h}h{m:02d}m  "
                  f"{d.get('efficiency_pct', 0):>5.1f}% "
                  f"{d.get('score', 0):>4}")

    # ----- correlate -----

    def correlate(self, days=14):
        """分析睡眠与咖啡因摄入的关联。

        Args:
            days: 分析天数，默认 14
        """
        start_iso = (datetime.now() - timedelta(days=days)).isoformat()

        # Get sleep sessions
        sessions = self.store.query(record_type="sleep_session", start=start_iso)
        if not sessions:
            print("暂无睡眠记录，无法进行关联分析。")
            return

        # Get caffeine intakes via cross-skill reader
        caffeine_intakes = self.cross_reader.read_caffeine_intakes(start=start_iso)

        if not caffeine_intakes:
            print("暂无咖啡因摄入记录，无法进行关联分析。")
            print("[提示] 使用 caffeine-tracker 记录咖啡因摄入后再来分析。")
            return

        # Group caffeine by date
        caffeine_by_date = {}
        for rec in caffeine_intakes:
            date_str = rec["timestamp"][:10]
            if date_str not in caffeine_by_date:
                caffeine_by_date[date_str] = []
            caffeine_by_date[date_str].append(rec)

        # Build correlation records
        correlations = []
        for session in sessions:
            sd = session["data"]
            sleep_date = sd.get("date", "")
            bedtime = sd.get("bedtime", "00:00")
            sleep_score = sd.get("score", 0)

            # Get caffeine for this date
            day_caffeine = caffeine_by_date.get(sleep_date, [])
            caffeine_total = sum(r["data"].get("mg", 0) for r in day_caffeine)

            # Hours between last caffeine and bedtime
            last_caffeine_hours = None
            if day_caffeine:
                bed_h, bed_m = map(int, bedtime.split(":"))
                bed_minutes = bed_h * 60 + bed_m
                if bed_minutes < 360:
                    # Bedtime before 6 AM means overnight, treat as next day
                    bed_minutes += 24 * 60

                last_time = "00:00"
                for rec in day_caffeine:
                    t = rec["data"].get("time", "00:00")
                    if t > last_time:
                        last_time = t
                lc_h, lc_m = map(int, last_time.split(":"))
                lc_minutes = lc_h * 60 + lc_m
                last_caffeine_hours = round((bed_minutes - lc_minutes) / 60.0, 1)

            corr_data = {
                "date": sleep_date,
                "sleep_score": sleep_score,
                "caffeine_total_mg": caffeine_total,
                "last_caffeine_hours_before_bed": last_caffeine_hours,
            }
            correlations.append(corr_data)
            self.store.append("correlation", corr_data)

        # Analyze: split into high-caffeine and low-caffeine days
        if len(correlations) < 2:
            print("关联数据不足 (需至少 2 天)。")
            return

        caffeine_amounts = [c["caffeine_total_mg"] for c in correlations]
        median_caffeine = sorted(caffeine_amounts)[len(caffeine_amounts) // 2]

        high_caffeine_scores = [c["sleep_score"] for c in correlations
                                if c["caffeine_total_mg"] > median_caffeine]
        low_caffeine_scores = [c["sleep_score"] for c in correlations
                               if c["caffeine_total_mg"] <= median_caffeine]

        print(f"\n=== 睡眠-咖啡因关联分析 (近 {days} 天) ===")
        print(f"  分析天数: {len(correlations)} 天")
        print(f"  咖啡因中位数: {median_caffeine}mg/天")

        if high_caffeine_scores:
            avg_high = sum(high_caffeine_scores) / len(high_caffeine_scores)
            print(f"\n  高咖啡因日 (>{median_caffeine}mg):")
            print(f"    天数: {len(high_caffeine_scores)}")
            print(f"    平均睡眠评分: {avg_high:.1f}")

        if low_caffeine_scores:
            avg_low = sum(low_caffeine_scores) / len(low_caffeine_scores)
            print(f"\n  低咖啡因日 (<={median_caffeine}mg):")
            print(f"    天数: {len(low_caffeine_scores)}")
            print(f"    平均睡眠评分: {avg_low:.1f}")

        if high_caffeine_scores and low_caffeine_scores:
            avg_high = sum(high_caffeine_scores) / len(high_caffeine_scores)
            avg_low = sum(low_caffeine_scores) / len(low_caffeine_scores)
            diff = avg_low - avg_high

            if diff > 5:
                effect = f"高咖啡因日睡眠评分平均低 {diff:.1f} 分，咖啡因可能影响睡眠质量"
            elif diff < -5:
                effect = f"高咖啡因日睡眠评分反而高 {abs(diff):.1f} 分，未见负面影响"
            else:
                effect = "咖啡因摄入量对睡眠评分无显著影响"
            print(f"\n  结论: {effect}")

        # Analyze late caffeine effect
        late_scores = [c["sleep_score"] for c in correlations
                       if c["last_caffeine_hours_before_bed"] is not None
                       and c["last_caffeine_hours_before_bed"] < 6]
        early_scores = [c["sleep_score"] for c in correlations
                        if c["last_caffeine_hours_before_bed"] is not None
                        and c["last_caffeine_hours_before_bed"] >= 6]

        if late_scores and early_scores:
            avg_late = sum(late_scores) / len(late_scores)
            avg_early = sum(early_scores) / len(early_scores)
            print(f"\n  睡前6h内有咖啡因: 平均评分 {avg_late:.1f} ({len(late_scores)} 天)")
            print(f"  睡前6h外无咖啡因: 平均评分 {avg_early:.1f} ({len(early_scores)} 天)")

        # Detail table
        print(f"\n  {'日期':<12} {'睡眠分':>6} {'咖啡因':>8} {'末次距睡':>8}")
        print(f"  {'-'*38}")
        for c in correlations:
            lch = c.get("last_caffeine_hours_before_bed")
            lch_str = f"{lch:.1f}h" if lch is not None else "-"
            print(f"  {c['date']:<12} {c['sleep_score']:>6} "
                  f"{c['caffeine_total_mg']:>6}mg {lch_str:>8}")

    # ----- chart -----

    def chart(self, days=14):
        """生成睡眠阶段堆叠柱状图。

        Args:
            days: 图表天数，默认 14
        """
        start = (datetime.now() - timedelta(days=days)).isoformat()
        sessions = self.store.query(record_type="sleep_session", start=start)

        if not sessions:
            print("暂无睡眠记录，无法生成图表。")
            return ""

        dates = []
        deep_vals = []
        light_vals = []
        rem_vals = []
        awake_vals = []
        has_any_stages = False

        for rec in sessions:
            d = rec["data"]
            dates.append(d.get("date", "?"))
            deep = d.get("deep_min") or 0
            light = d.get("light_min") or 0
            rem = d.get("rem_min") or 0
            awake = d.get("awake_min") or 0

            if d.get("deep_min") is not None or d.get("rem_min") is not None:
                has_any_stages = True

            deep_vals.append(deep)
            light_vals.append(light)
            rem_vals.append(rem)
            awake_vals.append(awake)

        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(dates))

        if has_any_stages:
            # Stacked bar chart with sleep stages
            ax.bar(x, deep_vals, color="navy", label="Deep", alpha=0.9)
            ax.bar(x, light_vals, bottom=deep_vals, color="skyblue",
                   label="Light", alpha=0.9)
            bottom_rem = [d + l for d, l in zip(deep_vals, light_vals)]
            ax.bar(x, rem_vals, bottom=bottom_rem, color="purple",
                   label="REM", alpha=0.9)
            bottom_awake = [b + r for b, r in zip(bottom_rem, rem_vals)]
            ax.bar(x, awake_vals, bottom=bottom_awake, color="salmon",
                   label="Awake", alpha=0.9)
        else:
            # Simple bar chart with total sleep time
            total_vals = [rec["data"].get("total_min", 0) for rec in sessions]
            awake_vals_chart = [rec["data"].get("awake_min", 0) for rec in sessions]
            sleep_vals = [t - a for t, a in zip(total_vals, awake_vals_chart)]
            ax.bar(x, sleep_vals, color="steelblue", label="Sleep", alpha=0.9)
            ax.bar(x, awake_vals_chart, bottom=sleep_vals, color="salmon",
                   label="Awake", alpha=0.9)

        # Reference lines
        ax.axhline(y=420, color="green", linestyle="--", alpha=0.5, label="7h minimum")
        ax.axhline(y=480, color="green", linestyle="-.", alpha=0.3, label="8h ideal")

        ax.set_title(f"Sleep Stages (last {days} days)", fontsize=14)
        ax.set_ylabel("Minutes")
        ax.set_xticks(x)
        ax.set_xticklabels([d[-5:] for d in dates], rotation=45, ha="right")
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()

        now = datetime.now()
        chart_path = os.path.join(
            self.store.charts_dir,
            f"sleep_stages_{now.strftime('%Y%m%d')}.png"
        )
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"睡眠阶段图已保存: {chart_path}")
        return chart_path

    # ----- _update_memory -----

    def _update_memory(self):
        """更新 health memory 文件。"""
        latest = self.store.get_latest(record_type="sleep_session", n=1)
        last_night = latest[0]["data"] if latest else None

        seven_day = self._seven_day_summary()

        # Check for correlation data
        corr_records = self.store.get_latest(record_type="correlation", n=1)
        correlations = None
        if corr_records:
            cd = corr_records[0]["data"]
            caffeine_total = cd.get("caffeine_total_mg", 0)
            if caffeine_total > 0:
                correlations = {
                    "caffeine_effect": (
                        f"Last recorded day: {cd.get('caffeine_total_mg', 0)}mg caffeine, "
                        f"sleep score {cd.get('sleep_score', '?')}"
                    ),
                }

        self.memory_writer.update_sleep(last_night, seven_day, correlations)
        self.memory_writer.update_daily_snapshot()

    # ----- _seven_day_summary -----

    def _seven_day_summary(self):
        """计算最近 7 天的睡眠摘要。

        Returns:
            dict with avg_score, avg_total_min, avg_efficiency, trend_direction
        """
        start = (datetime.now() - timedelta(days=7)).isoformat()
        sessions = self.store.query(record_type="sleep_session", start=start)

        if not sessions:
            return None

        scores = [r["data"].get("score", 0) for r in sessions]
        totals = [r["data"].get("total_min", 0) for r in sessions]
        efficiencies = [r["data"].get("efficiency_pct", 0) for r in sessions]

        trend_info = self.store.trend("sleep_session", "score", window=7)
        direction = trend_info.get("direction", "stable")

        return {
            "avg_score": round(sum(scores) / len(scores), 1),
            "avg_total_min": round(sum(totals) / len(totals), 1),
            "avg_efficiency": round(sum(efficiencies) / len(efficiencies), 1),
            "trend_direction": direction,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="睡眠分析")
    sub = parser.add_subparsers(dest="command")

    # log
    p_log = sub.add_parser("log", help="记录睡眠")
    p_log.add_argument("--bedtime", required=True, help="就寝时间 (HH:MM)")
    p_log.add_argument("--wake", required=True, help="起床时间 (HH:MM)")
    p_log.add_argument("--deep", type=int, default=None, help="深睡时长 (分钟)")
    p_log.add_argument("--light", type=int, default=None, help="浅睡时长 (分钟)")
    p_log.add_argument("--rem", type=int, default=None, help="REM时长 (分钟)")
    p_log.add_argument("--awake", type=int, default=None, help="夜间清醒时长 (分钟)")
    p_log.add_argument("--date", default=None, help="日期 (YYYY-MM-DD)")
    p_log.add_argument("--data-dir", default=None, help="数据目录")

    # import
    p_import = sub.add_parser("import", help="导入 Apple Health 数据")
    p_import.add_argument("--file", required=True, help="Apple Health export.xml 路径")
    p_import.add_argument("--data-dir", default=None, help="数据目录")

    # score
    p_score = sub.add_parser("score", help="睡眠评分详情")
    p_score.add_argument("--nights", type=int, default=1, help="查看最近几晚")
    p_score.add_argument("--data-dir", default=None, help="数据目录")

    # trend
    p_trend = sub.add_parser("trend", help="睡眠趋势")
    p_trend.add_argument("--days", type=int, default=14, help="天数")
    p_trend.add_argument("--data-dir", default=None, help="数据目录")

    # correlate
    p_corr = sub.add_parser("correlate", help="睡眠-咖啡因关联分析")
    p_corr.add_argument("--days", type=int, default=14, help="天数")
    p_corr.add_argument("--data-dir", default=None, help="数据目录")

    # chart
    p_chart = sub.add_parser("chart", help="生成睡眠阶段图")
    p_chart.add_argument("--days", type=int, default=14, help="天数")
    p_chart.add_argument("--data-dir", default=None, help="数据目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    analyzer = SleepAnalyzer(data_dir=getattr(args, "data_dir", None))

    if args.command == "log":
        analyzer.log(
            bedtime=args.bedtime,
            wake_time=args.wake,
            deep_min=args.deep,
            light_min=args.light,
            rem_min=args.rem,
            awake_min=args.awake,
            date=args.date,
        )
    elif args.command == "import":
        analyzer.import_apple_health(args.file)
    elif args.command == "score":
        analyzer.score(n=args.nights)
    elif args.command == "trend":
        analyzer.trend(days=args.days)
    elif args.command == "correlate":
        analyzer.correlate(days=args.days)
    elif args.command == "chart":
        analyzer.chart(days=args.days)


if __name__ == "__main__":
    main()
