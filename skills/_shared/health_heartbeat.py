#!/usr/bin/env python3
"""Lightweight proactive health heartbeat checks for VitaClaw."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from cross_skill_reader import CrossSkillReader
from health_data_store import HealthDataStore
from health_memory import HealthMemoryWriter
from health_reminder_center import HealthReminderCenter
from patient_archive_bridge import PatientArchiveBridge


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_LABEL = {"high": "高优先级", "medium": "中优先级", "low": "低优先级"}


def _resolve_reader_data_dir(
    data_dir: str | None,
    memory_dir: str | None,
    workspace_root: str | None,
) -> str | None:
    if data_dir:
        return str(Path(data_dir).expanduser().resolve())
    if workspace_root:
        return str((Path(workspace_root).expanduser().resolve() / "data"))
    if memory_dir:
        memory_path = Path(memory_dir).expanduser().resolve()
        if memory_path.name == "health" and memory_path.parent.name == "memory":
            return str(memory_path.parent.parent / "data")
        return str(memory_path / "_skill-data")
    return None


class HealthHeartbeat:
    """Run lightweight health maintenance checks and produce reminders."""

    METRICS = {
        "blood_pressure": {
            "label": "血压",
            "titles": {"Blood Pressure", "血压"},
        },
        "blood_sugar": {
            "label": "血糖",
            "titles": {"Blood Sugar", "血糖"},
        },
        "weight": {
            "label": "体重",
            "titles": {"Weight", "体重"},
        },
        "sleep": {
            "label": "睡眠",
            "titles": {"Sleep", "睡眠"},
        },
        "supplements": {
            "label": "补剂",
            "titles": {"Supplements", "补剂"},
        },
        "medication": {
            "label": "用药",
            "titles": {"Medication", "用药"},
        },
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
        self.reader = CrossSkillReader(
            data_dir=_resolve_reader_data_dir(
                data_dir=data_dir,
                memory_dir=memory_dir,
                workspace_root=workspace_root,
            )
        )
        self.memory_writer = HealthMemoryWriter(
            memory_root=memory_dir,
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
        self.reminder_center = HealthReminderCenter(
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )
        self.weekly_store = HealthDataStore("weekly-health-digest", data_dir=data_dir)

    def _now(self) -> datetime:
        return self._now_fn()

    def _today(self) -> str:
        return self._now().date().isoformat()

    def _date_str(self, days_ago: int) -> str:
        return (self._now().date() - timedelta(days=days_ago)).isoformat()

    def _daily_path(self, date_str: str) -> Path:
        return self.memory_writer.daily_dir / f"{date_str}.md"

    def _daily_sections(self, date_str: str) -> set[str]:
        path = self._daily_path(date_str)
        if not path.exists():
            return set()
        sections = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^##\s+(.+?)\s+\[", line.strip())
            if match:
                sections.add(match.group(1))
        return sections

    def _item_path(self, slug: str) -> Path:
        return self.memory_writer.items_dir / f"{slug}.md"

    def _read_recent_status(self, slug: str) -> dict[str, str]:
        path = self._item_path(slug)
        if not path.exists():
            return {}

        status = {}
        in_section = False
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "## Recent Status":
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.startswith("- ") and ":" in line:
                key, value = line[2:].split(":", 1)
                status[key.strip().lower()] = value.strip()
        return status

    def _item_has_history_rows(self, slug: str) -> bool:
        path = self._item_path(slug)
        if not path.exists():
            return False

        in_history = False
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "## History":
                in_history = True
                continue
            if in_history and line.startswith("## "):
                break
            if not in_history or not line.startswith("|"):
                continue

            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not cells or cells[0] == "Date" or set(cells[0]) == {"-"}:
                continue
            if any(cell and cell.lower() != "pending" for cell in cells):
                return True
        return False

    def _item_has_data(self, slug: str) -> bool:
        status = self._read_recent_status(slug)
        if any(value and value.lower() != "pending" for value in status.values()):
            return True
        return self._item_has_history_rows(slug)

    def _extract_iso_date(self, text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        return match.group(1) if match else None

    def _extract_int(self, text: str | None) -> int | None:
        if not text:
            return None
        match = re.search(r"(-?\d+)", text)
        return int(match.group(1)) if match else None

    def _parse_iso_datetime(self, text: str | None) -> datetime | None:
        if not text:
            return None
        value = text.strip()
        if not value:
            return None
        try:
            if len(value) == 10 and value.count("-") == 2:
                return datetime.fromisoformat(f"{value}T00:00:00")
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _metric_is_tracked(self, metric_key: str) -> bool:
        item_slug = metric_key.replace("_", "-")
        item_has_data = self._item_has_data(item_slug)
        if metric_key == "blood_pressure":
            return (
                item_has_data
                or bool(self.reader.read_blood_pressure())
                or bool(self.reader.read_chronic_blood_pressure())
            )
        if metric_key == "blood_sugar":
            return item_has_data or bool(self.reader.read_glucose_data())
        if metric_key == "weight":
            return item_has_data or bool(self.reader.read_weight_data())
        if metric_key == "sleep":
            return item_has_data or bool(self.reader.read_sleep_data())
        if metric_key == "supplements":
            return item_has_data or bool(self.reader.read_supplement_doses())
        if metric_key == "medication":
            return item_has_data or bool(self.reader.read_medication_doses())
        return item_has_data

    def _tracked_metrics(self) -> dict[str, dict]:
        return {
            key: meta
            for key, meta in self.METRICS.items()
            if self._metric_is_tracked(key)
        }

    def _metric_missing_on(self, metric_key: str, date_str: str) -> bool:
        sections = self._daily_sections(date_str)
        titles = self.METRICS[metric_key]["titles"]
        return not any(title in sections for title in titles)

    def _missing_streak(self, metric_key: str, days: int = 3) -> int:
        streak = 0
        for offset in range(days):
            if self._metric_missing_on(metric_key, self._date_str(offset)):
                streak += 1
            else:
                break
        return streak

    def _bp_records(self, days: int = 14) -> list[dict]:
        start = f"{self._date_str(days - 1)}T00:00:00"
        records = self.reader.read_blood_pressure(start=start)
        records.extend(self.reader.read_chronic_blood_pressure(start=start))
        records.sort(key=lambda item: item.get("timestamp", ""))
        return records

    def _glucose_records(self, days: int = 30) -> list[dict]:
        start = f"{self._date_str(days - 1)}T00:00:00"
        records = self.reader.read_glucose_data(start=start)
        records.sort(key=lambda item: item.get("timestamp", ""))
        return records

    def _issues_missing_records(self) -> list[dict]:
        issues = []
        for metric_key, meta in self._tracked_metrics().items():
            if not self._metric_missing_on(metric_key, self._today()):
                continue
            streak = self._missing_streak(metric_key, days=3)
            priority = "medium" if streak >= 3 else "low"
            issues.append(
                {
                    "priority": priority,
                    "title": f"{meta['label']}记录缺失",
                    "reason": f"今天的健康日记里还没有 {meta['label']} 记录。"
                    if streak < 3
                    else f"{meta['label']} 已连续 {streak} 天没有写入健康日记。",
                    "next_step": f"今天补录一次 {meta['label']}，并补充症状、诱因或执行情况。",
                    "follow_up": "今天晚些时候再次检查是否已补录。",
                }
            )
        return issues

    def _issues_bp_risk(self) -> list[dict]:
        issues = []
        records = self._bp_records()
        if not records:
            return issues

        latest = records[-1]
        latest_data = latest.get("data", {})
        sys_val = float(latest_data.get("sys") or latest_data.get("systolic") or 0)
        dia_val = float(latest_data.get("dia") or latest_data.get("diastolic") or 0)
        timestamp = latest.get("timestamp", "")[:16].replace("T", " ")
        if sys_val >= 180 or dia_val >= 120:
            issues.append(
                {
                    "priority": "high",
                    "title": "血压危急值",
                    "reason": f"最近一次血压为 {int(sys_val)}/{int(dia_val)} mmHg ({timestamp})，已达到危急范围。",
                    "next_step": "不要继续常规自我管理建议，建议立即联系急救或尽快就医。",
                    "follow_up": "立刻处理，不等待下一次 heartbeat。",
                }
            )
            return issues

        recent = records[-3:]
        if len(recent) == 3 and all(
            (float(r.get("data", {}).get("sys") or r.get("data", {}).get("systolic") or 0) >= 140)
            or (float(r.get("data", {}).get("dia") or r.get("data", {}).get("diastolic") or 0) >= 90)
            for r in recent
        ):
            issues.append(
                {
                    "priority": "high",
                    "title": "血压连续偏高",
                    "reason": f"最近 3 次血压均高于 140/90，最新为 {int(sys_val)}/{int(dia_val)} mmHg。",
                    "next_step": "尽快复盘测量时段、症状、漏服药或诱因，并准备医生可读的连续记录。",
                    "follow_up": "今天内补充上下文；若伴胸痛、头痛、视物异常等症状，尽快就医。",
                }
            )
        return issues

    def _issues_glucose_risk(self) -> list[dict]:
        issues = []
        records = self._glucose_records()
        if not records:
            return issues

        latest = records[-1]
        latest_value = float(latest.get("data", {}).get("value") or 0)
        context = str(latest.get("data", {}).get("context", "") or "")
        timestamp = latest.get("timestamp", "")[:16].replace("T", " ")

        if latest_value < 3.9:
            issues.append(
                {
                    "priority": "high",
                    "title": "低血糖风险",
                    "reason": f"最近一次血糖为 {latest_value} mmol/L ({timestamp}, {context})，低于 3.9。",
                    "next_step": "立即按低血糖处理流程补充快速糖，并结合症状决定是否寻求急救帮助。",
                    "follow_up": "15 分钟内复测，必要时尽快联系医生。",
                }
            )
            return issues

        fasting_records = [
            record for record in records if "fast" in str(record.get("data", {}).get("context", "")).lower() or "空腹" in str(record.get("data", {}).get("context", ""))
        ]
        if len(fasting_records) >= 3 and all(float(record.get("data", {}).get("value") or 0) > 7.0 for record in fasting_records[-3:]):
            issues.append(
                {
                    "priority": "medium",
                    "title": "空腹血糖连续偏高",
                    "reason": "最近 3 次空腹血糖都高于 7.0 mmol/L。",
                    "next_step": "复盘晚餐、夜宵、运动和用药执行，并准备近期血糖摘要。",
                    "follow_up": "1-2 天内继续补测并结合医生建议调整计划。",
                }
            )

        if "post" in context.lower() or "餐后" in context:
            if latest_value > 10.0:
                issues.append(
                    {
                        "priority": "medium",
                        "title": "餐后血糖偏高",
                        "reason": f"最近一次餐后血糖为 {latest_value} mmol/L ({timestamp})，高于常见目标。",
                        "next_step": "补充这餐的食物、份量和运动情况，便于后续分析诱因。",
                        "follow_up": "下次类似餐食时继续记录，观察是否重复出现。",
                    }
                )
        return issues

    def _issues_adherence(self) -> list[dict]:
        issues = []
        start = f"{self._date_str(6)}T00:00:00"
        supplement_records = self.reader.read_supplement_doses(start=start)
        if supplement_records:
            total = len(supplement_records)
            taken = sum(1 for record in supplement_records if record.get("data", {}).get("taken", True))
            pct = round(100 * taken / total, 1) if total else 0
            if total >= 3 and pct < 80:
                issues.append(
                    {
                        "priority": "medium",
                        "title": "补剂依从率下降",
                        "reason": f"最近 7 天补剂依从率只有 {pct}%。",
                        "next_step": "优先找出最常漏掉的时段或补剂，并把执行绑定到固定生活动作。",
                        "follow_up": "本周内再次观察依从率是否回升。",
                    }
                )

        medication_records = self.reader.read_medication_doses(start=start)
        if medication_records:
            total = len(medication_records)
            taken = sum(1 for record in medication_records if record.get("data", {}).get("taken", True))
            pct = round(100 * taken / total, 1) if total else 0
            if total >= 3 and pct < 90:
                issues.append(
                    {
                        "priority": "high",
                        "title": "用药依从率下降",
                        "reason": f"最近 7 天用药依从率为 {pct}%，低于更稳妥的目标。",
                        "next_step": "尽快确认是否漏服、断药或时间混乱，并补记原因。",
                        "follow_up": "今天内确认后续 3 天的用药安排。",
                    }
                )
        return issues

    def _issues_weekly_digest(self) -> list[dict]:
        issues = []
        week_start = (self._now().date() - timedelta(days=self._now().weekday())).isoformat()
        previous_week_start = (self._now().date() - timedelta(days=self._now().weekday() + 7)).isoformat()
        digest_records = self.weekly_store.query("digest")
        current_exists = any(record.get("data", {}).get("week_start") == week_start for record in digest_records)
        previous_exists = any(record.get("data", {}).get("week_start") == previous_week_start for record in digest_records)

        if self._now().weekday() >= 6 and not current_exists:
            issues.append(
                {
                    "priority": "low",
                    "title": "本周周报待生成",
                    "reason": "已经接近本周结束，但本周健康周报还没有生成。",
                    "next_step": "运行 weekly-health-digest，生成本周趋势、亮点和问题摘要。",
                    "follow_up": "今天内完成周报，便于下周继续追踪。",
                }
            )

        if self._now().weekday() <= 2 and not previous_exists:
            issues.append(
                {
                    "priority": "medium",
                    "title": "上周周报缺失",
                    "reason": "上周的健康周报还没有沉淀，连续性复盘会断档。",
                    "next_step": "补生成上一周周报，避免长期趋势链条中断。",
                    "follow_up": "本周前半段补齐即可。",
                }
            )
        return issues

    def _issues_monthly_digest(self) -> list[dict]:
        issues = []
        today = self._now().date()
        current_month = today.strftime("%Y-%m")
        previous_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        digest_records = self.weekly_store.query("monthly_digest")
        current_exists = any(record.get("data", {}).get("month") == current_month for record in digest_records)
        previous_exists = any(record.get("data", {}).get("month") == previous_month for record in digest_records)

        if today.day >= 28 and not current_exists:
            issues.append(
                {
                    "priority": "low",
                    "title": "本月月报待生成",
                    "reason": f"{current_month} 已接近月底，但本月月报还没有生成。",
                    "next_step": "运行 weekly-health-digest generate-monthly，沉淀本月趋势、风险和下月重点。",
                    "follow_up": "月底前完成月报，便于下一轮长期复盘。",
                }
            )

        if today.day <= 5 and not previous_exists:
            issues.append(
                {
                    "priority": "medium",
                    "title": "上月月报缺失",
                    "reason": f"{previous_month} 的月报尚未沉淀，月度复盘链条出现断档。",
                    "next_step": "补生成上月月报，便于保留完整月度趋势。",
                    "follow_up": "本月前 5 天内补齐即可。",
                }
            )
        return issues

    def _issues_memory_distillation(self) -> list[dict]:
        issues = []
        last_distilled = self.memory_writer.last_memory_distilled_at()

        latest_daily = None
        daily_files = sorted(self.memory_writer.daily_dir.glob("*.md"))
        if daily_files:
            latest_daily = datetime.strptime(daily_files[-1].stem, "%Y-%m-%d")

        if not latest_daily:
            return issues

        if last_distilled is None:
            issues.append(
                {
                    "priority": "low",
                    "title": "长期画像尚未蒸馏",
                    "reason": "daily 和 items 已经开始积累，但 `MEMORY.md` 里还没有最近健康运营摘要。",
                    "next_step": "运行 distill-health-memory，把近期趋势、断点和重点任务写回 `MEMORY.md`。",
                    "follow_up": "本周内完成第一次蒸馏即可。",
                }
            )
            return issues

        if latest_daily.date() > last_distilled.date():
            delta_days = (latest_daily.date() - last_distilled.date()).days
            issues.append(
                {
                    "priority": "medium" if delta_days >= 7 else "low",
                    "title": "长期画像需要更新",
                    "reason": f"`MEMORY.md` 最近一次蒸馏停留在 {last_distilled.date().isoformat()}，而 daily 已更新到 {latest_daily.date().isoformat()}。",
                    "next_step": "运行 distill-health-memory，把最近趋势和待办沉淀回长期画像。",
                    "follow_up": "本轮周报或月报后同步完成，避免长期画像滞后。",
                }
            )
        return issues

    def _issues_behavior_plans(self) -> list[dict]:
        issues = []
        rows = self.memory_writer.list_behavior_plans(statuses={"active", "in_progress", "blocked"})
        if not rows:
            return issues

        now = self._now()
        for row in rows:
            due_text = row.get("Due At")
            due_at = self._parse_iso_datetime(due_text)
            title = row.get("Title") or "未命名行为计划"
            topic = row.get("Topic") or "behavior-plan"
            risk_policy = row.get("Risk Policy") or "normal"
            next_step = row.get("Next Step") or "尽快更新计划状态或补充执行记录。"
            consequence = row.get("If Ignored") or "执行闭环会中断，后续趋势判断会变弱。"
            status = row.get("Status") or "active"
            reason_prefix = f"{row.get('Scenario', 'health')} 的行为计划“{title}”"

            if status == "blocked":
                issues.append(
                    {
                        "priority": "medium" if risk_policy != "high-risk-only" else "high",
                        "title": f"行为计划受阻：{title}",
                        "reason": f"{reason_prefix} 当前被标记为 blocked。{consequence}",
                        "next_step": next_step,
                        "follow_up": "今天内确认阻塞原因，并决定是继续、拆小还是调整节奏。",
                        "topic": "behavior-plan",
                        "category": "behavior-plan",
                        "source_refs": [str(self.memory_writer.behavior_plans_path)],
                        "threshold": f"Status = blocked | Topic = {topic}",
                        "execution_mode": "heartbeat",
                    }
                )
                continue

            if due_at is None:
                continue
            delta_minutes = int((due_at - now).total_seconds() // 60)
            if delta_minutes < 0:
                priority = "high" if risk_policy in {"focus-closely", "high-risk-only"} or abs(delta_minutes) >= 24 * 60 else "medium"
                issues.append(
                    {
                        "priority": priority,
                        "title": f"行为计划已到期：{title}",
                        "reason": f"{reason_prefix} 原定于 {due_text} 执行，但目前仍未完成。{consequence}",
                        "next_step": next_step,
                        "follow_up": "若今天仍未处理，会继续跟进并可能转成执行障碍。",
                        "topic": "behavior-plan",
                        "category": "behavior-plan",
                        "source_refs": [str(self.memory_writer.behavior_plans_path)],
                        "threshold": f"Due At < now ({due_text})",
                        "execution_mode": "heartbeat",
                    }
                )
            elif delta_minutes <= 60:
                issues.append(
                    {
                        "priority": "medium" if risk_policy != "high-risk-only" else "high",
                        "title": f"行为计划即将到点：{title}",
                        "reason": f"{reason_prefix} 将在 {due_text} 到点，需要按计划执行。若忽略：{consequence}",
                        "next_step": next_step,
                        "follow_up": "到点后若仍未处理，会自动继续跟进。",
                        "topic": "behavior-plan",
                        "category": "behavior-plan",
                        "source_refs": [str(self.memory_writer.behavior_plans_path)],
                        "threshold": f"Due At <= 60 min ({due_text})",
                        "execution_mode": "heartbeat",
                    }
                )
            elif delta_minutes <= 24 * 60 and risk_policy in {"focus-closely", "high-risk-only"}:
                issues.append(
                    {
                        "priority": "low",
                        "title": f"行为计划临近窗口：{title}",
                        "reason": f"{reason_prefix} 将在 24 小时内到点，属于需要重点盯紧的主题。",
                        "next_step": next_step,
                        "follow_up": "若今天未处理，我会在更接近 due time 时再次提醒。",
                        "topic": "behavior-plan",
                        "category": "behavior-plan",
                        "source_refs": [str(self.memory_writer.behavior_plans_path)],
                        "threshold": f"Due At <= 24h ({due_text})",
                        "execution_mode": "heartbeat",
                    }
                )
        return issues

    def _issues_execution_barriers(self) -> list[dict]:
        issues = []
        for row in self.memory_writer.latest_execution_barriers(limit=4):
            date_text = row.get("Date")
            date_obj = self._parse_iso_datetime(date_text)
            if not date_obj:
                continue
            days_ago = (self._now().date() - date_obj.date()).days
            if days_ago > 14:
                continue
            issues.append(
                {
                    "priority": "medium",
                    "title": f"执行障碍待处理：{row.get('Barrier', '未命名障碍')}",
                    "reason": f"{row.get('Scenario', 'health')} 最近记录到执行障碍：{row.get('Impact', '影响待补充')}。",
                    "next_step": row.get("Next Step") or "先把障碍拆小，再确认下一次最小可执行动作。",
                    "follow_up": "若持续反复出现，建议升级到长期画像中的执行障碍画像。",
                    "topic": "execution-barrier",
                    "category": "behavior-plan",
                    "source_refs": [str(self.memory_writer.execution_barriers_path)],
                    "threshold": row.get("Pattern") or "Barrier recorded within 14 days",
                    "execution_mode": "heartbeat",
                }
            )
        return issues

    def _issues_stalled_improvement(self) -> list[dict]:
        issues = []

        bp_records = self._bp_records(days=14)
        if len(bp_records) >= 6:
            values = [
                (
                    float(record.get("data", {}).get("sys") or record.get("data", {}).get("systolic") or 0),
                    float(record.get("data", {}).get("dia") or record.get("data", {}).get("diastolic") or 0),
                )
                for record in bp_records
            ]
            midpoint = len(values) // 2
            first_avg_sys = sum(sys for sys, _ in values[:midpoint]) / midpoint
            second_avg_sys = sum(sys for sys, _ in values[midpoint:]) / max(1, len(values) - midpoint)
            first_avg_dia = sum(dia for _, dia in values[:midpoint]) / midpoint
            second_avg_dia = sum(dia for _, dia in values[midpoint:]) / max(1, len(values) - midpoint)
            if second_avg_sys >= 135 and second_avg_dia >= 85 and second_avg_sys >= first_avg_sys - 2:
                issues.append(
                    {
                        "priority": "medium",
                        "title": "血压改善停滞",
                        "reason": f"最近 14 天后半段平均血压约为 {round(second_avg_sys,1)}/{round(second_avg_dia,1)} mmHg，较前半段没有明显下降。",
                        "next_step": "复盘近期饮食、运动、睡眠和用药执行，并确认下一次复诊/复查安排。",
                        "follow_up": "如果再持续 1 周没有改善，建议把连续记录整理给医生确认。",
                        "topic": "blood-pressure",
                        "category": "daily-monitoring",
                        "source_refs": [str(self.memory_writer.items_dir / "blood-pressure.md")],
                        "threshold": "14-day trend shows no meaningful improvement while average remains elevated",
                        "execution_mode": "heartbeat",
                    }
                )

        glucose_records = self._glucose_records(days=21)
        if len(glucose_records) >= 6:
            values = [float(record.get("data", {}).get("value") or 0) for record in glucose_records]
            midpoint = len(values) // 2
            first_avg = sum(values[:midpoint]) / midpoint
            second_avg = sum(values[midpoint:]) / max(1, len(values) - midpoint)
            if second_avg >= 7.5 and second_avg >= first_avg - 0.3:
                issues.append(
                    {
                        "priority": "medium",
                        "title": "血糖改善停滞",
                        "reason": f"最近 21 天后半段平均血糖约为 {round(second_avg,1)} mmol/L，较前半段没有明显改善。",
                        "next_step": "复盘餐后峰值、饮食结构、运动和监测频率，并准备下一次复查摘要。",
                        "follow_up": "若继续停滞，建议结合医生意见重新评估方案。",
                        "topic": "blood-sugar",
                        "category": "daily-monitoring",
                        "source_refs": [str(self.memory_writer.items_dir / "blood-sugar.md")],
                        "threshold": "21-day trend shows no meaningful improvement while mean remains elevated",
                        "execution_mode": "heartbeat",
                    }
                )
        return issues

    def _issues_patient_archive(self) -> list[dict]:
        issues = []
        if not self.archive_bridge.is_available():
            return issues

        pending = self.archive_bridge.unclassified_files()
        if pending:
            priority = "high" if len(pending) >= 5 else "medium"
            sample = "、".join(path.name for path in pending[:3])
            issues.append(
                {
                    "priority": priority,
                    "title": "待整理病历",
                    "reason": f"患者档案里还有 {len(pending)} 份未分类原始文件待整理。示例：{sample}。",
                    "next_step": "优先把未分类文件归档进 medical-record-organizer，并补充摘要与时间线。",
                    "follow_up": "本周内至少清空一批未分类文件，避免病历资料继续堆积。",
                }
            )

        if self.archive_bridge.needs_sync():
            latest_date = self.archive_bridge.latest_timeline_date()
            latest_hint = f"最近事件日期为 {latest_date}。" if latest_date else "归档索引有更新。"
            issues.append(
                {
                    "priority": "low" if not pending else "medium",
                    "title": "病历归档有新更新待同步",
                    "reason": f"medical-record-organizer 侧有新内容，但健康工作区摘要尚未刷新。{latest_hint}",
                    "next_step": "运行 sync-patient-archive，把 INDEX / timeline / Apple Health 摘要同步到 memory/health/files。",
                    "follow_up": "下次周报或月报前同步一次，保持病历和健康工作区同频。",
                }
            )
        return issues

    def _issues_due_schedule(self) -> list[dict]:
        issues = []
        today = self._now().date()

        appointment_status = self._read_recent_status("appointments")
        follow_up_date = self._extract_iso_date(
            appointment_status.get("next follow-up")
            or appointment_status.get("next recheck")
            or appointment_status.get("next appointment")
        )
        follow_up_details = (
            appointment_status.get("next follow-up details")
            or appointment_status.get("preparation status")
            or "建议补充具体复查项目和准备事项"
        )
        if follow_up_date:
            days_until = (datetime.strptime(follow_up_date, "%Y-%m-%d").date() - today).days
            if days_until < 0:
                issues.append(
                    {
                        "priority": "high",
                        "title": "复查/复诊已逾期",
                        "reason": f"原定 {follow_up_date} 的复查/复诊节点还未完成，已经逾期 {abs(days_until)} 天。",
                        "next_step": f"尽快确认是否已完成或重新预约，并更新 appointments.md。当前备注：{follow_up_details}。",
                        "follow_up": "今天内更新安排；若继续延后，升级为更强提醒。",
                    }
                )
            elif days_until <= 3:
                issues.append(
                    {
                        "priority": "medium",
                        "title": "复查/复诊即将到期",
                        "reason": f"下一个复查/复诊节点在 {follow_up_date}，距离现在还有 {days_until} 天。",
                        "next_step": f"确认预约、检查单、陪诊或准备事项。当前备注：{follow_up_details}。",
                        "follow_up": "到期前 1 天再次检查是否准备完成。",
                    }
                )
            briefing_path = self.memory_writer.files_dir / f"visit-briefing-{follow_up_date}.md"
            if days_until <= 3 and not briefing_path.exists():
                issues.append(
                    {
                        "priority": "medium" if days_until >= 0 else "high",
                        "title": "门诊前 briefing 待生成",
                        "reason": f"下一个复查/复诊节点在 {follow_up_date}，但门诊前摘要还没有生成。",
                        "next_step": "运行 generate_visit_briefing.py，整理近期指标、风险、时间轴和要问医生的问题。",
                        "follow_up": "若今天未生成，明天继续跟进，直到门诊前材料齐备。",
                    }
                )

        latest_appointment_date = self._extract_iso_date(appointment_status.get("latest appointment"))
        if latest_appointment_date:
            days_since_latest = (today - datetime.strptime(latest_appointment_date, "%Y-%m-%d").date()).days
            followup_path = self.memory_writer.files_dir / f"visit-follow-up-{latest_appointment_date}.md"
            if 0 <= days_since_latest <= 3 and not followup_path.exists():
                issues.append(
                    {
                        "priority": "medium",
                        "title": "门诊后 follow-up 待记录",
                        "reason": f"{latest_appointment_date} 的最近一次门诊已经发生，但 follow-up 文档尚未落地。",
                        "next_step": "运行 record_visit_followup.py，把医生建议、下次复查和执行待办写回 appointments 与 daily。",
                        "follow_up": "今天内记录最好；若仍未处理，明天继续提醒。",
                    }
                )

        medication_status = self._read_recent_status("medications")
        refill_date = self._extract_iso_date(medication_status.get("next refill"))
        coverage_days = self._extract_int(medication_status.get("stock coverage days"))
        refill_context = medication_status.get("latest") or medication_status.get("risks") or "请确认主要长期用药库存"

        if refill_date:
            days_until = (datetime.strptime(refill_date, "%Y-%m-%d").date() - today).days
            if days_until < 0:
                issues.append(
                    {
                        "priority": "high",
                        "title": "药物续配已逾期",
                        "reason": f"药物续配日期 {refill_date} 已经过期 {abs(days_until)} 天。",
                        "next_step": f"立即核对库存、处方和取药渠道，避免断药。当前备注：{refill_context}。",
                        "follow_up": "今天内确认新的续药安排。",
                    }
                )
            elif days_until <= 7:
                issues.append(
                    {
                        "priority": "medium" if days_until <= 3 else "low",
                        "title": "药物续配即将到期",
                        "reason": f"药物续配日期为 {refill_date}，距离现在还有 {days_until} 天。",
                        "next_step": f"提前确认余量、处方和取药计划。当前备注：{refill_context}。",
                        "follow_up": "若今天未处理，明后天继续跟进。",
                    }
                )

        if coverage_days is not None and coverage_days <= 7:
            issues.append(
                {
                    "priority": "high" if coverage_days <= 3 else "medium",
                    "title": "药物库存偏低",
                    "reason": f"当前药物库存预计只够 {coverage_days} 天，接近断药风险。",
                    "next_step": "尽快补齐库存天数，并在 medications.md 更新 Next refill / Stock coverage days。",
                    "follow_up": "库存恢复到安全区后自动静默。",
                }
            )
        return issues

    def _issues_annual_checkup(self) -> list[dict]:
        issues = []
        today = self._now().date()
        status = self._read_recent_status("annual-checkup")
        next_checkup = self._extract_iso_date(status.get("next annual checkup"))
        reminder_window = self._extract_int(status.get("reminder window days")) or 30
        latest = status.get("latest annual checkup") or "pending"
        preparation = status.get("preparation status") or "建议确认体检套餐、项目和预约时间"

        if not next_checkup:
            return issues

        days_until = (datetime.strptime(next_checkup, "%Y-%m-%d").date() - today).days
        if days_until < 0:
            issues.append(
                {
                    "priority": "medium" if abs(days_until) < 30 else "high",
                    "title": "年度体检已逾期",
                    "reason": f"年度体检原定于 {next_checkup}，目前已逾期 {abs(days_until)} 天。",
                    "next_step": f"尽快确认是否已经完成体检或重新预约，并更新 annual-checkup.md。最近记录：{latest}。",
                    "follow_up": "若今天未处理，接下来几天继续跟进，直到重新确定时间。",
                }
            )
        elif days_until <= reminder_window:
            issues.append(
                {
                    "priority": "low" if days_until > 7 else "medium",
                    "title": "年度体检即将到期",
                    "reason": f"下一次年度体检日期为 {next_checkup}，距离现在还有 {days_until} 天。",
                    "next_step": f"确认预约、套餐、空腹要求和要携带的历史资料。当前准备状态：{preparation}。",
                    "follow_up": "若今天未处理，我会在后续窗口继续提醒，避免错过年度基线更新。",
                }
            )
        return issues

    def _infer_topic(self, issue: dict) -> str:
        text = f"{issue.get('title', '')} {issue.get('reason', '')}".lower()
        mapping = (
            ("血压", "blood-pressure"),
            ("blood pressure", "blood-pressure"),
            ("血糖", "blood-sugar"),
            ("glucose", "blood-sugar"),
            ("weight", "weight"),
            ("体重", "weight"),
            ("sleep", "sleep"),
            ("睡眠", "sleep"),
            ("supplement", "supplements"),
            ("补剂", "supplements"),
            ("medication", "medication"),
            ("用药", "medication"),
            ("续配", "medication"),
            ("appointments", "appointments"),
            ("复查", "appointments"),
            ("复诊", "appointments"),
            ("annual checkup", "annual-checkup"),
            ("体检", "annual-checkup"),
            ("行为计划", "behavior-plan"),
            ("execution barrier", "execution-barrier"),
            ("执行障碍", "execution-barrier"),
            ("周报", "weekly-digest"),
            ("月报", "monthly-digest"),
            ("长期画像", "memory-distillation"),
            ("病历", "patient-archive"),
            ("archive", "patient-archive"),
        )
        for keyword, topic in mapping:
            if keyword in text:
                return topic
        return "general"

    def _infer_trigger(self, issue: dict) -> str:
        text = f"{issue.get('title', '')} {issue.get('reason', '')}"
        if "缺失" in text:
            return "missing"
        if any(keyword in text for keyword in ("到期", "逾期", "月底", "周报", "月报")):
            return "time"
        if any(keyword in text for keyword in ("偏高", "危急", "风险", "下降")):
            return "state"
        if any(keyword in text for keyword in ("病历", "Apple Health", "归档")):
            return "event"
        return "event"

    def _infer_category(self, issue: dict) -> str:
        topic = issue.get("topic") or self._infer_topic(issue)
        if topic in {"blood-pressure", "blood-sugar", "weight", "sleep"}:
            return "daily-monitoring"
        if topic in {"medication", "supplements"}:
            return "adherence"
        if topic in {"appointments"}:
            return "follow-up"
        if topic in {"annual-checkup"}:
            return "preventive-care"
        if topic in {"weekly-digest", "monthly-digest", "memory-distillation"}:
            return "operations"
        if topic in {"patient-archive"}:
            return "records"
        if topic in {"behavior-plan", "execution-barrier"}:
            return "behavior-plan"
        return "general"

    def _infer_sources(self, topic: str) -> list[str]:
        mapping = {
            "blood-pressure": [str(self.memory_writer.items_dir / "blood-pressure.md")],
            "blood-sugar": [str(self.memory_writer.items_dir / "blood-sugar.md")],
            "weight": [str(self.memory_writer.items_dir / "weight.md")],
            "sleep": [str(self.memory_writer.items_dir / "sleep.md")],
            "supplements": [str(self.memory_writer.items_dir / "supplements.md")],
            "medication": [str(self.memory_writer.items_dir / "medications.md")],
            "appointments": [str(self.memory_writer.items_dir / "appointments.md")],
            "annual-checkup": [str(self.memory_writer.items_dir / "annual-checkup.md")],
            "behavior-plan": [str(self.memory_writer.behavior_plans_path)],
            "execution-barrier": [str(self.memory_writer.execution_barriers_path)],
            "weekly-digest": [str(self.memory_writer.weekly_digest_path)],
            "monthly-digest": [str(self.memory_writer.monthly_digest_path)],
            "memory-distillation": [str(self.memory_writer.memory_doc_path)] if self.memory_writer.memory_doc_path else [],
            "patient-archive": [str(self.memory_writer.files_dir / "patient-archive-summary.md")],
        }
        return mapping.get(topic, [])

    def _infer_threshold(self, issue: dict) -> str | None:
        title = issue.get("title", "")
        if "血压危急值" in title:
            return "最近一次血压 >= 180/120 mmHg"
        if "血压连续偏高" in title:
            return "最近 3 次血压均 >= 140/90 mmHg"
        if "低血糖风险" in title:
            return "最近一次血糖 < 3.9 mmol/L"
        if "空腹血糖连续偏高" in title:
            return "最近 3 次空腹血糖 > 7.0 mmol/L"
        if "餐后血糖偏高" in title:
            return "最近一次餐后血糖 > 10.0 mmol/L"
        if "药物库存偏低" in title:
            return "Stock coverage days <= 7"
        if "药物续配即将到期" in title:
            return "Next refill <= 7 days"
        if "复查/复诊即将到期" in title:
            return "Next follow-up <= 3 days"
        if "复查/复诊已逾期" in title:
            return "Next follow-up date < today"
        if "年度体检即将到期" in title:
            return "Next annual checkup <= reminder window days"
        if "年度体检已逾期" in title:
            return "Next annual checkup date < today"
        if "行为计划已到期" in title:
            return "Behavior plan due time already passed"
        if "行为计划即将到点" in title:
            return "Behavior plan due within 60 minutes"
        return None

    def _enrich_issue(self, issue: dict) -> dict:
        enriched = dict(issue)
        topic = enriched.get("topic") or self._infer_topic(enriched)
        enriched["topic"] = topic
        enriched.setdefault("trigger", self._infer_trigger(enriched))
        enriched.setdefault("category", self._infer_category(enriched))
        enriched.setdefault("source_refs", self._infer_sources(topic))
        threshold = self._infer_threshold(enriched)
        if threshold:
            enriched.setdefault("threshold", threshold)
        enriched.setdefault("dedupe_key", f"{topic}:{enriched.get('title', 'untitled')}")
        return enriched

    def _render_markdown(self, issues: list[dict]) -> str:
        buckets = {"high": [], "medium": [], "low": []}
        for issue in issues:
            buckets[issue["priority"]].append(issue)

        lines = [f"# Health Heartbeat -- {self._today()}", ""]
        if not issues:
            lines.extend(
                [
                    "## 状态",
                    "- 当前没有检测到需要提醒的事项，继续保持连续记录。",
                ]
            )
            return "\n".join(lines)

        for priority in ("high", "medium", "low"):
            lines.append(f"## {PRIORITY_LABEL[priority]}")
            if not buckets[priority]:
                lines.append("- 本轮无事项")
                lines.append("")
                continue
            for issue in buckets[priority]:
                lines.append(f"- {issue['title']}: {issue['reason']}")
                if issue.get("threshold"):
                    lines.append(f"  依据：{issue['threshold']}")
                if issue.get("source_refs"):
                    lines.append(f"  来源：{', '.join(issue['source_refs'])}")
                lines.append(f"  现在该做什么：{issue['next_step']}")
                lines.append(f"  跟进时间：{issue['follow_up']}")
                if issue.get("delivery_note"):
                    lines.append(f"  推送策略：{issue['delivery_note']}")
                if issue.get("execution_mode"):
                    lines.append(f"  执行模式：{issue['execution_mode']}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _record_execution_barriers_from_tasks(self, tasks: list[dict]) -> None:
        for task in tasks:
            if task.get("topic") not in {"behavior-plan", "blood-pressure", "blood-sugar"}:
                continue
            if task.get("status") not in {"open", "snoozed", "monitor_only"}:
                continue
            if int(task.get("follow_up_count", 0)) < 2 and int(task.get("occurrences", 0)) < 3:
                continue
            self.memory_writer.record_execution_barrier(
                scenario=task.get("topic", "health"),
                barrier=task.get("title", "Repeated follow-up"),
                impact=task.get("reason", "Repeated follow-up detected"),
                pattern=f"follow_up_count={task.get('follow_up_count', 0)}, occurrences={task.get('occurrences', 0)}",
                next_step=task.get("next_step", "拆小动作并重新安排下一次执行。"),
                source_refs=task.get("source_refs", []),
            )

    def run(self, write_report: bool = True) -> dict:
        issues = []
        issues.extend(self._issues_missing_records())
        issues.extend(self._issues_bp_risk())
        issues.extend(self._issues_glucose_risk())
        issues.extend(self._issues_adherence())
        issues.extend(self._issues_weekly_digest())
        issues.extend(self._issues_monthly_digest())
        issues.extend(self._issues_due_schedule())
        issues.extend(self._issues_annual_checkup())
        issues.extend(self._issues_memory_distillation())
        issues.extend(self._issues_patient_archive())
        issues.extend(self._issues_behavior_plans())
        issues.extend(self._issues_execution_barriers())
        issues.extend(self._issues_stalled_improvement())
        issues = [self._enrich_issue(issue) for issue in issues]
        issues.sort(key=lambda item: PRIORITY_ORDER[item["priority"]])

        reminder_result = self.reminder_center.sync_issues(issues, write=write_report)
        issues = reminder_result["issues"]
        if write_report:
            self._record_execution_barriers_from_tasks(reminder_result.get("tasks", []))

        markdown = self._render_markdown(issues)
        report_path = None
        if write_report:
            report_path = self.memory_writer.update_heartbeat_report(markdown, self._today())

        return {
            "date": self._today(),
            "issues": issues,
            "push_issues": reminder_result["push_issues"],
            "suppressed_issues": reminder_result["suppressed_issues"],
            "markdown": markdown,
            "report_path": report_path,
            "task_board_path": reminder_result.get("task_board_path"),
            "task_state_path": reminder_result.get("task_state_path"),
        }
