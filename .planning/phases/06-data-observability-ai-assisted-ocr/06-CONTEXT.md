# Phase 6: Data Observability & AI-Assisted OCR - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Two capabilities: (1) HealthDataStore.stats() API + CLI dashboard for data visibility, (2) LLM-enhanced OCR field extraction with LOINC concept mapping and skill routing suggestions.

</domain>

<decisions>
## Implementation Decisions

### Data Observability
- **D-01:** Add `stats()` method to `HealthDataStore` class. Returns dict with: `record_count`, `last_updated` (ISO timestamp), `earliest_record`, `latest_record`, `time_span_days` for a given skill. Accepts optional `person_id` parameter for per-person filtering.
- **D-02:** Add a class-level `global_stats()` classmethod that iterates all skill data directories under `data/` and returns aggregated stats per skill. Accepts optional `person_id`.
- **D-03:** CLI script `scripts/health_data_dashboard.py` outputs a markdown table: Skill | Records | Last Updated | Time Span | Person. Supports `--person-id`, `--format markdown|json`, `--sort-by records|updated|span`.
- **D-04:** Exposed as `skills/health-data-dashboard/SKILL.md` for AI invocation.

### AI-Assisted OCR
- **D-05:** LLM post-processing is implemented as a new module `skills/medical-document-ocr/scripts/ocr_llm_enhancer.py`. It takes raw OCR text output and uses the OpenClaw runtime's LLM (via the host AI) to extract structured fields — no direct API calls, no cost concerns, since the LLM is already running.
- **D-06:** The enhancer is invoked by the OCR pipeline AFTER PaddleOCR extraction and BEFORE user confirmation. It enhances the staging JSON by: (1) correcting misread values using medical context, (2) identifying field types (e.g., "GLU" → fasting glucose), (3) adding units where missing.
- **D-07:** LOINC mapping uses `ConceptResolver` with `schemas/health-concepts.yaml`. Each extracted field is matched to a concept ID. New concepts are logged as "unmapped" rather than silently dropped.
- **D-08:** Skill routing: each mapped concept has a `producer` field in health-concepts.yaml pointing to the skill that tracks it (e.g., `blood-pressure-tracker`). The enhancer suggests which skill should store each field.
- **D-09:** The LLM enhancer is optional — if the host AI is unavailable (e.g., running in pure script mode), the pipeline falls back to PaddleOCR-only extraction. Graceful degradation, not failure.

### Claude's Discretion
- LLM prompt design for field extraction (few-shot examples, output format)
- How to handle concepts not in health-concepts.yaml (log + suggest addition vs ignore)
- Dashboard visual formatting details (column widths, empty state messages)
- Whether stats() should cache results or always scan fresh

</decisions>

<canonical_refs>
## Canonical References

### Data Layer
- `skills/_shared/health_data_store.py` — Add stats() and global_stats() methods
- `skills/_shared/cross_skill_reader.py` — Reference for cross-skill data access patterns

### OCR Pipeline (Phase 2)
- `skills/medical-document-ocr/scripts/ocr_pipeline.py` — Pipeline to integrate LLM enhancer into
- `skills/medical-document-ocr/scripts/ocr_store.py` — Storage bridge (downstream of enhancer)

### Concept Registry
- `schemas/health-concepts.yaml` — Health concept registry for LOINC mapping
- `skills/_shared/concept_resolver.py` — ConceptResolver class for concept lookup

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ConceptResolver`: Already maps concept IDs to skills, LOINC codes, field schemas. Direct use for LOINC mapping.
- `OCRPipeline.process()`: Returns staging JSON that can be enhanced before confirmation.
- `HealthDataStore`: All JSONL query methods already exist — stats() aggregates existing data.

### Integration Points
- `ocr_llm_enhancer.py` slots between `ocr_pipeline.process()` output and `ocr_store.store_confirmed_fields()` input
- `stats()` reads from existing JSONL files in `data/{skill-name}/`
- Dashboard CLI reads from `global_stats()` output

</code_context>

<specifics>
## Specific Ideas

- LLM enhancer uses the host AI (OpenClaw runtime) — zero additional cost, no API key needed
- Stats should be fast — scan JSONL file line counts rather than parsing every record
- LOINC mapping logs unmapped concepts rather than failing — keeps the pipeline flowing

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-data-observability-ai-assisted-ocr*
*Context gathered: 2026-03-26*
