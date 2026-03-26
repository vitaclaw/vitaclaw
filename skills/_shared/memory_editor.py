#!/usr/bin/env python3
"""Self-editing memory for VitaClaw AI Agent.

Allows the agent to propose and apply updates to health memory items,
with audit trail and domain-scoped edit permissions.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class MemoryUpdate:
    """A proposed update to a memory item."""

    def __init__(
        self,
        item_path: str,
        section: str,
        old_content: str,
        new_content: str,
        reason: str,
        domain: str = "health",
        requires_confirmation: bool = False,
    ):
        self.item_path = item_path
        self.section = section
        self.old_content = old_content
        self.new_content = new_content
        self.reason = reason
        self.domain = domain
        self.requires_confirmation = requires_confirmation
        self.status = "proposed"  # proposed | approved | applied | rejected
        self.proposed_at = datetime.now().isoformat(timespec="seconds")
        self.applied_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "item_path": self.item_path,
            "section": self.section,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "reason": self.reason,
            "domain": self.domain,
            "requires_confirmation": self.requires_confirmation,
            "status": self.status,
            "proposed_at": self.proposed_at,
            "applied_at": self.applied_at,
        }


class MemoryEditor:
    """Propose and apply updates to health memory with audit trail.

    Edit permissions are domain-scoped:
      - health: Agent can auto-edit item rollups and daily logs
      - cognitive: Requires user confirmation (v2)
      - social: Requires user confirmation (v3)
    """

    # Domains where the agent can auto-edit without user confirmation
    AUTO_EDIT_DOMAINS = {"health"}

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

        self._audit_file = self._memory / "_edit_audit.jsonl"
        self._pending: list[MemoryUpdate] = []

    def _now(self) -> datetime:
        return self._now_fn()

    def propose_update(
        self,
        item_path: str,
        section: str,
        old_content: str,
        new_content: str,
        reason: str,
        domain: str = "health",
    ) -> MemoryUpdate:
        """Propose a memory update. Auto-approved for health domain."""
        requires_confirmation = domain not in self.AUTO_EDIT_DOMAINS
        update = MemoryUpdate(
            item_path=item_path,
            section=section,
            old_content=old_content,
            new_content=new_content,
            reason=reason,
            domain=domain,
            requires_confirmation=requires_confirmation,
        )

        if not requires_confirmation:
            update.status = "approved"

        self._pending.append(update)
        return update

    def apply_update(self, update: MemoryUpdate) -> bool:
        """Apply an approved update to the memory file."""
        if update.status not in ("approved",):
            return False

        file_path = self._memory / update.item_path
        if not file_path.exists():
            return False

        content = file_path.read_text(encoding="utf-8")
        if update.old_content not in content:
            update.status = "rejected"
            self._write_audit(update, "old_content_not_found")
            return False

        new_content = content.replace(update.old_content, update.new_content, 1)
        file_path.write_text(new_content, encoding="utf-8")

        update.status = "applied"
        update.applied_at = self._now().isoformat(timespec="seconds")
        self._write_audit(update, "applied")
        return True

    def apply_all_pending(self) -> list[MemoryUpdate]:
        """Apply all approved pending updates. Returns list of applied updates."""
        applied: list[MemoryUpdate] = []
        for update in self._pending:
            if update.status == "approved":
                if self.apply_update(update):
                    applied.append(update)
        self._pending = [u for u in self._pending if u.status not in ("applied", "rejected")]
        return applied

    def get_pending(self) -> list[MemoryUpdate]:
        """Return pending updates requiring user confirmation."""
        return [u for u in self._pending if u.status == "proposed" and u.requires_confirmation]

    def approve(self, update: MemoryUpdate) -> None:
        """User approves a pending update."""
        update.status = "approved"

    def reject(self, update: MemoryUpdate) -> None:
        """User rejects a pending update."""
        update.status = "rejected"
        self._write_audit(update, "user_rejected")

    def _write_audit(self, update: MemoryUpdate, action: str) -> None:
        """Write audit record."""
        self._audit_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": self._now().isoformat(timespec="seconds"),
            "action": action,
            **update.to_dict(),
        }
        with self._audit_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
