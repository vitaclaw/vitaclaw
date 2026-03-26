#!/usr/bin/env python3
"""SMART Health Card (SHC) generator and verifier for VitaClaw.

Wraps a FHIR Bundle into a JWS (JSON Web Signature) per the SMART Health Card
specification, generates a QR-code URI (shc:/...), and verifies externally
issued SHCs.

Dependencies (optional):
  - cryptography: For ES256 key generation and JWS signing
  - python-jose: For JWS creation (fallback: manual compact JWS)

If neither package is installed the module still loads but operations
that require cryptography will raise RuntimeError.
"""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from datetime import datetime

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def _b64url(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    """Base64url decode with padding restoration."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


class SmartHealthCard:
    """Generate and verify SMART Health Cards (FHIR + JWS + QR)."""

    SHC_HEADER = {"zip": "DEF", "alg": "ES256", "kid": ""}

    def __init__(self, private_key=None, public_key=None, issuer: str = ""):
        self._private_key = private_key
        self._public_key = public_key
        self.issuer = issuer

    # ── Key Management ────────────────────────────────────────

    def generate_keys(self) -> dict:
        """Generate an ES256 key pair for signing SHCs.

        Returns dict with 'private_key' and 'public_key' objects and
        'kid' (key ID derived from public JWK thumbprint).
        """
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography package required for key generation")

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        self._private_key = private_key
        self._public_key = public_key

        kid = self._compute_kid(public_key)
        return {"private_key": private_key, "public_key": public_key, "kid": kid}

    def _compute_kid(self, public_key) -> str:
        """Compute JWK thumbprint as key ID per RFC 7638."""
        numbers = public_key.public_numbers()
        x = numbers.x.to_bytes(32, "big")
        y = numbers.y.to_bytes(32, "big")
        jwk_dict = {"crv": "P-256", "kty": "EC", "x": _b64url(x), "y": _b64url(y)}
        canonical = json.dumps(jwk_dict, sort_keys=True, separators=(",", ":"))
        return _b64url(hashlib.sha256(canonical.encode()).digest())

    # ── SHC Creation ──────────────────────────────────────────

    def create_shc(self, fhir_bundle: dict) -> str:
        """Create a SMART Health Card JWS from a FHIR Bundle.

        Returns the compact JWS string.
        """
        if not HAS_CRYPTO or self._private_key is None:
            raise RuntimeError("Private key required for SHC creation")

        # Build payload (vc = verifiable credential)
        payload = {
            "iss": self.issuer,
            "nbf": int(datetime.now().timestamp()),
            "vc": {
                "type": ["https://smarthealth.cards#health-card"],
                "credentialSubject": {
                    "fhirVersion": "4.0.1",
                    "fhirBundle": fhir_bundle,
                },
            },
        }

        # Header
        kid = self._compute_kid(self._private_key.public_key())
        header = {"zip": "DEF", "alg": "ES256", "kid": kid}
        header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())

        # Compress + encode payload
        payload_json = json.dumps(payload, separators=(",", ":")).encode()
        compressed = zlib.compress(payload_json, level=zlib.Z_BEST_COMPRESSION)
        # Remove zlib header (2 bytes) and checksum (4 bytes) for raw DEFLATE
        payload_b64 = _b64url(compressed[2:-4])

        # Sign
        signing_input = f"{header_b64}.{payload_b64}".encode()
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

        der_sig = self._private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der_sig)
        sig_bytes = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        sig_b64 = _b64url(sig_bytes)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def to_qr_uri(self, jws: str) -> str:
        """Convert a JWS to an shc:/ QR code URI (numeric encoding).

        Each character of the JWS is converted to two digits: ord(c) - 45.
        """
        numeric = "".join(f"{ord(c) - 45:02d}" for c in jws)
        return f"shc:/{numeric}"

    def from_qr_uri(self, uri: str) -> str:
        """Decode an shc:/ URI back to a JWS string."""
        if not uri.startswith("shc:/"):
            raise ValueError("Not a valid shc:/ URI")
        numeric = uri[5:]
        chars = []
        for i in range(0, len(numeric), 2):
            chars.append(chr(int(numeric[i : i + 2]) + 45))
        return "".join(chars)

    # ── SHC Verification ──────────────────────────────────────

    def verify_shc(self, jws: str, public_key=None) -> dict:
        """Verify a SMART Health Card JWS and extract the FHIR Bundle.

        Args:
            jws: Compact JWS string.
            public_key: Optional public key for verification. Uses self._public_key if not given.

        Returns:
            Dict with 'valid' (bool), 'payload' (decoded VC), and 'fhir_bundle'.
        """
        pub = public_key or self._public_key
        if not HAS_CRYPTO or pub is None:
            return {"valid": False, "error": "No public key available", "payload": None, "fhir_bundle": None}

        parts = jws.split(".")
        if len(parts) != 3:
            return {"valid": False, "error": "Invalid JWS format", "payload": None, "fhir_bundle": None}

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        sig_bytes = _b64url_decode(sig_b64)
        r = int.from_bytes(sig_bytes[:32], "big")
        s = int.from_bytes(sig_bytes[32:], "big")

        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

        der_sig = encode_dss_signature(r, s)

        try:
            pub.verify(der_sig, signing_input, ec.ECDSA(hashes.SHA256()))
        except Exception:
            return {"valid": False, "error": "Signature verification failed", "payload": None, "fhir_bundle": None}

        # Decompress payload
        compressed = _b64url_decode(payload_b64)
        # Add zlib header for raw deflate data
        decompressed = zlib.decompress(compressed, -zlib.MAX_WBITS)
        payload = json.loads(decompressed)

        fhir_bundle = payload.get("vc", {}).get("credentialSubject", {}).get("fhirBundle")

        return {"valid": True, "payload": payload, "fhir_bundle": fhir_bundle}
