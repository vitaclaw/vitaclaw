#!/usr/bin/env python3
"""Three-layer context builder for LLM-native memory interface.

Provides tiered context to fit within token budgets:
  - Hot (~2K tokens): Today's data + alerts + current status
  - Warm (~4K tokens): Trends + plans + graph summary
  - Cold (unlimited): Complete history + archives

Domain-aware: v1 builds health context; v2 will add cognitive/behavioral.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1 token per 3 CJK chars or 4 English chars."""
    cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other_count = len(text) - cjk_count
    return int(cjk_count / 3 + other_count / 4)


class TwinMemoryContext:
    """Build tiered context for LLM consumption.

    Usage:
        ctx = TwinMemoryContext(workspace_root="/path/to/vitaclaw")
        prompt_section = ctx.build_context("血压趋势", budget_tokens=4000)
    """

    def __init__(
        self,
        data_dir: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        if workspace_root:
            self._workspace = Path(workspace_root)
        else:
            self._workspace = _repo_root()

        if memory_dir:
            self._memory = Path(memory_dir)
        else:
            self._memory = self._workspace / "memory" / "health"

        if data_dir:
            self._data_dir = data_dir
        else:
            self._data_dir = str(self._workspace / "data")

    def _now(self) -> datetime:
        return self._now_fn()

    def _read_file(self, path: Path, max_chars: int = 10000) -> str:
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        return text[:max_chars]

    def _build_hot(self, query: str, domains: list[str]) -> str:
        """Hot layer: today's data + alerts + current conditions."""
        parts: list[str] = []
        today = self._now().date().isoformat()

        if "health" in domains:
            # Today's daily log
            daily = self._read_file(self._memory / "daily" / f"{today}.md", max_chars=3000)
            if daily:
                parts.append(f"## 今日健康记录 ({today})\n{daily}")

            # Health profile summary
            profile = self._read_file(self._memory / "_health-profile.md", max_chars=2000)
            if profile:
                parts.append(f"## 健康画像\n{profile}")

            # Heartbeat alerts
            heartbeat_path = self._memory / "heartbeat" / "task-board.md"
            alerts = self._read_file(heartbeat_path, max_chars=1000)
            if alerts:
                parts.append(f"## 健康警报\n{alerts}")

        # v2 placeholder: cognitive domain hot context
        # if "cognitive" in domains: ...

        return "\n\n".join(parts)

    def _build_warm(self, query: str, domains: list[str]) -> str:
        """Warm layer: trends + plans + graph summary + item rollups."""
        parts: list[str] = []

        if "health" in domains:
            # Weekly digest
            weekly = self._read_file(self._memory / "weekly-digest.md", max_chars=3000)
            if weekly:
                parts.append(f"## 本周趋势\n{weekly}")

            # Relevant item files based on query
            items_dir = self._memory / "items"
            if items_dir.exists():
                for item_file in sorted(items_dir.glob("*.md")):
                    item_name = item_file.stem
                    # Include if query mentions this item or if it's a key metric
                    if self._is_relevant(query, item_name):
                        content = self._read_file(item_file, max_chars=2000)
                        if content:
                            parts.append(f"## {item_name}\n{content}")

            # Knowledge graph summary (if available)
            try:
                from .health_knowledge_graph import HealthKnowledgeGraph

                graph = HealthKnowledgeGraph(data_dir=self._data_dir)
                stats = graph.stats()
                if stats["active_nodes"] > 0:
                    parts.append(
                        f"## 知识图谱\n"
                        f"- 节点: {stats['active_nodes']}, 边: {stats['active_edges']}\n"
                        f"- 类型: {', '.join(stats['node_types'])}"
                    )
            except Exception:
                pass

        return "\n\n".join(parts)

    def _build_cold(self, query: str, domains: list[str]) -> str:
        """Cold layer: monthly digests + older daily logs + archives."""
        parts: list[str] = []

        if "health" in domains:
            # Monthly digest
            monthly = self._read_file(self._memory / "monthly-digest.md", max_chars=4000)
            if monthly:
                parts.append(f"## 月度趋势\n{monthly}")

            # Recent daily logs (last 7 days, excluding today)
            for i in range(1, 8):
                day = (self._now() - timedelta(days=i)).date().isoformat()
                daily = self._read_file(self._memory / "daily" / f"{day}.md", max_chars=1500)
                if daily:
                    parts.append(f"## {day}\n{daily}")

        return "\n\n".join(parts)

    def _is_relevant(self, query: str, item_name: str) -> bool:
        """Check if an item is relevant to the query."""
        query_lower = query.lower()
        item_lower = item_name.lower()

        # Direct match
        if item_lower in query_lower or query_lower in item_lower:
            return True

        # Chinese keyword mapping
        zh_map = {
            "blood-pressure": ["血压", "bp", "收缩压", "舒张压", "高血压"],
            "blood-sugar": ["血糖", "glucose", "糖尿病"],
            "weight": ["体重", "bmi", "减重"],
            "sleep": ["睡眠", "失眠", "sleep"],
            "medications": ["用药", "药物", "medication"],
            "supplements": ["补剂", "维生素", "supplement"],
            "caffeine": ["咖啡因", "咖啡", "caffeine"],
            "heart-rate-hrv": ["心率", "hrv", "心率变异"],
            "kidney-function": ["肾功能", "肌酐", "kidney"],
            "liver-function": ["肝功能", "转氨酶", "liver"],
            "blood-lipids": ["血脂", "胆固醇", "lipid"],
        }
        keywords = zh_map.get(item_lower, [])
        return any(kw in query_lower for kw in keywords)

    def build_context(
        self,
        query: str = "",
        budget_tokens: int = 4000,
        domains: list[str] | None = None,
    ) -> str:
        """Build context string within token budget.

        Fills hot first, then warm, then cold until budget is reached.
        """
        domains = domains or ["health"]

        hot = self._build_hot(query, domains)
        hot_tokens = _estimate_tokens(hot)

        if hot_tokens >= budget_tokens:
            return hot[: budget_tokens * 4]  # rough char limit

        warm = self._build_warm(query, domains)
        warm_tokens = _estimate_tokens(warm)

        if hot_tokens + warm_tokens >= budget_tokens:
            remaining = budget_tokens - hot_tokens
            return hot + "\n\n" + warm[: remaining * 4]

        cold = self._build_cold(query, domains)
        remaining = budget_tokens - hot_tokens - warm_tokens
        return hot + "\n\n" + warm + "\n\n" + cold[: remaining * 4]

    def score_relevance(
        self,
        record: dict,
        query: str = "",
        recency_weight: float = 0.3,
        relevance_weight: float = 0.3,
        importance_weight: float = 0.2,
        confidence_weight: float = 0.2,
    ) -> float:
        """Score a record's priority for context inclusion.

        Recency × Relevance × Importance × Confidence
        """
        now = self._now()
        timestamp = record.get("timestamp", "")
        meta = record.get("_meta", {})

        # Recency: exponential decay over 90 days
        recency = 0.5
        if timestamp:
            try:
                record_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if record_time.tzinfo is None:
                    record_time = record_time.replace(tzinfo=now.astimezone().tzinfo)
                days_ago = (now.astimezone() - record_time).days
                recency = max(0.0, 1.0 - days_ago / 90.0)
            except (ValueError, TypeError):
                pass

        # Relevance: simple keyword matching
        relevance = 0.5
        if query:
            record_type = record.get("type", "")
            concept = meta.get("concept", "")
            note = record.get("note", "")
            text_blob = f"{record_type} {concept} {note}".lower()
            if query.lower() in text_blob:
                relevance = 1.0

        # Importance: based on record type (clinical > operational)
        importance_map = {
            "bp": 0.9,
            "glucose": 0.9,
            "dose": 0.8,
            "weight": 0.7,
            "sleep_session": 0.7,
            "intake": 0.5,
            "dose_log": 0.5,
            "digest": 0.3,
            "operations_run": 0.1,
        }
        importance = importance_map.get(record.get("type", ""), 0.5)

        # Confidence from _meta
        confidence = meta.get("confidence", 1.0)

        return (
            recency_weight * recency
            + relevance_weight * relevance
            + importance_weight * importance
            + confidence_weight * confidence
        )
