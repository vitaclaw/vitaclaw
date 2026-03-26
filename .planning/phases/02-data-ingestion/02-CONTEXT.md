# Phase 2: Data Ingestion - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Three data ingestion channels: (1) guided onboarding for user profile setup, (2) file-based wearable data import from Google Fit, Huawei Health, and Xiaomi/Mi Fitness, and (3) OCR pipeline for Chinese medical documents (体检报告, 检验单, 门诊病历, 处方单). All channels write to person-aware storage via the person_id data layer from Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Onboarding Flow
- **D-01:** Onboarding is implemented as a SKILL.md (e.g., `skills/health-onboarding/SKILL.md`) with structured prompt that guides the AI through a conversational flow. No Python UI — the AI runtime handles the conversation.
- **D-02:** Onboarding collects: basic demographics (age, sex, height), chronic conditions, current medications + dosages, supplements, primary health goals, preferred reminder cadence, and care team (primary doctor info). Flow is conversational, not form-like.
- **D-03:** Onboarding output populates three files: `USER.md` (preferences), `IDENTITY.md` (role + service target), and `memory/health/_health-profile.md` (structured health baseline). Also registers person in `_family.yaml` if family mode is active.
- **D-04:** Re-running onboarding merges updates into existing files rather than overwriting. Existing data is preserved unless explicitly contradicted.

### Device Import
- **D-05:** All importers follow the Apple Health import pattern: a Python script in `scripts/` that reads an export file, parses records, maps to HealthDataStore JSONL format, and appends with dedup.
- **D-06:** Each importer is a separate script: `scripts/import_google_fit_export.py`, `scripts/import_huawei_health_export.py`, `scripts/import_xiaomi_health_export.py`. Plus a corresponding SKILL.md that the AI can invoke.
- **D-07:** Shared base class `HealthImporterBase` in `skills/_shared/health_importer_base.py` provides: file discovery (ZIP extraction), record mapping, fuzzy dedup (timestamp within 60s + metric within 5% = same record), progress reporting, and person_id passthrough.
- **D-08:** Metrics to extract from all platforms: heart rate, steps, sleep (duration + stages if available), weight, blood pressure (if available), activities (type + duration + calories). Unsupported metric types are logged as warnings and skipped, not errors.
- **D-09:** Google Fit format: Google Takeout ZIP → CSV files (daily activity, heart rate) + TCX (activities). Huawei: Settings export ZIP → CSV/JSON + GPX. Xiaomi: Account data export ZIP → CSV files.
- **D-10:** Fuzzy dedup across devices: when importing from a second device, records with timestamps within 60 seconds and values within 5% of an existing record are treated as duplicates and skipped. The first-imported record wins.

### OCR Pipeline
- **D-11:** OCR pipeline is implemented as a SKILL.md (`skills/medical-document-ocr/SKILL.md`) + Python implementation that orchestrates: (1) document type classification, (2) text/table extraction via PaddleOCR PP-StructureV2, (3) structured field extraction, (4) display for user confirmation, (5) storage on confirmation.
- **D-12:** Supported document types in priority order: 体检报告 (physical exam report — table-heavy, most common), 检验单 (lab test results — structured tables), 门诊病历 (outpatient records — mixed text), 处方单 (prescriptions — medication lists). The system should attempt all types rather than requiring user to specify.
- **D-13:** Table extraction uses PP-StructureV2 for lab reports and exam reports (table layouts). Raw text OCR (PP-OCRv5) is used for prescriptions and outpatient records (paragraph text).
- **D-14:** After OCR extraction, structured fields are displayed to the user in a clear format showing: extracted value, unit, reference range (if found), and the item name mapped to a health concept. User confirms, edits, or rejects each field before storage.
- **D-15:** Confirmed fields are stored as HealthDataStore records (mapped to appropriate skill data directories, e.g., blood-pressure-tracker, blood-sugar-tracker) AND the original document image/PDF is archived in `memory/health/files/` with metadata.
- **D-16:** When OCR extraction fails or confidence is low (<60%), the system shows the raw text and asks the user to manually identify key values rather than silently dropping data.
- **D-17:** OCR pipeline accepts image files (JPG, PNG, HEIC) and PDF files. HEIC support via pillow-heif (already a dependency).

### Claude's Discretion
- Exact Google Fit / Huawei / Xiaomi CSV field name mappings — these vary by export version and should be discovered defensively from actual export files.
- PaddleOCR model selection and initialization parameters.
- Whether to use LLM post-processing for field extraction (may improve accuracy for messy documents).
- Onboarding question phrasing and conversation flow design.
- Progress reporting format during import (print statements vs structured output).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Importers (reference pattern)
- `scripts/import_apple_health_export.py` — Apple Health XML importer, the reference pattern for all new importers
- `skills/apple-health-digest/SKILL.md` — How Apple Health import is exposed as a skill

### OCR Infrastructure
- `privacy_desensitize.py` — Existing PaddleOCR usage in the project
- `skills/medical-record-organizer/scripts/redact_ocr.py` — Existing OCR text processing
- `skills/medical-record-organizer/SKILL.md` — Medical record organization skill

### Data Layer (from Phase 1)
- `skills/_shared/health_data_store.py` — JSONL storage with person_id support
- `skills/_shared/health_memory.py` — Memory writer with per-person paths
- `schemas/health-concepts.yaml` — Health concept registry for field mapping
- `schemas/health-data-record.schema.json` — Record schema (now includes person_id)

### Onboarding
- `scripts/init_health_workspace.py` — Existing workspace init script
- `USER.md` — User preferences template (currently empty)
- `IDENTITY.md` — Agent identity template (currently empty)
- `memory/health/_health-profile.md` — Health profile structure

### Research
- `.planning/research/FEATURES.md` — Feature landscape with device import format details
- `.planning/research/STACK.md` — PaddleOCR PP-StructureV2 recommendations
- `.planning/research/PITFALLS.md` — OCR and import pitfalls to avoid

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/import_apple_health_export.py`: Complete importer with ZIP extraction, XML parsing, JSONL writing, and dedup. Direct reference for new importers.
- `privacy_desensitize.py`: PaddleOCR initialization and usage patterns. Shows how to handle model loading and image processing.
- `skills/medical-record-organizer/scripts/redact_ocr.py`: Line-by-line OCR text processing. Needs upgrade to PP-StructureV2 for table extraction.
- `skills/_shared/concept_resolver.py` + `schemas/health-concepts.yaml`: Concept registry for mapping OCR-extracted lab items to health data types.

### Established Patterns
- Skill = SKILL.md (prompt) + optional Python implementation + optional scripts/
- CLI scripts use argparse with --format markdown|json
- Health data written to `data/{skill-name}/records.jsonl` via HealthDataStore
- Import scripts are standalone CLI tools invocable by the AI runtime

### Integration Points
- New importers write via `HealthDataStore.append()` with person_id
- OCR results write to skill-specific data directories (blood-pressure-tracker, etc.)
- Onboarding writes to USER.md, IDENTITY.md, _health-profile.md
- All new skills need SKILL.md with YAML frontmatter for manifest discovery

</code_context>

<specifics>
## Specific Ideas

- Fuzzy dedup (60s window, 5% tolerance) prevents duplicate records when users import from multiple wearable devices
- OCR confirmation is mandatory — no auto-commit of extracted health values
- PP-StructureV2 for table layouts (lab reports), PP-OCRv5 for text (prescriptions)
- Onboarding is a SKILL.md conversation, not a Python script with prompts

</specifics>

<deferred>
## Deferred Ideas

- **AI-powered field extraction with LOINC mapping** (OCR-V2-01, OCR-V2-02) — v2 enhancement, not in this phase
- **Conversational profiling** (ONBD-V2-01, ONBD-V2-02) — v2 enhancement for smarter onboarding

</deferred>

---

*Phase: 02-data-ingestion*
*Context gathered: 2026-03-26*
