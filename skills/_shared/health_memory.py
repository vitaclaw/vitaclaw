#!/usr/bin/env python3
"""Helpers for writing to the shared memory/health workspace."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_memory_root(
    workspace_root: str | None = None, memory_root: str | None = None
) -> Path:
    if memory_root:
        return Path(memory_root).expanduser().resolve()

    env = __import__("os").environ
    if "VITACLAW_MEMORY_DIR" in env:
        return Path(env["VITACLAW_MEMORY_DIR"]).expanduser().resolve()

    if workspace_root:
        base = Path(workspace_root).expanduser().resolve()
    elif "OPENCLAW_WORKSPACE" in env:
        base = Path(env["OPENCLAW_WORKSPACE"]).expanduser().resolve()
    elif "VITACLAW_WORKSPACE" in env:
        base = Path(env["VITACLAW_WORKSPACE"]).expanduser().resolve()
    else:
        base = _repo_root()

    return base / "memory" / "health"


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            return parts[1].lstrip()
    return text


def _format_duration(total_min) -> str:
    if total_min is None:
        return "?"
    hours, minutes = divmod(int(total_min), 60)
    return f"{hours}h{minutes:02d}min"


def _parse_date(text: str) -> datetime | None:
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None


def _plus_one_year(date_str: str) -> str | None:
    base = _parse_date(date_str)
    if base is None:
        return None
    try:
        return base.replace(year=base.year + 1).strftime("%Y-%m-%d")
    except ValueError:
        # Handle leap day by falling back to Feb 28 next year.
        return base.replace(month=2, day=28, year=base.year + 1).strftime("%Y-%m-%d")


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class HealthMemoryWriter:
    """Write skill outputs into the shared markdown-based health memory."""

    def __init__(
        self,
        workspace_root: str | None = None,
        memory_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.base_dir = _resolve_memory_root(
            workspace_root=workspace_root, memory_root=memory_root
        )
        if workspace_root:
            self.workspace_dir = Path(workspace_root).expanduser().resolve()
        elif self.base_dir.parent.name == "memory":
            self.workspace_dir = self.base_dir.parent.parent
        else:
            self.workspace_dir = None
        self.daily_dir = self.base_dir / "daily"
        self.items_dir = self.base_dir / "items"
        self.files_dir = self.base_dir / "files"
        self.weekly_dir = self.base_dir / "weekly"
        self.monthly_dir = self.base_dir / "monthly"
        self.quarterly_dir = self.base_dir / "quarterly"
        self.heartbeat_dir = self.base_dir / "heartbeat"
        self.team_dir = self.base_dir / "team"
        self.team_tasks_dir = self.team_dir / "tasks"
        self.team_briefs_dir = self.team_dir / "briefs"
        self.team_audit_dir = self.team_dir / "audit"
        self.heartbeat_preferences_path = self.heartbeat_dir / "preferences.md"
        self.heartbeat_task_board_path = self.heartbeat_dir / "task-board.md"
        self.heartbeat_task_state_path = self.heartbeat_dir / "task-state.json"
        self.team_board_path = self.team_dir / "team-board.md"
        self.dispatch_log_path = self.team_audit_dir / "dispatch-log.jsonl"
        self.behavior_plans_path = self.items_dir / "behavior-plans.md"
        self.execution_barriers_path = self.items_dir / "execution-barriers.md"
        self.write_audit_path = self.files_dir / "write-audit.md"
        self.profile_path = self.base_dir / "_health-profile.md"
        self.weekly_digest_path = self.base_dir / "weekly-digest.md"
        self.monthly_digest_path = self.base_dir / "monthly-digest.md"
        self.memory_doc_path = self.workspace_dir / "MEMORY.md" if self.workspace_dir else None
        self._ensure_structure()

    def _now(self) -> datetime:
        return self._now_fn()

    def _now_iso(self) -> str:
        return self._now().isoformat(timespec="seconds")

    def _mean(self, values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 1)

    def _value_status(self, value: float, low: float | None = None, high: float | None = None) -> str:
        if low is not None and value < low:
            return "Low"
        if high is not None and value > high:
            return "High"
        return "In range"

    def _trend_from_values(self, values: list[float], stable_delta: float = 0.5) -> str:
        if len(values) < 2:
            return "Insufficient data"
        delta = values[-1] - values[0]
        if delta > stable_delta:
            return "Rising"
        if delta < -stable_delta:
            return "Falling"
        return "Stable"

    def _ensure_structure(self) -> None:
        for path in (
            self.base_dir,
            self.daily_dir,
            self.items_dir,
            self.files_dir,
            self.weekly_dir,
            self.monthly_dir,
            self.quarterly_dir,
            self.heartbeat_dir,
            self.team_dir,
            self.team_tasks_dir,
            self.team_briefs_dir,
            self.team_audit_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

        if not self.profile_path.exists():
            self.profile_path.write_text(
                "\n".join(
                    [
                        "---",
                        f"updated_at: {self._now_iso()}",
                        "---",
                        "",
                        "# Health Profile",
                        "",
                        "## Baseline",
                        "- Name: pending",
                        "- Date of birth: pending",
                        "- Sex: pending",
                        "",
                        "## Conditions",
                        "- None documented yet",
                        "",
                        "## Medications",
                        "- None documented yet",
                        "",
                        "## Allergies",
                        "- None documented yet",
                        "",
                        "## Care Preferences",
                        "- Prioritize continuity, privacy, and clear clinical boundaries",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

        if not self.heartbeat_preferences_path.exists():
            self.heartbeat_preferences_path.write_text(
                "\n".join(
                    [
                        "---",
                        f"updated_at: {self._now_iso()}",
                        "---",
                        "",
                        "# Reminder Preferences",
                        "",
                        "## Delivery",
                        "- Primary channel: heartbeat-report",
                        "- Push channel: pending",
                        "- Tone: gentle",
                        "",
                        "## Schedule",
                        "- Quiet hours: 22:00-08:00",
                        "- Working hours: 09:00-18:00",
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
                        "- Focus closely: blood pressure, blood sugar, medication, appointments",
                        "- High-risk-only topics: sleep, supplements",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

        if not self.team_board_path.exists():
            self.team_board_path.write_text(
                "\n".join(
                    [
                        f"# Team Board -- {self._now().date().isoformat()}",
                        "",
                        "## Open Tasks",
                        "- none",
                        "",
                        "## Active Roles",
                        "- health-chief-of-staff: pending",
                        "",
                        "## Latest Outputs",
                        "- none",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

        if not self.dispatch_log_path.exists():
            self.dispatch_log_path.write_text("", encoding="utf-8")

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")

    def _render_item_document(
        self,
        item_slug: str,
        title: str,
        unit: str,
        recent_lines: list[str],
        headers: list[str],
        rows: list[list[str]],
        thresholds: list[str] | None = None,
        rollup_rules: list[str] | None = None,
    ) -> str:
        doc_lines = [
            "---",
            f"item: {item_slug}",
            f"unit: {unit}",
            f"updated_at: {self._now_iso()}",
            "---",
            "",
            f"# {title}",
            "",
            "## Recent Status",
            *[line if line.startswith("- ") else f"- {line}" for line in recent_lines if line],
            "",
            "## History",
            self._history_table(headers, rows),
            "",
        ]
        if thresholds:
            doc_lines.extend(
                [
                    "## Thresholds",
                    *[line if line.startswith("- ") else f"- {line}" for line in thresholds if line],
                    "",
                ]
            )
        if rollup_rules:
            doc_lines.extend(
                [
                    "## Rollup Rules",
                    *[line if line.startswith("- ") else f"- {line}" for line in rollup_rules if line],
                    "",
                ]
            )
        return "\n".join(doc_lines)

    def _upsert_markdown_section(
        self,
        path: Path,
        heading: str,
        lines: list[str],
    ) -> str:
        section_body = "\n".join(lines).rstrip()
        section = f"{heading}\n\n{section_body}\n"

        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            content = ""

        pattern = re.compile(
            rf"^{re.escape(heading)}\n.*?(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        if pattern.search(content):
            updated = pattern.sub(section + "\n", content, count=1).rstrip() + "\n"
        else:
            updated = (content.rstrip() + "\n\n" + section).lstrip("\n")
        self._write_text(path, updated)
        return str(path)

    def _daily_template(self, date_str: str) -> str:
        now_iso = self._now_iso()
        return "\n".join(
            [
                "---",
                f"date: {date_str}",
                f"updated_at: {now_iso}",
                "---",
                "",
                f"# {date_str}",
                "",
                "## Health Files",
                "| File | Type | Summary | Path |",
                "|------|------|---------|------|",
                "",
            ]
        )

    def _update_frontmatter(self, content: str, date_str: str) -> str:
        body = _strip_frontmatter(content)
        now_iso = self._now_iso()
        frontmatter = "\n".join(
            [
                "---",
                f"date: {date_str}",
                f"updated_at: {now_iso}",
                "---",
                "",
            ]
        )
        if not body.startswith(f"# {date_str}"):
            body = f"# {date_str}\n\n{body.lstrip()}"
        return frontmatter + body.lstrip()

    def _ensure_daily_file(self, date_str: str) -> Path:
        path = self.daily_dir / f"{date_str}.md"
        if not path.exists():
            self._write_text(path, self._daily_template(date_str))
        else:
            content = path.read_text(encoding="utf-8")
            if "## Health Files" not in content:
                content = content.rstrip() + "\n\n## Health Files\n| File | Type | Summary | Path |\n|------|------|---------|------|\n"
            self._write_text(path, self._update_frontmatter(content, date_str))
        return path

    def _build_section(
        self, title: str, skill_name: str, lines: list[str], time_label: str | None = None
    ) -> str:
        now_label = time_label or self._now().strftime("%H:%M")
        formatted = [line if line.startswith(("- ", "| ")) else f"- {line}" for line in lines if line]
        return f"## {title} [{skill_name} · {now_label}]\n" + "\n".join(formatted) + "\n"

    def _upsert_daily_section(
        self,
        date_str: str,
        title: str,
        skill_name: str,
        lines: list[str],
        time_label: str | None = None,
    ) -> Path:
        path = self._ensure_daily_file(date_str)
        content = path.read_text(encoding="utf-8")
        section = self._build_section(title, skill_name, lines, time_label=time_label)
        pattern = re.compile(
            rf"^## {re.escape(title)} \[{re.escape(skill_name)} · [^\]]+\]\n.*?(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )

        if pattern.search(content):
            updated = pattern.sub(section + "\n", content, count=1)
        elif "## Health Files" in content:
            updated = content.replace("## Health Files", section + "\n## Health Files", 1)
        else:
            updated = content.rstrip() + "\n\n" + section

        self._write_text(path, self._update_frontmatter(updated, date_str))
        return path

    def _read_history_rows(self, path: Path) -> list[list[str]]:
        if not path.exists():
            return []

        rows = []
        in_history = False
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "## History":
                in_history = True
                continue
            if in_history and line.startswith("## "):
                break
            if in_history and line.startswith("|"):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if not cells or cells[0] == "Date" or set(cells[0]) == {"-"}:
                    continue
                rows.append(cells)
        return rows

    def _history_table(self, headers: list[str], rows: list[list[str]]) -> str:
        header = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        body = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
        return "\n".join([header, separator] + body)

    def _read_table_section(self, path: Path, heading: str) -> tuple[list[str], list[list[str]]]:
        if not path.exists():
            return [], []

        in_section = False
        headers: list[str] = []
        rows: list[list[str]] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == heading:
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if not in_section or not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not headers:
                headers = cells
                continue
            if not cells or set(cells[0]) == {"-"}:
                continue
            rows.append(cells)
        return headers, rows

    def _upsert_item_file(
        self,
        item_slug: str,
        title: str,
        unit: str,
        recent_lines: list[str],
        headers: list[str],
        row: list[str],
        row_date: str,
        row_identity: str | None = None,
        identity_columns: int = 1,
        retention_days: int = 90,
    ) -> Path:
        path = self.items_dir / f"{item_slug}.md"
        cutoff = self._now() - timedelta(days=retention_days)
        identity_value = row_identity or row_date

        existing_rows = []
        for existing in self._read_history_rows(path):
            if not existing:
                continue
            date_value = _parse_date(existing[0])
            if date_value and date_value < cutoff:
                continue
            existing_identity = "|".join(existing[:identity_columns]).strip()
            if existing_identity == identity_value:
                continue
            existing_rows.append(existing)

        rows = [row] + existing_rows
        content = "\n".join(
            [
                self._render_item_document(
                    item_slug=item_slug,
                    title=title,
                    unit=unit,
                    recent_lines=recent_lines,
                    headers=headers,
                    rows=rows,
                )
            ]
        )
        self._write_text(path, content)
        return path

    def _read_behavior_plan_rows(self) -> list[dict[str, str]]:
        headers, rows = self._read_table_section(self.behavior_plans_path, "## History")
        if not headers:
            return []
        result = []
        for row in rows:
            payload = {}
            for index, header in enumerate(headers):
                payload[header] = row[index] if index < len(row) else ""
            result.append(payload)
        return result

    def upsert_behavior_plan(
        self,
        plan_id: str,
        scenario: str,
        title: str,
        cadence: str,
        due_at: str,
        status: str = "active",
        topic: str = "general",
        risk_policy: str = "normal",
        consequence: str = "",
        next_step: str = "",
        notes: str = "",
    ) -> str:
        headers = [
            "Date",
            "Plan ID",
            "Scenario",
            "Title",
            "Cadence",
            "Due At",
            "Status",
            "Topic",
            "Risk Policy",
            "If Ignored",
            "Next Step",
            "Notes",
        ]
        rows = []
        current_date = due_at[:10] if len(due_at) >= 10 else self._now().date().isoformat()
        new_row = [
            current_date,
            plan_id,
            scenario,
            title,
            cadence,
            due_at,
            status,
            topic,
            risk_policy,
            consequence,
            next_step,
            notes,
        ]
        seen = False
        for existing in self._read_behavior_plan_rows():
            if existing.get("Plan ID") == plan_id:
                rows.append(new_row)
                seen = True
                continue
            rows.append([existing.get(header, "") for header in headers])
        if not seen:
            rows.append(new_row)

        def sort_key(row: list[str]) -> tuple[str, str]:
            status_rank = "0" if row[6] in {"active", "in_progress"} else "1"
            return (status_rank, row[5])

        rows = sorted(rows, key=sort_key)
        active_rows = [row for row in rows if row[6] in {"active", "in_progress", "blocked"}]
        recent_lines = [
            f"Active plans: {len(active_rows)}",
            (
                f"Next due plan: {active_rows[0][5]} | {active_rows[0][3]} [{active_rows[0][6]}]"
                if active_rows
                else "Next due plan: pending"
            ),
            "Focus topics: "
            + (", ".join(sorted({row[7] for row in active_rows if row[7]})) if active_rows else "pending"),
            "High-risk-only plans: "
            + (", ".join(row[3] for row in active_rows if row[8] == "high-risk-only") or "none"),
        ]
        content = self._render_item_document(
            item_slug="behavior-plans",
            title="Behavior Plan Records",
            unit="active plan",
            recent_lines=recent_lines,
            headers=headers,
            rows=rows,
            thresholds=[
                "Heartbeat uses minute-level due time when `Due At` includes HH:MM.",
                "Plans marked `high-risk-only` only escalate proactively on high-risk signals.",
            ],
            rollup_rules=[
                "Weekly digest highlights overdue or repeatedly deferred plans.",
                "Distillation writes persistent execution barriers back to MEMORY.md.",
            ],
        )
        self._write_text(self.behavior_plans_path, content)
        return str(self.behavior_plans_path)

    def list_behavior_plans(self, statuses: set[str] | None = None) -> list[dict[str, str]]:
        rows = self._read_behavior_plan_rows()
        if not statuses:
            return rows
        return [row for row in rows if row.get("Status") in statuses]

    def record_execution_barrier(
        self,
        scenario: str,
        barrier: str,
        impact: str,
        pattern: str,
        next_step: str,
        source_refs: list[str] | None = None,
        recorded_at: str | None = None,
    ) -> str:
        recorded_at = recorded_at or self._now_iso()
        headers = [
            "Date",
            "Scenario",
            "Barrier",
            "Impact",
            "Pattern",
            "Next Step",
            "Source Refs",
        ]
        existing_headers, existing_rows = self._read_table_section(self.execution_barriers_path, "## History")
        rows = existing_rows if existing_headers else []
        row = [
            recorded_at[:10],
            scenario,
            barrier,
            impact,
            pattern,
            next_step,
            "; ".join(source_refs or []),
        ]
        row_identity = "|".join(row[:3])
        deduped = [row]
        for existing in rows:
            existing_identity = "|".join(existing[:3]).strip()
            if existing_identity == row_identity:
                continue
            deduped.append(existing)
        recent_lines = [
            f"Latest barrier: {barrier} ({recorded_at[:10]}, {scenario})",
            f"Impact: {impact}",
            f"Pattern: {pattern}",
            f"Next step: {next_step}",
        ]
        content = self._render_item_document(
            item_slug="execution-barriers",
            title="Execution Barrier Records",
            unit="barrier",
            recent_lines=recent_lines,
            headers=headers,
            rows=deduped[:60],
            thresholds=[
                "Repeated barrier patterns should escalate into long-term coaching focus.",
                "High-risk barriers can trigger stronger follow-up cadence.",
            ],
            rollup_rules=[
                "Weekly digest summarizes recurring barriers and skipped actions.",
                "Distillation writes stable barrier patterns back to MEMORY.md.",
            ],
        )
        self._write_text(self.execution_barriers_path, content)
        return str(self.execution_barriers_path)

    def latest_execution_barriers(self, limit: int = 5) -> list[dict[str, str]]:
        headers, rows = self._read_table_section(self.execution_barriers_path, "## History")
        if not headers:
            return []
        result = []
        for row in rows[:limit]:
            result.append(
                {
                    header: row[index] if index < len(row) else ""
                    for index, header in enumerate(headers)
                }
            )
        return result

    def append_write_audit(
        self,
        scenario: str,
        target: str,
        reason: str,
        source_refs: list[str] | None = None,
        recorded_at: str | None = None,
    ) -> str:
        recorded_at = recorded_at or self._now_iso()
        headers, rows = self._read_table_section(self.write_audit_path, "## Entries")
        if not headers:
            headers = ["Timestamp", "Scenario", "Target", "Reason", "Sources"]
            rows = []
        rows = [[recorded_at, scenario, target, reason, "; ".join(source_refs or [])]] + rows[:199]
        content = "\n".join(
            [
                f"# Write Audit -- {self._now().date().isoformat()}",
                "",
                "## Entries",
                self._history_table(headers, rows),
                "",
            ]
        )
        self._write_text(self.write_audit_path, content)
        return str(self.write_audit_path)

    def register_health_file(
        self,
        file_type: str,
        summary: str,
        path: str | Path,
        date_str: str | None = None,
        filename: str | None = None,
    ) -> str:
        target_date = date_str or self._now().date().isoformat()
        daily_path = self._ensure_daily_file(target_date)
        file_path = Path(path)
        file_label = filename or file_path.name
        content = daily_path.read_text(encoding="utf-8")

        headers, rows = self._read_table_section(daily_path, "## Health Files")
        if not headers:
            headers = ["File", "Type", "Summary", "Path"]

        new_rows = [[file_label, file_type, summary, str(file_path)]]
        for row in rows:
            if len(row) < 4:
                continue
            if row[3] == str(file_path) or row[0] == file_label:
                continue
            new_rows.append(row)

        table = self._history_table(headers, new_rows)
        section = f"## Health Files\n{table}\n"
        pattern = re.compile(
            r"^## Health Files\n.*?(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        if pattern.search(content):
            updated = pattern.sub(section + "\n", content, count=1)
        else:
            updated = content.rstrip() + "\n\n" + section
        self._write_text(daily_path, self._update_frontmatter(updated, target_date))
        return str(daily_path)

    def update_daily_snapshot(self) -> str:
        today = self._now().date().isoformat()
        return str(self._ensure_daily_file(today))

    def update_caffeine(self, level: float, intake_list: list[dict], safe: str) -> str:
        now = self._now()
        date_str = now.date().isoformat()
        total_mg = sum(float(item.get("mg", 0) or 0) for item in intake_list)
        intake_summary = ", ".join(
            f"{item.get('drink', '?')} {int(item.get('mg', 0) or 0)}mg ({item.get('time', '?')})"
            for item in intake_list
        ) or "No intake recorded"

        self._upsert_daily_section(
            date_str,
            "Caffeine",
            "caffeine-tracker",
            [
                f"Residual: ~{round(level)}mg",
                f"Safe to sleep: {safe}",
                f"Today's intake: {intake_summary}",
                f"Total: {round(total_mg)}mg / 400mg",
            ],
        )

        trend_label = "Low intake" if total_mg < 100 else ("Moderate intake" if total_mg < 300 else "High intake")
        drinks = ", ".join(item.get("drink", "?") for item in intake_list) or "-"
        self._upsert_item_file(
            item_slug="caffeine",
            title="Caffeine Records",
            unit="mg",
            recent_lines=[
                f"Latest: {round(total_mg)}mg total, ~{round(level)}mg residual ({date_str} {now.strftime('%H:%M')})",
                f"Safe sleep time: {safe}",
                f"Trend: {trend_label}",
            ],
            headers=["Date", "Total Intake (mg)", "Peak Residual (mg)", "Safe Sleep Time", "Drinks", "Notes"],
            row=[date_str, str(round(total_mg)), str(round(level)), safe, drinks, ""],
            row_date=date_str,
        )
        return str(self.daily_dir / f"{date_str}.md")

    def update_sleep(
        self, last_night: dict | None, seven_day: dict | None, correlations: dict | None
    ) -> str | None:
        if not last_night:
            return None

        date_str = last_night.get("date") or datetime.now().date().isoformat()
        score = last_night.get("score", "?")
        duration = _format_duration(last_night.get("total_min"))
        efficiency = last_night.get("efficiency_pct", "?")
        bedtime = last_night.get("bedtime", "?")
        wake_time = last_night.get("wake_time", "?")
        awake_min = last_night.get("awake_min")

        stage_lines = []
        total_min = last_night.get("total_min") or 0
        if total_min:
            stage_parts = []
            for key, label in (("light_min", "Light"), ("deep_min", "Deep"), ("rem_min", "REM"), ("awake_min", "Awake")):
                value = last_night.get(key)
                if value is None:
                    continue
                pct = round((float(value) / float(total_min)) * 100, 1)
                stage_parts.append(f"{label} {pct}%")
            if stage_parts:
                stage_lines.append("Stages: " + ", ".join(stage_parts))

        daily_lines = [
            f"Score: {score}/100",
            f"Duration: {duration} ({bedtime}-{wake_time})",
            f"Efficiency: {efficiency}%",
        ]
        if awake_min is not None:
            daily_lines.append(f"Awake time: {awake_min}min")
        daily_lines.extend(stage_lines)
        if correlations:
            for label, summary in correlations.items():
                daily_lines.append(f"{label}: {summary}")

        self._upsert_daily_section(date_str, "Sleep", "sleep-analyzer", daily_lines)

        recent_lines = [
            f"Latest: Score {score}, {duration}, Efficiency {efficiency}% ({date_str})",
        ]
        if seven_day:
            recent_lines.append(
                f"7-day average score: {seven_day.get('avg_score', '?')}"
            )
            recent_lines.append(
                f"7-day average duration: {_format_duration(seven_day.get('avg_total_min'))}"
            )
            trend_map = {
                "rising": "Improving",
                "falling": "Declining",
                "stable": "Stable",
            }
            recent_lines.append(
                f"Trend: {trend_map.get(seven_day.get('trend_direction'), seven_day.get('trend_direction', 'Stable'))}"
            )

        note_parts = []
        if correlations:
            note_parts.extend(correlations.values())

        self._upsert_item_file(
            item_slug="sleep",
            title="Sleep Records",
            unit="score (0-100)",
            recent_lines=recent_lines,
            headers=["Date", "Score", "Duration", "Efficiency", "Latency", "Bedtime", "Waketime", "Notes"],
            row=[
                date_str,
                str(score),
                duration,
                f"{efficiency}%",
                "",
                bedtime,
                wake_time,
                " | ".join(note_parts),
            ],
            row_date=date_str,
        )
        return str(self.daily_dir / f"{date_str}.md")

    def update_supplements(
        self,
        active_regimen: list[dict],
        today_adherence: dict,
        warnings: list[str] | None = None,
    ) -> str:
        date_str = self._now().date().isoformat()
        warnings = warnings or []
        regimen_summary = "; ".join(
            f"{item.get('name', '?')} {item.get('dose', '?')} ({item.get('timing', '?')})"
            for item in active_regimen
        ) or "No active supplements"

        daily_lines = [
            f"Active regimen: {len(active_regimen)} items",
            (
                f"Today's adherence: {today_adherence.get('taken', 0)}/"
                f"{today_adherence.get('expected', 0)} "
                f"({round(float(today_adherence.get('rate_pct', 0)), 1)}%)"
            ),
            f"Items: {regimen_summary}",
        ]
        for warning in warnings:
            daily_lines.append(f"Warning: {warning}")

        self._upsert_daily_section(
            date_str, "Supplements", "supplement-manager", daily_lines
        )

        self._upsert_item_file(
            item_slug="supplements",
            title="Supplement Records",
            unit="daily regimen",
            recent_lines=[
                f"Latest: {len(active_regimen)} active supplements ({date_str})",
                (
                    f"Today's adherence: {today_adherence.get('taken', 0)}/"
                    f"{today_adherence.get('expected', 0)} "
                    f"({round(float(today_adherence.get('rate_pct', 0)), 1)}%)"
                ),
                f"Warnings: {'; '.join(warnings) if warnings else 'None'}",
            ],
            headers=["Date", "Active Items", "Taken", "Expected", "Adherence", "Warnings", "Notes"],
            row=[
                date_str,
                str(len(active_regimen)),
                str(today_adherence.get("taken", 0)),
                str(today_adherence.get("expected", 0)),
                f"{round(float(today_adherence.get('rate_pct', 0)), 1)}%",
                "; ".join(warnings),
                regimen_summary,
            ],
            row_date=date_str,
        )
        return str(self.daily_dir / f"{date_str}.md")

    def update_weekly_digest(self, digest_content: str) -> str:
        self._write_text(self.weekly_digest_path, digest_content)

        match = re.search(
            r"#\s*健康周报\s*--\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})",
            digest_content,
        )
        if match:
            week_start = datetime.strptime(match.group(1), "%Y-%m-%d")
            iso_year, iso_week, _ = week_start.isocalendar()
            weekly_path = self.weekly_dir / f"{iso_year}-W{iso_week:02d}.md"
            self._write_text(weekly_path, digest_content)

        return str(self.weekly_digest_path)

    def update_monthly_digest(self, digest_content: str) -> str:
        self._write_text(self.monthly_digest_path, digest_content)

        match = re.search(
            r"#\s*健康月报\s*--\s*(\d{4}-\d{2})",
            digest_content,
        )
        if match:
            monthly_path = self.monthly_dir / f"{match.group(1)}.md"
            self._write_text(monthly_path, digest_content)

        return str(self.monthly_digest_path)

    def update_long_term_memory(
        self,
        summary_lines: list[str],
        task_lines: list[str] | None = None,
        risk_lines: list[str] | None = None,
        source_lines: list[str] | None = None,
    ) -> str | None:
        if not self.memory_doc_path:
            return None

        if not self.memory_doc_path.exists():
            self._write_text(
                self.memory_doc_path,
                "\n".join(
                    [
                        "# VitaClaw Long-Term Memory",
                        "",
                        "## 最近健康运营摘要",
                        "- 待生成",
                        "",
                        "## 当前重点任务",
                        "- 待生成",
                    ]
                ),
            )

        summary_block = [
            f"- Last distilled: {self._now().date().isoformat()}",
            *summary_lines,
        ]
        self._upsert_markdown_section(
            self.memory_doc_path,
            "## 最近健康运营摘要",
            summary_block,
        )
        if task_lines:
            self._upsert_markdown_section(
                self.memory_doc_path,
                "## 当前重点任务",
                task_lines,
            )
        if risk_lines:
            self._upsert_markdown_section(
                self.memory_doc_path,
                "## 风险与待跟进",
                risk_lines,
            )
        if source_lines:
            self._upsert_markdown_section(
                self.memory_doc_path,
                "## 最近来源",
                source_lines,
            )
        return str(self.memory_doc_path)

    def update_appointments(
        self,
        visit_date: str,
        department_doctor: str,
        purpose: str,
        status: str = "completed",
        owner: str = "self",
        notes: str = "",
        latest_appointment: str | None = None,
        next_follow_up: str | None = None,
        next_follow_up_details: str | None = None,
        preparation_status: str | None = None,
    ) -> str:
        latest_value = latest_appointment or f"{visit_date} {purpose}".strip()
        next_value = next_follow_up or "pending"
        next_details_value = next_follow_up_details or "pending"
        preparation_value = preparation_status or (
            "待确认下次复查安排" if next_follow_up else "本次随访已记录"
        )

        self._upsert_item_file(
            item_slug="appointments",
            title="Appointment Records",
            unit="planned events",
            recent_lines=[
                f"Latest appointment: {latest_value}",
                f"Next follow-up: {next_value}",
                f"Next follow-up details: {next_details_value}",
                f"Preparation status: {preparation_value}",
            ],
            headers=["Date", "Department / Doctor", "Purpose", "Status", "Owner", "Notes"],
            row=[visit_date, department_doctor, purpose, status, owner, notes],
            row_date=visit_date,
            row_identity="|".join([visit_date, department_doctor, purpose]),
            identity_columns=3,
            retention_days=365,
        )
        return str(self.items_dir / "appointments.md")

    def update_annual_checkup(
        self,
        report_date: str,
        source_name: str | None = None,
        notes: str | None = None,
        next_checkup: str | None = None,
        preparation_status: str | None = None,
        reminder_window_days: int = 30,
        status: str = "completed",
    ) -> str:
        next_due = next_checkup or _plus_one_year(report_date) or "pending"
        self._upsert_item_file(
            item_slug="annual-checkup",
            title="Annual Checkup Records",
            unit="preventive care",
            recent_lines=[
                f"Latest annual checkup: {report_date} ({source_name or 'Annual checkup report'})",
                f"Next annual checkup: {next_due}",
                f"Reminder window days: {reminder_window_days}",
                f"Preparation status: {preparation_status or '本年度体检已完成'}",
                f"Notes: {notes or 'pending'}",
            ],
            headers=["Date", "Source", "Status", "Next Annual Checkup", "Notes"],
            row=[
                report_date,
                source_name or "Annual checkup report",
                status,
                next_due,
                notes or "",
            ],
            row_date=report_date,
            row_identity="|".join([report_date, source_name or "Annual checkup report"]),
            identity_columns=2,
            retention_days=730,
        )
        return str(self.items_dir / "annual-checkup.md")

    def update_medications(
        self,
        date_str: str,
        medications: list[dict],
        adherence: str | None = None,
        next_refill: str | None = None,
        stock_coverage_days: int | None = None,
        risks: str | None = None,
    ) -> str:
        regimen_summary = "; ".join(
            f"{item.get('name', '?')} {item.get('dose', '?')} {item.get('frequency', '').strip()}".strip()
            for item in medications
        ) or "pending"
        recent_lines = [
            f"Latest: {regimen_summary}",
            f"Adherence: {adherence or 'pending'}",
            f"Next refill: {next_refill or 'pending'}",
            f"Stock coverage days: {stock_coverage_days if stock_coverage_days is not None else 'pending'}",
            f"Risks: {risks or 'pending'}",
        ]
        headers = ["Date", "Medication", "Dose", "Frequency", "Status", "Notes"]
        rows: list[list[str]] = []
        for item in medications:
            rows.append(
                [
                    date_str,
                    item.get("name", ""),
                    item.get("dose", ""),
                    item.get("frequency", ""),
                    item.get("status", "active"),
                    item.get("notes", ""),
                ]
            )
        existing_rows = self._read_history_rows(self.items_dir / "medications.md")
        for existing in existing_rows:
            if existing and existing[0] != date_str:
                rows.append(existing)
        content = self._render_item_document(
            item_slug="medications",
            title="Medication Records",
            unit="active regimen",
            recent_lines=recent_lines,
            headers=headers,
            rows=rows,
            thresholds=[
                "Refill reminder lead time: 7 days",
                "Escalate when stock coverage days drop below 3 or repeated misses occur",
            ],
            rollup_rules=[
                "Weekly digest summarizes adherence and missed-dose patterns.",
                "Monthly digest highlights refill debt and regimen changes.",
            ],
        )
        self._write_text(self.items_dir / "medications.md", content)
        return str(self.items_dir / "medications.md")

    def last_memory_distilled_at(self) -> datetime | None:
        if not self.memory_doc_path or not self.memory_doc_path.exists():
            return None

        match = re.search(
            r"^- Last distilled:\s*(\d{4}-\d{2}-\d{2})",
            self.memory_doc_path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if not match:
            return None
        return _parse_date(match.group(1))

    def update_heartbeat_report(self, report_content: str, date_str: str | None = None) -> str:
        target_date = date_str or self._now().date().isoformat()
        report_path = self.heartbeat_dir / f"{target_date}.md"
        self._write_text(report_path, report_content)
        return str(report_path)

    def update_heartbeat_task_board(self, board_content: str) -> str:
        self._write_text(self.heartbeat_task_board_path, board_content)
        return str(self.heartbeat_task_board_path)

    def write_team_task(
        self,
        task_id: str,
        role: str,
        scenario: str,
        priority: str,
        status: str,
        due_at: str,
        execution_mode: str,
        privacy_tier: str,
        source_refs: list[str] | None = None,
        summary_lines: list[str] | None = None,
        next_steps: list[str] | None = None,
        created_at: str | None = None,
    ) -> str:
        created_at = created_at or self._now_iso()
        path = self.team_tasks_dir / f"{task_id}.md"
        lines = [
            "---",
            f"task_id: {task_id}",
            f"created_at: {created_at}",
            f"role: {role}",
            f"scenario: {scenario}",
            f"priority: {priority}",
            f"status: {status}",
            f"due_at: {due_at}",
            f"execution_mode: {execution_mode}",
            f"privacy_tier: {privacy_tier}",
            "source_refs:",
        ]
        for ref in source_refs or []:
            lines.append(f"  - {ref}")
        lines.extend(
            [
                "---",
                "",
                f"# Team Task -- {task_id}",
                "",
                "## Summary",
            ]
        )
        for line in summary_lines or ["- pending"]:
            lines.append(line if line.startswith("- ") else f"- {line}")
        lines.extend(["", "## Next Steps"])
        for line in next_steps or ["- pending"]:
            lines.append(line if line.startswith("- ") else f"- {line}")
        self._write_text(path, "\n".join(lines))
        return str(path)

    def write_role_brief(
        self,
        task_id: str,
        role: str,
        scenario: str,
        sections: dict[str, list[str]],
        sources: list[str] | None = None,
        evidence: list[str] | None = None,
        recommended_writebacks: list[str] | None = None,
        follow_up: list[str] | None = None,
        disclaimer: str | None = None,
    ) -> str:
        path = self.team_briefs_dir / f"{task_id}-{role}.md"
        lines = [
            "---",
            f"task_id: {task_id}",
            f"role: {role}",
            f"scenario: {scenario}",
            f"generated_at: {self._now_iso()}",
            "---",
            "",
            f"# Role Brief -- {role}",
            "",
        ]
        section_order = [
            "## 记录",
            "## 解读",
            "## 趋势",
            "## 风险",
            "## 建议",
            "## 必须就医",
        ]
        for heading in section_order:
            lines.extend([heading, ""])
            values = sections.get(heading) or ["- 暂无。"]
            for value in values:
                lines.append(value if value.startswith(("- ", "| ")) else f"- {value}")
            lines.append("")
        lines.extend(["## Sources", ""])
        for item in sources or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        lines.extend(["", "## Evidence", ""])
        for item in evidence or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        lines.extend(["", "## Recommended Writebacks", ""])
        for item in recommended_writebacks or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        lines.extend(["", "## Follow-up", ""])
        for item in follow_up or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        if disclaimer:
            lines.extend(["", "## Disclaimer", "", f"- {disclaimer}"])
        self._write_text(path, "\n".join(lines))
        return str(path)

    def update_team_board(
        self,
        open_tasks: list[str],
        active_roles: list[str],
        latest_outputs: list[str],
        generated_at: str | None = None,
    ) -> str:
        generated_at = generated_at or self._now().date().isoformat()
        lines = [f"# Team Board -- {generated_at}", "", "## Open Tasks"]
        for item in open_tasks or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        lines.extend(["", "## Active Roles"])
        for item in active_roles or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        lines.extend(["", "## Latest Outputs"])
        for item in latest_outputs or ["- none"]:
            lines.append(item if item.startswith("- ") else f"- {item}")
        self._write_text(self.team_board_path, "\n".join(lines))
        return str(self.team_board_path)

    def append_dispatch_log(
        self,
        task_id: str,
        scenario: str,
        role: str,
        event: str,
        target: str,
        reason: str,
        source_refs: list[str] | None = None,
        timestamp: str | None = None,
    ) -> str:
        payload = {
            "timestamp": timestamp or self._now_iso(),
            "task_id": task_id,
            "scenario": scenario,
            "role": role,
            "event": event,
            "target": target,
            "reason": reason,
            "source_refs": source_refs or [],
        }
        with self.dispatch_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return str(self.dispatch_log_path)

    def write_health_file(
        self,
        filename: str,
        title: str,
        sections: list[tuple[str, list[str]]],
        date_str: str | None = None,
        file_type: str | None = None,
        summary: str | None = None,
    ) -> str:
        path = self.files_dir / filename
        lines = [title, ""]
        for heading, section_lines in sections:
            lines.append(heading)
            lines.append("")
            lines.extend(section_lines or ["- pending"])
            lines.append("")
        self._write_text(path, "\n".join(lines).rstrip())
        if file_type and summary:
            self.register_health_file(
                file_type=file_type,
                summary=summary,
                path=path,
                date_str=date_str,
            )
        return str(path)

    def _bp_trend_label(self, records: list[dict]) -> str:
        if len(records) < 2:
            return "Insufficient data"

        sys_values = [float(record.get("data", {}).get("sys", 0) or 0) for record in records]
        dia_values = [float(record.get("data", {}).get("dia", 0) or 0) for record in records]
        if not sys_values or not dia_values:
            return "Insufficient data"

        sys_delta = sys_values[-1] - sys_values[0]
        dia_delta = dia_values[-1] - dia_values[0]
        if sys_delta <= -5 or dia_delta <= -3:
            return "Improving"
        if sys_delta >= 5 or dia_delta >= 3:
            return "Rising"
        return "Stable"

    def update_blood_pressure(
        self,
        latest_record: dict,
        day_records: list[dict],
        window_records: list[dict] | None = None,
    ) -> str | None:
        if not latest_record:
            return None

        timestamp = latest_record.get("timestamp", "")
        date_str = timestamp[:10]
        time_label = timestamp[11:16] if len(timestamp) >= 16 else None
        day_records = sorted(day_records, key=lambda item: item.get("timestamp", ""))
        window_records = sorted(window_records or day_records, key=lambda item: item.get("timestamp", ""))

        daily_lines = []
        for record in day_records:
            record_timestamp = record.get("timestamp", "")
            entry_time = record_timestamp[11:16] if len(record_timestamp) >= 16 else "??:??"
            data = record.get("data", {})
            line = f"{entry_time}: {data.get('sys', '?')}/{data.get('dia', '?')} mmHg"
            if data.get("hr") is not None:
                line += f", pulse {data.get('hr')}"
            if data.get("context"):
                line += f" [{data.get('context')}]"
            if record.get("note"):
                line += f" -- {record.get('note')}"
            daily_lines.append(line)

        if day_records:
            sys_values = [float(record.get("data", {}).get("sys", 0) or 0) for record in day_records]
            dia_values = [float(record.get("data", {}).get("dia", 0) or 0) for record in day_records]
            daily_lines.append(
                f"Daily average: {round(sum(sys_values) / len(sys_values), 1)}/{round(sum(dia_values) / len(dia_values), 1)} mmHg"
            )

        self._upsert_daily_section(
            date_str,
            "Blood Pressure",
            "blood-pressure-tracker",
            daily_lines,
            time_label=time_label,
        )

        latest_data = latest_record.get("data", {})
        latest_context = latest_data.get("context") or "-"
        sys_values = [float(record.get("data", {}).get("sys", 0) or 0) for record in window_records]
        dia_values = [float(record.get("data", {}).get("dia", 0) or 0) for record in window_records]
        avg_sys = round(sum(sys_values) / len(sys_values), 1) if sys_values else None
        avg_dia = round(sum(dia_values) / len(dia_values), 1) if dia_values else None

        recent_lines = [
            (
                f"Latest: {latest_data.get('sys', '?')}/{latest_data.get('dia', '?')} mmHg "
                f"({date_str} {time_label or '??:??'}, {latest_context})"
            ),
        ]
        if avg_sys is not None and avg_dia is not None:
            recent_lines.append(
                f"7-day average: {avg_sys}/{avg_dia} mmHg across {len(window_records)} readings"
            )
        recent_lines.append(f"Trend: {self._bp_trend_label(window_records)}")
        if latest_record.get("note"):
            recent_lines.append(f"Latest category: {latest_record.get('note')}")

        note_parts = [latest_record.get("note", "")]
        if latest_data.get("arm"):
            note_parts.append(f"arm={latest_data.get('arm')}")
        if latest_data.get("position"):
            note_parts.append(f"position={latest_data.get('position')}")

        self._upsert_item_file(
            item_slug="blood-pressure",
            title="Blood Pressure Records",
            unit="mmHg",
            recent_lines=recent_lines,
            headers=["Date", "Time", "Systolic", "Diastolic", "Pulse", "Context", "Notes"],
            row=[
                date_str,
                time_label or "",
                str(latest_data.get("sys", "")),
                str(latest_data.get("dia", "")),
                str(latest_data.get("hr", "")) if latest_data.get("hr") is not None else "",
                latest_context,
                "; ".join(part for part in note_parts if part),
            ],
            row_date=date_str,
            row_identity=f"{date_str}|{time_label or ''}",
            identity_columns=2,
        )
        return str(self.daily_dir / f"{date_str}.md")

    def _glucose_slot(self, record: dict) -> str | None:
        data = record.get("data", {})
        context = str(data.get("context", "") or "").lower()
        kind = str(data.get("kind", "") or "").lower()
        combined = " ".join(part for part in (kind, context) if part)

        if "hba1c" in combined or "糖化" in combined:
            return "hba1c"
        if "fast" in combined or "空腹" in combined:
            return "fasting"
        if "dinner" in combined or "晚餐" in combined or "post_dinner" in combined:
            return "post_dinner_2h"
        if "lunch" in combined or "午餐" in combined or "post_lunch" in combined:
            return "post_lunch_2h"
        if "breakfast" in combined or "早餐" in combined or "post_breakfast" in combined:
            return "post_breakfast_2h"
        if "post" in combined or "餐后" in combined:
            return "postprandial"
        return None

    def update_blood_sugar(
        self,
        day_records: list[dict],
        window_records: list[dict] | None = None,
        measurement_date: str | None = None,
    ) -> str | None:
        day_records = sorted(day_records, key=lambda item: item.get("timestamp", ""))
        window_records = sorted(window_records or day_records, key=lambda item: item.get("timestamp", ""))
        if not day_records and not window_records:
            return None

        date_str = measurement_date or (day_records[-1].get("timestamp", "")[:10] if day_records else self._now().date().isoformat())
        latest_slot_records: dict[str, dict] = {}
        for record in day_records:
            slot = self._glucose_slot(record)
            if slot:
                latest_slot_records[slot] = record

        def record_value(record: dict | None) -> float | None:
            if not record:
                return None
            return _safe_float(record.get("data", {}).get("value"))

        fasting_value = record_value(latest_slot_records.get("fasting"))
        lunch_value = record_value(latest_slot_records.get("post_lunch_2h"))
        dinner_value = record_value(latest_slot_records.get("post_dinner_2h"))
        hba1c_value = record_value(latest_slot_records.get("hba1c"))

        daily_values = [value for value in (fasting_value, lunch_value, dinner_value) if value is not None]
        daily_lines = []
        if fasting_value is not None:
            daily_lines.append(f"Fasting: {fasting_value} mmol/L ({self._value_status(fasting_value, low=3.9, high=7.0)})")
        if lunch_value is not None:
            daily_lines.append(f"2h post-lunch: {lunch_value} mmol/L ({self._value_status(lunch_value, low=3.9, high=10.0)})")
        if dinner_value is not None:
            daily_lines.append(f"2h post-dinner: {dinner_value} mmol/L ({self._value_status(dinner_value, low=3.9, high=10.0)})")
        if daily_values:
            daily_mean = self._mean(daily_values)
            daily_lines.append(f"Daily mean: {daily_mean} mmol/L")
            daily_lines.append(f"Estimated HbA1c: ~{round((daily_mean + 2.59) / 1.59, 1)}%")
        if hba1c_value is not None:
            daily_lines.append(f"HbA1c: {hba1c_value}%")

        self._upsert_daily_section(
            date_str,
            "Blood Sugar",
            "chronic-condition-monitor",
            daily_lines,
            time_label=day_records[-1].get("timestamp", "")[11:16] if day_records else None,
        )

        fasting_values = []
        postprandial_values = []
        all_glucose_values = []
        latest_fasting = None
        latest_postprandial = None
        latest_hba1c = None
        for record in window_records:
            slot = self._glucose_slot(record)
            value = record_value(record)
            if value is None or slot is None:
                continue
            if slot == "hba1c":
                latest_hba1c = record
                continue
            all_glucose_values.append(value)
            if slot == "fasting":
                fasting_values.append(value)
                latest_fasting = record
            else:
                postprandial_values.append(value)
                latest_postprandial = record

        recent_lines = []
        if latest_fasting:
            recent_lines.append(
                f"Latest fasting: {record_value(latest_fasting)} mmol/L ({latest_fasting.get('timestamp', '')[:10]})"
            )
        if latest_postprandial:
            recent_lines.append(
                f"Latest postprandial: {record_value(latest_postprandial)} mmol/L ({latest_postprandial.get('timestamp', '')[:10]})"
            )
        fasting_avg = self._mean(fasting_values)
        postprandial_avg = self._mean(postprandial_values)
        if fasting_avg is not None:
            recent_lines.append(f"30-day fasting average: {fasting_avg} mmol/L")
        if postprandial_avg is not None:
            recent_lines.append(f"30-day postprandial average: {postprandial_avg} mmol/L")
        if all_glucose_values:
            mean_glucose = self._mean(all_glucose_values)
            recent_lines.append(f"Estimated HbA1c (eHbA1c): ~{round((mean_glucose + 2.59) / 1.59, 1)}%")
            tir_count = sum(1 for value in all_glucose_values if 3.9 <= value <= 10.0)
            recent_lines.append(f"TIR (3.9-10.0 mmol/L): {round((tir_count / len(all_glucose_values)) * 100, 1)}%")
        if latest_hba1c:
            recent_lines.append(
                f"Latest HbA1c: {record_value(latest_hba1c)}% ({latest_hba1c.get('timestamp', '')[:10]})"
            )

        notes = []
        for record in day_records:
            note = str(record.get("note", "") or "").strip()
            if note:
                notes.append(note)

        self._upsert_item_file(
            item_slug="blood-sugar",
            title="Blood Sugar Records",
            unit="mmol/L",
            recent_lines=recent_lines,
            headers=["Date", "Fasting", "Post-Lunch 2h", "Post-Dinner 2h", "HbA1c", "Notes"],
            row=[
                date_str,
                f"{fasting_value}" if fasting_value is not None else "",
                f"{lunch_value}" if lunch_value is not None else "",
                f"{dinner_value}" if dinner_value is not None else "",
                f"{hba1c_value}" if hba1c_value is not None else "",
                "; ".join(notes),
            ],
            row_date=date_str,
        )
        return str(self.daily_dir / f"{date_str}.md")

    def update_weight(
        self,
        latest_record: dict,
        window_records: list[dict] | None = None,
        height_cm: float | None = None,
    ) -> str | None:
        if not latest_record:
            return None

        timestamp = latest_record.get("timestamp", "")
        date_str = timestamp[:10]
        time_label = timestamp[11:16] if len(timestamp) >= 16 else None
        latest_weight = _safe_float(latest_record.get("data", {}).get("kg"))
        if latest_weight is None:
            return None

        bmi = None
        if height_cm and height_cm > 0:
            bmi = round(latest_weight / ((height_cm / 100) ** 2), 1)

        self._upsert_daily_section(
            date_str,
            "Weight",
            "chronic-condition-monitor",
            [
                f"Weight: {latest_weight} kg",
                f"BMI: {bmi}" if bmi is not None else "",
                f"Note: {latest_record.get('note')}" if latest_record.get("note") else "",
            ],
            time_label=time_label,
        )

        window_records = sorted(window_records or [latest_record], key=lambda item: item.get("timestamp", ""))
        weights = [_safe_float(record.get("data", {}).get("kg")) for record in window_records]
        weights = [value for value in weights if value is not None]
        recent_lines = [f"Latest: {latest_weight} kg ({date_str})"]
        if weights:
            recent_lines.append(f"30-day trend: {self._trend_from_values(weights, stable_delta=0.3)}")
        if bmi is not None:
            recent_lines.append(f"BMI: {bmi}")

        self._upsert_item_file(
            item_slug="weight",
            title="Weight Records",
            unit="kg",
            recent_lines=recent_lines,
            headers=["Date", "Weight (kg)", "BMI", "Notes"],
            row=[
                date_str,
                f"{latest_weight}",
                f"{bmi}" if bmi is not None else "",
                str(latest_record.get("note", "") or ""),
            ],
            row_date=date_str,
        )
        return str(self.daily_dir / f"{date_str}.md")

    def update_checkup_summary(
        self,
        report_date: str,
        items: list[dict],
        source_name: str | None = None,
    ) -> str:
        abnormal_items = [item for item in items if item.get("status") != "正常"]
        top_abnormal = []
        for item in abnormal_items[:5]:
            value = str(item.get("value", "")).strip()
            unit = str(item.get("unit", "")).strip()
            line = f"{item.get('item', 'Unknown')}: {value}{(' ' + unit) if unit else ''}"
            if item.get("priority_label"):
                line += f" [{item.get('priority_label')}]"
            top_abnormal.append(line)

        lines = [
            f"Source: {source_name or 'Annual checkup report'}",
            f"Items extracted: {len(items)}",
            f"Abnormal findings: {len(abnormal_items)}",
        ]
        if top_abnormal:
            lines.append("Top abnormalities: " + "; ".join(top_abnormal))

        self._upsert_daily_section(
            report_date,
            "Annual Checkup",
            "checkup-report-interpreter",
            lines,
            time_label=self._now().strftime("%H:%M"),
        )
        return str(self.daily_dir / f"{report_date}.md")

    def _extract_recent_status(self, item_path: Path) -> str:
        if not item_path.exists():
            return ""

        lines = item_path.read_text(encoding="utf-8").splitlines()
        start = None
        collected = []
        for index, line in enumerate(lines):
            if line.strip() == "## Recent Status":
                start = index + 1
                continue
            if start is not None and line.startswith("## "):
                break
            if start is not None and line.strip():
                collected.append(line)
        return "\n".join(collected).strip()

    def read_health_context(self) -> str:
        parts = []

        if self.profile_path.exists():
            profile = _strip_frontmatter(self.profile_path.read_text(encoding="utf-8")).strip()
            if profile:
                parts.append(profile)

        recent_daily = sorted(self.daily_dir.glob("*.md"), reverse=True)[:3]
        for daily_path in recent_daily:
            daily = _strip_frontmatter(daily_path.read_text(encoding="utf-8")).strip()
            if daily:
                parts.append(daily)

        for item_name in (
            "blood-pressure",
            "blood-sugar",
            "weight",
            "sleep",
            "caffeine",
            "medications",
            "supplements",
            "heart-rate-hrv",
            "kidney-function",
            "liver-function",
            "blood-lipids",
            "tumor-markers",
            "mental-health-score",
            "appointments",
            "annual-checkup",
            "behavior-plans",
            "execution-barriers",
        ):
            item_path = self.items_dir / f"{item_name}.md"
            recent_status = self._extract_recent_status(item_path)
            if recent_status:
                parts.append(f"## {item_name.title()} Snapshot\n{recent_status}")

        return "\n\n".join(part for part in parts if part).strip()
