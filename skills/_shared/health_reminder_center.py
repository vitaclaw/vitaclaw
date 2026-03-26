#!/usr/bin/env python3
"""Stateful reminder/task management for VitaClaw health heartbeat."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta

from .health_memory import HealthMemoryWriter

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class HealthReminderCenter:
    """Track heartbeat issues as tasks with preferences and follow-up cadence."""

    DEFAULT_PREFERENCES = {
        "primary_channel": "heartbeat-report",
        "push_channel": "pending",
        "tone": "gentle",
        "quiet_hours": "22:00-08:00",
        "working_hours": "09:00-18:00",
        "repeat_hours": {"low": 24, "medium": 12, "high": 4},
        "follow_up_hours": {"low": 36, "medium": 24, "high": 8},
        "focus_closely": [
            "blood-pressure",
            "blood-sugar",
            "medication",
            "appointments",
        ],
        "high_risk_only_topics": ["sleep", "supplements"],
    }

    def __init__(
        self,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.writer = HealthMemoryWriter(
            memory_root=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )
        self.preferences_path = self.writer.heartbeat_preferences_path
        self.task_state_path = self.writer.heartbeat_task_state_path
        self.task_board_path = self.writer.heartbeat_task_board_path

    def _now(self) -> datetime:
        return self._now_fn()

    def _now_iso(self) -> str:
        return self._now().isoformat(timespec="seconds")

    def _normalize_topic(self, value: str | None) -> str:
        if not value:
            return "general"
        normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
        normalized = re.sub(r"-+", "-", normalized)
        return normalized or "general"

    def _parse_int(self, value: str | None, default: int) -> int:
        if not value:
            return default
        match = re.search(r"(-?\d+)", value)
        return int(match.group(1)) if match else default

    def _parse_list(self, value: str | None) -> list[str]:
        if not value:
            return []
        return [self._normalize_topic(item) for item in re.split(r"[，,;/]+", value) if item.strip()]

    def load_preferences(self) -> dict:
        preferences = json.loads(json.dumps(self.DEFAULT_PREFERENCES))
        if not self.preferences_path.exists():
            return preferences

        for raw_line in self.preferences_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line.startswith("- ") or ":" not in line:
                continue
            key, value = line[2:].split(":", 1)
            normalized_key = key.strip().lower()
            value = value.strip()
            if normalized_key == "primary channel":
                preferences["primary_channel"] = value
            elif normalized_key == "push channel":
                preferences["push_channel"] = value
            elif normalized_key == "tone":
                preferences["tone"] = value
            elif normalized_key == "quiet hours":
                preferences["quiet_hours"] = value
            elif normalized_key == "working hours":
                preferences["working_hours"] = value
            elif normalized_key == "low priority repeat hours":
                preferences["repeat_hours"]["low"] = self._parse_int(value, preferences["repeat_hours"]["low"])
            elif normalized_key == "medium priority repeat hours":
                preferences["repeat_hours"]["medium"] = self._parse_int(value, preferences["repeat_hours"]["medium"])
            elif normalized_key == "high priority repeat hours":
                preferences["repeat_hours"]["high"] = self._parse_int(value, preferences["repeat_hours"]["high"])
            elif normalized_key == "low priority follow-up hours":
                preferences["follow_up_hours"]["low"] = self._parse_int(value, preferences["follow_up_hours"]["low"])
            elif normalized_key == "medium priority follow-up hours":
                preferences["follow_up_hours"]["medium"] = self._parse_int(
                    value, preferences["follow_up_hours"]["medium"]
                )
            elif normalized_key == "high priority follow-up hours":
                preferences["follow_up_hours"]["high"] = self._parse_int(value, preferences["follow_up_hours"]["high"])
            elif normalized_key == "focus closely":
                preferences["focus_closely"] = self._parse_list(value)
            elif normalized_key == "high-risk-only topics":
                preferences["high_risk_only_topics"] = self._parse_list(value)
        return preferences

    def _empty_state(self) -> dict:
        return {"updated_at": self._now_iso(), "tasks": []}

    def load_state(self) -> dict:
        if not self.task_state_path.exists():
            return self._empty_state()
        try:
            state = json.loads(self.task_state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return self._empty_state()
        if "tasks" not in state or not isinstance(state["tasks"], list):
            return self._empty_state()
        return state

    def save_state(self, state: dict) -> str:
        state["updated_at"] = self._now_iso()
        self.task_state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return str(self.task_state_path)

    def _task_id(self, dedupe_key: str, topic: str) -> str:
        digest = hashlib.md5(dedupe_key.encode("utf-8")).hexdigest()[:8]
        return f"{self._normalize_topic(topic)}-{digest}"

    def _parse_iso(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _parse_time_window(self, window: str) -> tuple[tuple[int, int], tuple[int, int]] | None:
        match = re.fullmatch(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})", window.strip())
        if not match:
            return None
        start = (int(match.group(1)), int(match.group(2)))
        end = (int(match.group(3)), int(match.group(4)))
        return start, end

    def _in_quiet_hours(self, preferences: dict) -> bool:
        window = self._parse_time_window(preferences.get("quiet_hours", ""))
        if not window:
            return False
        now = self._now()
        start, end = window
        current_minutes = now.hour * 60 + now.minute
        start_minutes = start[0] * 60 + start[1]
        end_minutes = end[0] * 60 + end[1]
        if start_minutes == end_minutes:
            return False
        if start_minutes < end_minutes:
            return start_minutes <= current_minutes < end_minutes
        return current_minutes >= start_minutes or current_minutes < end_minutes

    def _next_quiet_end(self, preferences: dict) -> datetime:
        window = self._parse_time_window(preferences.get("quiet_hours", ""))
        now = self._now()
        if not window:
            return now
        _, end = window
        target = now.replace(hour=end[0], minute=end[1], second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    def _delivery_status(self, task: dict, issue: dict, preferences: dict) -> tuple[str, str | None, str | None]:
        priority = issue.get("priority", "low")
        repeat_hours = preferences["repeat_hours"].get(priority, 24)
        follow_up_hours = preferences["follow_up_hours"].get(priority, 24)
        topic = self._normalize_topic(issue.get("topic"))
        now = self._now()

        if task.get("status") == "snoozed":
            snoozed_until = self._parse_iso(task.get("snoozed_until"))
            if snoozed_until and now < snoozed_until:
                return (
                    "snoozed",
                    snoozed_until.isoformat(timespec="seconds"),
                    f"已手动静默到 {snoozed_until.strftime('%Y-%m-%d %H:%M')}",
                )
            task["status"] = "open"
            task["snoozed_until"] = None

        if topic in preferences.get("high_risk_only_topics", []) and priority != "high":
            next_follow_up = now + timedelta(hours=follow_up_hours)
            return (
                "monitor_only",
                next_follow_up.isoformat(timespec="seconds"),
                "按当前偏好仅在高风险时主动推送，本轮先保留在任务板中观察。",
            )

        if self._in_quiet_hours(preferences) and priority != "high":
            next_follow_up = self._next_quiet_end(preferences)
            return (
                "deferred",
                next_follow_up.isoformat(timespec="seconds"),
                f"当前处于安静时段，自动顺延到 {next_follow_up.strftime('%H:%M')} 再跟进。",
            )

        last_sent = self._parse_iso(task.get("last_sent_at"))
        if last_sent and now < last_sent + timedelta(hours=repeat_hours):
            next_follow_up = last_sent + timedelta(hours=repeat_hours)
            return (
                "suppressed_repeat",
                next_follow_up.isoformat(timespec="seconds"),
                f"同类提醒短时间内不重复发送，下一次最早在 {next_follow_up.strftime('%Y-%m-%d %H:%M')} 跟进。",
            )

        next_follow_up = now + timedelta(hours=follow_up_hours)
        return (
            "deliver",
            next_follow_up.isoformat(timespec="seconds"),
            f"若未处理，我会在 {next_follow_up.strftime('%Y-%m-%d %H:%M')} 再次跟进。",
        )

    def _sort_tasks(self, tasks: list[dict]) -> list[dict]:
        return sorted(
            tasks,
            key=lambda item: (
                PRIORITY_ORDER.get(item.get("priority", "low"), 9),
                item.get("status") not in {"open", "snoozed"},
                item.get("last_detected_at", ""),
                item.get("title", ""),
            ),
        )

    def _render_board(self, tasks: list[dict]) -> str:
        buckets = {
            "open": [],
            "snoozed": [],
            "monitor_only": [],
            "resolved": [],
            "completed": [],
        }
        for task in self._sort_tasks(tasks):
            status = task.get("status", "open")
            if status not in buckets:
                buckets["open"].append(task)
            else:
                buckets[status].append(task)

        lines = [f"# Heartbeat Task Board -- {self._now().date().isoformat()}", ""]
        lines.extend(
            [
                "- `manage_health_tasks.py list` 查看任务",
                "- `manage_health_tasks.py complete <task_id>` 标记已处理",
                "- `manage_health_tasks.py snooze <task_id> --hours 24` 临时静默",
                "",
            ]
        )

        section_labels = {
            "open": "## Open",
            "snoozed": "## Snoozed",
            "monitor_only": "## Monitor Only",
            "resolved": "## Resolved",
            "completed": "## Completed",
        }
        for status in ("open", "snoozed", "monitor_only", "resolved", "completed"):
            lines.append(section_labels[status])
            if not buckets[status]:
                lines.append("- none")
                lines.append("")
                continue
            for task in buckets[status][:20]:
                lines.append(f"- [ ] {task['id']} | {task.get('priority', 'low')} | {task.get('title', 'Untitled')}")
                lines.append(f"  状态：{task.get('status')}")
                lines.append(f"  原因：{task.get('reason', 'pending')}")
                if task.get("next_step"):
                    lines.append(f"  下一步：{task['next_step']}")
                if task.get("next_follow_up_at"):
                    lines.append(f"  下次跟进：{task['next_follow_up_at']}")
                if task.get("delivery_note"):
                    lines.append(f"  推送策略：{task['delivery_note']}")
                if task.get("execution_mode"):
                    lines.append(f"  执行模式：{task['execution_mode']}")
                if task.get("source_refs"):
                    lines.append(f"  来源：{', '.join(task['source_refs'])}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def sync_issues(self, issues: list[dict], write: bool = True) -> dict:
        preferences = self.load_preferences()
        state = self.load_state()
        tasks = state.get("tasks", [])
        tasks_by_key = {task.get("dedupe_key"): task for task in tasks if task.get("dedupe_key")}
        now_iso = self._now_iso()
        current_keys = set()
        push_issues: list[dict] = []
        suppressed_issues: list[dict] = []
        synced_issues: list[dict] = []

        for issue in issues:
            topic = self._normalize_topic(issue.get("topic"))
            dedupe_key = issue.get("dedupe_key") or f"{topic}:{issue.get('title', 'untitled')}"
            task = tasks_by_key.get(dedupe_key)
            if task is None:
                task = {
                    "id": self._task_id(dedupe_key, topic),
                    "dedupe_key": dedupe_key,
                    "topic": topic,
                    "first_detected_at": now_iso,
                    "follow_up_count": 0,
                    "occurrences": 0,
                    "status": "open",
                }
                tasks.append(task)
                tasks_by_key[dedupe_key] = task

            current_keys.add(dedupe_key)
            task["title"] = issue.get("title", task.get("title"))
            task["reason"] = issue.get("reason", task.get("reason"))
            task["next_step"] = issue.get("next_step", task.get("next_step"))
            task["priority"] = issue.get("priority", task.get("priority", "low"))
            task["category"] = issue.get("category", task.get("category", "general"))
            task["trigger"] = issue.get("trigger", task.get("trigger", "event"))
            task["threshold"] = issue.get("threshold")
            task["source_refs"] = issue.get("source_refs", [])
            task["sticky"] = bool(issue.get("sticky", task.get("sticky", False)))
            task["execution_mode"] = issue.get("execution_mode", task.get("execution_mode", "heartbeat"))
            task["last_detected_at"] = now_iso
            task["occurrences"] = int(task.get("occurrences", 0)) + 1

            if task.get("status") in {"completed", "silenced"}:
                issue["task_id"] = task["id"]
                issue["delivery_status"] = "manual_silence"
                issue["delivery_note"] = "该事项已被手动关闭，除非重新打开任务，否则不再主动推送。"
                synced_issues.append(issue)
                suppressed_issues.append(issue)
                continue

            delivery_status, next_follow_up_at, delivery_note = self._delivery_status(
                task,
                issue,
                preferences,
            )
            task["next_follow_up_at"] = next_follow_up_at
            task["delivery_note"] = delivery_note

            if delivery_status == "deliver":
                if task.get("last_sent_at"):
                    task["follow_up_count"] = int(task.get("follow_up_count", 0)) + 1
                task["last_sent_at"] = now_iso
                task["status"] = "open"
                push_issues.append(issue)
            elif delivery_status == "snoozed":
                task["status"] = "snoozed"
                suppressed_issues.append(issue)
            elif delivery_status == "monitor_only":
                task["status"] = "monitor_only"
                suppressed_issues.append(issue)
            else:
                task["status"] = "open"
                suppressed_issues.append(issue)

            issue["task_id"] = task["id"]
            issue["delivery_status"] = delivery_status
            issue["next_follow_up_at"] = next_follow_up_at
            issue["delivery_note"] = delivery_note
            synced_issues.append(issue)

        for task in tasks:
            if task.get("dedupe_key") in current_keys:
                continue
            if task.get("sticky") and task.get("status") in {"open", "snoozed", "monitor_only"}:
                continue
            if task.get("status") in {"open", "snoozed", "monitor_only"}:
                task["status"] = "resolved"
                task["resolved_at"] = now_iso
                task["delivery_note"] = "该事项当前未再触发，已自动归档为 resolved。"

        state["tasks"] = self._sort_tasks(tasks)
        state_path = None
        board_path = None
        if write:
            state_path = self.save_state(state)
            board_path = self.writer.update_heartbeat_task_board(self._render_board(state["tasks"]))

        return {
            "issues": synced_issues,
            "push_issues": push_issues,
            "suppressed_issues": suppressed_issues,
            "preferences": preferences,
            "task_board_path": board_path,
            "task_state_path": state_path,
            "tasks": state["tasks"],
        }

    def list_tasks(self, status: str | None = None) -> list[dict]:
        tasks = self.load_state().get("tasks", [])
        if not status:
            return self._sort_tasks(tasks)
        return [task for task in self._sort_tasks(tasks) if task.get("status") == status]

    def _update_task(self, task_id: str, **updates) -> dict | None:
        state = self.load_state()
        for task in state.get("tasks", []):
            if task.get("id") != task_id:
                continue
            task.update(updates)
            self.save_state(state)
            self.writer.update_heartbeat_task_board(self._render_board(state["tasks"]))
            return task
        return None

    def complete_task(self, task_id: str, note: str = "") -> dict | None:
        updates = {
            "status": "completed",
            "completed_at": self._now_iso(),
            "delivery_note": note or "已手动标记为 completed。",
            "snoozed_until": None,
        }
        return self._update_task(task_id, **updates)

    def snooze_task(
        self,
        task_id: str,
        hours: int | None = None,
        until: str | None = None,
        note: str = "",
    ) -> dict | None:
        if until:
            try:
                target = datetime.fromisoformat(until)
            except ValueError:
                return None
        else:
            target = self._now() + timedelta(hours=hours or 24)
        updates = {
            "status": "snoozed",
            "snoozed_until": target.isoformat(timespec="seconds"),
            "next_follow_up_at": target.isoformat(timespec="seconds"),
            "delivery_note": note or f"已静默到 {target.strftime('%Y-%m-%d %H:%M')}",
        }
        return self._update_task(task_id, **updates)

    def reopen_task(self, task_id: str, note: str = "") -> dict | None:
        updates = {
            "status": "open",
            "delivery_note": note or "已重新打开任务。",
            "completed_at": None,
            "resolved_at": None,
            "snoozed_until": None,
        }
        return self._update_task(task_id, **updates)
