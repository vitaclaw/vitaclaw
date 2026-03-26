#!/usr/bin/env python3
"""Build a unified health timeline from workspace and patient archive sources."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from .health_memory import HealthMemoryWriter
from .patient_archive_bridge import PatientArchiveBridge


def _parse_table(path: Path) -> tuple[list[str], list[list[str]]]:
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


class HealthTimelineBuilder:
    """Merge archive, Apple Health, items, and digests into one timeline."""

    APPLE_REPORTS = {
        "体重变化.md": ("Apple Health 体重", lambda row: f"体重 {row[1]} kg"),
        "血压记录.md": ("Apple Health 血压", lambda row: f"血压 {row[2]}/{row[3]} mmHg"),
        "心率趋势.md": ("Apple Health 心率", lambda row: f"平均心率 {row[1]} bpm"),
        "步数记录.md": ("Apple Health 步数", lambda row: f"步数 {row[1]}"),
        "睡眠记录.md": ("Apple Health 睡眠", lambda row: f"睡眠 {row[1]}"),
        "血氧记录.md": ("Apple Health 血氧", lambda row: f"平均血氧 {row[1]}%"),
    }

    def __init__(
        self,
        workspace_root: str | None = None,
        memory_dir: str | None = None,
        patients_root: str | None = None,
        patient_id: str | None = None,
        now_fn=None,
        knowledge_graph=None,
    ):
        self._now_fn = now_fn or datetime.now
        self.writer = HealthMemoryWriter(
            workspace_root=workspace_root,
            memory_root=memory_dir,
            now_fn=self._now_fn,
        )
        self.archive_bridge = PatientArchiveBridge(
            workspace_root=workspace_root,
            memory_dir=memory_dir,
            patients_root=patients_root,
            patient_id=patient_id,
            now_fn=self._now_fn,
        )
        self._knowledge_graph = knowledge_graph
        self.output_path = self.writer.files_dir / "health-timeline.md"

    def _now(self) -> datetime:
        return self._now_fn()

    def _enrich_with_graph(self, entries: list[dict]) -> None:
        """Add knowledge graph context to timeline entries where available."""
        graph = self._knowledge_graph
        for entry in entries:
            entry_type = entry.get("type", "").lower()
            # Try to find related entities from the graph for known concepts
            concept_map = {
                "血压": "blood-pressure",
                "blood pressure": "blood-pressure",
                "apple health 血压": "blood-pressure",
                "体重": "weight",
                "apple health 体重": "weight",
                "心率": "heart-rate",
                "apple health 心率": "heart-rate",
                "血糖": "blood-sugar",
                "睡眠": "sleep",
                "apple health 睡眠": "sleep",
            }
            concept = None
            for keyword, cid in concept_map.items():
                if keyword in entry_type:
                    concept = cid
                    break
            if concept:
                node = graph.find_node_by_name(concept)
                if node:
                    neighbors = graph.query_neighbors(node["id"], depth=1)
                    related = [
                        n["name"] for n in neighbors if n.get("type") == "medication" and not n.get("invalid_at")
                    ]
                    if related:
                        entry["graph_context"] = related

    def _item_entries(self, days: int) -> list[dict]:
        entries = []
        cutoff = self._now().date() - timedelta(days=days)
        for path in sorted(self.writer.items_dir.glob("*.md")):
            headers, rows = _parse_table(path)
            if not headers or not rows:
                continue
            title = path.stem.replace("-", " ")
            for row in rows:
                try:
                    date_obj = datetime.strptime(row[0], "%Y-%m-%d").date()
                except ValueError:
                    continue
                if date_obj < cutoff:
                    continue
                detail_parts = []
                for header, value in zip(headers[1:4], row[1:4]):
                    if value:
                        detail_parts.append(f"{header}: {value}")
                if not detail_parts:
                    detail_parts = row[1:4]
                entries.append(
                    {
                        "date": row[0],
                        "source": "workspace-item",
                        "type": title,
                        "summary": " | ".join(part for part in detail_parts if part),
                        "path": str(path),
                    }
                )
        return entries

    def _digest_entries(self) -> list[dict]:
        entries = []
        for path, entry_type in (
            (self.writer.weekly_digest_path, "健康周报"),
            (self.writer.monthly_digest_path, "健康月报"),
        ):
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            title = None
            for line in text.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            if not title:
                continue
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", title)
            if not date_match:
                date_match = re.search(r"(\d{4}-\d{2})", title)
            if not date_match:
                continue
            date_text = date_match.group(1)
            if len(date_text) == 7:
                date_text = f"{date_text}-01"
            entries.append(
                {
                    "date": date_text,
                    "source": "workspace-digest",
                    "type": entry_type,
                    "summary": title,
                    "path": str(path),
                }
            )
        return entries

    def _archive_entries(self, days: int) -> list[dict]:
        entries = []
        if not self.archive_bridge.is_available():
            return entries
        cutoff = self._now().date() - timedelta(days=days)
        for entry in self.archive_bridge.timeline_entries(limit=1000):
            try:
                date_obj = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            except ValueError:
                continue
            if date_obj < cutoff:
                continue
            entries.append(
                {
                    "date": entry["date"],
                    "source": "patient-archive",
                    "type": entry["type"],
                    "summary": entry["summary"],
                    "path": entry["filepath"],
                }
            )
        return entries

    def _apple_health_entries(self, days: int) -> list[dict]:
        entries = []
        if not self.archive_bridge.is_available():
            return entries
        cutoff = self._now().date() - timedelta(days=days)
        apple_dir = self.archive_bridge.patient_dir / "09_Apple_Health"
        if not apple_dir.exists():
            return entries
        for path in sorted(apple_dir.glob("*.md")):
            config = self.APPLE_REPORTS.get(path.name)
            if not config:
                continue
            entry_type, formatter = config
            _, rows = _parse_table(path)
            for row in rows:
                if not row:
                    continue
                date_text = row[0]
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
                    continue
                if datetime.strptime(date_text, "%Y-%m-%d").date() < cutoff:
                    continue
                entries.append(
                    {
                        "date": date_text,
                        "source": "apple-health",
                        "type": entry_type,
                        "summary": formatter(row),
                        "path": str(path),
                    }
                )
        return entries

    def build(self, days: int = 180, max_entries: int = 120, write: bool = True) -> dict:
        entries = []
        entries.extend(self._archive_entries(days))
        entries.extend(self._apple_health_entries(days))
        entries.extend(self._item_entries(days))
        entries.extend(self._digest_entries())

        entries.sort(
            key=lambda item: (item.get("date", ""), item.get("type", "")),
            reverse=True,
        )
        entries = entries[:max_entries]

        # Optionally enrich entries with knowledge graph context
        if self._knowledge_graph is not None:
            self._enrich_with_graph(entries)

        lines = [
            f"# Unified Health Timeline -- {self._now().date().isoformat()}",
            "",
            "- Sources merged: patient archive, Apple Health, workspace items, digests",
            f"- Entries: {len(entries)}",
            "",
        ]
        if not entries:
            lines.extend(["- 当前没有可用于生成统一时间轴的数据。", ""])
        else:
            current_month = None
            for entry in entries:
                month_key = entry["date"][:7]
                if month_key != current_month:
                    lines.append(f"## {month_key}")
                    current_month = month_key
                line = f"- {entry['date']} | {entry['type']} | {entry['summary']} | {entry['source']} | {entry['path']}"
                if entry.get("graph_context"):
                    line += f" | 关联药物: {', '.join(entry['graph_context'])}"
                lines.append(line)

        markdown = "\n".join(lines).rstrip() + "\n"
        if write:
            self.output_path.write_text(markdown, encoding="utf-8")
        return {
            "date": self._now().date().isoformat(),
            "entry_count": len(entries),
            "timeline_path": str(self.output_path) if write else None,
            "markdown": markdown,
            "entries": entries,
        }
