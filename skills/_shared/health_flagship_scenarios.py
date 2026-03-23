#!/usr/bin/env python3
"""Flagship productized health scenarios for VitaClaw Iteration 2."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


SHARED_DIR = Path(__file__).resolve().parent
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from health_heartbeat import HealthHeartbeat
from health_memory import HealthMemoryWriter
from health_scenario_runtime import HealthScenarioRuntime
from health_visit_workflow import HealthVisitWorkflow


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = _repo_root()
for path in (
    ROOT / "skills" / "blood-pressure-tracker",
    ROOT / "skills" / "chronic-condition-monitor",
    ROOT / "skills" / "checkup-report-interpreter",
    ROOT / "skills" / "weekly-health-digest",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from blood_pressure_tracker import BloodPressureTracker  # noqa: E402
from chronic_condition_monitor import ChronicConditionMonitor  # noqa: E402
from checkup_report_interpreter import CheckupReportInterpreter  # noqa: E402
from weekly_health_digest import WeeklyHealthDigest  # noqa: E402


class _ScenarioBase:
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
        self.runtime = HealthScenarioRuntime(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            now_fn=self._now_fn,
        )
        self.writer = self.runtime.writer
        self.heartbeat = HealthHeartbeat(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.visit_workflow = HealthVisitWorkflow(
            data_dir=data_dir,
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self.data_dir = data_dir

    def _now(self) -> datetime:
        return self._now_fn()

    def _today(self) -> str:
        return self._now().date().isoformat()

    def _read_recent_status_lines(self, slug: str) -> list[str]:
        path = self.writer.items_dir / f"{slug}.md"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        in_section = False
        result = []
        for raw in lines:
            line = raw.strip()
            if line == "## Recent Status":
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.startswith("- "):
                result.append(line)
        return result

    def _recent_status_pairs(self, slug: str) -> dict[str, str]:
        pairs = {}
        for line in self._read_recent_status_lines(slug):
            clean = line[2:] if line.startswith("- ") else line
            if ":" not in clean:
                continue
            key, value = clean.split(":", 1)
            pairs[key.strip().lower()] = value.strip()
        return pairs

    def _filter_heartbeat(self, topics: set[str]) -> list[dict]:
        issues = self.heartbeat.run(write_report=False)["issues"]
        return [issue for issue in issues if issue.get("topic") in topics]

    def _format_issue_lines(self, issues: list[dict]) -> list[str]:
        if not issues:
            return ["当前没有需要优先升级的场景风险。"]
        lines = []
        for issue in issues[:5]:
            lines.append(
                f"[{issue.get('priority', 'low')}] {issue['title']}：{issue['reason']}"
            )
            if issue.get("threshold"):
                lines.append(f"依据：{issue['threshold']}")
        return lines

    def _parse_medications(self, medications: list[str] | None) -> list[dict]:
        result = []
        for raw in medications or []:
            parts = [part.strip() for part in raw.split("|")]
            if not parts or not parts[0]:
                continue
            result.append(
                {
                    "name": parts[0],
                    "dose": parts[1] if len(parts) > 1 else "",
                    "frequency": parts[2] if len(parts) > 2 else "",
                    "notes": parts[3] if len(parts) > 3 else "",
                    "status": "active",
                }
            )
        return result

    def _persist_medications(
        self,
        date_str: str,
        medications: list[dict],
        adherence: str | None,
        next_refill: str | None,
        stock_coverage_days: int | None,
        risks: str | None,
        writebacks: list[str],
    ) -> None:
        if not medications and not any([adherence, next_refill, stock_coverage_days, risks]):
            return
        writebacks.append(
            self.writer.update_medications(
                date_str=date_str,
                medications=medications,
                adherence=adherence,
                next_refill=next_refill,
                stock_coverage_days=stock_coverage_days,
                risks=risks,
            )
        )

    def _schedule_follow_up(
        self,
        next_follow_up: str | None,
        details: str | None,
        purpose: str,
        writebacks: list[str],
        latest_appointment: str | None = None,
    ) -> None:
        if not next_follow_up:
            return
        writebacks.append(
            self.writer.update_appointments(
                visit_date=next_follow_up,
                department_doctor="待确认科室/医生",
                purpose=purpose,
                status="planned",
                owner="self",
                notes=details or "",
                latest_appointment=latest_appointment or "pending",
                next_follow_up=next_follow_up,
                next_follow_up_details=details,
                preparation_status="待生成 briefing",
            )
        )


class HypertensionDailyCopilot(_ScenarioBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tracker = BloodPressureTracker(
            data_dir=self.data_dir,
            memory_dir=str(self.writer.base_dir),
            now_fn=self._now_fn,
        )
        self.digest = WeeklyHealthDigest(
            data_dir=self.data_dir,
            memory_dir=str(self.writer.base_dir),
            now_fn=self._now_fn,
        )

    def daily_entry(
        self,
        systolic: int | None = None,
        diastolic: int | None = None,
        pulse: int | None = None,
        context: str = "home",
        timestamp: str | None = None,
        medications: list[str] | None = None,
        adherence: str | None = None,
        next_refill: str | None = None,
        stock_coverage_days: int | None = None,
        diet_summary: str | None = None,
        exercise_summary: str | None = None,
        weight: float | None = None,
        symptoms: str | None = None,
        next_follow_up: str | None = None,
        next_follow_up_details: str | None = None,
        write: bool = True,
    ) -> dict:
        date_str = (timestamp or self._now().isoformat(timespec="seconds"))[:10]
        writebacks: list[str] = []
        sources = [
            str(self.writer.items_dir / "blood-pressure.md"),
            str(self.writer.items_dir / "medications.md"),
            str(self.writer.items_dir / "appointments.md"),
        ]
        evidence = [
            "高血压危象阈值：最近一次血压 >= 180/120 mmHg。",
            "连续高压阈值：最近 3 次血压均 >= 140/90 mmHg。",
            "续药提醒阈值：Next refill <= 7 days 或 Stock coverage days <= 7。",
        ]

        latest_record = None
        if systolic is not None and diastolic is not None:
            latest_record = self.tracker.record(
                systolic,
                diastolic,
                hr=pulse,
                context=context,
                timestamp=timestamp or self._now().isoformat(timespec="seconds"),
            )
            writebacks.append(str(self.writer.daily_dir / f"{date_str}.md"))
            writebacks.append(str(self.writer.items_dir / "blood-pressure.md"))

        parsed_meds = self._parse_medications(medications)
        self._persist_medications(
            date_str=date_str,
            medications=parsed_meds,
            adherence=adherence,
            next_refill=next_refill,
            stock_coverage_days=stock_coverage_days,
            risks="需结合医生建议评估" if parsed_meds else None,
            writebacks=writebacks,
        )

        if any([diet_summary, exercise_summary, weight, symptoms]):
            self.writer._upsert_daily_section(
                date_str,
                "Hypertension Copilot Notes",
                "hypertension-daily-copilot",
                [
                    f"Diet: {diet_summary or 'pending'}",
                    f"Exercise: {exercise_summary or 'pending'}",
                    f"Weight: {weight if weight is not None else 'pending'}",
                    f"Symptoms: {symptoms or 'pending'}",
                ],
            )
            writebacks.append(str(self.writer.daily_dir / f"{date_str}.md"))

        latest_appointment = self._recent_status_pairs("appointments").get("latest appointment")
        self._schedule_follow_up(
            next_follow_up=next_follow_up,
            details=next_follow_up_details,
            purpose="高血压复查",
            writebacks=writebacks,
            latest_appointment=latest_appointment,
        )

        next_bp_due = (self._now() + timedelta(hours=12)).replace(minute=0, second=0, microsecond=0)
        writebacks.append(
            self.writer.upsert_behavior_plan(
                plan_id="hypertension-daily-bp",
                scenario="hypertension-daily-copilot",
                title="补齐下一次家庭血压记录",
                cadence="daily",
                due_at=next_bp_due.isoformat(timespec="minutes"),
                topic="blood-pressure",
                risk_policy="focus-closely",
                consequence="连续性不足会削弱血压趋势判断和就医准备质量。",
                next_step="按标准化方式补录下一次家庭血压，并写上症状/诱因。",
            )
        )
        if next_follow_up:
            writebacks.append(
                self.writer.upsert_behavior_plan(
                    plan_id=f"hypertension-followup-{next_follow_up}",
                    scenario="hypertension-daily-copilot",
                    title="为下一次高血压复诊准备材料",
                    cadence="event",
                    due_at=f"{next_follow_up}T09:00",
                    topic="appointments",
                    risk_policy="focus-closely",
                    consequence="缺少连续记录会影响医生判断和方案调整。",
                    next_step="提前生成 briefing，并准备近 1-2 周家庭血压记录。",
                )
            )

        issues = self._filter_heartbeat({"blood-pressure", "medication", "appointments", "behavior-plan"})
        must_seek = []
        if latest_record:
            data = latest_record.get("data", {})
            if float(data.get("sys") or 0) >= 180 or float(data.get("dia") or 0) >= 120:
                must_seek.append("当前血压已达到危急范围，请立即联系急救或尽快就医。")
        if symptoms and any(keyword in symptoms for keyword in ("胸痛", "视物", "头痛", "呼吸困难", "blurred", "chest pain")):
            must_seek.append("伴随危险症状时，不要继续普通自我管理，建议尽快就医。")

        bp_status = self._read_recent_status_lines("blood-pressure")
        med_status = self._read_recent_status_lines("medications")
        follow_up_tasks = []
        follow_up_tasks.append(
            self.runtime.build_task(
                title="安排下一次家庭血压记录",
                reason=f"高血压场景已经为下一次家庭血压记录排好了 due time：{next_bp_due.isoformat(timespec='minutes')}。",
                next_step="按标准化方式完成下一次血压测量，并补上症状/诱因。",
                follow_up="到点后若仍未处理，会继续跟进。",
                priority="low",
                topic="behavior-plan",
                source_refs=[str(self.writer.behavior_plans_path)],
                dedupe_key="hypertension-next-bp-task",
            )
        )
        if systolic is None or diastolic is None:
            follow_up_tasks.append(
                self.runtime.build_task(
                    title="补录家庭血压",
                    reason="本次高血压场景没有新的血压读数，趋势判断会变弱。",
                    next_step="今天补录至少 1 次标准化家庭血压，并写上测量时段。",
                    follow_up="今天晚些时候再次检查是否已补录。",
                    priority="medium",
                    topic="blood-pressure",
                    source_refs=[str(self.writer.items_dir / "blood-pressure.md")],
                )
            )
        if not diet_summary:
            follow_up_tasks.append(
                self.runtime.build_task(
                    title="补充今日饮食摘要",
                    reason="缺少饮食信息时，很难判断血压波动是否与盐分或饮食结构有关。",
                    next_step="补充今日高盐食物、外卖、汤面或夜宵情况。",
                    follow_up="若今晚仍未补录，明天继续提醒。",
                    priority="low",
                    topic="behavior-plan",
                    source_refs=[str(self.writer.daily_dir / f"{date_str}.md")],
                )
            )

        sections = {
            "## 记录": [
                *(bp_status[:3] or ["当前还没有新的家庭血压读数。"]),
                *(med_status[:3] or ["当前还没有新的用药状态更新。"]),
                f"饮食摘要：{diet_summary or 'pending'}",
                f"运动摘要：{exercise_summary or 'pending'}",
                f"症状：{symptoms or 'pending'}",
            ],
            "## 解读": [
                (
                    f"最新血压分级：{self.tracker.classify(systolic, diastolic)['label']}"
                    if systolic is not None and diastolic is not None
                    else "当前没有新血压，解读将更多依赖最近历史。"
                ),
                f"用药依从性口径：{adherence or 'pending'}",
                "输出优先保留连续记录和阈值依据，不替代医生调整处方。",
            ],
            "## 趋势": bp_status[1:4] or ["等待连续读数形成更稳定的趋势判断。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": [
                "继续保留晨起/晚间双时点血压，并把症状和诱因写进 daily。",
                "优先处理任务板中的续药、复诊和行为计划事项。",
                "如近期要就诊，提前生成门诊 briefing。"
                if next_follow_up
                else "若近期计划复诊，记得把家庭血压记录整理为医生可读摘要。",
            ],
            "## 必须就医": must_seek or ["当前没有触发“必须就医”级别信号，但若出现胸痛、严重头痛、呼吸困难等症状应立即升级。"],
        }

        return self.runtime.persist_result(
            filename=f"hypertension-daily-{date_str}.md",
            title="Hypertension Daily Copilot",
            date_str=date_str,
            sections=sections,
            sources=sources,
            evidence=evidence,
            scenario="hypertension-daily-copilot",
            file_type="hypertension-copilot",
            summary=f"{date_str} 高血压日常闭环摘要",
            alerts=[issue["title"] for issue in issues[:3]],
            follow_up_tasks=follow_up_tasks,
            writebacks=sorted(set(writebacks)),
            audit_reason="高血压日常闭环写回",
        )

    def weekly_review(self, week_of: str | None = None) -> dict:
        self.digest.generate(week_of=week_of)
        week_start, week_end = self.digest._get_week_range(week_of)
        issues = self._filter_heartbeat({"blood-pressure", "medication", "appointments"})
        sections = {
            "## 记录": [
                f"周报范围：{week_start} ~ {week_end}",
                f"已生成周报：{self.writer.weekly_digest_path}",
            ],
            "## 解读": ["本次周度复盘会优先引用已经沉淀的 weekly-digest 和 items recent status。"],
            "## 趋势": self._read_recent_status_lines("blood-pressure")[:3] or ["等待更多周级连续数据。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": [
                "先阅读本周周报，再决定是否需要更新复诊计划或生活方式重点。",
                "把本周最常见的波动诱因写入 daily 或 behavior-plans。",
            ],
            "## 必须就医": ["如本周已出现危急血压或危险症状，请直接依据 task board 和 heartbeat 升级。"] if issues else ["本周未见新的必须就医级别结论。"],
        }
        follow_up_tasks = [
            self.runtime.build_task(
                title=f"阅读并确认高血压周报：{week_start}",
                reason="周报已生成，但还需要人工确认下周的复盘重点。",
                next_step="打开 weekly-digest.md，确认本周的高血压趋势、依从性和下周重点。",
                follow_up="若明天仍未处理，会继续提醒。",
                priority="low",
                topic="weekly-digest",
                source_refs=[str(self.writer.weekly_digest_path)],
                dedupe_key=f"hypertension-weekly-review:{week_start}",
            )
        ]
        return self.runtime.persist_result(
            filename=f"hypertension-weekly-review-{week_start}.md",
            title="Hypertension Weekly Review",
            date_str=week_end,
            sections=sections,
            sources=[str(self.writer.weekly_digest_path), str(self.writer.items_dir / "blood-pressure.md")],
            evidence=["周报来源于 weekly-health-digest 聚合结果。"],
            scenario="hypertension-daily-copilot",
            file_type="hypertension-weekly-review",
            summary=f"{week_start} 高血压周度复盘",
            follow_up_tasks=follow_up_tasks,
            writebacks=[str(self.writer.weekly_digest_path)],
        )

    def medication_review(self) -> dict:
        med_status = self._read_recent_status_lines("medications")
        issues = self._filter_heartbeat({"medication", "appointments"})
        sections = {
            "## 记录": med_status or ["当前还没有完整的长期用药快照。"],
            "## 解读": ["这里仅做依从性、续药和 follow-up 管理，不替代 DDI 或处方调整结论。"],
            "## 趋势": med_status[1:4] if med_status else ["等待连续用药记录形成趋势。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": [
                "确认 Next refill / Stock coverage days 是否仍然准确。",
                "若药物方案刚调整，尽快更新 medications.md 和 appointments.md。",
            ],
            "## 必须就医": ["若出现断药风险、严重不良反应或医生要求尽快复查，请优先就医。"],
        }
        return self.runtime.persist_result(
            filename=f"hypertension-medication-review-{self._today()}.md",
            title="Hypertension Medication Review",
            date_str=self._today(),
            sections=sections,
            sources=[str(self.writer.items_dir / "medications.md"), str(self.writer.items_dir / "appointments.md")],
            evidence=["续药预警依据 medications.md 的 Next refill 与 Stock coverage days。"],
            scenario="hypertension-daily-copilot",
            file_type="hypertension-medication-review",
            summary=f"{self._today()} 高血压用药复盘",
            writebacks=[],
        )


class DiabetesControlHub(_ScenarioBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitor = ChronicConditionMonitor(
            data_dir=self.data_dir,
            memory_dir=str(self.writer.base_dir),
            now_fn=self._now_fn,
        )
        self.digest = WeeklyHealthDigest(
            data_dir=self.data_dir,
            memory_dir=str(self.writer.base_dir),
            now_fn=self._now_fn,
        )

    def daily_log(
        self,
        glucose_entries: list[dict] | None = None,
        weight_kg: float | None = None,
        height_cm: float | None = None,
        meals_summary: str | None = None,
        exercise_summary: str | None = None,
        medications: list[str] | None = None,
        adherence: str | None = None,
        next_follow_up: str | None = None,
        next_follow_up_details: str | None = None,
        symptoms: str | None = None,
        write: bool = True,
    ) -> dict:
        date_str = self._today()
        writebacks: list[str] = []
        glucose_entries = glucose_entries or []
        for entry in glucose_entries:
            timestamp = entry.get("timestamp") or f"{date_str}T08:00:00"
            self.monitor.record(
                "glucose",
                {"value": float(entry["value"])},
                context=entry.get("context", ""),
                note=entry.get("note", ""),
                timestamp=timestamp,
            )
            date_str = timestamp[:10]
        if weight_kg is not None:
            self.monitor.record(
                "weight",
                {"kg": weight_kg, "height_cm": height_cm},
                note="Diabetes daily log",
                timestamp=f"{date_str}T07:05:00",
            )
        if glucose_entries:
            writebacks.extend(
                [
                    str(self.writer.daily_dir / f"{date_str}.md"),
                    str(self.writer.items_dir / "blood-sugar.md"),
                ]
            )
        if weight_kg is not None:
            writebacks.append(str(self.writer.items_dir / "weight.md"))

        parsed_meds = self._parse_medications(medications)
        self._persist_medications(
            date_str=date_str,
            medications=parsed_meds,
            adherence=adherence,
            next_refill=None,
            stock_coverage_days=None,
            risks="糖尿病用药需医生确认调整" if parsed_meds else None,
            writebacks=writebacks,
        )
        latest_appointment = self._recent_status_pairs("appointments").get("latest appointment")
        self._schedule_follow_up(
            next_follow_up=next_follow_up,
            details=next_follow_up_details,
            purpose="糖尿病复查",
            writebacks=writebacks,
            latest_appointment=latest_appointment,
        )

        next_glucose_due = (self._now() + timedelta(hours=8)).replace(second=0, microsecond=0)
        writebacks.append(
            self.writer.upsert_behavior_plan(
                plan_id="diabetes-next-glucose-log",
                scenario="diabetes-control-hub",
                title="补齐下一次血糖记录",
                cadence="daily",
                due_at=next_glucose_due.isoformat(timespec="minutes"),
                topic="blood-sugar",
                risk_policy="focus-closely",
                consequence="无法持续判断血糖改善是否停滞，也不利于复诊准备。",
                next_step="按空腹或餐后场景补录下一次血糖，并写上餐食/运动背景。",
            )
        )

        if any([meals_summary, exercise_summary, symptoms]):
            self.writer._upsert_daily_section(
                date_str,
                "Diabetes Copilot Notes",
                "diabetes-control-hub",
                [
                    f"Meals: {meals_summary or 'pending'}",
                    f"Exercise: {exercise_summary or 'pending'}",
                    f"Symptoms: {symptoms or 'pending'}",
                ],
            )
            writebacks.append(str(self.writer.daily_dir / f"{date_str}.md"))

        issues = self._filter_heartbeat({"blood-sugar", "weight", "medication", "appointments", "behavior-plan"})
        must_seek = []
        latest_glucose = glucose_entries[-1]["value"] if glucose_entries else None
        if latest_glucose is not None and float(latest_glucose) < 3.9:
            must_seek.append("当前血糖已低于 3.9 mmol/L，请立即按低血糖流程处理并视情况求助急救。")
        if latest_glucose is not None and float(latest_glucose) > 16.7 and symptoms:
            must_seek.append("高血糖合并明显症状时，需要警惕 DKA 或急性失代偿，建议尽快就医。")

        sugar_status = self._read_recent_status_lines("blood-sugar")
        weight_status = self._read_recent_status_lines("weight")
        follow_up_tasks = []
        follow_up_tasks.append(
            self.runtime.build_task(
                title="安排下一次血糖记录",
                reason=f"糖尿病场景已经为下一次血糖记录排好了 due time：{next_glucose_due.isoformat(timespec='minutes')}。",
                next_step="按空腹或餐后场景补录下一次血糖，并补上餐食/运动背景。",
                follow_up="到点后若仍未处理，会继续跟进。",
                priority="low",
                topic="behavior-plan",
                source_refs=[str(self.writer.behavior_plans_path)],
                dedupe_key="diabetes-next-glucose-task",
            )
        )
        if not glucose_entries:
            follow_up_tasks.append(
                self.runtime.build_task(
                    title="补录血糖记录",
                    reason="本次糖尿病场景没有新的血糖数据，趋势和风险判断会明显变弱。",
                    next_step="补录至少 1 次空腹或餐后血糖，并写上 context。",
                    follow_up="今天晚些时候再次检查是否已补录。",
                    priority="medium",
                    topic="blood-sugar",
                    source_refs=[str(self.writer.items_dir / "blood-sugar.md")],
                )
            )
        sections = {
            "## 记录": [
                *(sugar_status[:4] or ["当前还没有新的血糖读数。"]),
                *(weight_status[:2] or []),
                f"饮食摘要：{meals_summary or 'pending'}",
                f"运动摘要：{exercise_summary or 'pending'}",
                f"症状：{symptoms or 'pending'}",
            ],
            "## 解读": [
                "糖尿病场景优先输出纵向趋势、TIR/eHbA1c线索和复查准备，不直接给出剂量调整结论。",
                f"用药依从性口径：{adherence or 'pending'}",
            ],
            "## 趋势": sugar_status[1:5] or ["等待连续血糖记录形成更稳定趋势。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": [
                "优先把餐后高峰对应的餐食和运动背景补完整。",
                "如近期要复查，提前准备最近 1-2 周的连续血糖与体重摘要。",
                "关注 task board 中的行为计划和 follow-up 项目。",
            ],
            "## 必须就医": must_seek or ["当前没有触发必须就医级别信号，但如出现低血糖意识障碍、疑似 DKA 等情况应立即升级。"],
        }
        return self.runtime.persist_result(
            filename=f"diabetes-daily-{date_str}.md",
            title="Diabetes Control Hub",
            date_str=date_str,
            sections=sections,
            sources=[
                str(self.writer.items_dir / "blood-sugar.md"),
                str(self.writer.items_dir / "weight.md"),
                str(self.writer.items_dir / "appointments.md"),
            ],
            evidence=[
                "低血糖阈值：最近一次血糖 < 3.9 mmol/L。",
                "改善停滞阈值：21-day trend shows no meaningful improvement while mean remains elevated。",
            ],
            scenario="diabetes-control-hub",
            file_type="diabetes-control-hub",
            summary=f"{date_str} 糖尿病日常闭环摘要",
            alerts=[issue["title"] for issue in issues[:3]],
            follow_up_tasks=follow_up_tasks,
            writebacks=sorted(set(writebacks)),
            audit_reason="糖尿病日常闭环写回",
        )

    def weekly_review(self, week_of: str | None = None) -> dict:
        self.digest.generate(week_of=week_of)
        week_start, week_end = self.digest._get_week_range(week_of)
        issues = self._filter_heartbeat({"blood-sugar", "appointments", "medication"})
        sections = {
            "## 记录": [
                f"周报范围：{week_start} ~ {week_end}",
                f"已生成周报：{self.writer.weekly_digest_path}",
            ],
            "## 解读": ["本次会优先参考 weekly-digest、血糖 recent status 和复查计划。"],
            "## 趋势": self._read_recent_status_lines("blood-sugar")[:4] or ["等待更多周级连续数据。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": [
                "先阅读本周周报，再确认下周最需要盯紧的餐后高峰或执行障碍。",
                "如计划复查，提前准备连续血糖和体重摘要。",
            ],
            "## 必须就医": ["若本周已出现严重低血糖或明显急性恶化，请直接升级到急救/就医。"] if issues else ["本周未见新的必须就医级别结论。"],
        }
        follow_up_tasks = [
            self.runtime.build_task(
                title=f"阅读并确认糖尿病周报：{week_start}",
                reason="新的糖尿病周度复盘已生成，但还需要人工确认下周的重点。",
                next_step="打开 weekly-digest.md，确认最值得优先处理的波动模式。",
                follow_up="若明天仍未处理，会继续提醒。",
                priority="low",
                topic="weekly-digest",
                source_refs=[str(self.writer.weekly_digest_path)],
                dedupe_key=f"diabetes-weekly-review:{week_start}",
            )
        ]
        return self.runtime.persist_result(
            filename=f"diabetes-weekly-review-{week_start}.md",
            title="Diabetes Weekly Review",
            date_str=week_end,
            sections=sections,
            sources=[str(self.writer.weekly_digest_path), str(self.writer.items_dir / "blood-sugar.md")],
            evidence=["周报来源于 weekly-health-digest 聚合结果。"],
            scenario="diabetes-control-hub",
            file_type="diabetes-weekly-review",
            summary=f"{week_start} 糖尿病周度复盘",
            follow_up_tasks=follow_up_tasks,
            writebacks=[str(self.writer.weekly_digest_path)],
        )

    def checkup_review(self) -> dict:
        status = self._read_recent_status_lines("annual-checkup")
        issues = self._filter_heartbeat({"annual-checkup", "appointments"})
        sections = {
            "## 记录": status or ["当前还没有年度体检摘要。"],
            "## 解读": ["体检后的糖尿病复盘会优先关注 HbA1c、空腹血糖、肾功能和 follow-up 计划。"],
            "## 趋势": self._read_recent_status_lines("blood-sugar")[:4] or ["等待更多长期血糖摘要。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": [
                "把体检里与糖代谢、肾功能、血脂相关的异常项纳入下次复查计划。",
            ],
            "## 必须就医": ["若体检提示危急异常或症状明显恶化，应尽快联系医生。"],
        }
        return self.runtime.persist_result(
            filename=f"diabetes-checkup-review-{self._today()}.md",
            title="Diabetes Checkup Review",
            date_str=self._today(),
            sections=sections,
            sources=[str(self.writer.items_dir / "annual-checkup.md"), str(self.writer.items_dir / "blood-sugar.md")],
            evidence=["年度体检异常 follow-up 应回到复查和长期趋势上下文中判断。"],
            scenario="diabetes-control-hub",
            file_type="diabetes-checkup-review",
            summary=f"{self._today()} 糖尿病体检复盘",
            writebacks=[],
        )


class AnnualCheckupAdvisorWorkflow(_ScenarioBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.interpreter = CheckupReportInterpreter(
            memory_dir=str(self.writer.base_dir),
            now_fn=self._now_fn,
        )

    def import_report(
        self,
        items: list[dict] | None = None,
        items_json_path: str | None = None,
        pdf_path: str | None = None,
        report_date: str | None = None,
        previous_items: list[dict] | None = None,
        next_follow_up: str | None = None,
        next_follow_up_details: str | None = None,
    ) -> dict:
        date_str = report_date or self._today()
        writebacks: list[str] = []

        if items_json_path:
            items = json.loads(Path(items_json_path).read_text(encoding="utf-8"))
        if pdf_path and not items:
            self.interpreter.generate_report(pdf_path, previous_items=previous_items, report_date=date_str)
            source_name = Path(pdf_path).name
            items = []
        else:
            source_name = Path(pdf_path).name if pdf_path else "structured-checkup-input.json"
        prioritized = self.interpreter.prioritize(items or [])
        if prioritized:
            writebacks.extend(
                self.interpreter.persist_items_to_memory(
                    prioritized,
                    report_date=date_str,
                    report_path=pdf_path or source_name,
                )
            )
        high_items = [item for item in prioritized if item.get("priority") in {"critical", "high"}]
        moderate_items = [item for item in prioritized if item.get("priority") == "moderate"]

        latest_appointment = self._recent_status_pairs("appointments").get("latest appointment")
        self._schedule_follow_up(
            next_follow_up=next_follow_up,
            details=next_follow_up_details,
            purpose="年度体检异常项 follow-up",
            writebacks=writebacks,
            latest_appointment=latest_appointment,
        )

        next_annual = (datetime.fromisoformat(date_str) + timedelta(days=365)).date().isoformat()
        writebacks.append(
            self.writer.upsert_behavior_plan(
                plan_id=f"annual-checkup-{next_annual}",
                scenario="annual-checkup-advisor",
                title="准备下一次年度体检",
                cadence="annual",
                due_at=f"{next_annual}T09:00",
                topic="annual-checkup",
                risk_policy="normal",
                consequence="年度基线更新会断档，长期趋势难以连续对比。",
                next_step="在 reminder window 内完成预约、套餐确认和资料整理。",
            )
        )
        for item in high_items[:3]:
            due_days = 1 if item.get("priority") == "critical" else 7
            due_at = (datetime.fromisoformat(date_str) + timedelta(days=due_days)).replace(hour=9, minute=0)
            writebacks.append(
                self.writer.upsert_behavior_plan(
                    plan_id=f"checkup-followup-{item.get('item', 'unknown')}-{date_str}",
                    scenario="annual-checkup-advisor",
                    title=f"跟进体检异常：{item.get('item', 'unknown')}",
                    cadence="event",
                    due_at=due_at.isoformat(timespec="minutes"),
                    topic="annual-checkup",
                    risk_policy="focus-closely",
                    consequence="异常项若没有明确 follow-up，后续风险管理会断链。",
                    next_step=f"围绕 {item.get('item', 'unknown')} 确认复查或专科就诊安排。",
                )
            )

        issues = self._filter_heartbeat({"annual-checkup", "appointments", "behavior-plan"})
        must_seek = []
        for item in high_items:
            must_seek.append(
                f"{item.get('item', 'Unknown')} 被标记为 {item.get('priority_label', item.get('priority'))}，建议尽快和医生确认。"
            )
        abnormal_summary = []
        for item in high_items[:4] + moderate_items[:4]:
            abnormal_summary.append(
                f"{item.get('item', 'Unknown')}: {item.get('value', '')}{(' ' + str(item.get('unit', '')).strip()) if str(item.get('unit', '')).strip() else ''} [{item.get('priority_label', item.get('priority'))}]"
            )
        follow_up_tasks = []
        for item in high_items[:3]:
            follow_up_tasks.append(
                self.runtime.build_task(
                    title=f"确认体检异常 follow-up：{item.get('item', 'Unknown')}",
                    reason=f"{item.get('item', 'Unknown')} 在本次体检中被标记为 {item.get('priority_label', item.get('priority'))}。",
                    next_step=f"确认复查时间、科室或医生，并把安排写入 appointments.md。",
                    follow_up="若今天未确认，接下来几天继续跟进。",
                    priority="high" if item.get("priority") == "critical" else "medium",
                    topic="annual-checkup",
                    source_refs=[str(self.writer.items_dir / "annual-checkup.md")],
                    dedupe_key=f"checkup-followup-task:{item.get('item', 'unknown')}:{date_str}",
                    execution_mode="isolated-session" if item.get("priority") == "critical" else "heartbeat",
                )
            )

        sections = {
            "## 记录": [
                f"报告日期：{date_str}",
                f"数据来源：{source_name}",
                f"共识别 {len(prioritized)} 个项目",
                *(abnormal_summary[:5] or ["本次未解析到异常项目。"]),
            ],
            "## 解读": [
                "年度体检场景会把异常项、历史比较、follow-up 和下次年度基线更新串成一条连续链路。",
                "结论优先保留为风险分层和 follow-up 建议，不直接替代明确诊断。",
            ],
            "## 趋势": self._read_recent_status_lines("annual-checkup")[:4] or ["等待更多年度体检历史形成纵向趋势。"],
            "## 风险": self._format_issue_lines(issues) or abnormal_summary[:4],
            "## 建议": [
                "优先处理高优先级异常项，并把复查/就诊安排写入 appointments.md。",
                "如果下次要就诊，提前生成门诊 briefing 并带上年度对比材料。",
                "把持续异常项纳入长期 behavior plans，避免只看一次报告。",
            ],
            "## 必须就医": must_seek or ["当前没有触发体检红灯的必须就医项，但异常项仍应按优先级安排 follow-up。"],
        }
        return self.runtime.persist_result(
            filename=f"annual-checkup-advisor-{date_str}.md",
            title="Annual Checkup Advisor",
            date_str=date_str,
            sections=sections,
            sources=[
                pdf_path or source_name,
                str(self.writer.items_dir / "annual-checkup.md"),
                str(self.writer.items_dir / "appointments.md"),
            ],
            evidence=[
                "体检高优先级 follow-up 由 checkup-report-interpreter 的 priority 规则驱动。",
                "年度体检提醒窗口依据 annual-checkup.md 的 Next annual checkup / Reminder window days。",
            ],
            scenario="annual-checkup-advisor",
            file_type="annual-checkup-advisor",
            summary=f"{date_str} 年度体检导入与 follow-up 摘要",
            alerts=[item.get("item", "Unknown") for item in high_items[:3]],
            follow_up_tasks=follow_up_tasks,
            writebacks=sorted(set(writebacks)),
            audit_reason="年度体检导入与 follow-up 写回",
        )

    def follow_up_review(self) -> dict:
        issues = self._filter_heartbeat({"annual-checkup", "appointments"})
        sections = {
            "## 记录": self._read_recent_status_lines("annual-checkup")[:5] or ["当前还没有年度体检摘要。"],
            "## 解读": ["这里聚焦年度体检后的 follow-up、预约准备和异常项闭环。"],
            "## 趋势": self._read_recent_status_lines("appointments")[:4] or ["等待更多 follow-up 记录。"],
            "## 风险": self._format_issue_lines(issues),
            "## 建议": ["优先关闭最靠近 due date 的体检 follow-up 事项。"],
            "## 必须就医": ["若体检异常已被标记为 critical，请优先按医生路径尽快处理。"] if issues else ["当前没有新的必须就医级别结论。"],
        }
        return self.runtime.persist_result(
            filename=f"annual-checkup-followup-{self._today()}.md",
            title="Annual Checkup Follow-up Review",
            date_str=self._today(),
            sections=sections,
            sources=[str(self.writer.items_dir / "annual-checkup.md"), str(self.writer.items_dir / "appointments.md")],
            evidence=["体检 follow-up 依据异常项优先级和 appointments.md 的计划状态。"],
            scenario="annual-checkup-advisor",
            file_type="annual-checkup-followup-review",
            summary=f"{self._today()} 年度体检 follow-up 复盘",
            writebacks=[],
        )
