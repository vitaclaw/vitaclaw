#!/usr/bin/env python3
"""Data exchange engine: personal node ↔ hospital/research.

Orchestrates consent-checked, granularity-filtered data sharing:
  - Export (personal → hospital): filter by consent, map to FHIR
  - Import (hospital → personal): parse FHIR, add provenance
  - Visit briefing: auto-assemble pre-visit data package
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .consent_manager import ConsentManager
from .cross_skill_reader import CrossSkillReader
from .fhir_mapper import FHIRMapper
from .health_data_store import HealthDataStore


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class SharePackage:
    """A prepared data sharing package."""

    def __init__(
        self,
        grantee: str,
        purpose: str,
        fhir_bundle: dict | None = None,
        summary_text: str = "",
        record_count: int = 0,
        concepts: list[str] | None = None,
        granularity: str = "raw",
    ):
        self.grantee = grantee
        self.purpose = purpose
        self.fhir_bundle = fhir_bundle
        self.summary_text = summary_text
        self.record_count = record_count
        self.concepts = concepts or []
        self.granularity = granularity
        self.created_at = datetime.now().isoformat(timespec="seconds")


class HealthDataExchange:
    """Orchestrate health data import/export with consent enforcement."""

    def __init__(
        self,
        data_dir: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        now_fn=None,
    ):
        self._now_fn = now_fn or datetime.now
        self._data_dir = data_dir
        self._mapper = FHIRMapper()
        self._reader = CrossSkillReader(data_dir=data_dir)
        self._consent = ConsentManager(
            memory_dir=memory_dir,
            workspace_root=workspace_root,
            now_fn=self._now_fn,
        )

    # ── Export (Personal → Hospital) ─────────────────────────

    def prepare_share(
        self,
        grantee: str,
        purpose: str,
        concepts: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> SharePackage:
        """Prepare a consent-checked FHIR Bundle for sharing.

        Automatically filters by consent policy and applies granularity.
        """
        # If no concepts specified, find all concepts the grantee has access to
        if concepts is None:
            concepts = self._discover_granted_concepts(grantee, purpose)

        # Collect records for each concept
        all_records: list[dict] = []
        granted_concepts: list[str] = []
        granularity = "raw"

        for concept in concepts:
            result = self._consent.check(grantee, concept, purpose)
            if not result.allowed:
                continue
            granted_concepts.append(concept)
            granularity = result.granularity

            records = self._reader.read(concept, start=start, end=end)
            # Log the access
            self._consent.log_access(grantee, concept, purpose, result)
            all_records.extend(records)

        # Apply granularity
        if granularity == "raw":
            fhir_bundle = self._mapper.to_fhir_bundle(all_records)
            summary = f"Sharing {len(all_records)} raw records for {', '.join(granted_concepts)}"
        else:
            transformed = self._consent.apply_granularity(all_records, granularity)
            fhir_bundle = None  # Non-raw data is returned as summary, not FHIR
            summary = json.dumps(transformed, ensure_ascii=False, indent=2)

        return SharePackage(
            grantee=grantee,
            purpose=purpose,
            fhir_bundle=fhir_bundle,
            summary_text=summary,
            record_count=len(all_records),
            concepts=granted_concepts,
            granularity=granularity,
        )

    def _discover_granted_concepts(self, grantee: str, purpose: str) -> list[str]:
        """Find all concepts the grantee has access to."""
        try:
            from .concept_resolver import ConceptResolver

            resolver = ConceptResolver()
            all_concepts = resolver.list_concepts()
        except ImportError:
            return []

        granted: list[str] = []
        for concept in all_concepts:
            result = self._consent.check(grantee, concept, purpose)
            if result.allowed:
                granted.append(concept)
        return granted

    # ── Import (Hospital → Personal) ─────────────────────────

    def ingest_fhir(
        self,
        bundle: dict,
        issuer: str = "",
        issuer_signature: str | None = None,
    ) -> list[dict]:
        """Import a FHIR Bundle into VitaClaw.

        Each record gets _meta.source="import" and _meta.issuer.
        """
        records = self._mapper.from_fhir_bundle(bundle)
        ingested: list[dict] = []

        for record in records:
            meta = record.get("_meta", {})
            meta["source"] = "import"
            if issuer:
                meta["issuer"] = issuer
            if issuer_signature:
                meta["issuer_signature"] = issuer_signature
            record["_meta"] = meta

            # Store via HealthDataStore
            skill = record.get("skill", "fhir-import")
            store = HealthDataStore(skill, data_dir=self._data_dir)
            stored = store.append(
                record_type=record["type"],
                data=record["data"],
                note=record.get("note", ""),
                timestamp=record.get("timestamp"),
                meta=meta,
            )
            ingested.append(stored)

        return ingested

    # ── Visit Briefing ───────────────────────────────────────

    def prepare_visit_briefing(
        self,
        doctor_policy_id: str,
        visit_purpose: str = "follow_up",
    ) -> SharePackage:
        """Auto-assemble pre-visit data package for a doctor.

        Uses the doctor's consent policy to determine what to share.
        """
        policy = self._consent.get_policy(doctor_policy_id)
        if not policy:
            return SharePackage(
                grantee="unknown",
                purpose=visit_purpose,
                summary_text=f"No policy found: {doctor_policy_id}",
            )

        grantee = policy.get("grantee", "")
        concepts = policy.get("concepts", [])
        if concepts == ["*"]:
            concepts = self._discover_granted_concepts(grantee, visit_purpose)

        return self.prepare_share(
            grantee=grantee,
            purpose=visit_purpose,
            concepts=concepts,
        )
