#!/usr/bin/env python3
"""Memory lifecycle management for VitaClaw health facts.

Implements the four-stage lifecycle:
  Formation → Consolidation → Evolution → Archival

Each health fact in items/*.md carries metadata:
  - confidence: 0.0-1.0
  - valid_until: optional expiry date
  - source_count: number of supporting records
  - stage: formation | consolidated | evolved | archived

Domain-agnostic: works for health, cognitive, behavioral, social facts.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class HealthFact:
    """A single health fact with lifecycle metadata."""

    def __init__(
        self,
        text: str,
        confidence: float = 1.0,
        valid_until: str | None = None,
        source_count: int = 1,
        stage: str = "formation",
        domain: str = "health",
        created_at: str | None = None,
        updated_at: str | None = None,
        sources: list[str] | None = None,
    ):
        self.text = text
        self.confidence = confidence
        self.valid_until = valid_until
        self.source_count = source_count
        self.stage = stage  # formation | consolidated | evolved | archived
        self.domain = domain
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")
        self.updated_at = updated_at or self.created_at
        self.sources = sources or []

    def is_expired(self, now: datetime | None = None) -> bool:
        if not self.valid_until:
            return False
        now = now or datetime.now()
        try:
            expiry = datetime.fromisoformat(self.valid_until)
            return now > expiry
        except ValueError:
            return False

    def to_markdown_line(self) -> str:
        """Serialize to markdown list item with inline metadata."""
        meta_parts = [f"confidence={self.confidence:.1f}"]
        if self.valid_until:
            meta_parts.append(f"until={self.valid_until}")
        meta_parts.append(f"sources={self.source_count}")
        meta_parts.append(f"stage={self.stage}")
        meta_str = " | ".join(meta_parts)
        return f"- {self.text} <!-- {meta_str} -->"

    @classmethod
    def from_markdown_line(cls, line: str) -> HealthFact | None:
        """Parse a markdown list item with inline metadata."""
        line = line.strip()
        if not line.startswith("- "):
            return None

        # Extract metadata comment
        meta_match = re.search(r"<!--\s*(.+?)\s*-->", line)
        text = re.sub(r"\s*<!--.*?-->", "", line[2:]).strip()

        confidence = 1.0
        valid_until = None
        source_count = 1
        stage = "formation"

        if meta_match:
            meta_str = meta_match.group(1)
            for part in meta_str.split("|"):
                part = part.strip()
                if part.startswith("confidence="):
                    try:
                        confidence = float(part.split("=", 1)[1])
                    except ValueError:
                        pass
                elif part.startswith("until="):
                    valid_until = part.split("=", 1)[1].strip()
                elif part.startswith("sources="):
                    try:
                        source_count = int(part.split("=", 1)[1])
                    except ValueError:
                        pass
                elif part.startswith("stage="):
                    stage = part.split("=", 1)[1].strip()

        return cls(
            text=text,
            confidence=confidence,
            valid_until=valid_until,
            source_count=source_count,
            stage=stage,
        )


class MemoryLifecycle:
    """Manage the lifecycle of health facts in memory.

    Stages:
      1. Formation: New fact from a single observation
      2. Consolidation: Fact confirmed by multiple sources (source_count >= 3)
      3. Evolution: Fact updated when new data contradicts or refines it
      4. Archival: Fact expired or superseded, moved to archive
    """

    def __init__(
        self,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        if memory_dir:
            self._memory = Path(memory_dir)
        elif workspace_root:
            self._memory = Path(workspace_root) / "memory" / "health"
        else:
            self._memory = _repo_root() / "memory" / "health"

        self._archive_dir = self._memory / "archive"

    def _now(self) -> datetime:
        return self._now_fn()

    def consolidate(self, fact: HealthFact) -> HealthFact:
        """Promote a fact from formation to consolidated if enough sources."""
        if fact.stage == "formation" and fact.source_count >= 3:
            fact.stage = "consolidated"
            fact.updated_at = self._now().isoformat(timespec="seconds")
        return fact

    def evolve(self, old_fact: HealthFact, new_text: str, new_confidence: float | None = None) -> HealthFact:
        """Update a fact with new information (evolution stage)."""
        old_fact.text = new_text
        old_fact.stage = "evolved"
        old_fact.updated_at = self._now().isoformat(timespec="seconds")
        if new_confidence is not None:
            old_fact.confidence = new_confidence
        return old_fact

    def archive(self, fact: HealthFact, reason: str = "expired") -> HealthFact:
        """Move a fact to archived stage."""
        fact.stage = "archived"
        fact.updated_at = self._now().isoformat(timespec="seconds")
        return fact

    def check_expirations(self, facts: list[HealthFact]) -> tuple[list[HealthFact], list[HealthFact]]:
        """Check facts for expiration. Returns (active, expired)."""
        now = self._now()
        active: list[HealthFact] = []
        expired: list[HealthFact] = []
        for fact in facts:
            if fact.is_expired(now):
                self.archive(fact, reason="expired")
                expired.append(fact)
            else:
                active.append(fact)
        return active, expired

    def write_archive(self, facts: list[HealthFact], category: str = "general") -> Path:
        """Write archived facts to archive directory."""
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self._archive_dir / f"{category}.md"

        lines: list[str] = []
        if archive_path.exists():
            lines = archive_path.read_text(encoding="utf-8").splitlines()

        archived_at = self._now().isoformat(timespec="seconds")
        for fact in facts:
            lines.append(f"- [archived {archived_at}] {fact.text}")

        archive_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return archive_path

    def process_item_facts(self, item_path: Path) -> dict:
        """Process all facts in an item file: consolidate, check expirations.

        Returns summary of actions taken.
        """
        if not item_path.exists():
            return {"processed": 0, "consolidated": 0, "archived": 0}

        content = item_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        processed = 0
        consolidated = 0
        archived_facts: list[HealthFact] = []
        new_lines: list[str] = []

        for line in lines:
            fact = HealthFact.from_markdown_line(line)
            if fact is None:
                new_lines.append(line)
                continue

            processed += 1

            # Check expiration
            if fact.is_expired(self._now()):
                self.archive(fact, reason="expired")
                archived_facts.append(fact)
                continue

            # Try consolidation
            old_stage = fact.stage
            self.consolidate(fact)
            if fact.stage != old_stage:
                consolidated += 1

            new_lines.append(fact.to_markdown_line())

        # Write back
        item_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        # Archive expired facts
        if archived_facts:
            category = item_path.stem
            self.write_archive(archived_facts, category=category)

        return {
            "processed": processed,
            "consolidated": consolidated,
            "archived": len(archived_facts),
        }
