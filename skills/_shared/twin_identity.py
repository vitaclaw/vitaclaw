#!/usr/bin/env python3
"""Identity management for VitaClaw Digital Twin.

Manages owner identity, twin instance, family members, and Ed25519 key pairs.
The owner (real person) and twin (digital instance) are separate identities.
The twin acts on behalf of the owner, but its decisions can be audited.

v1: Local Ed25519 keys for signing records.
v2: DID (W3C Decentralized Identifier) support.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class TwinIdentity:
    """Manage identities for the personal health data node.

    Identity hierarchy:
      owner (real person) → twin (digital instance) → family members
    """

    def __init__(
        self,
        identity_path: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
    ):
        if identity_path:
            self._identity_path = Path(identity_path)
        elif memory_dir:
            self._identity_path = Path(memory_dir) / "_identity.yaml"
        elif workspace_root:
            self._identity_path = Path(workspace_root) / "memory" / "health" / "_identity.yaml"
        else:
            self._identity_path = _repo_root() / "memory" / "health" / "_identity.yaml"

        self._keys_dir = self._identity_path.parent / "_keys"
        self._config: dict = {}
        self._private_key = None
        self._public_key = None
        self._load()

    def _load(self) -> None:
        if self._identity_path.exists() and HAS_YAML:
            self._config = yaml.safe_load(self._identity_path.read_text(encoding="utf-8")) or {}

    def _save(self) -> None:
        if not HAS_YAML:
            self._identity_path.parent.mkdir(parents=True, exist_ok=True)
            self._identity_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return
        self._identity_path.parent.mkdir(parents=True, exist_ok=True)
        self._identity_path.write_text(
            yaml.dump(self._config, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )

    # ── Owner & Twin Identity ────────────────────────────────

    @property
    def owner_id(self) -> str:
        return self._config.get("owner", {}).get("id", "")

    @property
    def twin_id(self) -> str:
        return self._config.get("twin", {}).get("id", "")

    @property
    def display_name(self) -> str:
        return self._config.get("owner", {}).get("display_name", "")

    def initialize(
        self,
        owner_id: str,
        display_name: str = "",
        generate_keys: bool = True,
    ) -> dict:
        """Initialize identity for a new user."""
        twin_id = f"{owner_id}:twin"
        now = datetime.now().isoformat(timespec="seconds")

        self._config = {
            "owner": {
                "id": owner_id,
                "display_name": display_name,
                "created_at": now,
            },
            "twin": {
                "id": twin_id,
                "created_at": now,
                "domains": {
                    "health": {"status": "active", "since": now[:10]},
                    "cognitive": {"status": "planned"},
                    "social": {"status": "planned"},
                },
            },
            "family": [],
        }

        if generate_keys and HAS_CRYPTO:
            pub_key_b64 = self._generate_keypair()
            self._config["owner"]["public_key"] = f"ed25519:{pub_key_b64}"

        self._save()
        return self._config

    def _generate_keypair(self) -> str:
        """Generate Ed25519 keypair. Returns base64 public key."""
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography package required for key generation")

        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        self._keys_dir.mkdir(parents=True, exist_ok=True)

        # Save private key (PEM)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        (self._keys_dir / "owner.pem").write_bytes(private_pem)

        # Return base64 public key
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(public_bytes).decode()

    def _load_private_key(self):
        """Load private key from disk."""
        if self._private_key:
            return self._private_key
        if not HAS_CRYPTO:
            return None
        key_path = self._keys_dir / "owner.pem"
        if not key_path.exists():
            return None
        self._private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        return self._private_key

    def sign_record(self, record: dict) -> str | None:
        """Sign a record's content with the owner's Ed25519 key.

        Returns base64 signature or None if keys not available.
        """
        private_key = self._load_private_key()
        if not private_key:
            return None

        # Sign the canonical JSON of the record (excluding _meta.signature)
        signable = {k: v for k, v in record.items() if k != "_meta"}
        signable_json = json.dumps(signable, sort_keys=True, ensure_ascii=False).encode()
        signature = private_key.sign(signable_json)
        return base64.b64encode(signature).decode()

    def verify_signature(self, record: dict, signature_b64: str) -> bool:
        """Verify a record's signature."""
        if not HAS_CRYPTO:
            return False

        pub_key_str = self._config.get("owner", {}).get("public_key", "")
        if not pub_key_str.startswith("ed25519:"):
            return False

        pub_bytes = base64.b64decode(pub_key_str[8:])
        public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        signable = {k: v for k, v in record.items() if k != "_meta"}
        signable_json = json.dumps(signable, sort_keys=True, ensure_ascii=False).encode()

        try:
            public_key.verify(base64.b64decode(signature_b64), signable_json)
            return True
        except Exception:
            return False

    # ── Family ───────────────────────────────────────────────

    def add_family_member(
        self,
        member_id: str,
        relation: str,
        delegate_until: str | None = None,
    ) -> dict:
        """Add a family member to the identity."""
        member = {
            "id": member_id,
            "relation": relation,
            "twin_id": f"{member_id}:twin",
            "delegate_until": delegate_until,
        }
        family = self._config.setdefault("family", [])
        # Update existing or append
        for i, existing in enumerate(family):
            if existing.get("id") == member_id:
                family[i] = member
                self._save()
                return member
        family.append(member)
        self._save()
        return member

    def get_family(self) -> list[dict]:
        return self._config.get("family", [])

    def is_delegate_active(self, member_id: str, now: datetime | None = None) -> bool:
        """Check if delegation for a family member is still active."""
        now = now or datetime.now()
        for member in self._config.get("family", []):
            if member.get("id") == member_id:
                until = member.get("delegate_until")
                if until is None:
                    return True  # Permanent delegation
                try:
                    return now < datetime.fromisoformat(until)
                except ValueError:
                    return False
        return False

    def get_config(self) -> dict:
        return dict(self._config)
