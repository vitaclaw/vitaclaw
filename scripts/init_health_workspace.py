#!/usr/bin/env python3
"""Initialize a VitaClaw health workspace in a target directory."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


TEMPLATES = {
    "health-agent": {
        "directory": "openclaw-health-agent",
        "summary": "个人健康总管模板",
    },
    "health-family-agent": {
        "directory": "openclaw-health-family-agent",
        "summary": "家人照护 / 家庭健康协同模板",
    },
    "health-research-agent": {
        "directory": "openclaw-health-research-agent",
        "summary": "健康研究 / 指南情报模板",
    },
    "health-checkup-agent": {
        "directory": "openclaw-health-agent",
        "summary": "体检顾问 / 年度健康基线模板",
    },
    "health-chronic-agent": {
        "directory": "openclaw-health-agent",
        "summary": "慢病管理模板（默认支持高血压 / 糖尿病）",
    },
    "health-mental-support-agent": {
        "directory": "openclaw-health-agent",
        "summary": "支持型心理健康模板（含危机分流）",
    },
    "health-postop-agent": {
        "directory": "openclaw-health-family-agent",
        "summary": "术后恢复 / 家庭照护模板",
    },
    "health-team-agent": {
        "directory": "openclaw-health-agent",
        "summary": "chief-led 多 agent 健康团队模板",
    },
    "health-oncology-agent": {
        "directory": "openclaw-health-agent",
        "summary": "肿瘤线 / 受限专科模板",
    },
}

DEFAULT_CORE_ITEMS = {
    "annual-checkup.md": {
        "title": "Annual Checkup Records",
        "item": "annual-checkup",
        "unit": "preventive care",
        "recent": [
            "Latest annual checkup: pending",
            "Next annual checkup: pending",
            "Reminder window days: 30",
            "Preparation status: pending",
            "Notes: pending",
        ],
        "history": "| Date | Source | Status | Next Annual Checkup | Notes |\n| --- | --- | --- | --- | --- |",
        "thresholds": [
            "Reminder window days: 30",
            "Escalate when overdue days: 14",
        ],
        "rollup": [
            "Monthly digest records annual checkup due status and preparation gaps.",
            "Quarterly distillation only writes stable timing changes back to MEMORY.md.",
        ],
    },
    "appointments.md": {
        "title": "Appointment Records",
        "item": "appointments",
        "unit": "planned events",
        "recent": [
            "Latest appointment: pending",
            "Next follow-up: pending",
            "Next follow-up details: pending",
            "Preparation status: pending",
        ],
        "history": "| Date | Department / Doctor | Purpose | Status | Owner | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Escalate if follow-up is overdue by: 7 days",
            "Briefing lead time: 3 days",
        ],
        "rollup": [
            "Weekly digest highlights missed or upcoming visits.",
            "Monthly digest consolidates follow-up completion and scheduling debt.",
        ],
    },
    "behavior-plans.md": {
        "title": "Behavior Plan Records",
        "item": "behavior-plans",
        "unit": "active plan",
        "recent": [
            "Active plans: 0",
            "Next due plan: pending",
            "Focus topics: pending",
            "High-risk-only plans: none",
        ],
        "history": "| Date | Plan ID | Scenario | Title | Cadence | Due At | Status | Topic | Risk Policy | If Ignored | Next Step | Notes |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Heartbeat uses minute-level due time when `Due At` includes HH:MM.",
            "Plans marked `high-risk-only` only escalate proactively on high-risk signals.",
        ],
        "rollup": [
            "Weekly digest highlights overdue or repeatedly deferred plans.",
            "Distillation writes persistent execution barriers back to MEMORY.md.",
        ],
    },
    "blood-pressure.md": {
        "title": "Blood Pressure Records",
        "item": "blood-pressure",
        "unit": "mmHg",
        "recent": [
            "Latest: pending",
            "7-day average: pending",
            "Trend: pending",
        ],
        "history": "| Date | Time | Systolic | Diastolic | Pulse | Context | Notes |\n| --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Target home BP: <135/85 mmHg unless clinician says otherwise",
            "Urgent escalation: >=180 systolic or >=120 diastolic with concerning symptoms",
        ],
        "rollup": [
            "Weekly digest summarizes 7-day averages and consecutive elevation patterns.",
            "Monthly digest compares morning/evening drift and risk status changes.",
        ],
    },
    "blood-lipids.md": {
        "title": "Blood Lipids Records",
        "item": "blood-lipids",
        "unit": "mmol/L",
        "recent": [
            "Latest lipid panel: pending",
            "LDL-C trend: pending",
            "Risk context: pending",
        ],
        "history": "| Date | TC | LDL-C | HDL-C | TG | Non-HDL | ApoB | Notes |\n| --- | --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "LDL-C target: clinician-defined",
            "Escalate when triglycerides are persistently elevated or rapid worsening occurs",
        ],
        "rollup": [
            "Monthly digest tracks LDL-C/TG direction and treatment adherence context.",
        ],
    },
    "blood-sugar.md": {
        "title": "Blood Sugar Records",
        "item": "blood-sugar",
        "unit": "mmol/L",
        "recent": [
            "Latest fasting: pending",
            "Latest postprandial: pending",
            "30-day fasting average: pending",
            "Estimated HbA1c (eHbA1c): pending",
        ],
        "history": "| Date | Fasting | Post-Lunch 2h | Post-Dinner 2h | HbA1c | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Default fasting target: 3.9-7.0 mmol/L",
            "Default postprandial target: <=10.0 mmol/L",
        ],
        "rollup": [
            "Weekly digest calculates TIR and fasting/postprandial averages.",
            "Monthly digest updates eHbA1c and identifies sustained worsening.",
        ],
    },
    "caffeine.md": {
        "title": "Caffeine Records",
        "item": "caffeine",
        "unit": "mg",
        "recent": [
            "Latest: pending",
            "Safe sleep time: pending",
            "Trend: pending",
        ],
        "history": "| Date | Total Intake (mg) | Peak Residual (mg) | Safe Sleep Time | Drinks | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Default daily soft cap: 400 mg",
            "High-risk-only reminders can suppress low-priority caffeine nudges",
        ],
        "rollup": [
            "Weekly digest correlates caffeine with sleep score drift.",
        ],
    },
    "execution-barriers.md": {
        "title": "Execution Barrier Records",
        "item": "execution-barriers",
        "unit": "barrier",
        "recent": [
            "Latest barrier: pending",
            "Impact: pending",
            "Pattern: pending",
            "Next step: pending",
        ],
        "history": "| Date | Scenario | Barrier | Impact | Pattern | Next Step | Source Refs |\n| --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Repeated barrier patterns should escalate into long-term coaching focus.",
            "High-risk barriers can trigger stronger follow-up cadence.",
        ],
        "rollup": [
            "Weekly digest summarizes recurring barriers and skipped actions.",
            "Distillation writes stable barrier patterns back to MEMORY.md.",
        ],
    },
    "heart-rate-hrv.md": {
        "title": "Heart Rate and HRV Records",
        "item": "heart-rate-hrv",
        "unit": "bpm / ms",
        "recent": [
            "Latest resting heart rate: pending",
            "Latest HRV: pending",
            "Trend: pending",
        ],
        "history": "| Date | Resting HR | HRV | Source | Context | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Escalate if resting HR is markedly above baseline with symptoms",
            "Track HRV against personal baseline instead of population averages",
        ],
        "rollup": [
            "Weekly digest highlights baseline deviation and recovery signals.",
        ],
    },
    "kidney-function.md": {
        "title": "Kidney Function Records",
        "item": "kidney-function",
        "unit": "eGFR / creatinine",
        "recent": [
            "Latest creatinine: pending",
            "Latest eGFR: pending",
            "Trend: pending",
        ],
        "history": "| Date | Creatinine | eGFR | UACR | CKD Stage | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Escalate when eGFR decline is rapid or new albuminuria appears",
            "Use lab reference range plus clinician-set threshold when available",
        ],
        "rollup": [
            "Monthly digest tracks CKD stage drift and overdue recheck windows.",
        ],
    },
    "liver-function.md": {
        "title": "Liver Function Records",
        "item": "liver-function",
        "unit": "U/L",
        "recent": [
            "Latest ALT/AST: pending",
            "Trend: pending",
            "Medication context: pending",
        ],
        "history": "| Date | ALT | AST | GGT | ALP | Bilirubin | Notes |\n| --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Escalate when values are clearly worsening or symptoms are present",
            "Flag medication, alcohol, supplement, or illness context in Notes",
        ],
        "rollup": [
            "Monthly digest calls out persistent abnormality and follow-up debt.",
        ],
    },
    "medications.md": {
        "title": "Medication Records",
        "item": "medications",
        "unit": "active regimen",
        "recent": [
            "Latest: pending",
            "Adherence: pending",
            "Next refill: pending",
            "Stock coverage days: pending",
            "Risks: pending",
        ],
        "history": "| Date | Medication | Dose | Frequency | Status | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Refill reminder lead time: 7 days",
            "Escalate when coverage days drop below 3 or repeated misses occur",
        ],
        "rollup": [
            "Weekly digest summarizes adherence and missed-dose patterns.",
            "Monthly digest highlights refill debt and regimen changes.",
        ],
    },
    "mental-health-score.md": {
        "title": "Mental Health Score Records",
        "item": "mental-health-score",
        "unit": "score",
        "recent": [
            "Latest PHQ-9: pending",
            "Latest GAD-7: pending",
            "Trend: pending",
        ],
        "history": "| Date | Tool | Score | Severity | Trigger | Notes |\n| --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "High-risk mental health signals always override low-priority reminders",
            "Escalate immediately for self-harm risk or severe worsening",
        ],
        "rollup": [
            "Weekly digest surfaces mood/sleep/function changes together.",
        ],
    },
    "sleep.md": {
        "title": "Sleep Records",
        "item": "sleep",
        "unit": "score (0-100)",
        "recent": [
            "Latest: pending",
            "7-day average score: pending",
            "7-day average duration: pending",
            "Trend: pending",
        ],
        "history": "| Date | Score | Duration | Efficiency | Latency | Bedtime | Waketime | Notes |\n| --- | --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Escalate when sleep worsens together with mood, BP, or safety signals",
            "Use multi-night trend instead of single-night judgment",
        ],
        "rollup": [
            "Weekly digest compares score, duration, and adherence impact.",
        ],
    },
    "supplements.md": {
        "title": "Supplement Records",
        "item": "supplements",
        "unit": "daily regimen",
        "recent": [
            "Latest: pending",
            "Today's adherence: pending",
            "Warnings: pending",
        ],
        "history": "| Date | Active Items | Taken | Expected | Adherence | Warnings | Notes |\n| --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Escalate when interactions, duplicated ingredients, or repeated misses appear",
        ],
        "rollup": [
            "Weekly digest summarizes adherence and warning recurrence.",
        ],
    },
    "tumor-markers.md": {
        "title": "Tumor Marker Records",
        "item": "tumor-markers",
        "unit": "lab-specific",
        "recent": [
            "Latest marker panel: pending",
            "Trend: pending",
            "Clinical context: pending",
        ],
        "history": "| Date | Marker | Value | Unit | Reference | Trend | Notes |\n| --- | --- | --- | --- | --- | --- | --- |",
        "thresholds": [
            "Never interpret tumor markers in isolation from imaging or clinician context",
            "Escalate when rapid rise or multi-marker worsening is documented",
        ],
        "rollup": [
            "Monthly digest tracks marker direction and pending oncology follow-up.",
        ],
    },
    "weight.md": {
        "title": "Weight Records",
        "item": "weight",
        "unit": "kg",
        "recent": [
            "Latest: pending",
            "30-day trend: pending",
            "BMI: pending",
        ],
        "history": "| Date | Weight (kg) | BMI | Notes |\n| --- | --- | --- | --- |",
        "thresholds": [
            "Track against personal goal and clinician-defined concern threshold",
            "Escalate when unintentional change is rapid or persistent",
        ],
        "rollup": [
            "Weekly digest compares start/end of week and trend direction.",
            "Monthly digest highlights sustained change and goal distance.",
        ],
    },
}
ONBOARDING_QUESTIONS = [
    ("health_role", "健康角色定位", "例如：个人健康总管 / 家庭照护协调者 / 研究支持分身"),
    ("audience", "使用人群（本人 / 家人 / 患者 / 照护者）", "例如：本人"),
    ("scenario_focus", "场景 focus", "例如：hypertension / diabetes / annual-checkup / family-care / mental-support"),
    ("primary_goals", "主要健康目标", "可写多个，用分号分隔"),
    ("conditions_and_medications", "既有慢病与长期用药", "可写多个，用分号分隔；没有就写 无"),
    ("reminder_preference", "提醒偏好与输出语气", "例如：低打扰、先数据后建议、高风险强提醒"),
    ("reminder_strength", "提醒强度", "例如：gentle / balanced / proactive"),
    ("focus_closely", "需要重点盯紧的指标/主题", "例如：blood-pressure; blood-sugar; appointments"),
    ("high_risk_only_topics", "只在高风险时提醒的主题", "例如：sleep; supplements；没有就写 无"),
    ("default_cadence", "场景默认 cadence", "例如：bp=12h; glucose=8h; weekly-review=Sun 18:00"),
    ("care_team", "常用医院 / 医生 / 科室", "可写多个，用分号分隔；没有就写 待补充"),
]

TEMPLATE_DEFAULTS = {
    "health-checkup-agent": {
        "scenario_focus": "annual-checkup",
        "reminder_strength": "balanced",
        "focus_closely": "annual-checkup; appointments",
        "high_risk_only_topics": "sleep; supplements",
        "default_cadence": "annual-checkup=30d-window; monthly-review=1x",
    },
    "health-chronic-agent": {
        "scenario_focus": "hypertension",
        "reminder_strength": "proactive",
        "focus_closely": "blood-pressure; blood-sugar; medication; appointments",
        "high_risk_only_topics": "supplements",
        "default_cadence": "bp=12h; glucose=8h; weekly-review=Sun 18:00",
    },
    "health-mental-support-agent": {
        "scenario_focus": "mental-support",
        "reminder_strength": "gentle",
        "focus_closely": "sleep; mental-health-score",
        "high_risk_only_topics": "supplements",
        "default_cadence": "sleep-check=24h; weekly-assessment=7d",
    },
    "health-postop-agent": {
        "scenario_focus": "postop-recovery",
        "reminder_strength": "proactive",
        "focus_closely": "appointments; medication; weight",
        "high_risk_only_topics": "sleep",
        "default_cadence": "wound-check=12h; follow-up=event",
    },
    "health-team-agent": {
        "scenario_focus": "hypertension",
        "reminder_strength": "proactive",
        "focus_closely": "blood-pressure; blood-sugar; appointments; behavior-plans",
        "high_risk_only_topics": "supplements",
        "default_cadence": "chief=30m; bp=12h; glucose=8h; weekly-review=Sun 18:00",
    },
    "health-oncology-agent": {
        "scenario_focus": "oncology-care",
        "reminder_strength": "balanced",
        "focus_closely": "tumor-markers; appointments; annual-checkup; timeline",
        "high_risk_only_topics": "supplements",
        "default_cadence": "oncology-review=event; marker-check=30d; chief=30m",
    },
}

TEAM_ROLE_CADENCE = {
    "health-chief-of-staff": "30m",
    "health-main": "2h",
    "health-records": "6h",
    "health-metrics": "2h",
    "health-lifestyle": "12h",
    "health-safety": "30m",
    "health-research": "0m",
    "health-mental": "8h",
    "health-family": "6h",
    "health-oncology": "0m",
}

PACKAGE_ROLE_MATRIX = {
    "core": [
        "health-chief-of-staff",
        "health-main",
        "health-records",
        "health-metrics",
        "health-lifestyle",
        "health-safety",
        "health-research",
        "health-mental",
    ],
    "family-care": ["health-family"],
    "oncology": ["health-oncology"],
    "labs": [],
}

TEMPLATE_PACKAGE_DEFAULTS = {
    "health-agent": ["core"],
    "health-family-agent": ["core", "family-care"],
    "health-research-agent": ["core"],
    "health-checkup-agent": ["core"],
    "health-chronic-agent": ["core"],
    "health-mental-support-agent": ["core"],
    "health-postop-agent": ["core", "family-care"],
    "health-team-agent": ["core"],
    "health-oncology-agent": ["core", "oncology", "labs"],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def available_templates() -> list[str]:
    return sorted(TEMPLATES)


def template_root(template_name: str) -> Path:
    if template_name not in TEMPLATES:
        available = ", ".join(available_templates())
        raise ValueError(f"Unknown template '{template_name}'. Available: {available}")
    return repo_root() / "templates" / TEMPLATES[template_name]["directory"]


def iter_template_files(source_root: Path) -> list[Path]:
    return sorted(path for path in source_root.rglob("*") if path.is_file())


def copy_template_file(source_root: Path, target_root: Path, source: Path, force: bool) -> str:
    relative_path = source.relative_to(source_root)
    target = target_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not force:
        return f"skip   {relative_path.as_posix()}"

    shutil.copy2(source, target)
    return f"create {relative_path.as_posix()}"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _item_template(filename: str, payload: dict, now_iso: str) -> str:
    recent_lines = "\n".join(f"- {line}" for line in payload["recent"])
    threshold_lines = "\n".join(f"- {line}" for line in payload["thresholds"])
    rollup_lines = "\n".join(f"- {line}" for line in payload["rollup"])
    return "\n".join(
        [
            "---",
            f"item: {payload['item']}",
            f"unit: {payload['unit']}",
            f"updated_at: {now_iso}",
            "---",
            "",
            f"# {payload['title']}",
            "",
            "## Recent Status",
            recent_lines,
            "",
            "## History",
            payload["history"],
            "",
            "## Thresholds",
            threshold_lines,
            "",
            "## Rollup Rules",
            rollup_lines,
            "",
        ]
    )


def ensure_core_item_templates(target_dir: Path, force: bool = False) -> list[str]:
    now_iso = datetime.now().isoformat(timespec="seconds")
    logs: list[str] = []
    items_dir = target_dir / "memory" / "health" / "items"
    for filename, payload in sorted(DEFAULT_CORE_ITEMS.items()):
        path = items_dir / filename
        if path.exists() and not force:
            continue
        _write_text(path, _item_template(filename, payload, now_iso))
        logs.append(f"create memory/health/items/{filename}")
    return logs


def ensure_runtime_files(target_dir: Path, force: bool = False) -> list[str]:
    logs: list[str] = []
    for relative in (
        Path("memory/health/monthly/.gitkeep"),
        Path("memory/health/quarterly/.gitkeep"),
        Path("memory/health/team/tasks/.gitkeep"),
        Path("memory/health/team/briefs/.gitkeep"),
        Path("memory/health/team/audit/.gitkeep"),
    ):
        path = target_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            continue
        _write_text(path, "")
        logs.append(f"create {relative.as_posix()}")

    board_path = target_dir / "memory" / "health" / "heartbeat" / "task-board.md"
    if not board_path.exists() or force:
        _write_text(
            board_path,
            "\n".join(
                [
                    "# Heartbeat Task Board -- pending",
                    "",
                    "- 初始化后运行 `python3 scripts/run_health_heartbeat.py` 生成第一版任务板。",
                    "",
                    "## Open",
                    "- none",
                ]
            ),
        )
        logs.append("create memory/health/heartbeat/task-board.md")

    state_path = target_dir / "memory" / "health" / "heartbeat" / "task-state.json"
    if not state_path.exists() or force:
        _write_text(state_path, '{\n  "updated_at": "pending",\n  "tasks": []\n}')
        logs.append("create memory/health/heartbeat/task-state.json")

    team_board_path = target_dir / "memory" / "health" / "team" / "team-board.md"
    if not team_board_path.exists() or force:
        _write_text(
            team_board_path,
            "\n".join(
                [
                    "# Team Board -- pending",
                    "",
                    "## Open Tasks",
                    "- 初始化后运行 `python3 scripts/run_health_chief_of_staff.py heartbeat` 生成第一版团队状态板。",
                    "",
                    "## Active Roles",
                    "- health-chief-of-staff: pending",
                    "",
                    "## Latest Outputs",
                    "- none",
                ]
            ),
        )
        logs.append("create memory/health/team/team-board.md")

    dispatch_path = target_dir / "memory" / "health" / "team" / "audit" / "dispatch-log.jsonl"
    if not dispatch_path.exists() or force:
        _write_text(dispatch_path, "")
        logs.append("create memory/health/team/audit/dispatch-log.jsonl")
    return logs


def init_workspace(
    target_dir: Path,
    template_name: str = "health-agent",
    packages: list[str] | None = None,
    force: bool = False,
) -> list[str]:
    source_root = template_root(template_name)
    logs = []
    for source in iter_template_files(source_root):
        logs.append(copy_template_file(source_root, target_dir, source, force))
    logs.extend(ensure_core_item_templates(target_dir, force=force))
    logs.extend(ensure_runtime_files(target_dir, force=force))
    logs.extend(write_workspace_config(target_dir, template_name=template_name, packages=packages, force=force))
    return logs


def _split_semicolon_items(value: str) -> list[str]:
    parts = [part.strip() for part in value.replace("；", ";").split(";")]
    return [part for part in parts if part]


def collect_onboarding_answers(input_fn=input) -> dict[str, str]:
    answers: dict[str, str] = {}
    for key, question, hint in ONBOARDING_QUESTIONS:
        prompt = f"{question}\n> {hint}\n> "
        answers[key] = input_fn(prompt).strip()
    return answers


def _with_template_defaults(template_name: str, answers: dict[str, str]) -> dict[str, str]:
    merged = dict(TEMPLATE_DEFAULTS.get(template_name, {}))
    merged.update({key: value for key, value in answers.items() if value})
    return merged


def _bulletize(value: str, default: str = "待填写") -> list[str]:
    items = _split_semicolon_items(value)
    if not items:
        return [default]
    return items


def _render_identity(template_name: str, answers: dict[str, str]) -> str:
    title = {
        "health-agent": "VitaClaw Health Identity",
        "health-family-agent": "VitaClaw Family Health Identity",
        "health-research-agent": "VitaClaw Research Identity",
        "health-checkup-agent": "VitaClaw Checkup Identity",
        "health-chronic-agent": "VitaClaw Chronic Care Identity",
        "health-mental-support-agent": "VitaClaw Mental Support Identity",
        "health-postop-agent": "VitaClaw Post-Op Identity",
        "health-team-agent": "VitaClaw Chief-Led Team Identity",
        "health-oncology-agent": "VitaClaw Oncology Identity",
    }[template_name]
    audience = answers.get("audience", "待填写") or "待填写"
    role = answers.get("health_role", "待填写") or "待填写"
    return "\n".join(
        [
            f"# {title}",
            "",
            "## 定位",
            f"- 角色：{role}",
            f"- 服务对象：{audience}",
            "- 默认原则：连续、克制、长期跟踪、先事实后建议",
            "",
            "## Iteration 1 记忆策略",
            "- 长期记忆默认仅在 direct chat 中主动加载",
            "- group / public 场景默认不自动加载 `MEMORY.md`",
            "- Iteration 1 不启用 QMD",
            "",
            "## Iteration 2 场景化默认",
            f"- 场景 focus：{answers.get('scenario_focus', '待填写') or '待填写'}",
            f"- 提醒强度：{answers.get('reminder_strength', 'balanced') or 'balanced'}",
            "",
            "## Iteration 3 团队默认",
            "- 默认单入口：`health-chief-of-staff`",
            "- 长期事实写回：`health-main`",
            "- specialist 只生成 brief / task / 审计，不直接改长期画像",
        ]
    )


def _render_user(answers: dict[str, str]) -> str:
    care_team = _bulletize(answers.get("care_team", ""), default="待补充")
    goals = _bulletize(answers.get("primary_goals", ""), default="待补充")
    lines = [
        "# User Preferences",
        "",
        "## 使用画像",
        f"- 健康角色定位：{answers.get('health_role', '待填写') or '待填写'}",
        f"- 服务对象：{answers.get('audience', '待填写') or '待填写'}",
        f"- 场景 focus：{answers.get('scenario_focus', '待填写') or '待填写'}",
        "",
        "## 目标偏好",
    ]
    lines.extend(f"- {item}" for item in goals)
    lines.extend(
        [
            "",
            "## 提醒与表达",
            f"- 提醒偏好与输出语气：{answers.get('reminder_preference', '待填写') or '待填写'}",
            f"- 提醒强度：{answers.get('reminder_strength', 'balanced') or 'balanced'}",
            f"- 重点盯紧：{answers.get('focus_closely', '待填写') or '待填写'}",
            f"- 仅高风险提醒：{answers.get('high_risk_only_topics', '待填写') or '待填写'}",
            f"- 默认 cadence：{answers.get('default_cadence', '待填写') or '待填写'}",
            "- 输出层级：记录 / 解读 / 趋势 / 风险 / 建议 / 必须就医",
            "",
            "## 常用医疗资源",
        ]
    )
    lines.extend(f"- {item}" for item in care_team)
    return "\n".join(lines)


def _render_memory(answers: dict[str, str]) -> str:
    conditions = _bulletize(answers.get("conditions_and_medications", ""), default="待补充")
    goals = _bulletize(answers.get("primary_goals", ""), default="待补充")
    lines = [
        "# VitaClaw Long-Term Memory",
        "",
        "## 使用边界",
        "- 这里只记录长期稳定事实，不记录当天临时事件。",
        "- daily/ 只写当天发生的记录、执行、波动和临时处理。",
        "- items/ 只写纵向聚合、阈值、趋势和历史表。",
        "- 患者档案目录只存原始证据，MEMORY.md 只保留最小必要摘要。",
        "",
        "## 长期角色与服务对象",
        f"- 健康角色定位：{answers.get('health_role', '待填写') or '待填写'}",
        f"- 服务对象：{answers.get('audience', '待填写') or '待填写'}",
        f"- 场景 focus：{answers.get('scenario_focus', '待填写') or '待填写'}",
        "",
        "## 长期目标",
    ]
    lines.extend(f"- {item}" for item in goals)
    lines.extend(
        [
            "",
            "## 已知诊断与长期用药",
        ]
    )
    lines.extend(f"- {item}" for item in conditions)
    lines.extend(
        [
            "",
            "## 提醒与沟通偏好",
            f"- {answers.get('reminder_preference', '待填写') or '待填写'}",
            f"- 提醒强度：{answers.get('reminder_strength', 'balanced') or 'balanced'}",
            f"- 重点盯紧：{answers.get('focus_closely', '待填写') or '待填写'}",
            f"- 仅高风险提醒：{answers.get('high_risk_only_topics', '待填写') or '待填写'}",
            f"- 默认 cadence：{answers.get('default_cadence', '待填写') or '待填写'}",
            "",
            "## 常用医疗资源",
        ]
    )
    lines.extend(f"- {item}" for item in _bulletize(answers.get("care_team", ""), default="待补充"))
    lines.extend(
        [
            "",
            "## 读取顺序",
            "1. `BOOTSTRAP.md`",
            "2. `SOUL.md`",
            "3. `MEMORY.md`",
            "4. `memory/health/_health-profile.md`",
            "5. 最近 1-3 天 `memory/health/daily/*.md`",
            "6. 按需读取相关 `memory/health/items/*.md`",
        ]
    )
    return "\n".join(lines)


def _render_profile(answers: dict[str, str]) -> str:
    now_iso = datetime.now().isoformat(timespec="seconds")
    conditions = _bulletize(answers.get("conditions_and_medications", ""), default="待补充")
    goals = _bulletize(answers.get("primary_goals", ""), default="待补充")
    lines = [
        "---",
        f"updated_at: {now_iso}",
        "---",
        "",
        "# Health Profile",
        "",
        "## Baseline",
        "- Name: pending",
        "- Date of birth: pending",
        "- Sex: pending",
        f"- Service role: {answers.get('health_role', '待填写') or '待填写'}",
        f"- Audience: {answers.get('audience', '待填写') or '待填写'}",
        f"- Scenario focus: {answers.get('scenario_focus', '待填写') or '待填写'}",
        "",
        "## Conditions",
    ]
    lines.extend(f"- {item}" for item in conditions)
    lines.extend(
        [
            "",
            "## Long-Term Goals",
        ]
    )
    lines.extend(f"- {item}" for item in goals)
    lines.extend(
        [
            "",
            "## Medications",
            "- 从长期事实中补齐固定用药、剂量和频率",
            "",
            "## Care Team",
        ]
    )
    lines.extend(f"- {item}" for item in _bulletize(answers.get("care_team", ""), default="待补充"))
    lines.extend(
        [
            "",
            "## Reminder Preferences",
            f"- {answers.get('reminder_preference', '待填写') or '待填写'}",
            f"- Strength: {answers.get('reminder_strength', 'balanced') or 'balanced'}",
            f"- Focus closely: {answers.get('focus_closely', '待填写') or '待填写'}",
            f"- High-risk-only topics: {answers.get('high_risk_only_topics', '待填写') or '待填写'}",
            f"- Default cadence: {answers.get('default_cadence', '待填写') or '待填写'}",
            "",
            "## Risk Thresholds",
            "- 危急生命体征、明显进行性恶化、急性危险症状、严重精神危机优先升级",
            "- 具体阈值后续写入相关 item 的 `## Thresholds`",
        ]
    )
    return "\n".join(lines)


def _render_preferences(answers: dict[str, str]) -> str:
    return "\n".join(
        [
            "---",
            f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
            "---",
            "",
            "# Reminder Preferences",
            "",
            "## Delivery",
            "- Primary channel: heartbeat-report",
            "- Push channel: openclaw-native",
            f"- Tone: {answers.get('reminder_strength', 'balanced') or 'balanced'}",
            "",
            "## Schedule",
            "- Quiet hours: 22:00-08:00",
            "- Working hours: 09:00-18:00",
            f"- Scenario cadence: {answers.get('default_cadence', 'pending') or 'pending'}",
            "",
            "## Repeat Cadence",
            "- Low priority repeat hours: 24",
            "- Medium priority repeat hours: 12",
            "- High priority repeat hours: 4",
            "",
            "## Follow-up Cadence",
            "- Low priority follow-up hours: 36",
            "- Medium priority follow-up hours: 24",
            "- High priority follow-up hours: 8",
            "",
            "## Focus",
            f"- Focus closely: {answers.get('focus_closely', 'blood pressure, blood sugar, appointments') or 'blood pressure, blood sugar, appointments'}",
            f"- High-risk-only topics: {answers.get('high_risk_only_topics', 'sleep, supplements') or 'sleep, supplements'}",
            "",
        ]
    )


def _seed_behavior_plans(target_dir: Path, answers: dict[str, str]) -> str:
    focus = answers.get("scenario_focus", "general") or "general"
    default_title = {
        "hypertension": "补齐下一次家庭血压记录",
        "diabetes": "补齐下一次血糖记录",
        "annual-checkup": "准备下一次年度体检或异常项 follow-up",
        "mental-support": "完成下一次睡眠/情绪支持性记录",
        "postop-recovery": "完成下一次术后恢复检查",
    }.get(focus, "完成下一次健康关键动作")
    cadence = answers.get("default_cadence", "pending") or "pending"
    content = "\n".join(
        [
            "---",
            "item: behavior-plans",
            "unit: active plan",
            f"updated_at: {datetime.now().isoformat(timespec='seconds')}",
            "---",
            "",
            "# Behavior Plan Records",
            "",
            "## Recent Status",
            "- Active plans: 1",
            f"- Next due plan: onboarding-seed | {default_title}",
            f"- Focus topics: {answers.get('focus_closely', focus) or focus}",
            f"- High-risk-only plans: {answers.get('high_risk_only_topics', 'none') or 'none'}",
            "",
            "## History",
            "| Date | Plan ID | Scenario | Title | Cadence | Due At | Status | Topic | Risk Policy | If Ignored | Next Step | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            f"| {datetime.now().date().isoformat()} | onboarding-seed | {focus} | {default_title} | {cadence} | pending | active | {focus} | focus-closely | 健康闭环会中断 | 按模板运行对应场景入口脚本 | 初始化自动生成 |",
            "",
            "## Thresholds",
            "- Heartbeat uses minute-level due time when `Due At` includes HH:MM.",
            "- Plans marked `high-risk-only` only escalate proactively on high-risk signals.",
            "",
            "## Rollup Rules",
            "- Weekly digest highlights overdue or repeatedly deferred plans.",
            "- Distillation writes persistent execution barriers back to MEMORY.md.",
            "",
        ]
    )
    path = target_dir / "memory" / "health" / "items" / "behavior-plans.md"
    _write_text(path, content)
    return path.relative_to(target_dir).as_posix()


def _normalize_packages(template_name: str, packages: list[str] | None = None) -> list[str]:
    result = ["core"]
    for item in TEMPLATE_PACKAGE_DEFAULTS.get(template_name, ["core"]):
        if item not in result:
            result.append(item)
    for item in packages or []:
        clean = item.strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _enabled_roles(packages: list[str]) -> list[str]:
    roles: list[str] = []
    for package in packages:
        for role in PACKAGE_ROLE_MATRIX.get(package, []):
            if role not in roles:
                roles.append(role)
    return roles


def _workspace_config_text(target_dir: Path, template_name: str, packages: list[str]) -> str:
    roles = _enabled_roles(packages)
    agent_blocks = []
    for role in roles:
        cadence = TEAM_ROLE_CADENCE.get(role, "0m")
        default = "true" if role == "health-chief-of-staff" else "false"
        agent_blocks.append(
            "\n".join(
                [
                    "      {",
                    f'        id: "{role}",',
                    f"        default: {default},",
                    f'        workspace: "{target_dir}",',
                    "        heartbeat: {",
                    f'          every: "{cadence}",',
                    "        },",
                    "      },",
                ]
            )
        )
    default_roles = ", ".join(f'"{role}"' for role in roles)
    packages_text = ", ".join(f'"{item}"' for item in packages)
    route_table = "\n".join(
        [
            '        "hypertension-daily-copilot": ["health-metrics", "health-lifestyle"],',
            '        "diabetes-control-hub": ["health-metrics", "health-lifestyle"],',
            '        "annual-checkup-advisor": ["health-records", "health-metrics"],',
            '        "mental-support": ["health-mental"],',
            '        "research-brief": ["health-research"],',
            '        "family-care": ["health-family"],',
            '        "oncology-review": ["health-oncology", "health-research", "health-safety"],',
        ]
    )
    return "\n".join(
        [
            "{",
            '  identity: { name: "VitaClaw", theme: "chief-led health team", emoji: "🩺" },',
            "  agents: {",
            "    defaults: {",
            f'      workspace: "{target_dir}",',
            '      userTimezone: "Asia/Shanghai",',
            "      heartbeat: {",
            '        every: "2h",',
            "        lightContext: false,",
            "        isolatedSession: false,",
            '        target: "none",',
            '        directPolicy: "block",',
            "      },",
            "      memorySearch: {",
            '        extraPaths: ["memory/health"],',
            "        longTermPolicy: {",
            '          mode: "direct-chat-only",',
            "          loadMemoryInDirectChats: true,",
            "          loadMemoryInGroupChats: false,",
            "          loadMemoryInPublicThreads: false,",
            "          qmdEnabled: false,",
            "        },",
            "      },",
            "      sandbox: { mode: \"non-main\", scope: \"agent\" },",
            "    },",
            "    list: [",
            *agent_blocks,
            "    ],",
            "  },",
            "  vitaclaw: {",
            "    proactiveService: {",
            '      deliveryModel: "openclaw-native",',
            "      appointmentLeadTimeDays: 3,",
            "      refillLeadTimeDays: 7,",
            "    },",
            "    team: {",
            '      entryAgent: "health-chief-of-staff",',
            f"      defaultEnabledRoles: [{default_roles}],",
            "      roleCadence: {",
            *[f'        "{role}": "{TEAM_ROLE_CADENCE[role]}",' for role in roles if role in TEAM_ROLE_CADENCE],
            "      },",
            "      routeTable: {",
            route_table,
            "      },",
            "      privacyDefaults: {",
            "        loadMemoryInGroupChats: false,",
            "        loadMemoryInPublicThreads: false,",
            "        publicAgentsCanReadPatientArchive: false,",
            "      },",
            '      externalActionPolicy: "high-threshold",',
            f"      packageMatrix: [{packages_text}],",
            f'      template: "{template_name}",',
            "    },",
            "  },",
            "}",
        ]
    )


def write_workspace_config(
    target_dir: Path,
    template_name: str,
    packages: list[str] | None = None,
    force: bool = False,
) -> list[str]:
    package_list = _normalize_packages(template_name, packages)
    path = target_dir / "openclaw.health.json5"
    if path.exists() and not force:
        return []
    _write_text(path, _workspace_config_text(target_dir, template_name, package_list))
    return [f"create {path.relative_to(target_dir).as_posix()}"]


def apply_onboarding(
    target_dir: Path,
    template_name: str,
    packages: list[str] | None = None,
    answers: dict[str, str] | None = None,
    input_fn=input,
) -> list[str]:
    resolved_answers = _with_template_defaults(
        template_name,
        answers or collect_onboarding_answers(input_fn=input_fn),
    )
    logs: list[str] = []
    writes = {
        target_dir / "IDENTITY.md": _render_identity(template_name, resolved_answers),
        target_dir / "USER.md": _render_user(resolved_answers),
        target_dir / "MEMORY.md": _render_memory(resolved_answers),
        target_dir / "memory" / "health" / "_health-profile.md": _render_profile(resolved_answers),
        target_dir / "memory" / "health" / "heartbeat" / "preferences.md": _render_preferences(resolved_answers),
    }
    for path, content in writes.items():
        _write_text(path, content)
        logs.append(f"onboard {path.relative_to(target_dir).as_posix()}")
    logs.append(f"onboard {_seed_behavior_plans(target_dir, resolved_answers)}")
    logs.extend(write_workspace_config(target_dir, template_name=template_name, packages=packages, force=True))
    return logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a VitaClaw health workspace")
    parser.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    parser.add_argument(
        "--template",
        choices=available_templates(),
        default="health-agent",
        help="Template variant to initialize",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates and exit",
    )
    parser.add_argument(
        "--packages",
        default="",
        help="Comma-separated package selection: core,family-care,oncology,labs",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--onboard",
        action="store_true",
        help="Run the interactive onboarding wizard after copying the template",
    )
    args = parser.parse_args()

    if args.list_templates:
        print("Available VitaClaw templates:")
        for name in available_templates():
            print(f"  {name:<22} {TEMPLATES[name]['summary']}")
        return

    target_dir = Path(args.target).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    packages = [item.strip() for item in args.packages.split(",") if item.strip()]

    print(f"Initializing VitaClaw health workspace at: {target_dir}")
    print(f"Using template: {args.template} ({TEMPLATES[args.template]['summary']})")
    for message in init_workspace(
        target_dir,
        template_name=args.template,
        packages=packages,
        force=args.force,
    ):
        print(f"  {message}")

    if args.onboard:
        print("Starting onboarding wizard...")
        for message in apply_onboarding(
            target_dir,
            template_name=args.template,
            packages=packages,
        ):
            print(f"  {message}")


if __name__ == "__main__":
    main()
