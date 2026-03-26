#!/usr/bin/env python3
"""Computable consent and authorization for VitaClaw data sharing.

Manages who can see what, at what granularity, and logs all access.
Consent policies are YAML files — human-readable, version-controlled.

Granularity levels:
  - raw: Full original records
  - summary: Statistical aggregates only (mean, trend, range)
  - trend_only: Only direction (rising/falling/stable)
  - existence_only: Only yes/no for data existence (ZKP-inspired)
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


class ConsentResult:
    """Result of a consent check."""

    def __init__(
        self,
        allowed: bool,
        policy_id: str | None = None,
        granularity: str = "raw",
        reason: str = "",
    ):
        self.allowed = allowed
        self.policy_id = policy_id
        self.granularity = granularity
        self.reason = reason

    def __bool__(self) -> bool:
        return self.allowed


class ConsentManager:
    """Manage consent policies for health data sharing."""

    GRANULARITY_LEVELS = ("raw", "summary", "trend_only", "existence_only")

    def __init__(
        self,
        policy_path: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        if policy_path:
            self._policy_path = Path(policy_path)
        elif memory_dir:
            self._policy_path = Path(memory_dir) / "_consent_policies.yaml"
        elif workspace_root:
            self._policy_path = Path(workspace_root) / "memory" / "health" / "_consent_policies.yaml"
        else:
            self._policy_path = _repo_root() / "memory" / "health" / "_consent_policies.yaml"

        self._audit_path = self._policy_path.parent / "_access_audit.jsonl"
        self._policies: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self._policy_path.exists():
            return
        try:
            if HAS_YAML:
                raw = yaml.safe_load(self._policy_path.read_text(encoding="utf-8")) or {}
            else:
                raw = json.loads(self._policy_path.read_text(encoding="utf-8"))
            self._policies = raw.get("policies", [])
        except Exception:
            self._policies = []

    def _now(self) -> datetime:
        return self._now_fn()

    def _save(self) -> None:
        self._policy_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"policies": self._policies}
        if HAS_YAML:
            self._policy_path.write_text(
                yaml.dump(data, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )
        else:
            self._policy_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    # ── Policy CRUD ──────────────────────────────────────────

    def add_policy(self, policy: dict) -> dict:
        """Add or update a consent policy."""
        policy_id = policy.get("id", "")
        # Update existing
        for i, existing in enumerate(self._policies):
            if existing.get("id") == policy_id:
                self._policies[i] = policy
                self._save()
                return policy
        self._policies.append(policy)
        self._save()
        return policy

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a consent policy by ID."""
        before = len(self._policies)
        self._policies = [p for p in self._policies if p.get("id") != policy_id]
        if len(self._policies) < before:
            self._save()
            return True
        return False

    def get_policy(self, policy_id: str) -> dict | None:
        for p in self._policies:
            if p.get("id") == policy_id:
                return p
        return None

    def list_policies(self) -> list[dict]:
        return list(self._policies)

    # ── Consent Checking ─────────────────────────────────────

    def check(self, grantee: str, concept: str, purpose: str = "") -> ConsentResult:
        """Check if a grantee has access to a specific concept.

        Returns ConsentResult with allowed, granularity, and policy details.
        """
        now = self._now()

        for policy in self._policies:
            if not self._matches_grantee(policy, grantee):
                continue
            if not self._matches_concept(policy, concept):
                continue
            if purpose and policy.get("purpose") and policy["purpose"] != purpose:
                continue
            if not self._is_valid(policy, now):
                continue
            if policy.get("requires_break_glass", False):
                # Emergency policies need explicit break-glass declaration
                if purpose != "emergency":
                    continue

            return ConsentResult(
                allowed=True,
                policy_id=policy.get("id"),
                granularity=policy.get("granularity", "raw"),
                reason=f"Policy {policy.get('id')} grants access",
            )

        return ConsentResult(
            allowed=False,
            reason=f"No policy grants {grantee} access to {concept}",
        )

    def _matches_grantee(self, policy: dict, grantee: str) -> bool:
        policy_grantee = policy.get("grantee", "")
        if policy_grantee == grantee:
            return True
        # Wildcard type matching: "any:emergency_physician" matches any emergency doc
        if ":" in policy_grantee:
            ptype, prole = policy_grantee.split(":", 1)
            if ptype == "any":
                return grantee.endswith(f":{prole}") or grantee == prole
        return False

    def _matches_concept(self, policy: dict, concept: str) -> bool:
        concepts = policy.get("concepts", [])
        if concepts == ["*"] or concept in concepts:
            return True
        return False

    def _is_valid(self, policy: dict, now: datetime) -> bool:
        valid_from = policy.get("valid_from")
        valid_until = policy.get("valid_until")
        now_str = now.isoformat()[:10]

        if valid_from and now_str < valid_from:
            return False
        if valid_until and now_str > valid_until:
            return False
        return True

    # ── Record Filtering ─────────────────────────────────────

    def filter_records(self, records: list[dict], grantee: str, purpose: str = "") -> list[dict]:
        """Filter records based on consent policies for a grantee."""
        filtered: list[dict] = []
        for record in records:
            meta = record.get("_meta", {})
            concept = meta.get("concept", "")
            if not concept:
                # Try to resolve from type
                try:
                    from concept_resolver import ConceptResolver

                    resolver = ConceptResolver()
                    concept = resolver.resolve_from_type(record.get("type", "")) or ""
                except (ImportError, KeyError):
                    pass

            if not concept:
                continue

            result = self.check(grantee, concept, purpose)
            if result.allowed:
                filtered.append(record)

        return filtered

    def apply_granularity(self, records: list[dict], granularity: str) -> list[dict] | dict:
        """Transform records according to granularity level.

        - raw: return as-is
        - summary: return statistical summary
        - trend_only: return only trend direction
        - existence_only: return only count
        """
        if granularity == "raw":
            return records

        if granularity == "existence_only":
            return {"exists": len(records) > 0, "count": len(records)}

        if granularity == "summary":
            if not records:
                return {"count": 0}
            # Compute basic statistics from numeric fields in data
            all_values: dict[str, list[float]] = {}
            for record in records:
                for key, val in record.get("data", {}).items():
                    if isinstance(val, (int, float)):
                        all_values.setdefault(key, []).append(val)
            summary = {"count": len(records), "time_range": {}}
            timestamps = [r.get("timestamp", "") for r in records if r.get("timestamp")]
            if timestamps:
                summary["time_range"] = {"start": min(timestamps), "end": max(timestamps)}
            for field, values in all_values.items():
                summary[field] = {
                    "mean": round(sum(values) / len(values), 2),
                    "min": min(values),
                    "max": max(values),
                }
            return summary

        if granularity == "trend_only":
            if not records:
                return {"trend": "no_data"}
            # Simple trend from first and last values
            all_values: dict[str, list[float]] = {}
            for record in records:
                for key, val in record.get("data", {}).items():
                    if isinstance(val, (int, float)):
                        all_values.setdefault(key, []).append(val)
            trends = {}
            for field, values in all_values.items():
                if len(values) >= 2:
                    diff = values[-1] - values[0]
                    if abs(diff) < 0.01:
                        trends[field] = "stable"
                    elif diff > 0:
                        trends[field] = "rising"
                    else:
                        trends[field] = "falling"
                else:
                    trends[field] = "insufficient_data"
            return {"trend": trends, "count": len(records)}

        return records

    # ── Audit Logging ────────────────────────────────────────

    def log_access(self, grantee: str, concept: str, purpose: str, result: ConsentResult) -> None:
        """Write access attempt to audit log."""
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": self._now().isoformat(timespec="seconds"),
            "grantee": grantee,
            "concept": concept,
            "purpose": purpose,
            "allowed": result.allowed,
            "policy_id": result.policy_id,
            "granularity": result.granularity,
        }
        with self._audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
