#!/usr/bin/env python3
"""Annual health report generator for VitaClaw.

Generates a comprehensive year-in-review HTML report with metric trajectories,
medication adherence, health events timeline, improvement areas, correlation
insights, and goals review.
"""

from __future__ import annotations

import base64
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ── Path setup (project convention) ─────────────────────────────
_SHARED_DIR = os.path.dirname(__file__)
if _SHARED_DIR not in sys.path:
    sys.path.insert(0, _SHARED_DIR)

try:
    from .cross_skill_reader import CrossSkillReader
    from .correlation_engine import CorrelationEngine
    from .health_chart_engine import HealthChartEngine
    from .health_memory import HealthMemoryWriter
except ImportError:
    from cross_skill_reader import CrossSkillReader  # noqa: E402
    from correlation_engine import CorrelationEngine  # noqa: E402
    from health_chart_engine import HealthChartEngine  # noqa: E402
    from health_memory import HealthMemoryWriter  # noqa: E402

try:
    from jinja2 import Template
except ImportError:
    Template = None  # type: ignore[assignment,misc]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ── Event keywords for daily log extraction ─────────────────────

_EVENT_KEYWORDS: dict[str, list[str]] = {
    "就医": ["就医", "复查", "门诊", "住院", "挂号", "看病", "检查", "体检", "手术"],
    "症状": ["头晕", "头痛", "胸闷", "心悸", "失眠", "疲劳", "恶心", "呕吐",
             "腹痛", "发烧", "咳嗽", "气短", "浮肿", "麻木"],
    "用药变化": ["换药", "停药", "加药", "减量", "新药", "调整剂量"],
    "异常指标": ["偏高", "偏低", "异常", "超标", "危险", "警告"],
    "生活方式": ["运动", "戒烟", "戒酒", "节食", "减肥", "锻炼"],
}


# ── HTML Template ───────────────────────────────────────────────

_ANNUAL_REPORT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ year }}年度健康报告{% if person_id %} - {{ person_id }}{% endif %}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #fafafa; color: #333; line-height: 1.6;
    max-width: 900px; margin: 0 auto; padding: 20px;
  }
  h1 { text-align: center; color: #2c3e50; margin: 30px 0; font-size: 28px; }
  .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 14px; }
  .sparse-notice { text-align: center; color: #e67e22; font-weight: bold; margin-bottom: 20px; }
  .section {
    background: #fff; border-radius: 8px; padding: 24px;
    margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-left: 4px solid #3498db;
  }
  .section h2 { color: #2c3e50; font-size: 20px; margin-bottom: 16px; }
  .section-trajectories { border-left-color: #27ae60; }
  .section-adherence { border-left-color: #e74c3c; }
  .section-events { border-left-color: #f39c12; }
  .section-improvements { border-left-color: #9b59b6; }
  .section-correlations { border-left-color: #1abc9c; }
  .section-goals { border-left-color: #e67e22; }
  .stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px; margin-top: 12px;
  }
  .stat-card {
    background: #f8f9fa; border-radius: 6px; padding: 16px; text-align: center;
  }
  .stat-value { font-size: 32px; font-weight: bold; color: #2c3e50; }
  .stat-label { color: #7f8c8d; font-size: 13px; margin-top: 4px; }
  .chart-img { max-width: 100%; height: auto; border-radius: 4px; margin: 12px 0; }
  .no-data { color: #95a5a6; font-style: italic; padding: 20px; text-align: center; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f8f9fa; font-weight: 600; color: #2c3e50; }
  tr:nth-child(even) td { background: #f9f9f9; }
  .adherence-grid { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
  .adherence-cell {
    width: 28px; height: 28px; border-radius: 4px; display: flex;
    align-items: center; justify-content: center; font-size: 10px; color: #fff;
  }
  .adherence-high { background: #27ae60; }
  .adherence-mid { background: #f39c12; }
  .adherence-low { background: #e74c3c; }
  .adherence-none { background: #ecf0f1; color: #bdc3c7; }
  .event-item {
    padding: 10px 0; border-bottom: 1px solid #f0f0f0;
    display: flex; gap: 12px; align-items: flex-start;
  }
  .event-date { color: #3498db; font-weight: 600; white-space: nowrap; min-width: 90px; }
  .event-type {
    background: #ecf0f1; border-radius: 4px; padding: 2px 8px;
    font-size: 12px; white-space: nowrap;
  }
  .improvement-up { color: #27ae60; }
  .improvement-down { color: #e74c3c; }
  .footer { text-align: center; color: #bdc3c7; font-size: 12px; margin-top: 30px; padding: 20px; }

  @media (max-width: 600px) {
    body { padding: 10px; }
    h1 { font-size: 22px; }
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .stat-value { font-size: 24px; }
  }
  @media print {
    body { background: #fff; max-width: 100%; }
    .section { box-shadow: none; break-inside: avoid; }
  }
</style>
</head>
<body>
<h1>{{ year }} 年度健康报告</h1>
<p class="subtitle">报告生成时间：{{ generated_at }}</p>

{% if sparse_notice %}
<p class="sparse-notice">{{ sparse_notice }}</p>
{% endif %}

<!-- Section 1: 年度概览 -->
<div class="section">
  <h2>年度概览</h2>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value">{{ overview.total_records }}</div>
      <div class="stat-label">总记录数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ overview.tracking_days }}</div>
      <div class="stat-label">追踪天数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ overview.doctor_visits }}</div>
      <div class="stat-label">就医次数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ overview.metrics_tracked }}</div>
      <div class="stat-label">追踪指标数</div>
    </div>
  </div>
</div>

<!-- Section 2: 指标轨迹 -->
<div class="section section-trajectories">
  <h2>指标轨迹</h2>
  {% if charts %}
    {% for chart in charts %}
    <div>
      <h3>{{ chart.title }}</h3>
      <img class="chart-img" src="data:image/png;base64,{{ chart.data }}" alt="{{ chart.title }}">
    </div>
    {% endfor %}
  {% else %}
  <p class="no-data">本年度暂无指标轨迹数据</p>
  {% endif %}
</div>

<!-- Section 3: 用药依从性 -->
<div class="section section-adherence">
  <h2>用药依从性</h2>
  {% if adherence %}
    {% for med_name, med_data in adherence.items() %}
    <div style="margin-bottom: 16px;">
      <h3>{{ med_name }}</h3>
      <p>追踪 {{ med_data.tracked_days }} 天 / {{ med_data.total_days }} 天，依从率 {{ "%.1f"|format(med_data.adherence_pct) }}%</p>
      <div class="adherence-grid">
        {% for m in med_data.monthly_breakdown %}
        <div class="adherence-cell {% if m.pct >= 80 %}adherence-high{% elif m.pct >= 50 %}adherence-mid{% elif m.pct > 0 %}adherence-low{% else %}adherence-none{% endif %}"
             title="{{ m.month }}月: {{ "%.0f"|format(m.pct) }}%">
          {{ m.month }}
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  {% else %}
  <p class="no-data">本年度暂无用药记录</p>
  {% endif %}
</div>

<!-- Section 4: 健康事件时间线 -->
<div class="section section-events">
  <h2>健康事件时间线</h2>
  {% if events %}
    {% for event in events %}
    <div class="event-item">
      <span class="event-date">{{ event.date }}</span>
      <span class="event-type">{{ event.type }}</span>
      <span>{{ event.context }}</span>
    </div>
    {% endfor %}
  {% else %}
  <p class="no-data">本年度暂无健康事件记录</p>
  {% endif %}
</div>

<!-- Section 5: 改善领域 -->
<div class="section section-improvements">
  <h2>改善领域</h2>
  {% if improvements %}
  <table>
    <thead>
      <tr><th>指标</th><th>变化方向</th><th>变化幅度</th></tr>
    </thead>
    <tbody>
      {% for item in improvements %}
      <tr>
        <td>{{ item.metric }}</td>
        <td class="{% if item.direction == '改善' %}improvement-up{% else %}improvement-down{% endif %}">
          {{ item.direction }}
        </td>
        <td>{{ "%.1f"|format(item.delta_pct) }}%</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="no-data">本年度暂无足够数据进行改善分析</p>
  {% endif %}
</div>

<!-- Section 6: 相关性洞察 -->
<div class="section section-correlations">
  <h2>相关性洞察</h2>
  {% if correlations %}
    {% for insight in correlations %}
    <p style="margin-bottom: 8px;">• {{ insight }}</p>
    {% endfor %}
  {% else %}
  <p class="no-data">本年度暂无显著相关性发现</p>
  {% endif %}
</div>

<!-- Section 7: 目标回顾 -->
<div class="section section-goals">
  <h2>目标回顾</h2>
  {% if goals %}
    {% for goal in goals %}
    <div style="margin-bottom: 12px;">
      <p><strong>目标：</strong>{{ goal.description }}</p>
      <p><strong>进展：</strong>{{ goal.progress }}</p>
    </div>
    {% endfor %}
  {% else %}
  <p class="no-data">本年度暂无设定健康目标</p>
  {% endif %}
</div>

<div class="footer">
  <p>由 VitaClaw 健康管理系统自动生成</p>
  <p>本报告仅供参考，不构成医疗建议</p>
</div>
</body>
</html>"""


# ── HealthAnnualReport ──────────────────────────────────────────


class HealthAnnualReport:
    """Generate a comprehensive annual health report as self-contained HTML.

    Composes existing engines (HealthChartEngine, CrossSkillReader,
    CorrelationEngine) to produce a year-in-review report with 7 sections:
    1. Year Overview
    2. Metric Trajectories
    3. Medication Adherence
    4. Health Events Timeline
    5. Improvement Areas
    6. Correlation Insights
    7. Goals Review
    """

    def __init__(
        self,
        data_dir: str | None = None,
        person_id: str | None = None,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
        year: int | None = None,
    ):
        self.data_dir = data_dir
        self.person_id = person_id
        self.workspace_root = workspace_root
        self.memory_dir = memory_dir
        self.year = year or datetime.now().year

        # Sub-engines
        self.chart_engine = HealthChartEngine(data_dir=data_dir, person_id=person_id)
        self.reader = CrossSkillReader(data_dir=data_dir)
        self.correlation_engine = CorrelationEngine(data_dir=data_dir)

        # Memory writer for file paths
        self.memory_writer = HealthMemoryWriter(
            workspace_root=workspace_root,
            memory_root=memory_dir,
            person_id=person_id,
        )

    # ── Main entry point ────────────────────────────────────────

    def generate(self, write: bool = True) -> dict:
        """Generate the annual health report.

        Args:
            write: If True, write HTML file to disk.

        Returns:
            {"path": str, "content": str, "format": "html"}
        """
        year = self.year

        # Gather data for all sections
        overview = self._year_overview(year)
        charts = self._metric_trajectories(year)
        adherence = self._medication_adherence(year)
        events = self._extract_events_from_daily_logs(year)
        improvements = self._improvement_areas(year)
        correlations = self._correlation_insights(year)
        goals = self._goals_review(year)

        # Sparse data notice
        sparse_notice = ""
        if overview["total_records"] == 0:
            sparse_notice = f"{year}年暂无健康追踪数据"
        elif overview["tracking_days"] < 30:
            sparse_notice = f"数据从较少天数开始（共{overview['tracking_days']}天追踪记录）"

        # Render HTML
        if Template is not None:
            template = Template(_ANNUAL_REPORT_HTML)
            html = template.render(
                year=year,
                person_id=self.person_id,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                sparse_notice=sparse_notice,
                overview=overview,
                charts=charts,
                adherence=adherence,
                events=events,
                improvements=improvements,
                correlations=correlations,
                goals=goals,
            )
        else:
            # Fallback without Jinja2 -- minimal HTML
            html = self._render_fallback(
                year, overview, charts, adherence, events,
                improvements, correlations, goals, sparse_notice,
            )

        # Output path
        files_dir = Path(self.memory_writer.files_dir)
        files_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(files_dir / f"annual-report-{year}.html")

        if write:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

        return {"path": output_path, "content": html, "format": "html"}

    # ── Section 1: Year Overview ────────────────────────────────

    def _year_overview(self, year: int) -> dict:
        """Count total records, tracking days, doctor visits, metrics tracked."""
        start = f"{year}-01-01"
        end = f"{year}-12-31T23:59:59"

        all_records: list[dict] = []
        metrics_with_data = 0

        # Gather records from known skills
        for read_fn in [
            self.reader.read_blood_pressure,
            self.reader.read_glucose_data,
            self.reader.read_weight_data,
            self.reader.read_sleep_data,
            self.reader.read_medication_doses,
        ]:
            try:
                records = read_fn(start=start, end=end, person_id=self.person_id)
                if records:
                    all_records.extend(records)
                    metrics_with_data += 1
            except Exception:
                pass

        # Distinct tracking days
        tracking_days = len({
            r.get("timestamp", "")[:10]
            for r in all_records
            if r.get("timestamp", "")[:10].startswith(str(year))
        })

        # Doctor visits from events
        events = self._extract_events_from_daily_logs(year)
        doctor_visits = len([e for e in events if e["type"] == "就医"])

        return {
            "total_records": len(all_records),
            "tracking_days": tracking_days,
            "doctor_visits": doctor_visits,
            "metrics_tracked": metrics_with_data,
        }

    # ── Section 2: Metric Trajectories ──────────────────────────

    def _metric_trajectories(self, year: int) -> list[dict]:
        """Generate 365-day charts and encode as base64 for HTML embedding."""
        charts = []
        chart_configs = [
            ("血压趋势", self.chart_engine.generate_blood_pressure_chart),
            ("血糖趋势", self.chart_engine.generate_blood_glucose_chart),
            ("体重趋势", self.chart_engine.generate_weight_chart),
            ("睡眠时长", self.chart_engine.generate_sleep_chart),
        ]

        for title, gen_fn in chart_configs:
            try:
                path = gen_fn(days=365)
                if path and os.path.isfile(path):
                    with open(path, "rb") as f:
                        data = base64.b64encode(f.read()).decode("ascii")
                    charts.append({"title": title, "data": data})
            except Exception:
                pass

        return charts

    # ── Section 3: Medication Adherence ─────────────────────────

    def _medication_adherence(self, year: int) -> dict:
        """Calculate medication adherence by drug.

        Returns:
            dict[med_name, {total_days, tracked_days, adherence_pct, monthly_breakdown}]
        """
        start = f"{year}-01-01"
        end = f"{year}-12-31T23:59:59"

        try:
            doses = self.reader.read_medication_doses(
                start=start, end=end, person_id=self.person_id,
            )
        except Exception:
            doses = []

        if not doses:
            return {}

        # Group by medication name
        med_days: dict[str, set[str]] = defaultdict(set)
        med_months: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))

        for dose in doses:
            ts = dose.get("timestamp", "")[:10]
            if not ts.startswith(str(year)):
                continue
            med_name = dose.get("data", {}).get("medication", "未知药物")
            med_days[med_name].add(ts)
            try:
                month = int(ts[5:7])
                med_months[med_name][month].add(ts)
            except (ValueError, IndexError):
                pass

        # Calculate adherence
        import calendar

        result = {}
        for med_name, days_set in med_days.items():
            # Total days in year (or up to today if current year)
            if year == datetime.now().year:
                total_days = (datetime.now() - datetime(year, 1, 1)).days + 1
            else:
                total_days = 366 if calendar.isleap(year) else 365

            tracked_days = len(days_set)
            adherence_pct = (tracked_days / total_days * 100) if total_days > 0 else 0

            # Monthly breakdown
            monthly = []
            for m in range(1, 13):
                days_in_month = calendar.monthrange(year, m)[1]
                tracked_in_month = len(med_months[med_name].get(m, set()))
                pct = (tracked_in_month / days_in_month * 100) if days_in_month > 0 else 0
                monthly.append({"month": m, "days": tracked_in_month, "pct": pct})

            result[med_name] = {
                "total_days": total_days,
                "tracked_days": tracked_days,
                "adherence_pct": adherence_pct,
                "monthly_breakdown": monthly,
            }

        return result

    # ── Section 4: Health Events Timeline ───────────────────────

    def _extract_events_from_daily_logs(self, year: int) -> list[dict]:
        """Extract health events from daily log files.

        Returns:
            List of {date, type, keyword, context} sorted chronologically.
        """
        daily_dir = Path(self.memory_writer.daily_dir)
        if not daily_dir.exists():
            return []

        events = []
        for log_file in sorted(daily_dir.glob(f"{year}-*.md")):
            date = log_file.stem  # YYYY-MM-DD
            try:
                content = log_file.read_text(encoding="utf-8")
            except Exception:
                continue

            for line in content.split("\n"):
                line_stripped = line.strip().lstrip("- ").strip()
                if not line_stripped:
                    continue

                for event_type, keywords in _EVENT_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in line_stripped:
                            events.append({
                                "date": date,
                                "type": event_type,
                                "keyword": keyword,
                                "context": line_stripped,
                            })
                            break  # one match per keyword group per line
                    else:
                        continue
                    break  # found a match, move to next line

        events.sort(key=lambda e: e["date"])
        return events

    # ── Section 5: Improvement Areas ────────────────────────────

    def _improvement_areas(self, year: int) -> list[dict]:
        """Compare Q1 vs Q4 averages for key metrics.

        Returns:
            list of {metric, direction, delta_pct}
        """
        q1_start, q1_end = f"{year}-01-01", f"{year}-03-31T23:59:59"
        q4_start, q4_end = f"{year}-10-01", f"{year}-12-31T23:59:59"

        improvements = []

        # BP (lower is better)
        try:
            q1_bp = self.reader.read_blood_pressure(
                start=q1_start, end=q1_end, person_id=self.person_id,
            )
            q4_bp = self.reader.read_blood_pressure(
                start=q4_start, end=q4_end, person_id=self.person_id,
            )
            if q1_bp and q4_bp:
                q1_sys = sum(r["data"]["systolic"] for r in q1_bp) / len(q1_bp)
                q4_sys = sum(r["data"]["systolic"] for r in q4_bp) / len(q4_bp)
                delta = ((q4_sys - q1_sys) / q1_sys) * 100 if q1_sys else 0
                direction = "改善" if delta < 0 else "恶化"
                improvements.append({
                    "metric": "收缩压",
                    "direction": direction,
                    "delta_pct": abs(delta),
                })

                q1_dia = sum(r["data"]["diastolic"] for r in q1_bp) / len(q1_bp)
                q4_dia = sum(r["data"]["diastolic"] for r in q4_bp) / len(q4_bp)
                delta_d = ((q4_dia - q1_dia) / q1_dia) * 100 if q1_dia else 0
                direction_d = "改善" if delta_d < 0 else "恶化"
                improvements.append({
                    "metric": "舒张压",
                    "direction": direction_d,
                    "delta_pct": abs(delta_d),
                })
        except Exception:
            pass

        # Glucose (lower is better)
        try:
            q1_gl = self.reader.read_glucose_data(
                start=q1_start, end=q1_end, person_id=self.person_id,
            )
            q4_gl = self.reader.read_glucose_data(
                start=q4_start, end=q4_end, person_id=self.person_id,
            )
            if q1_gl and q4_gl:
                q1_val = sum(
                    r["data"].get("value", r["data"].get("glucose", 0)) for r in q1_gl
                ) / len(q1_gl)
                q4_val = sum(
                    r["data"].get("value", r["data"].get("glucose", 0)) for r in q4_gl
                ) / len(q4_gl)
                delta = ((q4_val - q1_val) / q1_val) * 100 if q1_val else 0
                direction = "改善" if delta < 0 else "恶化"
                improvements.append({
                    "metric": "血糖",
                    "direction": direction,
                    "delta_pct": abs(delta),
                })
        except Exception:
            pass

        # Weight (depends on goal, default: lower is better for most users)
        try:
            q1_wt = self.reader.read_weight_data(
                start=q1_start, end=q1_end, person_id=self.person_id,
            )
            q4_wt = self.reader.read_weight_data(
                start=q4_start, end=q4_end, person_id=self.person_id,
            )
            if q1_wt and q4_wt:
                q1_val = sum(
                    r["data"].get("value", r["data"].get("weight", 0)) for r in q1_wt
                ) / len(q1_wt)
                q4_val = sum(
                    r["data"].get("value", r["data"].get("weight", 0)) for r in q4_wt
                ) / len(q4_wt)
                delta = ((q4_val - q1_val) / q1_val) * 100 if q1_val else 0
                direction = "改善" if delta < 0 else "恶化"
                improvements.append({
                    "metric": "体重",
                    "direction": direction,
                    "delta_pct": abs(delta),
                })
        except Exception:
            pass

        # Sleep (more is better)
        try:
            q1_sl = self.reader.read_sleep_data(
                start=q1_start, end=q1_end, person_id=self.person_id,
            )
            q4_sl = self.reader.read_sleep_data(
                start=q4_start, end=q4_end, person_id=self.person_id,
            )
            if q1_sl and q4_sl:
                q1_val = sum(
                    r["data"].get("total_min", r["data"].get("duration_min", 0)) for r in q1_sl
                ) / len(q1_sl)
                q4_val = sum(
                    r["data"].get("total_min", r["data"].get("duration_min", 0)) for r in q4_sl
                ) / len(q4_sl)
                delta = ((q4_val - q1_val) / q1_val) * 100 if q1_val else 0
                # For sleep, more is better (positive delta = improvement)
                direction = "改善" if delta > 0 else "恶化"
                improvements.append({
                    "metric": "睡眠时长",
                    "direction": direction,
                    "delta_pct": abs(delta),
                })
        except Exception:
            pass

        return improvements

    # ── Section 6: Correlation Insights ─────────────────────────

    def _correlation_insights(self, year: int) -> list[str]:
        """Get top 3 significant correlations as natural language insights."""
        try:
            results = self.correlation_engine.discover_correlations(
                window_days=365,
                person_id=self.person_id,
            )
            significant = [r for r in results if r.is_significant()]
            top3 = significant[:3]
            return [r.to_natural_language() for r in top3]
        except Exception:
            return []

    # ── Section 7: Goals Review ─────────────────────────────────

    def _goals_review(self, year: int) -> list[dict]:
        """Parse health profile for goals and compare with actual metrics."""
        items_dir = Path(self.memory_writer.items_dir)
        profile_path = items_dir / "_health-profile.md"

        if not profile_path.exists():
            return []

        try:
            content = profile_path.read_text(encoding="utf-8")
        except Exception:
            return []

        # Extract goals section
        goals = []
        in_goals = False
        for line in content.split("\n"):
            if re.match(r"^#+\s*目标|^#+\s*goals?", line, re.IGNORECASE):
                in_goals = True
                continue
            if in_goals:
                if re.match(r"^#+\s", line):
                    break  # next section
                stripped = line.strip().lstrip("- ").strip()
                if stripped:
                    goals.append({
                        "description": stripped,
                        "progress": "年度数据待对比分析",
                    })

        return goals

    # ── Fallback renderer (no Jinja2) ───────────────────────────

    def _render_fallback(
        self, year, overview, charts, adherence, events,
        improvements, correlations, goals, sparse_notice,
    ) -> str:
        """Minimal HTML rendering without Jinja2."""
        parts = [f"<!DOCTYPE html><html><head><title>{year}年度健康报告</title></head><body>"]
        parts.append(f"<h1>{year} 年度健康报告</h1>")
        if sparse_notice:
            parts.append(f"<p>{sparse_notice}</p>")

        parts.append("<h2>年度概览</h2>")
        parts.append(f"<p>总记录: {overview['total_records']}, 追踪天数: {overview['tracking_days']}</p>")

        parts.append("<h2>指标轨迹</h2>")
        if not charts:
            parts.append("<p>本年度暂无指标轨迹数据</p>")

        parts.append("<h2>用药依从性</h2>")
        if not adherence:
            parts.append("<p>本年度暂无用药记录</p>")

        parts.append("<h2>健康事件时间线</h2>")
        if not events:
            parts.append("<p>本年度暂无健康事件记录</p>")

        parts.append("<h2>改善领域</h2>")
        if not improvements:
            parts.append("<p>本年度暂无足够数据进行改善分析</p>")

        parts.append("<h2>相关性洞察</h2>")
        if not correlations:
            parts.append("<p>本年度暂无显著相关性发现</p>")

        parts.append("<h2>目标回顾</h2>")
        if not goals:
            parts.append("<p>本年度暂无设定健康目标</p>")

        parts.append("</body></html>")
        return "\n".join(parts)
