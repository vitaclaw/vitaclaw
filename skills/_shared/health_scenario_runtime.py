#!/usr/bin/env python3
"""Shared scenario runtime for productized VitaClaw health workflows."""

from __future__ import annotations

from datetime import datetime

from health_memory import HealthMemoryWriter
from health_reminder_center import HealthReminderCenter


DEFAULT_SECTION_ORDER = [
    "## 记录",
    "## 解读",
    "## 趋势",
    "## 风险",
    "## 建议",
    "## 必须就医",
]


class HealthScenarioRuntime:
    """Render consistent scenario outputs, write audits, and sticky follow-up tasks."""

    def __init__(
        self,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.writer = HealthMemoryWriter(
            workspace_root=workspace_root,
            memory_root=memory_dir,
            now_fn=self._now_fn,
        )
        self.reminder_center = HealthReminderCenter(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            now_fn=self._now_fn,
        )

    def _now(self) -> datetime:
        return self._now_fn()

    def _today(self) -> str:
        return self._now().date().isoformat()

    def build_task(
        self,
        title: str,
        reason: str,
        next_step: str,
        follow_up: str,
        priority: str = "medium",
        topic: str = "general",
        category: str = "scenario-follow-up",
        source_refs: list[str] | None = None,
        threshold: str | None = None,
        dedupe_key: str | None = None,
        sticky: bool = True,
        execution_mode: str | None = None,
    ) -> dict:
        return {
            "priority": priority,
            "title": title,
            "reason": reason,
            "next_step": next_step,
            "follow_up": follow_up,
            "topic": topic,
            "category": category,
            "trigger": "event",
            "source_refs": source_refs or [],
            "threshold": threshold,
            "dedupe_key": dedupe_key or f"{topic}:{title}",
            "sticky": sticky,
            "execution_mode": execution_mode or ("isolated-session" if priority == "high" else "heartbeat"),
        }

    def _normalize_section_lines(self, lines: list[str] | None, fallback: str = "暂无。") -> list[str]:
        if not lines:
            return [f"- {fallback}"]
        result = []
        for line in lines:
            if not line:
                continue
            result.append(line if line.startswith(("- ", "| ")) else f"- {line}")
        return result or [f"- {fallback}"]

    def render_markdown(
        self,
        title: str,
        date_str: str,
        sections: dict[str, list[str]],
        sources: list[str],
        evidence: list[str],
        alerts: list[str] | None = None,
        follow_up_tasks: list[dict] | None = None,
        writebacks: list[str] | None = None,
    ) -> str:
        lines = [f"# {title} -- {date_str}", ""]
        for heading in DEFAULT_SECTION_ORDER:
            lines.append(heading)
            lines.append("")
            lines.extend(self._normalize_section_lines(sections.get(heading), fallback="暂无。"))
            lines.append("")

        if alerts:
            lines.append("## Alerts")
            lines.append("")
            lines.extend(self._normalize_section_lines(alerts, fallback="暂无。"))
            lines.append("")

        if follow_up_tasks:
            lines.append("## Follow-up Tasks")
            lines.append("")
            for task in follow_up_tasks:
                lines.append(
                    f"- [{task.get('priority', 'medium')}] {task.get('title', 'Untitled')}：{task.get('next_step', 'pending')}"
                )
                lines.append(f"  如果不处理：{task.get('reason', 'pending')}")
                lines.append(f"  再次跟进：{task.get('follow_up', 'pending')}")
            lines.append("")

        if writebacks:
            lines.append("## Writebacks")
            lines.append("")
            lines.extend(self._normalize_section_lines(writebacks, fallback="暂无。"))
            lines.append("")

        lines.append("## Sources")
        lines.append("")
        lines.extend(self._normalize_section_lines(sources, fallback="暂无。"))
        lines.append("")
        lines.append("## Evidence")
        lines.append("")
        lines.extend(self._normalize_section_lines(evidence, fallback="暂无。"))
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def persist_result(
        self,
        filename: str,
        title: str,
        date_str: str,
        sections: dict[str, list[str]],
        sources: list[str],
        evidence: list[str],
        scenario: str,
        file_type: str,
        summary: str,
        alerts: list[str] | None = None,
        follow_up_tasks: list[dict] | None = None,
        writebacks: list[str] | None = None,
        audit_reason: str | None = None,
    ) -> dict:
        markdown = self.render_markdown(
            title=title,
            date_str=date_str,
            sections=sections,
            sources=sources,
            evidence=evidence,
            alerts=alerts,
            follow_up_tasks=follow_up_tasks,
            writebacks=writebacks,
        )
        section_payload = []
        for heading in DEFAULT_SECTION_ORDER:
            section_payload.append((heading, self._normalize_section_lines(sections.get(heading), fallback="暂无。")))
        if alerts:
            section_payload.append(("## Alerts", self._normalize_section_lines(alerts, fallback="暂无。")))
        if follow_up_tasks:
            task_lines = []
            for task in follow_up_tasks:
                task_lines.append(
                    f"[{task.get('priority', 'medium')}] {task.get('title', 'Untitled')}：{task.get('next_step', 'pending')}"
                )
                task_lines.append(f"如果不处理：{task.get('reason', 'pending')}")
                task_lines.append(f"再次跟进：{task.get('follow_up', 'pending')}")
            section_payload.append(("## Follow-up Tasks", self._normalize_section_lines(task_lines, fallback="暂无。")))
        if writebacks:
            section_payload.append(("## Writebacks", self._normalize_section_lines(writebacks, fallback="暂无。")))
        section_payload.append(("## Sources", self._normalize_section_lines(sources, fallback="暂无。")))
        section_payload.append(("## Evidence", self._normalize_section_lines(evidence, fallback="暂无。")))

        output_path = self.writer.write_health_file(
            filename=filename,
            title=f"# {title} -- {date_str}",
            sections=section_payload,
            date_str=date_str,
            file_type=file_type,
            summary=summary,
        )
        self.writer.append_write_audit(
            scenario=scenario,
            target=output_path,
            reason=audit_reason or summary,
            source_refs=sources,
        )
        for writeback in writebacks or []:
            self.writer.append_write_audit(
                scenario=scenario,
                target=writeback,
                reason=summary,
                source_refs=sources,
            )

        task_sync = None
        if follow_up_tasks:
            task_sync = self.reminder_center.sync_issues(follow_up_tasks, write=True)

        return {
            "title": title,
            "date": date_str,
            "markdown": markdown,
            "sections": sections,
            "output_path": output_path,
            "follow_up_task_count": len(follow_up_tasks or []),
            "task_board_path": task_sync.get("task_board_path") if task_sync else None,
            "task_state_path": task_sync.get("task_state_path") if task_sync else None,
            "sources_used": sources,
            "evidence": evidence,
            "writebacks": writebacks or [],
            "alerts": alerts or [],
            "follow_up_tasks": follow_up_tasks or [],
        }
