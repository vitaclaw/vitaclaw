#!/usr/bin/env python3
"""Doctor-ready visit summary generator for VitaClaw.

Composes existing engines (HealthChartEngine, CrossSkillReader,
HealthHeartbeat, HealthMemoryWriter) to produce multi-format clinical
summaries with embedded trend charts.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta
from pathlib import Path

# ── Imports (package-style for relative import compat) ──────────
from .health_chart_engine import HealthChartEngine
from .cross_skill_reader import CrossSkillReader
from .health_heartbeat import HealthHeartbeat
from .health_memory import HealthMemoryWriter

try:
    from jinja2 import Template
except ImportError:
    Template = None  # type: ignore[misc,assignment]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ── Jinja2 HTML template (inline, per project convention) ───────

_VISIT_SUMMARY_HTML = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>就诊摘要 - {{ date }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: "PingFang SC", "Heiti SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #fafafa; color: #333; line-height: 1.6;
    max-width: 900px; margin: 0 auto; padding: 20px;
  }
  h1 { font-size: 1.5em; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-bottom: 20px; }
  h2 { font-size: 1.2em; color: #2c3e50; margin: 24px 0 12px 0; border-left: 4px solid #3498db; padding-left: 10px; }
  .card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .profile-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .profile-grid dt { color: #7f8c8d; font-size: 0.9em; }
  .profile-grid dd { font-weight: 500; margin-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; margin: 8px 0; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
  th { background: #f8f9fa; color: #2c3e50; font-weight: 600; }
  tr:nth-child(even) { background: #fafafa; }
  .chart-img { max-width: 100%; height: auto; border-radius: 4px; margin: 8px 0; }
  .no-data { color: #95a5a6; font-style: italic; padding: 12px 0; }
  .issue { padding: 6px 0; border-bottom: 1px solid #f0f0f0; }
  .issue-high { color: #e74c3c; }
  .issue-medium { color: #f39c12; }
  .issue-low { color: #27ae60; }
  .questions { background: #fffde7; border-left: 4px solid #f9a825; padding: 12px 16px; border-radius: 4px; }
  .questions li { margin: 6px 0; }
  .footer { margin-top: 30px; padding-top: 12px; border-top: 1px solid #ecf0f1; color: #95a5a6; font-size: 0.8em; text-align: center; }
  @media print {
    body { background: #fff; padding: 0; }
    .card { box-shadow: none; border: 1px solid #eee; }
  }
  @media (max-width: 600px) {
    .profile-grid { grid-template-columns: 1fr; }
    body { padding: 12px; }
  }
</style>
</head>
<body>

<h1>就诊摘要</h1>

<h2>患者信息</h2>
<div class="card">
  <dl class="profile-grid">
    <dt>姓名</dt><dd>{{ profile.name }}</dd>
    <dt>年龄/出生日期</dt><dd>{{ profile.age_dob }}</dd>
    <dt>主要健康问题</dt><dd>{{ profile.conditions }}</dd>
  </dl>
</div>

<h2>近期生命体征</h2>
<div class="card">
{% if vitals.bp_records %}
  <h3 style="font-size:1em;margin:8px 0;">血压</h3>
  <table>
    <tr><th>日期</th><th>收缩压</th><th>舒张压</th><th>脉搏</th></tr>
    {% for r in vitals.bp_records[-5:] %}
    <tr><td>{{ r.date }}</td><td>{{ r.systolic }}</td><td>{{ r.diastolic }}</td><td>{{ r.pulse }}</td></tr>
    {% endfor %}
  </table>
{% else %}
  <p class="no-data">近期无血压记录</p>
{% endif %}

{% if charts.bp %}
  <img class="chart-img" src="{{ charts.bp }}" alt="血压趋势图">
{% endif %}

{% if vitals.glucose_records %}
  <h3 style="font-size:1em;margin:8px 0;">血糖</h3>
  <table>
    <tr><th>日期</th><th>血糖值 (mmol/L)</th></tr>
    {% for r in vitals.glucose_records[-5:] %}
    <tr><td>{{ r.date }}</td><td>{{ r.value }}</td></tr>
    {% endfor %}
  </table>
{% else %}
  <p class="no-data">近期无血糖记录</p>
{% endif %}

{% if charts.glucose %}
  <img class="chart-img" src="{{ charts.glucose }}" alt="血糖趋势图">
{% endif %}

{% if vitals.weight_records %}
  <h3 style="font-size:1em;margin:8px 0;">体重</h3>
  <table>
    <tr><th>日期</th><th>体重 (kg)</th></tr>
    {% for r in vitals.weight_records[-5:] %}
    <tr><td>{{ r.date }}</td><td>{{ r.value }}</td></tr>
    {% endfor %}
  </table>
{% else %}
  <p class="no-data">近期无体重记录</p>
{% endif %}

{% if charts.weight %}
  <img class="chart-img" src="{{ charts.weight }}" alt="体重趋势图">
{% endif %}
</div>

<h2>当前用药</h2>
<div class="card">
{% if medications %}
  <table>
    <tr><th>药物名称</th><th>剂量</th><th>频次</th><th>备注</th></tr>
    {% for med in medications %}
    <tr><td>{{ med.name }}</td><td>{{ med.dose }}</td><td>{{ med.frequency }}</td><td>{{ med.note }}</td></tr>
    {% endfor %}
  </table>
{% else %}
  <p class="no-data">未找到用药记录</p>
{% endif %}
</div>

<h2>近期检验结果</h2>
<div class="card">
{% if labs %}
  <table>
    <tr><th>日期</th><th>项目</th><th>结果</th><th>参考范围</th></tr>
    {% for lab in labs %}
    <tr><td>{{ lab.date }}</td><td>{{ lab.name }}</td><td>{{ lab.value }}</td><td>{{ lab.reference }}</td></tr>
    {% endfor %}
  </table>
{% else %}
  <p class="no-data">近期无检验结果</p>
{% endif %}
</div>

<h2>关注问题</h2>
<div class="card">
{% if issues %}
  {% for issue in issues %}
  <div class="issue issue-{{ issue.priority }}">
    <strong>[{{ issue.priority }}]</strong> {{ issue.title }}：{{ issue.reason }}
  </div>
  {% endfor %}
{% else %}
  <p class="no-data">当前无需特别关注的问题</p>
{% endif %}
</div>

<h2>就诊问题（可编辑）</h2>
<div class="card questions">
  <p>请在就诊前补充您想问医生的问题：</p>
  <ol>
    <li>_______________</li>
    <li>_______________</li>
    <li>_______________</li>
  </ol>
</div>

<div class="footer">
  由 VitaClaw 健康管理系统生成 | {{ date }}
</div>

</body>
</html>
"""


# ── HealthVisitSummary ──────────────────────────────────────────


class HealthVisitSummary:
    """Generate doctor-ready visit summaries in Markdown, HTML, or PDF format."""

    def __init__(
        self,
        data_dir: str | None = None,
        person_id: str | None = None,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
    ):
        self.data_dir = data_dir
        self.person_id = person_id
        self.workspace_root = workspace_root
        self.memory_dir = memory_dir

        self.chart_engine = HealthChartEngine(data_dir=data_dir, person_id=person_id)
        self.reader = CrossSkillReader(data_dir=data_dir)
        self.writer = HealthMemoryWriter(
            workspace_root=workspace_root,
            memory_root=memory_dir,
            person_id=person_id,
        )

    # ── Data collection ──────────────────────────────────────

    def _parse_profile(self) -> dict:
        """Parse _health-profile.md for patient header info."""
        profile = {"name": "未填写", "age_dob": "未填写", "conditions": "未填写"}
        path = self.writer.profile_path
        if not path.exists():
            return profile

        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return profile

        for line in text.splitlines():
            stripped = line.strip()
            # Look for key-value patterns in profile
            if stripped.startswith("- ") and ":" in stripped:
                key, _, value = stripped[2:].partition(":")
                key = key.strip().lower()
                value = value.strip()
                if not value or value.lower() == "pending":
                    value = "未填写"
                if key in ("name", "姓名"):
                    profile["name"] = value
                elif key in ("age", "年龄", "dob", "出生日期", "birth"):
                    profile["age_dob"] = value
                elif key in ("conditions", "主要健康问题", "diagnoses", "诊断"):
                    profile["conditions"] = value

        return profile

    def _parse_medications(self) -> list[dict]:
        """Parse medications from items/medications.md."""
        meds: list[dict] = []
        path = self.writer._resolve_items_path("medications")
        if not path.exists():
            return meds

        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return meds

        in_table = False
        for line in text.splitlines():
            stripped = line.strip()
            if "|" in stripped and ("药物" in stripped or "name" in stripped.lower() or "medication" in stripped.lower()):
                in_table = True
                continue
            if in_table and stripped.startswith("|") and "---" in stripped:
                continue
            if in_table and stripped.startswith("|"):
                parts = [p.strip() for p in stripped.split("|")[1:-1]]
                if len(parts) >= 2:
                    meds.append({
                        "name": parts[0] or "-",
                        "dose": parts[1] if len(parts) > 1 else "-",
                        "frequency": parts[2] if len(parts) > 2 else "-",
                        "note": parts[3] if len(parts) > 3 else "",
                    })
            elif in_table and not stripped.startswith("|"):
                in_table = False

        return meds

    def _collect_data(self, days: int = 30) -> dict:
        """Collect all data needed for the visit summary."""
        start = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")

        # 1. Patient header
        profile = self._parse_profile()

        # 2. Recent vitals
        bp_records = self.reader.read_blood_pressure(start=start, person_id=self.person_id)
        glucose_records = self.reader.read_glucose_data(start=start, person_id=self.person_id)
        weight_records = self.reader.read_weight_data(start=start, person_id=self.person_id)

        vitals = {
            "bp_records": [
                {
                    "date": r.get("timestamp", "")[:10],
                    "systolic": r.get("data", {}).get("systolic", r.get("data", {}).get("sys", "-")),
                    "diastolic": r.get("data", {}).get("diastolic", r.get("data", {}).get("dia", "-")),
                    "pulse": r.get("data", {}).get("pulse", r.get("data", {}).get("hr", "-")),
                }
                for r in bp_records
            ],
            "glucose_records": [
                {
                    "date": r.get("timestamp", "")[:10],
                    "value": r.get("data", {}).get("value", r.get("data", {}).get("glucose", "-")),
                }
                for r in glucose_records
            ],
            "weight_records": [
                {
                    "date": r.get("timestamp", "")[:10],
                    "value": r.get("data", {}).get("value", r.get("data", {}).get("weight", "-")),
                }
                for r in weight_records
            ],
        }

        # 3. Current medications
        medications = self._parse_medications()

        # 4. Recent lab results
        labs: list[dict] = []
        try:
            lab_records = self.reader.read("lab-result", start=start, person_id=self.person_id)
            for r in lab_records:
                data = r.get("data", {})
                labs.append({
                    "date": r.get("timestamp", "")[:10],
                    "name": data.get("name", data.get("item", "-")),
                    "value": data.get("value", "-"),
                    "reference": data.get("reference", data.get("range", "-")),
                })
        except Exception:
            pass

        # 5. Key concerns
        issues: list[dict] = []
        try:
            hb = HealthHeartbeat(data_dir=self.data_dir, person_id=self.person_id)
            result = hb.run(write_report=False)
            issues = result.get("issues", [])
        except Exception:
            pass

        return {
            "profile": profile,
            "vitals": vitals,
            "medications": medications,
            "labs": labs,
            "issues": issues,
        }

    # ── Chart generation ─────────────────────────────────────

    def _generate_charts(self, days: int = 30) -> dict[str, str]:
        """Generate chart PNGs and return metric -> file_path mapping."""
        charts: dict[str, str] = {}
        for name, method in [
            ("bp", self.chart_engine.generate_blood_pressure_chart),
            ("glucose", self.chart_engine.generate_blood_glucose_chart),
            ("weight", self.chart_engine.generate_weight_chart),
        ]:
            try:
                path = method(days)
                if path:
                    charts[name] = path
            except Exception:
                pass
        return charts

    def _charts_as_base64(self, days: int = 30) -> dict[str, str]:
        """Generate charts and return as base64 data URIs."""
        chart_paths = self._generate_charts(days)
        result: dict[str, str] = {}
        for name, path in chart_paths.items():
            try:
                with open(path, "rb") as f:
                    data = base64.b64encode(f.read()).decode("ascii")
                result[name] = f"data:image/png;base64,{data}"
            except (OSError, IOError):
                pass
        return result

    # ── Renderers ────────────────────────────────────────────

    def _render_markdown(self, data: dict, charts: dict[str, str]) -> str:
        """Render visit summary as Markdown."""
        lines: list[str] = []
        today = datetime.now().strftime("%Y-%m-%d")
        profile = data["profile"]
        vitals = data["vitals"]

        lines.append(f"# 就诊摘要 ({today})")
        lines.append("")

        # Patient header
        lines.append("## 患者信息")
        lines.append("")
        lines.append(f"- 姓名：{profile['name']}")
        lines.append(f"- 年龄/出生日期：{profile['age_dob']}")
        lines.append(f"- 主要健康问题：{profile['conditions']}")
        lines.append("")

        # Vitals
        lines.append("## 近期生命体征")
        lines.append("")

        if vitals["bp_records"]:
            lines.append("### 血压")
            lines.append("")
            lines.append("| 日期 | 收缩压 | 舒张压 | 脉搏 |")
            lines.append("|------|--------|--------|------|")
            for r in vitals["bp_records"][-5:]:
                lines.append(f"| {r['date']} | {r['systolic']} | {r['diastolic']} | {r['pulse']} |")
            lines.append("")
            if charts.get("bp"):
                lines.append(f"![血压趋势图]({charts['bp']})")
                lines.append("")
        else:
            lines.append("近期无血压记录")
            lines.append("")

        if vitals["glucose_records"]:
            lines.append("### 血糖")
            lines.append("")
            lines.append("| 日期 | 血糖值 (mmol/L) |")
            lines.append("|------|-----------------|")
            for r in vitals["glucose_records"][-5:]:
                lines.append(f"| {r['date']} | {r['value']} |")
            lines.append("")
            if charts.get("glucose"):
                lines.append(f"![血糖趋势图]({charts['glucose']})")
                lines.append("")
        else:
            lines.append("近期无血糖记录")
            lines.append("")

        if vitals["weight_records"]:
            lines.append("### 体重")
            lines.append("")
            lines.append("| 日期 | 体重 (kg) |")
            lines.append("|------|-----------|")
            for r in vitals["weight_records"][-5:]:
                lines.append(f"| {r['date']} | {r['value']} |")
            lines.append("")
            if charts.get("weight"):
                lines.append(f"![体重趋势图]({charts['weight']})")
                lines.append("")
        else:
            lines.append("近期无体重记录")
            lines.append("")

        # Medications
        lines.append("## 当前用药")
        lines.append("")
        if data["medications"]:
            lines.append("| 药物名称 | 剂量 | 频次 | 备注 |")
            lines.append("|----------|------|------|------|")
            for med in data["medications"]:
                lines.append(f"| {med['name']} | {med['dose']} | {med['frequency']} | {med['note']} |")
            lines.append("")
        else:
            lines.append("未找到用药记录")
            lines.append("")

        # Labs
        lines.append("## 近期检验结果")
        lines.append("")
        if data["labs"]:
            lines.append("| 日期 | 项目 | 结果 | 参考范围 |")
            lines.append("|------|------|------|----------|")
            for lab in data["labs"]:
                lines.append(f"| {lab['date']} | {lab['name']} | {lab['value']} | {lab['reference']} |")
            lines.append("")
        else:
            lines.append("近期无检验结果")
            lines.append("")

        # Concerns
        lines.append("## 关注问题")
        lines.append("")
        if data["issues"]:
            for issue in data["issues"]:
                priority = issue.get("priority", "medium")
                title = issue.get("title", "")
                reason = issue.get("reason", "")
                lines.append(f"- **[{priority}]** {title}：{reason}")
            lines.append("")
        else:
            lines.append("当前无需特别关注的问题")
            lines.append("")

        # Questions
        lines.append("## 就诊问题（可编辑）")
        lines.append("")
        lines.append("请在就诊前补充您想问医生的问题：")
        lines.append("")
        lines.append("1. _______________")
        lines.append("2. _______________")
        lines.append("3. _______________")
        lines.append("")

        lines.append(f"---\n*由 VitaClaw 健康管理系统生成 | {today}*")
        lines.append("")

        return "\n".join(lines)

    def _render_html(self, data: dict, charts: dict[str, str]) -> str:
        """Render visit summary as self-contained HTML with Jinja2."""
        today = datetime.now().strftime("%Y-%m-%d")

        # Convert chart paths to base64 for HTML embedding
        base64_charts: dict[str, str] = {}
        for name, path in charts.items():
            try:
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("ascii")
                base64_charts[name] = f"data:image/png;base64,{encoded}"
            except (OSError, IOError):
                pass

        if Template is not None:
            tmpl = Template(_VISIT_SUMMARY_HTML)
            return tmpl.render(
                date=today,
                profile=data["profile"],
                vitals=data["vitals"],
                medications=data["medications"],
                labs=data["labs"],
                issues=data["issues"],
                charts=base64_charts,
            )

        # Fallback: very basic HTML without Jinja2
        return self._render_html_fallback(data, base64_charts, today)

    def _render_html_fallback(self, data: dict, charts: dict[str, str], today: str) -> str:
        """Minimal HTML fallback when Jinja2 is not available."""
        md = self._render_markdown(data, charts)
        return f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'><title>就诊摘要</title><style>body{{font-family:'PingFang SC',sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#fafafa}}</style></head><body><pre>{md}</pre></body></html>"

    def _render_pdf(self, data: dict, charts: dict[str, str]) -> tuple[str, str]:
        """Render as PDF if weasyprint available, otherwise fallback to HTML.

        Returns (content, actual_format).
        """
        html = self._render_html(data, charts)
        try:
            from weasyprint import HTML as WeasyprintHTML

            pdf_bytes = WeasyprintHTML(string=html).write_pdf()
            return pdf_bytes.decode("latin-1") if isinstance(pdf_bytes, bytes) else pdf_bytes, "pdf"
        except ImportError:
            # weasyprint not installed -- fallback to HTML
            return html, "html"

    # ── Main entry point ─────────────────────────────────────

    def generate(
        self,
        days: int = 30,
        format: str = "markdown",
        write: bool = True,
    ) -> dict:
        """Generate visit summary in the specified format.

        Args:
            days: Number of days of data to include.
            format: Output format -- "markdown", "html", or "pdf".
            write: Whether to write output to files_dir.

        Returns:
            Dict with keys: path, content, format.
        """
        data = self._collect_data(days=days)
        charts = self._generate_charts(days=days)

        today = datetime.now().strftime("%Y-%m-%d")
        actual_format = format
        path = None

        if format == "markdown":
            content = self._render_markdown(data, charts)
            ext = "md"
        elif format == "html":
            content = self._render_html(data, charts)
            ext = "html"
        elif format == "pdf":
            content, actual_format = self._render_pdf(data, charts)
            ext = "pdf" if actual_format == "pdf" else "html"
        else:
            content = self._render_markdown(data, charts)
            ext = "md"
            actual_format = "markdown"

        if write:
            out_dir = self.writer.files_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = f"visit-summary-{today}.{ext}"
            out_path = out_dir / filename
            if ext == "pdf" and actual_format == "pdf":
                out_path.write_bytes(content.encode("latin-1") if isinstance(content, str) else content)
            else:
                out_path.write_text(content, encoding="utf-8")
            path = str(out_path)

        return {
            "path": path,
            "content": content,
            "format": actual_format,
        }
