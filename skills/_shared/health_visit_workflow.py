#!/usr/bin/env python3
"""Visit briefing and follow-up workflow for VitaClaw health workspaces."""

from __future__ import annotations

import re
from datetime import datetime

from .health_heartbeat import HealthHeartbeat
from .health_memory import HealthMemoryWriter
from .health_timeline_builder import HealthTimelineBuilder


class HealthVisitWorkflow:
    """Build clinician-ready briefing/follow-up artifacts from shared health memory."""

    ITEM_LABELS = {
        "blood-pressure": "血压",
        "blood-sugar": "血糖",
        "weight": "体重",
        "sleep": "睡眠",
        "medications": "用药",
        "supplements": "补剂",
        "appointments": "复查/复诊",
    }

    QUESTION_MAP = {
        "blood-pressure": "近期家庭血压波动/偏高，当前目标值、测量方法或治疗节奏是否需要调整？",
        "blood-sugar": "近期血糖控制波动较大，是否需要进一步评估饮食、运动、监测频率或治疗方案？",
        "weight": "近期体重变化是否提示需要调整饮食、运动或进一步检查？",
        "sleep": "近期睡眠/压力状态对整体健康管理的影响是否需要更系统处理？",
        "medication": "当前用药依从性、续配和服药时点是否需要优化？",
        "appointments": "下一次复查的时间点、项目和准备事项是否已经足够明确？",
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
        self.timeline_builder = HealthTimelineBuilder(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )

    def _now(self) -> datetime:
        return self._now_fn()

    def _read_recent_status(self, item_slug: str) -> list[str]:
        path = self.writer.items_dir / f"{item_slug}.md"
        if not path.exists():
            return []

        lines = path.read_text(encoding="utf-8").splitlines()
        in_section = False
        collected: list[str] = []
        for raw_line in lines:
            line = raw_line.strip()
            if line == "## Recent Status":
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.startswith("- "):
                clean = line[2:].strip()
                if clean.lower().endswith("pending"):
                    continue
                collected.append(clean)
        return collected

    def _appointments_status(self) -> dict[str, str]:
        status: dict[str, str] = {}
        for line in self._read_recent_status("appointments"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            status[key.strip().lower()] = value.strip()
        return status

    def _extract_iso_date(self, text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        return match.group(1) if match else None

    def _default_visit_context(
        self,
        visit_date: str | None = None,
        department: str | None = None,
        purpose: str | None = None,
        owner: str | None = None,
    ) -> dict:
        status = self._appointments_status()
        resolved_visit_date = (
            visit_date or self._extract_iso_date(status.get("next follow-up")) or self._now().date().isoformat()
        )
        details = status.get("next follow-up details") or status.get("latest appointment") or "待补充"
        return {
            "visit_date": resolved_visit_date,
            "department": department or "待补充科室/医生",
            "purpose": purpose or details,
            "owner": owner or "self",
            "details": details,
            "preparation_status": status.get("preparation status") or "pending",
        }

    def _metric_snapshot(self) -> list[str]:
        lines: list[str] = []
        for slug, label in self.ITEM_LABELS.items():
            statuses = self._read_recent_status(slug)
            if not statuses:
                continue
            lines.append(f"- {label}")
            for status in statuses[:2]:
                lines.append(f"- {status}")
        return lines[:12] or ["- 尚未积累足够的连续指标摘要。"]

    def _risk_snapshot(self) -> list[str]:
        issues = self.heartbeat.run(write_report=False)["issues"]
        lines = []
        for issue in issues[:6]:
            line = f"- [{issue['priority']}] {issue['title']}：{issue['reason']}"
            if issue.get("threshold"):
                line += f"（依据：{issue['threshold']}）"
            lines.append(line)
        return lines or ["- 当前没有高优先级风险，但仍建议携带近期连续记录。"]

    def _timeline_snapshot(self) -> list[str]:
        timeline = self.timeline_builder.build(write=False, max_entries=8)
        lines = []
        for entry in timeline["entries"][:6]:
            lines.append(f"- {entry['date']} | {entry['type']} | {entry['summary']} | {entry['source']}")
        return lines or ["- 当前没有足够的统一时间轴条目。"]

    def _questions(self, issues: list[dict], purpose: str) -> list[str]:
        lines: list[str] = []
        seen_topics = set()
        for issue in issues:
            topic = issue.get("topic", "general")
            if topic in seen_topics:
                continue
            seen_topics.add(topic)
            mapped = self.QUESTION_MAP.get(topic)
            if mapped:
                lines.append(f"- {mapped}")
            else:
                lines.append(f"- 针对“{issue['title']}”，本次门诊最需要优先确认的检查或行动是什么？")
            if len(lines) >= 4:
                break
        if not lines:
            lines.append(f"- 围绕“{purpose}”，本次最值得优先确认的目标、检查和下次复查节奏是什么？")
        return lines

    def generate_briefing(
        self,
        visit_date: str | None = None,
        department: str | None = None,
        purpose: str | None = None,
        owner: str | None = None,
        write: bool = True,
    ) -> dict:
        context = self._default_visit_context(
            visit_date=visit_date,
            department=department,
            purpose=purpose,
            owner=owner,
        )
        heartbeat_result = self.heartbeat.run(write_report=False)
        issues = heartbeat_result["issues"]

        summary_lines = [
            f"- 就诊日期：{context['visit_date']}",
            f"- 科室 / 医生：{context['department']}",
            f"- 目的：{context['purpose']}",
            f"- 准备状态：{context['preparation_status']}",
            f"- 陪同 / 负责人：{context['owner']}",
        ]

        prepare_lines = [
            f"- 带上近 1-2 周连续记录，尤其是与“{context['purpose']}”最相关的指标。",
            "- 如有最新检查报告、化验单、Apple Health 导出或病历更新，一并整理进健康工作区。",
            f"- 当前 appointment 备注：{context['details']}",
            f"- 周报：{self.writer.weekly_digest_path}",
            f"- 统一时间轴：{self.writer.files_dir / 'health-timeline.md'}",
        ]

        sections = [
            ("## Visit Context", summary_lines),
            ("## Metric Snapshot", self._metric_snapshot()),
            ("## Active Risks", self._risk_snapshot()),
            ("## Recent Timeline", self._timeline_snapshot()),
            ("## Questions To Ask", self._questions(issues, context["purpose"])),
            ("## Preparation Checklist", prepare_lines),
            (
                "## Sources",
                [
                    f"- {self.writer.items_dir / 'appointments.md'}",
                    f"- {self.writer.weekly_digest_path}",
                    f"- {self.writer.monthly_digest_path}",
                    f"- {self.writer.files_dir / 'health-timeline.md'}",
                ],
            ),
        ]

        markdown = (
            "\n".join(
                [
                    f"# Visit Briefing -- {context['visit_date']}",
                    "",
                    *["\n".join([heading, "", *(lines or ["- pending"]), ""]) for heading, lines in sections],
                ]
            ).rstrip()
            + "\n"
        )

        path = None
        if write:
            filename = f"visit-briefing-{context['visit_date']}.md"
            path = self.writer.write_health_file(
                filename=filename,
                title=f"# Visit Briefing -- {context['visit_date']}",
                sections=sections,
                date_str=context["visit_date"],
                file_type="visit-briefing",
                summary=f"{context['visit_date']} 门诊前 briefing",
            )

        return {
            "visit_date": context["visit_date"],
            "markdown": markdown,
            "path": path,
            "issues": issues,
        }

    def record_follow_up(
        self,
        visit_date: str,
        department: str,
        purpose: str,
        summary: str,
        plan: str | None = None,
        next_follow_up: str | None = None,
        next_follow_up_details: str | None = None,
        owner: str = "self",
        doctor: str | None = None,
        write: bool = True,
    ) -> dict:
        department_label = department if not doctor else f"{department} / {doctor}"
        notes = summary if not plan else f"{summary} | Plan: {plan}"
        appointments_path = self.writer.update_appointments(
            visit_date=visit_date,
            department_doctor=department_label,
            purpose=purpose,
            status="completed",
            owner=owner,
            notes=notes,
            latest_appointment=f"{visit_date} {purpose}",
            next_follow_up=next_follow_up,
            next_follow_up_details=next_follow_up_details,
            preparation_status="本次复诊已完成，待执行 follow-up",
        )

        self.writer._upsert_daily_section(
            visit_date,
            "Appointment Follow-up",
            "visit-follow-up",
            [
                f"Department: {department_label}",
                f"Purpose: {purpose}",
                f"Summary: {summary}",
                f"Plan: {plan or 'pending'}",
                f"Next follow-up: {next_follow_up or 'pending'}",
            ],
        )

        sections = [
            (
                "## Visit Summary",
                [
                    f"- 日期：{visit_date}",
                    f"- 科室 / 医生：{department_label}",
                    f"- 就诊目的：{purpose}",
                    f"- 摘要：{summary}",
                ],
            ),
            ("## Clinician Plan", [f"- {plan or '待补充'}"]),
            (
                "## Next Follow-up",
                [
                    f"- 下次复查：{next_follow_up or 'pending'}",
                    f"- 细节：{next_follow_up_details or 'pending'}",
                    f"- Owner：{owner}",
                ],
            ),
            (
                "## Sources",
                [
                    f"- {appointments_path}",
                    f"- {self.writer.daily_dir / f'{visit_date}.md'}",
                ],
            ),
        ]

        markdown = (
            "\n".join(
                [
                    f"# Visit Follow-up -- {visit_date}",
                    "",
                    *["\n".join([heading, "", *(lines or ["- pending"]), ""]) for heading, lines in sections],
                ]
            ).rstrip()
            + "\n"
        )

        path = None
        if write:
            path = self.writer.write_health_file(
                filename=f"visit-follow-up-{visit_date}.md",
                title=f"# Visit Follow-up -- {visit_date}",
                sections=sections,
                date_str=visit_date,
                file_type="visit-follow-up",
                summary=f"{visit_date} 门诊后 follow-up",
            )

        return {
            "visit_date": visit_date,
            "appointments_path": appointments_path,
            "markdown": markdown,
            "path": path,
        }
