#!/usr/bin/env python3
"""Bridge patient archives from medical-record-organizer into VitaClaw workspaces."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from .health_memory import HealthMemoryWriter


def _resolve_patients_root(patients_root: str | None = None) -> Path:
    if patients_root:
        return Path(patients_root).expanduser().resolve()
    if "VITACLAW_PATIENTS_DIR" in os.environ:
        return Path(os.environ["VITACLAW_PATIENTS_DIR"]).expanduser().resolve()
    if "OPENCLAW_PATIENTS_DIR" in os.environ:
        return Path(os.environ["OPENCLAW_PATIENTS_DIR"]).expanduser().resolve()
    return Path.home() / ".openclaw" / "patients"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extract_section_lines(text: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"^{re.escape(heading)}\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return []
    return [line.rstrip() for line in match.group(1).strip().splitlines() if line.strip()]


def _parse_table_rows(text: str) -> list[list[str]]:
    rows = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if set(cells[0]) == {"-"} or cells[0] in {"日期", "Date"}:
            continue
        rows.append(cells)
    return rows


def _iso_from_text(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    return match.group(1) if match else None


class PatientArchiveBridge:
    """Sync and summarize patient archives inside a health workspace."""

    def __init__(
        self,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
        patients_root: str | None = None,
        patient_id: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.writer = HealthMemoryWriter(
            workspace_root=workspace_root,
            memory_root=memory_dir,
            now_fn=self._now_fn,
        )
        self.patients_root = _resolve_patients_root(patients_root)
        self.link_path = self.writer.files_dir / "patient-archive-link.json"
        self.summary_path = self.writer.files_dir / "patient-archive-summary.md"
        self.patient_id = patient_id or self._linked_patient_id() or self._auto_patient_id()
        self.patient_dir = self.patients_root / self.patient_id if self.patient_id else None

    def _now(self) -> datetime:
        return self._now_fn()

    def _linked_patient_id(self) -> str | None:
        if not self.link_path.exists():
            return None
        try:
            payload = json.loads(self.link_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        patient_id = payload.get("patient_id")
        root = payload.get("patients_root")
        if root:
            self.patients_root = Path(root).expanduser().resolve()
        return patient_id

    def _auto_patient_id(self) -> str | None:
        if not self.patients_root.exists():
            return None
        patient_dirs = [path for path in sorted(self.patients_root.iterdir()) if path.is_dir()]
        if len(patient_dirs) == 1:
            return patient_dirs[0].name
        return None

    def is_available(self) -> bool:
        return bool(self.patient_dir and self.patient_dir.exists())

    def save_link(self) -> str | None:
        if not self.is_available():
            return None
        payload = {
            "patient_id": self.patient_id,
            "patients_root": str(self.patients_root),
            "linked_at": self._now().isoformat(timespec="seconds"),
        }
        self.link_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return str(self.link_path)

    def _index_highlights(self) -> list[str]:
        if not self.is_available():
            return []
        index_text = _read_text(self.patient_dir / "INDEX.md")
        lines = []
        for heading in ("## 基本信息", "## ★ 当前治疗状态", "## 合并症摘要"):
            for line in _extract_section_lines(index_text, heading):
                if line.startswith("- ") and "待填写" not in line and "—" not in line:
                    lines.append(line)
        return lines[:6]

    def timeline_entries(self, limit: int = 5) -> list[dict]:
        if not self.is_available():
            return []
        rows = _parse_table_rows(_read_text(self.patient_dir / "timeline.md"))
        entries = []
        for row in rows:
            if len(row) < 4:
                continue
            entries.append(
                {
                    "date": row[0],
                    "type": row[1],
                    "summary": row[2],
                    "filepath": row[3],
                }
            )
        return entries[:limit]

    def latest_timeline_date(self) -> str | None:
        entries = self.timeline_entries(limit=1)
        return entries[0]["date"] if entries else None

    def unclassified_files(self) -> list[Path]:
        if not self.is_available():
            return []
        pending_dir = self.patient_dir / "10_原始文件" / "未分类"
        if not pending_dir.exists():
            return []
        return sorted(path for path in pending_dir.iterdir() if path.is_file())

    def apple_health_reports(self) -> list[str]:
        if not self.is_available():
            return []
        apple_dir = self.patient_dir / "09_Apple_Health"
        if not apple_dir.exists():
            return []
        return sorted(path.name for path in apple_dir.iterdir() if path.is_file())

    def last_synced_at(self) -> datetime | None:
        if not self.link_path.exists():
            return None
        try:
            payload = json.loads(self.link_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        timestamp = payload.get("synced_at") or payload.get("linked_at")
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    def build_summary(self) -> dict:
        if not self.is_available():
            return {
                "available": False,
                "patient_id": self.patient_id,
                "patients_root": str(self.patients_root),
            }

        timeline = self.timeline_entries(limit=6)
        apple_reports = self.apple_health_reports()
        summary = {
            "available": True,
            "patient_id": self.patient_id,
            "archive_path": str(self.patient_dir),
            "patients_root": str(self.patients_root),
            "latest_timeline_date": self.latest_timeline_date(),
            "timeline_entries": timeline,
            "index_highlights": self._index_highlights(),
            "unclassified_count": len(self.unclassified_files()),
            "unclassified_files": [path.name for path in self.unclassified_files()[:10]],
            "apple_health_reports": apple_reports[:10],
            "apple_health_report_count": len(apple_reports),
            "timeline_updated_at": self._file_updated_at(self.patient_dir / "timeline.md"),
            "index_updated_at": self._file_updated_at(self.patient_dir / "INDEX.md"),
            "generated_at": self._now().isoformat(timespec="seconds"),
        }
        return summary

    def _file_updated_at(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")

    def needs_sync(self) -> bool:
        if not self.is_available():
            return False
        last_synced = self.last_synced_at()
        if last_synced is None or not self.summary_path.exists():
            return True

        for path in (
            self.patient_dir / "timeline.md",
            self.patient_dir / "INDEX.md",
        ):
            if path.exists() and datetime.fromtimestamp(path.stat().st_mtime) > last_synced:
                return True
        apple_dir = self.patient_dir / "09_Apple_Health"
        if apple_dir.exists():
            latest_apple = max(
                (datetime.fromtimestamp(path.stat().st_mtime) for path in apple_dir.iterdir() if path.is_file()),
                default=None,
            )
            if latest_apple and latest_apple > last_synced:
                return True
        return False

    def render_markdown(self, summary: dict) -> str:
        if not summary.get("available"):
            return "# Patient Archive Summary\n\n- 当前未解析到可用患者档案。\n"

        lines = [
            f"# Patient Archive Summary -- {summary['patient_id']}",
            "",
            f"- Archive path: {summary['archive_path']}",
            f"- Last synced: {summary['generated_at']}",
        ]
        if summary.get("latest_timeline_date"):
            lines.append(f"- Latest timeline date: {summary['latest_timeline_date']}")
        lines.append(f"- Pending unclassified files: {summary['unclassified_count']}")
        lines.append(f"- Apple Health reports: {summary['apple_health_report_count']}")

        highlights = summary.get("index_highlights") or []
        if highlights:
            lines.extend(["", "## Index Highlights", *highlights])

        entries = summary.get("timeline_entries") or []
        if entries:
            lines.extend(["", "## Latest Timeline"])
            for entry in entries:
                lines.append(f"- {entry['date']} | {entry['type']} | {entry['summary']} | {entry['filepath']}")

        if summary.get("apple_health_reports"):
            lines.extend(["", "## Apple Health Reports"])
            for name in summary["apple_health_reports"]:
                lines.append(f"- {name}")

        if summary.get("unclassified_files"):
            lines.extend(["", "## Pending Archive Inbox"])
            for name in summary["unclassified_files"]:
                lines.append(f"- {name}")

        return "\n".join(lines).rstrip() + "\n"

    def sync_to_workspace(self, write: bool = True) -> dict:
        summary = self.build_summary()
        if not write or not summary.get("available"):
            return summary

        self.summary_path.write_text(self.render_markdown(summary), encoding="utf-8")
        payload = {
            "patient_id": self.patient_id,
            "patients_root": str(self.patients_root),
            "linked_at": self.last_synced_at().isoformat(timespec="seconds")
            if self.last_synced_at()
            else self._now().isoformat(timespec="seconds"),
            "synced_at": self._now().isoformat(timespec="seconds"),
            "latest_timeline_date": summary.get("latest_timeline_date"),
        }
        self.link_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary["summary_path"] = str(self.summary_path)
        summary["link_path"] = str(self.link_path)
        return summary
