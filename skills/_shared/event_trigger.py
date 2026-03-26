#!/usr/bin/env python3
"""Event-driven health alert system for VitaClaw.

Evaluates records immediately upon ingestion (post-append hook) and
fires alerts for critical conditions without waiting for the next
scheduled heartbeat.

Architecture:
    HealthDataStore.append()
        → EventTrigger.on_record(record)
            → evaluate against CRITICAL_RULES
            → if triggered: push via PushDispatcher + log to audit

Design:
    - Rules are pure functions: (record_type, data) → Alert | None
    - Each rule declares a severity: critical | urgent | informational
    - Only critical/urgent rules trigger immediate push
    - Informational rules just log for the next heartbeat to pick up
    - Cooldown prevents alert fatigue (same rule won't fire twice in N minutes)
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path


def _safe_float(data: dict, *keys) -> float:
    """Extract first available numeric value from data dict."""
    for key in keys:
        val = data.get(key)
        if isinstance(val, (int, float)):
            return float(val)
    return 0.0


class Alert:
    """A triggered health alert."""

    def __init__(
        self,
        rule_id: str,
        severity: str,  # critical | urgent | informational
        title: str,
        reason: str,
        next_step: str,
        record: dict | None = None,
    ):
        self.rule_id = rule_id
        self.severity = severity
        self.title = title
        self.reason = reason
        self.next_step = next_step
        self.record = record
        self.timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    def to_push_issue(self) -> dict:
        """Convert to the push_issues format used by PushDispatcher."""
        priority_map = {"critical": "high", "urgent": "high", "informational": "low"}
        return {
            "priority": priority_map.get(self.severity, "medium"),
            "title": self.title,
            "reason": self.reason,
            "next_step": self.next_step,
            "topic": self.rule_id.split(":")[0] if ":" in self.rule_id else self.rule_id,
            "trigger": "event",
            "category": "immediate-alert",
            "execution_mode": "event-trigger",
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "title": self.title,
            "reason": self.reason,
            "next_step": self.next_step,
            "timestamp": self.timestamp,
        }


# ── Critical Rules ────────────────────────────────────────────


def _rule_bp_crisis(record_type: str, data: dict) -> Alert | None:
    """Blood pressure >= 180/120 → hypertensive crisis."""
    if record_type != "bp":
        return None
    sys_val = _safe_float(data, "systolic", "sys")
    dia_val = _safe_float(data, "diastolic", "dia")
    if sys_val >= 180 or dia_val >= 120:
        return Alert(
            rule_id="blood-pressure:crisis",
            severity="critical",
            title="血压危急值",
            reason=f"刚录入血压 {int(sys_val)}/{int(dia_val)} mmHg，已达危急范围。",
            next_step="不要继续自我管理，建议立即联系急救或尽快就医。",
        )
    return None


def _rule_bp_high(record_type: str, data: dict) -> Alert | None:
    """Blood pressure >= 160/100 → stage 2 hypertension alert."""
    if record_type != "bp":
        return None
    sys_val = _safe_float(data, "systolic", "sys")
    dia_val = _safe_float(data, "diastolic", "dia")
    # Skip if crisis rule already covers this
    if sys_val >= 180 or dia_val >= 120:
        return None
    if sys_val >= 160 or dia_val >= 100:
        return Alert(
            rule_id="blood-pressure:stage2",
            severity="urgent",
            title="血压显著偏高",
            reason=f"刚录入血压 {int(sys_val)}/{int(dia_val)} mmHg，属于 2 级高血压范围。",
            next_step="静坐 5 分钟后复测一次，并记录伴随症状。若伴胸痛/头痛/视物模糊，立即就医。",
        )
    return None


def _rule_hypoglycemia(record_type: str, data: dict) -> Alert | None:
    """Blood glucose < 3.9 mmol/L → hypoglycemia."""
    if record_type != "glucose":
        return None
    value = _safe_float(data, "value", "glucose")
    if 0 < value < 3.9:
        return Alert(
            rule_id="blood-sugar:hypoglycemia",
            severity="critical",
            title="低血糖风险",
            reason=f"刚录入血糖 {value} mmol/L，低于 3.9 安全阈值。",
            next_step="立即补充 15g 快速糖（葡萄糖片/果汁），15 分钟后复测。如有意识模糊/出汗，请求帮助。",
        )
    return None


def _rule_severe_hyperglycemia(record_type: str, data: dict) -> Alert | None:
    """Blood glucose >= 16.7 mmol/L (300 mg/dL) → severe hyperglycemia."""
    if record_type != "glucose":
        return None
    value = _safe_float(data, "value", "glucose")
    if value >= 16.7:
        return Alert(
            rule_id="blood-sugar:severe-hyperglycemia",
            severity="critical",
            title="严重高血糖",
            reason=f"刚录入血糖 {value} mmol/L，远高于安全范围。",
            next_step="检查是否漏服药物/胰岛素，大量饮水，若伴恶心/呼吸急促/意识改变，立即就医。",
        )
    return None


def _rule_heart_rate_extreme(record_type: str, data: dict) -> Alert | None:
    """Resting heart rate > 120 or < 40 bpm."""
    if record_type != "heart_rate":
        return None
    rhr = _safe_float(data, "resting_bpm", "heart_rate", "bpm")
    if rhr > 120:
        return Alert(
            rule_id="heart-rate:tachycardia",
            severity="urgent",
            title="静息心率异常偏高",
            reason=f"刚录入静息心率 {int(rhr)} bpm，显著高于正常范围。",
            next_step="排查发热、脱水、情绪或漏服心率控制药物。伴胸闷/眩晕请立即就医。",
        )
    if 0 < rhr < 40:
        return Alert(
            rule_id="heart-rate:bradycardia",
            severity="urgent",
            title="静息心率异常偏低",
            reason=f"刚录入静息心率 {int(rhr)} bpm，显著低于正常范围。",
            next_step="若伴头晕/乏力/晕厥前兆，请立即就医。运动员安静心率偏低可能正常，但仍建议关注。",
        )
    return None


def _rule_spo2_low(record_type: str, data: dict) -> Alert | None:
    """SpO2 < 92% → respiratory concern."""
    if record_type not in ("spo2", "blood_oxygen"):
        return None
    value = _safe_float(data, "spo2", "value", "oxygen_saturation")
    if 0 < value < 92:
        return Alert(
            rule_id="spo2:low",
            severity="critical",
            title="血氧饱和度偏低",
            reason=f"刚录入血氧 {value}%，低于 92% 安全阈值。",
            next_step="检查测量是否准确（手指温暖、静止），复测一次。若确认偏低伴呼吸困难，立即就医。",
        )
    return None


def _rule_temperature_fever(record_type: str, data: dict) -> Alert | None:
    """Temperature >= 39°C → high fever."""
    if record_type != "temperature":
        return None
    value = _safe_float(data, "temperature", "value", "temp")
    if value >= 39.0:
        severity = "critical" if value >= 40.0 else "urgent"
        return Alert(
            rule_id="temperature:fever",
            severity=severity,
            title="高热" if value >= 40.0 else "发热",
            reason=f"刚录入体温 {value}°C，{'超过 40°C 属于高热危急' if value >= 40.0 else '高于 39°C'}。",
            next_step="物理降温 + 退热药，监测体温变化。40°C 以上或伴意识改变请立即就医。",
        )
    return None


# All rules, evaluated in order (first match wins per category)
CRITICAL_RULES: list[Callable[[str, dict], Alert | None]] = [
    _rule_bp_crisis,
    _rule_bp_high,
    _rule_hypoglycemia,
    _rule_severe_hyperglycemia,
    _rule_heart_rate_extreme,
    _rule_spo2_low,
    _rule_temperature_fever,
]


class EventTrigger:
    """Evaluate records against critical rules and dispatch alerts.

    Usage:
        trigger = EventTrigger()
        store = HealthDataStore("bp-tracker")
        store.add_hook(trigger.on_record)
        # Now every append() auto-evaluates critical rules

    Or standalone:
        trigger = EventTrigger()
        alerts = trigger.evaluate(record)
    """

    def __init__(
        self,
        rules: list | None = None,
        cooldown_seconds: int = 300,
        audit_path: str | None = None,
        dispatcher=None,
    ):
        self._rules = rules if rules is not None else CRITICAL_RULES
        self._cooldown = cooldown_seconds
        self._last_fired: dict[str, float] = {}  # rule_id → timestamp
        self._audit_path = Path(audit_path) if audit_path else None
        self._dispatcher = dispatcher
        self._alert_history: list[Alert] = []

    def evaluate(self, record: dict) -> list[Alert]:
        """Evaluate a record against all rules. Returns triggered alerts."""
        record_type = record.get("type", "")
        data = record.get("data", {})
        now = time.monotonic()
        alerts: list[Alert] = []

        for rule_fn in self._rules:
            alert = rule_fn(record_type, data)
            if alert is None:
                continue

            # Cooldown: skip if same rule fired recently
            last = self._last_fired.get(alert.rule_id, 0)
            if now - last < self._cooldown:
                continue

            alert.record = record
            alerts.append(alert)
            self._last_fired[alert.rule_id] = now
            self._alert_history.append(alert)

        return alerts

    def on_record(self, record: dict) -> list[Alert]:
        """Post-append hook: evaluate + dispatch + audit.

        Designed to be registered via HealthDataStore.add_hook().
        """
        alerts = self.evaluate(record)
        if not alerts:
            return []

        # Dispatch pushable alerts (critical/urgent only)
        pushable = [a for a in alerts if a.severity in ("critical", "urgent")]
        if pushable and self._dispatcher:
            push_issues = [a.to_push_issue() for a in pushable]
            try:
                self._dispatcher(push_issues)
            except Exception:
                pass  # Push failure should not block data flow

        # Audit log
        if self._audit_path:
            self._write_audit(alerts)

        return alerts

    def _write_audit(self, alerts: list[Alert]) -> None:
        """Append alerts to audit JSONL."""
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_path.open("a", encoding="utf-8") as f:
                for alert in alerts:
                    f.write(json.dumps(alert.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass  # Audit failure should not block data flow

    @property
    def alert_history(self) -> list[Alert]:
        """Access in-memory alert history (for testing/debugging)."""
        return list(self._alert_history)

    def clear_cooldowns(self) -> None:
        """Reset all cooldown timers."""
        self._last_fired.clear()
