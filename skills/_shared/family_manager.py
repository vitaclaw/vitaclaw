#!/usr/bin/env python3
"""Family data model for VitaClaw — multi-member health management.

Supports:
  - Separate data directories per family member
  - Delegated management (parents manage children's data)
  - Selective sharing between family members
  - Sovereignty handoff (children gain full control at a specified age)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class FamilyManager:
    """Manage family member data directories and sharing policies."""

    def __init__(
        self,
        config_path: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        data_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        if workspace_root:
            self._workspace = Path(workspace_root)
        else:
            self._workspace = _repo_root()

        if config_path:
            self._config_path = Path(config_path)
        elif memory_dir:
            self._config_path = Path(memory_dir) / "_family.yaml"
        else:
            self._config_path = self._workspace / "memory" / "health" / "_family.yaml"

        if data_root:
            self._data_root = Path(data_root)
        else:
            self._data_root = self._workspace / "data"

        self._config: dict = {}
        self._load()

    def _load(self) -> None:
        if not self._config_path.exists():
            return
        try:
            if HAS_YAML:
                self._config = yaml.safe_load(self._config_path.read_text(encoding="utf-8")) or {}
            else:
                self._config = json.loads(self._config_path.read_text(encoding="utf-8"))
        except Exception:
            self._config = {}

    def _save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        if HAS_YAML:
            self._config_path.write_text(
                yaml.dump(self._config, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )
        else:
            self._config_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _now(self) -> datetime:
        return self._now_fn()

    # ── Member Management ────────────────────────────────────

    def add_member(
        self,
        member_id: str,
        display_name: str = "",
        relation: str = "",
        delegate_until: str | None = None,
    ) -> dict:
        """Add a family member. Creates their data directory."""
        members = self._config.setdefault("members", [])

        member = {
            "id": member_id,
            "display_name": display_name,
            "relation": relation,
            "delegate_until": delegate_until,
            "created_at": self._now().isoformat(timespec="seconds"),
        }

        # Update existing or append
        for i, existing in enumerate(members):
            if existing.get("id") == member_id:
                members[i] = member
                self._save()
                return member

        members.append(member)
        self._save()

        # Create data directory for member
        member_data_dir = self._data_root / member_id
        member_data_dir.mkdir(parents=True, exist_ok=True)

        return member

    def get_member(self, member_id: str) -> dict | None:
        for m in self._config.get("members", []):
            if m.get("id") == member_id:
                return m
        return None

    def list_members(self) -> list[dict]:
        return list(self._config.get("members", []))

    def get_member_data_dir(self, member_id: str) -> Path:
        """Return the data directory for a family member."""
        return self._data_root / member_id

    # ── Delegation ───────────────────────────────────────────

    def is_delegate_active(self, member_id: str) -> bool:
        """Check if delegation (e.g. parent managing child) is still active."""
        member = self.get_member(member_id)
        if not member:
            return False

        until = member.get("delegate_until")
        if until is None:
            return True  # Permanent delegation (e.g. spouse)

        try:
            return self._now() < datetime.fromisoformat(until)
        except ValueError:
            return False

    def can_write(self, requester_id: str, target_member_id: str) -> bool:
        """Check if requester can write data for target member."""
        # Owner can always write their own data
        if requester_id == target_member_id:
            return True

        # Check sharing rules for delegate_write
        for rule in self._config.get("family_sharing", []):
            if rule.get("from") == target_member_id and rule.get("to") == requester_id:
                if rule.get("delegate_write", False):
                    return self.is_delegate_active(target_member_id)

        return False

    def can_read(self, requester_id: str, target_member_id: str, concept: str = "*") -> bool:
        """Check if requester can read target member's data for a concept."""
        if requester_id == target_member_id:
            return True

        for rule in self._config.get("family_sharing", []):
            if rule.get("from") == target_member_id and rule.get("to") == requester_id:
                concepts = rule.get("concepts", [])
                if concepts == ["*"] or concept in concepts:
                    # Also check delegation is still active
                    return self.is_delegate_active(target_member_id)

        return False

    # ── Sharing Rules ────────────────────────────────────────

    def add_sharing_rule(
        self,
        from_id: str,
        to_id: str,
        concepts: list[str],
        delegate_write: bool = False,
    ) -> dict:
        """Add a sharing rule between family members."""
        rules = self._config.setdefault("family_sharing", [])
        rule = {
            "from": from_id,
            "to": to_id,
            "concepts": concepts,
            "delegate_write": delegate_write,
        }

        # Update existing or append
        for i, existing in enumerate(rules):
            if existing.get("from") == from_id and existing.get("to") == to_id:
                rules[i] = rule
                self._save()
                return rule

        rules.append(rule)
        self._save()
        return rule

    def get_sharing_rules(self, member_id: str | None = None) -> list[dict]:
        """Get sharing rules, optionally filtered by member."""
        rules = self._config.get("family_sharing", [])
        if member_id:
            return [r for r in rules if r.get("from") == member_id or r.get("to") == member_id]
        return list(rules)

    # ── Sovereignty Handoff ──────────────────────────────────

    def check_sovereignty_handoffs(self) -> list[dict]:
        """Check for members whose delegation should expire (sovereignty handoff).

        Returns list of members who have reached their delegate_until date.
        """
        now = self._now()
        handoffs: list[dict] = []
        for member in self._config.get("members", []):
            until = member.get("delegate_until")
            if until is None:
                continue
            try:
                if now >= datetime.fromisoformat(until):
                    handoffs.append(
                        {
                            "member_id": member["id"],
                            "display_name": member.get("display_name", ""),
                            "relation": member.get("relation", ""),
                            "delegate_until": until,
                            "status": "sovereignty_due",
                        }
                    )
            except ValueError:
                continue
        return handoffs
