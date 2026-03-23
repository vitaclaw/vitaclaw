#!/usr/bin/env python3
"""Automation-oriented health operations runner for VitaClaw."""

from __future__ import annotations

import contextlib
import io
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from health_data_store import HealthDataStore
from health_heartbeat import HealthHeartbeat
from health_reminder_center import HealthReminderCenter
from health_memory import HealthMemoryWriter
from health_memory_distiller import HealthMemoryDistiller
from health_timeline_builder import HealthTimelineBuilder
from patient_archive_bridge import PatientArchiveBridge


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


WEEKLY_DIR = _repo_root() / "skills" / "weekly-health-digest"
if str(WEEKLY_DIR) not in sys.path:
    sys.path.insert(0, str(WEEKLY_DIR))

from weekly_health_digest import WeeklyHealthDigest  # noqa: E402


class HealthOperationsRunner:
    """Run due health maintenance tasks for cron / automation."""

    def __init__(
        self,
        data_dir: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        patients_root: str | None = None,
        patient_id: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.writer = HealthMemoryWriter(
            memory_root=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )
        self.heartbeat = HealthHeartbeat(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.distiller = HealthMemoryDistiller(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.digest = WeeklyHealthDigest(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )
        self.store = HealthDataStore("health-operations", data_dir=data_dir)
        self.operations_dir = self.writer.heartbeat_dir / "operations"
        self.operations_dir.mkdir(parents=True, exist_ok=True)
        self.reminder_center = HealthReminderCenter(
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )
        self.archive_bridge = PatientArchiveBridge(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.timeline_builder = HealthTimelineBuilder(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )

    def _now(self) -> datetime:
        return self._now_fn()

    def _today(self) -> str:
        return self._now().date().isoformat()

    def _capture(self, fn, *args, **kwargs):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = fn(*args, **kwargs)
        return result, buffer.getvalue().strip()

    def _week_start(self, ref: datetime) -> str:
        monday = ref - timedelta(days=ref.weekday())
        return monday.strftime("%Y-%m-%d")

    def _month_label(self, ref: datetime) -> str:
        return ref.strftime("%Y-%m")

    def _has_weekly_digest(self, week_start: str) -> bool:
        for record in self.digest.store.query("digest"):
            if record.get("data", {}).get("week_start") == week_start:
                return True
        return False

    def _has_monthly_digest(self, month_label: str) -> bool:
        for record in self.digest.store.query("monthly_digest"):
            if record.get("data", {}).get("month") == month_label:
                return True
        return False

    def _weekly_targets(self) -> list[str]:
        targets: list[str] = []
        today = self._now()
        current_monday = self._week_start(today)
        previous_monday = self._week_start(today - timedelta(days=7))
        if today.weekday() >= 6 and not self._has_weekly_digest(current_monday):
            targets.append(current_monday)
        if today.weekday() <= 2 and not self._has_weekly_digest(previous_monday):
            targets.append(previous_monday)
        return targets

    def _monthly_targets(self) -> list[str]:
        targets: list[str] = []
        today = self._now()
        current_month = self._month_label(today)
        previous_month_date = today.replace(day=1) - timedelta(days=1)
        previous_month = self._month_label(previous_month_date)
        if today.day >= 28 and not self._has_monthly_digest(current_month):
            targets.append(f"{current_month}-15")
        if today.day <= 5 and not self._has_monthly_digest(previous_month):
            targets.append(f"{previous_month}-15")
        return targets

    def _needs_distill(self) -> bool:
        latest_daily = sorted(self.writer.daily_dir.glob("*.md"))
        if not latest_daily:
            return False
        last_distilled = self.writer.last_memory_distilled_at()
        if last_distilled is None:
            return True
        return latest_daily[-1].stem > last_distilled.date().isoformat()

    def _render_markdown(self, summary: dict) -> str:
        lines = [f"# Health Operations Report -- {summary['date']}", ""]
        lines.append("## Actions")
        if not summary["actions"]:
            lines.append("- 本轮没有触发新的后台运营动作。")
        else:
            for action in summary["actions"]:
                lines.append(f"- {action}")
        lines.append("")
        lines.append("## Heartbeat")
        lines.append(f"- Pushable issues: {summary['heartbeat_push_count']}")
        lines.append(f"- Total issues: {summary['heartbeat_issue_count']}")
        if summary.get("heartbeat_report_path"):
            lines.append(f"- Report: {summary['heartbeat_report_path']}")
        if summary.get("task_board_path"):
            lines.append(f"- Task board: {summary['task_board_path']}")
        lines.append("")
        lines.append("## Sources")
        for source in summary.get("sources", []):
            lines.append(f"- {source}")
        lines.append("")
        if summary.get("review_task_count"):
            lines.append("## User-Visible Tasks")
            lines.append(f"- Sticky review tasks created: {summary['review_task_count']}")
            if summary.get("task_board_path"):
                lines.append(f"- Task board: {summary['task_board_path']}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _digest_review_issues(self, generated_weekly: list[str], generated_monthly: list[str]) -> list[dict]:
        issues: list[dict] = []
        for week_start in generated_weekly:
            issues.append(
                {
                    "priority": "low",
                    "title": f"本周周报待阅读：{week_start}",
                    "reason": f"新的健康周报 {week_start} 已生成，但还没有被手动确认阅读。",
                    "next_step": "打开 weekly-digest.md，确认亮点、风险和下周重点，并按需完成任务板事项。",
                    "follow_up": "若仍未处理，明天继续提醒。",
                    "topic": "weekly-digest",
                    "category": "operations",
                    "trigger": "event",
                    "source_refs": [str(self.writer.weekly_digest_path)],
                    "dedupe_key": f"weekly-review:{week_start}",
                    "sticky": True,
                    "execution_mode": "isolated-session",
                }
            )
        for month_label in generated_monthly:
            issues.append(
                {
                    "priority": "medium",
                    "title": f"本月月报待阅读：{month_label}",
                    "reason": f"新的健康月报 {month_label} 已生成，建议尽快完成月度复盘。",
                    "next_step": "打开 monthly-digest.md，确认风险变化、执行障碍和下月重点。",
                    "follow_up": "若仍未处理，48 小时内继续提醒。",
                    "topic": "monthly-digest",
                    "category": "operations",
                    "trigger": "event",
                    "source_refs": [str(self.writer.monthly_digest_path)],
                    "dedupe_key": f"monthly-review:{month_label}",
                    "sticky": True,
                    "execution_mode": "isolated-session",
                }
            )
        return issues

    def run(
        self,
        force_weekly: bool = False,
        force_monthly: bool = False,
        force_distill: bool = False,
        write: bool = True,
    ) -> dict:
        actions: list[str] = []
        sources: list[str] = []
        generated_weekly: list[str] = []
        generated_monthly: list[str] = []
        review_task_count = 0
        task_board_path = None

        weekly_targets = self._weekly_targets()
        if force_weekly:
            weekly_targets = [self._today()]
        for week_of in weekly_targets:
            result, logs = self._capture(self.digest.generate, week_of=week_of)
            if result:
                week_start = self.digest._get_week_range(week_of)[0]
                generated_weekly.append(week_start)
                actions.append(f"自动生成周报：{week_start}")
                if logs:
                    sources.append(f"weekly:{week_start}")

        monthly_targets = self._monthly_targets()
        if force_monthly:
            monthly_targets = [self._today()]
        for month_of in monthly_targets:
            result, logs = self._capture(self.digest.generate_monthly, month_of=month_of)
            if result:
                month_label = self.digest._get_month_range(month_of)[0][:7]
                generated_monthly.append(month_label)
                actions.append(f"自动生成月报：{month_label}")
                if logs:
                    sources.append(f"monthly:{month_label}")

        if write and self.archive_bridge.is_available() and self.archive_bridge.needs_sync():
            archive_result = self.archive_bridge.sync_to_workspace(write=True)
            if archive_result.get("summary_path"):
                actions.append("同步患者档案摘要")
                sources.append(archive_result["summary_path"])

        if write and self.archive_bridge.is_available():
            timeline_result = self.timeline_builder.build(write=True)
            if timeline_result.get("timeline_path"):
                actions.append("刷新统一健康时间轴")
                sources.append(timeline_result["timeline_path"])

        heartbeat_result = self.heartbeat.run(write_report=write)
        if heartbeat_result.get("push_issues"):
            actions.append(f"刷新 heartbeat：{len(heartbeat_result['push_issues'])} 条可推送事项")
        elif write:
            actions.append("刷新 heartbeat：无新增可推送事项")

        distill_snapshot = None
        if force_distill or generated_weekly or generated_monthly or self._needs_distill():
            distill_snapshot, _ = self._capture(self.distiller.run, True)
            if distill_snapshot and distill_snapshot.get("memory_path"):
                actions.append("自动蒸馏长期画像：已更新 MEMORY.md")
                sources.append("memory-distill")

        review_issues = self._digest_review_issues(generated_weekly, generated_monthly)
        if review_issues and write:
            task_sync = self.reminder_center.sync_issues(review_issues, write=True)
            review_task_count = len(review_issues)
            task_board_path = task_sync.get("task_board_path")

        summary = {
            "date": self._today(),
            "generated_weekly": generated_weekly,
            "generated_monthly": generated_monthly,
            "heartbeat_issue_count": len(heartbeat_result.get("issues", [])),
            "heartbeat_push_count": len(heartbeat_result.get("push_issues", [])),
            "heartbeat_report_path": heartbeat_result.get("report_path"),
            "task_board_path": heartbeat_result.get("task_board_path"),
            "memory_path": (distill_snapshot or {}).get("memory_path") if distill_snapshot else None,
            "actions": actions,
            "review_task_count": review_task_count,
            "task_board_path": task_board_path or heartbeat_result.get("task_board_path"),
            "sources": sorted(set(sources + [
                str(self.writer.weekly_digest_path),
                str(self.writer.monthly_digest_path),
                str(self.writer.memory_doc_path) if self.writer.memory_doc_path else "",
            ])),
        }
        summary["sources"] = [item for item in summary["sources"] if item]

        report_path = None
        if write:
            markdown = self._render_markdown(summary)
            report_path = self.operations_dir / f"{self._today()}.md"
            report_path.write_text(markdown, encoding="utf-8")
            self.store.append(
                "operations_run",
                {
                    "date": self._today(),
                    "generated_weekly": generated_weekly,
                    "generated_monthly": generated_monthly,
                    "heartbeat_issue_count": summary["heartbeat_issue_count"],
                    "heartbeat_push_count": summary["heartbeat_push_count"],
                    "report_path": str(report_path),
                },
                note="Automated health operations run",
            )
        summary["report_path"] = str(report_path) if report_path else None
        return summary
