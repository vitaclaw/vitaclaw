#!/usr/bin/env python3
"""Import Apple Health export into a patient archive and sync summaries."""

from __future__ import annotations

import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path

from .patient_archive_bridge import PatientArchiveBridge


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[2]
APPLE_PARSER = _load_module(
    "vitaclaw_parse_apple_health",
    ROOT / "skills" / "apple-health-digest" / "scripts" / "parse_apple_health.py",
)
TIMELINE_UPDATER = _load_module(
    "vitaclaw_update_timeline",
    ROOT / "skills" / "health-timeline" / "scripts" / "update_timeline.py",
)


def _parse_markdown_table(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        return [], []

    headers = []
    rows = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if not headers:
            headers = cells
            continue
        if set(cells[0]) == {"-"}:
            continue
        rows.append(cells)
    return headers, rows


def _extract_date_range(text: str) -> tuple[datetime | None, datetime | None]:
    matches = re.findall(r"(\d{4}-\d{2}-\d{2})", text or "")
    if not matches:
        return None, None
    if len(matches) == 1:
        dt = datetime.strptime(matches[0], "%Y-%m-%d")
        return dt, dt
    return (
        datetime.strptime(matches[0], "%Y-%m-%d"),
        datetime.strptime(matches[1], "%Y-%m-%d"),
    )


class AppleHealthImporter:
    """Import Apple Health XML into patient archive and workspace bridge."""

    def __init__(
        self,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
        patients_root: str | None = None,
        patient_id: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.archive_bridge = PatientArchiveBridge(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )

    def _now(self) -> datetime:
        return self._now_fn()

    def _filter_records(
        self,
        records: dict[str, list[dict]],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, list[dict]]:
        if not start_date and not end_date:
            return records

        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        filtered = {}
        for metric, items in records.items():
            kept = []
            for item in items:
                dt = item.get("start")
                if dt is None:
                    continue
                if start_dt and dt < start_dt:
                    continue
                if end_dt and dt > end_dt + timedelta(days=1):
                    continue
                kept.append(item)
            filtered[metric] = kept
        return filtered

    def _write_reports(self, aggregated: dict, patient_id: str, output_dir: Path) -> list[str]:
        files_created = []
        for writer, key in (
            (APPLE_PARSER.write_heart_rate_md, "heart_rate"),
            (APPLE_PARSER.write_bp_md, "bp"),
            (APPLE_PARSER.write_spo2_md, "spo2"),
            (APPLE_PARSER.write_weight_md, "weight"),
            (APPLE_PARSER.write_steps_md, "steps"),
            (APPLE_PARSER.write_sleep_md, "sleep"),
        ):
            path = writer(aggregated.get(key, []), patient_id, output_dir)
            if path:
                files_created.append(path.name)
        return files_created

    def _load_treatments(self) -> list[dict]:
        patient_dir = self.archive_bridge.patient_dir
        if not patient_dir:
            return []
        path = patient_dir / "06_治疗决策历史" / "治疗决策总表.md"
        headers, rows = _parse_markdown_table(path)
        treatments = []
        for row in rows:
            if len(row) < 4:
                continue
            start_dt, end_dt = _extract_date_range(row[1])
            if not start_dt or not end_dt:
                continue
            treatments.append(
                {
                    "line": row[0],
                    "period": row[1],
                    "regimen": row[2],
                    "response": row[3],
                    "start": start_dt,
                    "end": end_dt,
                }
            )
        return treatments

    def _select_range(self, rows: list[dict], start: datetime, end: datetime, key: str = "date") -> list[dict]:
        selected = []
        for row in rows:
            date_text = row.get(key)
            if not date_text:
                continue
            dt = datetime.strptime(date_text, "%Y-%m-%d")
            if start <= dt <= end:
                selected.append(row)
        return selected

    def _baseline_range(self, start: datetime) -> tuple[datetime, datetime]:
        return start - timedelta(days=14), start - timedelta(days=1)

    def _avg(self, values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 1)

    def _build_correlation_report(self, patient_id: str, output_dir: Path, aggregated: dict) -> Path:
        path = output_dir / "治疗相关性分析.md"
        treatments = self._load_treatments()
        now_text = self._now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"# 治疗相关性分析 — {patient_id}",
            "",
            "> 数据来源：Apple Health 导出 + 治疗记录",
            f"> 生成时间：{now_text}",
            "",
        ]

        if not treatments:
            lines.extend(
                [
                    "## 总览",
                    "- 当前未检测到结构化治疗时间段，仅完成 Apple Health 数据导入和指标报告生成。",
                    "",
                ]
            )
            path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            return path

        lines.extend(["## 总览", "- 以下分析按治疗阶段对照 Apple Health 指标变化。", ""])

        for treatment in treatments:
            baseline_start, baseline_end = self._baseline_range(treatment["start"])
            weight_period = self._select_range(aggregated.get("weight", []), treatment["start"], treatment["end"])
            weight_base = self._select_range(aggregated.get("weight", []), baseline_start, baseline_end)
            hr_period = self._select_range(aggregated.get("heart_rate", []), treatment["start"], treatment["end"])
            hr_base = self._select_range(aggregated.get("heart_rate", []), baseline_start, baseline_end)
            steps_period = self._select_range(aggregated.get("steps", []), treatment["start"], treatment["end"])
            steps_base = self._select_range(aggregated.get("steps", []), baseline_start, baseline_end)
            sleep_period = self._select_range(aggregated.get("sleep", []), treatment["start"], treatment["end"])
            sleep_base = self._select_range(aggregated.get("sleep", []), baseline_start, baseline_end)

            lines.extend(
                [
                    f"## {treatment['line']} — {treatment['regimen']}（{treatment['period']}）",
                    f"- 疗效评估：{treatment['response']}",
                    "",
                    "### 体重变化",
                ]
            )
            if weight_period:
                start_weight = weight_period[0]["value"]
                end_weight = weight_period[-1]["value"]
                delta = round(end_weight - start_weight, 1)
                lines.append(f"- 治疗期起点体重：{start_weight} kg")
                lines.append(f"- 治疗期终点体重：{end_weight} kg")
                lines.append(f"- 治疗期变化：{delta:+.1f} kg")
                if weight_base:
                    base_avg = self._avg([row["value"] for row in weight_base])
                    lines.append(f"- 治疗前 14 天平均体重：{base_avg} kg")
            else:
                lines.append("- 无治疗期体重数据")

            lines.extend(["", "### 心率趋势"])
            if hr_period:
                period_avg = self._avg([row["avg"] for row in hr_period])
                lines.append(f"- 治疗期间平均心率：{period_avg} bpm")
                if hr_base:
                    base_avg = self._avg([row["avg"] for row in hr_base])
                    lines.append(f"- 治疗前 14 天平均心率：{base_avg} bpm")
                    if base_avg is not None and period_avg is not None:
                        lines.append(f"- 变化：{period_avg - base_avg:+.1f} bpm")
            else:
                lines.append("- 无治疗期心率数据")

            lines.extend(["", "### 活动水平"])
            if steps_period:
                period_avg = self._avg([row["total"] for row in steps_period])
                lines.append(f"- 治疗期间日均步数：{period_avg}")
                if steps_base:
                    base_avg = self._avg([row["total"] for row in steps_base])
                    lines.append(f"- 治疗前 14 天日均步数：{base_avg}")
                    if base_avg:
                        pct = round(((period_avg or 0) - base_avg) / base_avg * 100, 1)
                        lines.append(f"- 活动变化：{pct:+.1f}%")
            else:
                lines.append("- 无治疗期步数数据")

            lines.extend(["", "### 睡眠"])
            if sleep_period:
                period_avg = self._avg([row["hours"] for row in sleep_period])
                lines.append(f"- 治疗期间平均睡眠：{period_avg} 小时")
                if sleep_base:
                    base_avg = self._avg([row["hours"] for row in sleep_base])
                    lines.append(f"- 治疗前 14 天平均睡眠：{base_avg} 小时")
            else:
                lines.append("- 无治疗期睡眠数据")
            lines.append("")

        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return path

    def import_export(
        self,
        export_xml: str,
        start_date: str | None = None,
        end_date: str | None = None,
        sync_workspace: bool = True,
    ) -> dict:
        if not self.archive_bridge.is_available():
            return {
                "success": False,
                "error": "No patient archive available to import Apple Health data into.",
            }

        xml_path = Path(export_xml).expanduser().resolve()
        if not xml_path.exists():
            return {"success": False, "error": f"File not found: {xml_path}"}

        output_dir = self.archive_bridge.patient_dir / "09_Apple_Health"
        output_dir.mkdir(parents=True, exist_ok=True)

        records = APPLE_PARSER.collect_records(xml_path)
        records = self._filter_records(records, start_date=start_date, end_date=end_date)
        aggregated = {
            "heart_rate": APPLE_PARSER.aggregate_heart_rate(records.get("heart_rate", [])),
            "steps": APPLE_PARSER.aggregate_steps(records.get("steps", [])),
            "weight": APPLE_PARSER.aggregate_weight(records.get("weight", [])),
            "spo2": APPLE_PARSER.aggregate_spo2(records.get("spo2", [])),
            "sleep": APPLE_PARSER.aggregate_sleep(records.get("sleep", [])),
            "bp": APPLE_PARSER.match_blood_pressure(
                records.get("bp_systolic", []),
                records.get("bp_diastolic", []),
            ),
        }

        files_created = self._write_reports(aggregated, self.archive_bridge.patient_id, output_dir)
        correlation_path = self._build_correlation_report(
            self.archive_bridge.patient_id,
            output_dir,
            aggregated,
        )
        if correlation_path.name not in files_created:
            files_created.append(correlation_path.name)

        summary = APPLE_PARSER.compute_summary(
            records,
            aggregated,
            files_created,
            self.archive_bridge.patient_id,
        )
        summary["output_dir"] = str(output_dir)
        summary["correlation_report"] = correlation_path.name
        summary["patient_id"] = self.archive_bridge.patient_id

        date_hint = (summary.get("date_range") or {}).get("end") or self._now().date().isoformat()
        summary_line = "导入 Apple Health 数据"
        metrics = []
        for name in ("heart_rate", "weight", "steps", "blood_pressure", "sleep"):
            metric = (summary.get("metrics") or {}).get(name)
            if metric:
                metrics.append(name)
        if metrics:
            summary_line += "，包含 " + ", ".join(metrics[:5])
        TIMELINE_UPDATER.update_timeline(
            self.archive_bridge.patient_dir,
            date_hint,
            "Apple Health 导入",
            summary_line,
            f"09_Apple_Health/{correlation_path.name}",
        )

        synced = None
        if sync_workspace:
            synced = self.archive_bridge.sync_to_workspace(write=True)
        summary["workspace_sync"] = synced
        return summary

    def export_to_fhir_bundle(self, records: list[dict] | None = None) -> dict:
        """Export VitaClaw health records as a FHIR R4 Bundle.

        If no records are provided, exports the most recent Apple Health data
        available via the archive bridge.

        Args:
            records: Optional list of VitaClaw record dicts. If None, gathers
                     records from the archive bridge's Apple Health reports.

        Returns:
            FHIR Bundle dict.
        """
        from .fhir_mapper import FHIRMapper

        mapper = FHIRMapper()

        if records is not None:
            return mapper.to_fhir_bundle(records)

        # Gather records from Apple Health reports in the archive
        gathered: list[dict] = []
        if self.archive_bridge.is_available():
            apple_dir = self.archive_bridge.patient_dir / "09_Apple_Health"
            if apple_dir.exists():
                for path in sorted(apple_dir.glob("*.md")):
                    _, rows = _parse_markdown_table(path)
                    for row in rows:
                        if not row or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[0]):
                            continue
                        record = {
                            "type": "observation",
                            "timestamp": f"{row[0]}T00:00:00",
                            "skill": "apple-health-import",
                            "data": {"raw_row": row},
                            "_meta": {"domain": "health", "source": "device"},
                        }
                        gathered.append(record)

        return mapper.to_fhir_bundle(gathered)
