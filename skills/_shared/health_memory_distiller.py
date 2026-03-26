#!/usr/bin/env python3
"""Distill recent health operations into long-term MEMORY.md."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .health_heartbeat import HealthHeartbeat
from .health_memory import HealthMemoryWriter
from .patient_archive_bridge import PatientArchiveBridge


class HealthMemoryDistiller:
    """Summarize recent health operations back into long-term memory."""

    ITEM_LABELS = {
        "blood-pressure": "血压",
        "blood-sugar": "血糖",
        "weight": "体重",
        "sleep": "睡眠",
        "medications": "用药",
        "supplements": "补剂",
        "appointments": "复查/复诊",
        "behavior-plans": "行为计划",
        "execution-barriers": "执行障碍",
    }

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
        self.archive_bridge = PatientArchiveBridge(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )

    def _now(self) -> datetime:
        return self._now_fn()

    def _extract_recent_status(self, item_slug: str) -> list[str]:
        item_path = self.writer.items_dir / f"{item_slug}.md"
        if not item_path.exists():
            return []

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
                collected.append(line.strip())
        return collected

    def _has_non_pending_status(self, item_slug: str) -> bool:
        for line in self._extract_recent_status(item_slug):
            clean = line[2:] if line.startswith("- ") else line
            if clean and not clean.lower().endswith("pending"):
                return True
        return False

    def _latest_dated_files(self, directory: Path, limit: int = 3) -> list[str]:
        dated = [path.stem for path in sorted(directory.glob("*.md"), reverse=True)]
        return dated[:limit]

    def _digest_title(self, path: Path) -> str | None:
        if not path.exists():
            return None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return None

    def build_snapshot(self) -> dict:
        today = self._now().date().isoformat()
        heartbeat_result = self.heartbeat.run(write_report=False)
        issues = heartbeat_result["issues"]

        summary_lines = []
        daily_dates = self._latest_dated_files(self.writer.daily_dir, limit=7)
        if daily_dates:
            summary_lines.append(f"- 最近 daily 已覆盖到 {daily_dates[0]}。")
            summary_lines.append(f"- 最近 7 次 daily 日期：{', '.join(daily_dates)}。")

        weekly_title = self._digest_title(self.writer.weekly_digest_path)
        if weekly_title:
            summary_lines.append(f"- 最近周报：{weekly_title}。")

        monthly_title = self._digest_title(self.writer.monthly_digest_path)
        if monthly_title:
            summary_lines.append(f"- 最近月报：{monthly_title}。")

        archive_summary = self.archive_bridge.build_summary()
        if archive_summary.get("available"):
            pid = archive_summary["patient_id"]
            uc = archive_summary["unclassified_count"]
            summary_lines.append(
                f"- 患者档案 {pid} 已连接，未分类文件 {uc} 份。"
            )
            latest_timeline = archive_summary.get("timeline_entries") or []
            if latest_timeline:
                latest = latest_timeline[0]
                summary_lines.append(f"- 最近病历事件：{latest['date']} | {latest['type']} | {latest['summary']}。")

        for slug, label in self.ITEM_LABELS.items():
            status_lines = self._extract_recent_status(slug)
            if not status_lines:
                continue
            for line in status_lines[:2]:
                clean = line[2:] if line.startswith("- ") else line
                if clean.lower().endswith("pending"):
                    continue
                summary_lines.append(f"- {label}：{clean}")
                break

        if not summary_lines:
            summary_lines.append("- 近期尚未积累足够的健康运营数据。")

        barrier_rows = self.writer.latest_execution_barriers(limit=3)
        for row in barrier_rows:
            summary_lines.append(f"- 执行障碍：{row.get('Barrier', 'pending')} | {row.get('Impact', 'pending')}")

        active_issues = [issue for issue in issues if issue.get("priority") in {"high", "medium"}]
        task_lines = []
        for issue in active_issues[:4]:
            task_lines.append(f"- {issue['title']}：{issue['next_step']}")
        active_plans = self.writer.list_behavior_plans(statuses={"active", "in_progress", "blocked"})
        if active_plans:
            first = active_plans[0]
            task_lines.append(
                f"- 行为计划：{first.get('Title', 'pending')}"
                f" | 到期 {first.get('Due At', 'pending')}"
                f" | {first.get('Next Step', 'pending')}"
            )
        if not task_lines:
            task_lines = ["- 继续保持连续记录，并在周末前检查是否有缺失项。"]

        risk_lines = []
        for issue in issues[:5]:
            risk_lines.append(f"- [{issue['priority']}] {issue['title']}：{issue['reason']}")
        if not risk_lines:
            risk_lines = ["- 当前没有检测到明显高风险事项。"]

        source_lines = []
        if daily_dates:
            source_lines.append(f"- daily: {', '.join(daily_dates[:3])}")
        item_sources = [slug for slug in self.ITEM_LABELS if self._has_non_pending_status(slug)]
        if item_sources:
            source_lines.append(f"- items: {', '.join(item_sources)}")
        if weekly_title:
            source_lines.append(f"- weekly digest: {weekly_title}")
        if monthly_title:
            source_lines.append(f"- monthly digest: {monthly_title}")
        if archive_summary.get("available"):
            source_lines.append(f"- patient archive: {archive_summary['patient_id']}")
        if issues:
            source_lines.append(f"- heartbeat: {today} ({len(issues)} items)")

        # Build source reference comment for bidirectional tracing
        source_refs: list[str] = []
        for slug in self.ITEM_LABELS:
            item_path = self.writer.items_dir / f"{slug}.md"
            if item_path.exists() and self._has_non_pending_status(slug):
                source_refs.append(f"items/{slug}.md")
        for d in daily_dates[:3]:
            source_refs.append(f"daily/{d}.md")
        if weekly_title:
            source_refs.append("weekly-digest.md")
        if monthly_title:
            source_refs.append("monthly-digest.md")
        if archive_summary.get("available"):
            source_refs.append(f"patient_archive:{archive_summary['patient_id']}")
        if issues:
            source_refs.append(f"heartbeat:{today}")

        return {
            "date": today,
            "summary_lines": summary_lines[:8],
            "task_lines": task_lines[:5],
            "risk_lines": risk_lines[:5],
            "source_lines": source_lines[:6],
            "source_refs": source_refs,
        }

    def run(self, write: bool = True) -> dict:
        snapshot = self.build_snapshot()
        memory_path = None
        if write:
            memory_path = self.writer.update_long_term_memory(
                summary_lines=snapshot["summary_lines"],
                task_lines=snapshot["task_lines"],
                risk_lines=snapshot["risk_lines"],
                source_lines=snapshot["source_lines"],
            )
        snapshot["memory_path"] = memory_path
        return snapshot
