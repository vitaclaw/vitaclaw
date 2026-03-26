# Architecture Patterns

**Domain:** Integrating OCR pipeline, multi-device import, family multi-person, and visualization into existing VitaClaw skill-based health architecture
**Researched:** 2026-03-26

## Recommended Architecture

The four new capabilities map onto the existing layered architecture without requiring structural rewrites. Each new capability introduces components that slot into existing layers: new shared runtime modules in `skills/_shared/`, new skills in `skills/`, new CLI scripts in `scripts/`, and data stored in existing `data/` and `memory/health/` paths. The critical architectural change is introducing a **person_id** dimension that threads through HealthDataStore, HealthMemoryWriter, and all downstream consumers.

### High-Level Component Map

```
User Input
  |
  v
+-----------------------------------------------------+
| OpenClaw Runtime / Chief-of-Staff Router             |
+-----------------------------------------------------+
  |           |            |              |
  v           v            v              v
[OCR         [Device      [Person        [Visualization
 Pipeline]    Importers]   Context]       Engine]
  |           |            |              |
  +-----+-----+-----+------+-----+--------+
        |                        |
        v                        v
+------------------+    +------------------+
| HealthDataStore  |    | HealthMemoryWriter|
| (JSONL, per-skill|    | (markdown, per-  |
|  per-person)     |    |  person memory)  |
+------------------+    +------------------+
        |                        |
        v                        v
   data/{skill}/            memory/health/
   records.jsonl            daily/, items/, etc.
```

### Component Boundaries

| Component | Responsibility | Communicates With | New/Modified |
|-----------|---------------|-------------------|--------------|
| **OCR Pipeline** (`skills/_shared/health_ocr_pipeline.py`) | Orchestrate image/PDF intake: detect document type, run OCR, extract structured fields, present for confirmation, write to data store | PaddleOCR (external), HealthDataStore, HealthMemoryWriter, PatientArchiveBridge | **New** shared module |
| **Document Type Classifier** (inside OCR pipeline) | Classify input as: lab report, physical exam report, prescription, discharge summary, imaging report | OCR Pipeline (parent) | **New** (part of pipeline) |
| **Device Importer Base** (`skills/_shared/device_importer_base.py`) | Abstract base class defining the file-import contract: parse export file, map to health concepts, write via HealthDataStore | HealthDataStore, ConceptResolver | **New** shared module |
| **Google Fit Importer** (`skills/_shared/google_fit_bridge.py`) | Parse Google Fit Takeout JSON/CSV, map activities/vitals to VitaClaw concepts | DeviceImporterBase, HealthDataStore | **New** shared module |
| **Huawei Health Importer** (`skills/_shared/huawei_health_bridge.py`) | Parse Huawei Health export (JSON/CSV), map to VitaClaw concepts | DeviceImporterBase, HealthDataStore | **New** shared module |
| **Xiaomi Health Importer** (`skills/_shared/xiaomi_health_bridge.py`) | Parse Mi Fitness export data, map to VitaClaw concepts | DeviceImporterBase, HealthDataStore | **New** shared module |
| **Person Context Manager** (`skills/_shared/person_context.py`) | Resolve current person_id from conversation context, manage person registry, provide path helpers for per-person data/memory | HealthDataStore, HealthMemoryWriter, all skills | **New** shared module |
| **Visualization Engine** (`skills/_shared/health_chart_engine.py`) | Generate matplotlib charts from JSONL data: trend lines, multi-metric overlays, correlation plots | HealthDataStore (read), matplotlib | **New** shared module |
| **HealthDataStore** (`skills/_shared/health_data_store.py`) | JSONL record storage with per-skill directories | All data producers and consumers | **Modified**: add optional `person_id` to record envelope and query filters |
| **HealthMemoryWriter** (`skills/_shared/health_memory.py`) | Markdown memory management | All skills | **Modified**: support per-person memory subdirectories |
| **CrossSkillReader** (`skills/_shared/cross_skill_reader.py`) | Registry-driven cross-skill data aggregation | ConceptResolver, HealthDataStore | **Modified**: add `person_id` filter parameter |
| **PatientArchiveBridge** (`skills/_shared/patient_archive_bridge.py`) | Bridge patient archives into workspace | OCR Pipeline (as data source), HealthMemoryWriter | **Modified**: OCR output feeds into archive |
| **ConceptResolver** (`skills/_shared/concept_resolver.py`) | Map health concept IDs to metadata | health-concepts.yaml | **Modified**: add concepts for OCR-extracted fields (lab results, exam items) |

## Data Flow

### 1. OCR Pipeline Flow

```
Photo/PDF input
  |
  v
[Document Type Classifier]
  |  Determines: lab_report | physical_exam | prescription | discharge | imaging
  v
[PaddleOCR text extraction]
  |  Raw text boxes with coordinates
  v
[Field Extractor (per document type)]
  |  Structured dict: {metric: value, unit, reference_range, ...}
  v
[User Confirmation Step]  <-- CRITICAL: user reviews extracted values before commit
  |  User confirms, corrects, or rejects
  v
[HealthDataStore.append()]
  |  JSONL record with _meta.source = "ocr", _meta.document_type, _meta.original_file
  v
[HealthMemoryWriter]
  |  Updates daily log + relevant items/ files
  v
[PatientArchiveBridge] (optional)
     Stores original image + structured data in patient archive
```

**Key design decision:** The pipeline MUST pause for user confirmation before writing to the data store. Medical data accuracy is non-negotiable. The OCR output is a draft that the user approves.

**Where existing code lives:** `privacy_desensitize.py` already has PaddleOCR integration and PII detection. `skills/medical-record-organizer/scripts/redact_ocr.py` has regex-based field extraction for Chinese medical documents. The new pipeline reuses these OCR and PII patterns but adds structured field extraction and the confirmation-then-write workflow.

### 2. Multi-Device Import Flow

```
User exports data file from device app
  (Google Fit: Takeout ZIP → JSON/CSV
   Huawei: Health app export → JSON/CSV
   Xiaomi: Mi Fitness export → CSV)
  |
  v
[CLI Script: scripts/import_{device}_health.py]
  |  Follows same pattern as scripts/import_apple_health_export.py
  v
[Device-Specific Bridge: {device}_health_bridge.py]
  |  Parses device-specific format
  |  Maps to VitaClaw health concepts via ConceptResolver
  |  Deduplicates against existing records (by timestamp + type)
  v
[HealthDataStore.append()] per concept
  |  Each record tagged with _meta.source = "{device}"
  v
[PatientArchiveBridge] (optional)
  |  Writes summary to patient archive
  v
[HealthTimelineBuilder]
     Regenerates unified timeline
```

**Pattern to follow:** The existing `AppleHealthImporter` class in `skills/_shared/apple_health_bridge.py` is the reference implementation. It takes a workspace root, parses device-specific XML, maps to concepts, and syncs to workspace. New importers follow this exact contract but parse different file formats.

**Deduplication is critical:** Users may re-import overlapping date ranges. Each importer must detect and skip duplicate records by matching on (timestamp, record_type, key metric values).

### 3. Family Multi-Person Data Flow

```
User says: "Record mom's blood pressure 135/85"
  |
  v
[PersonContextManager.resolve(conversation_context)]
  |  Resolves person_id from:
  |    1. Explicit mention ("mom's", "for dad")
  |    2. Active person context (set by "switch to mom")
  |    3. Default person (self)
  |
  |  Returns: person_id = "mom" (or "self" for default)
  v
[Skill execution with person_id]
  |
  v
[HealthDataStore.append(person_id="mom")]
  |  Record envelope gains: {"person_id": "mom", ...}
  |  File path: data/{skill}/records.jsonl (all persons, filtered by person_id field)
  v
[HealthMemoryWriter(person_id="mom")]
  |  Writes to: memory/health/persons/mom/daily/YYYY-MM-DD.md
  |             memory/health/persons/mom/items/blood-pressure.md
  |  (Default "self" person continues using existing paths for backward compat)
  v
[CrossSkillReader.read(concept, person_id="mom")]
     Queries scoped to person
```

**Data isolation strategy:**

| Aspect | Default (self) | Family Member |
|--------|---------------|---------------|
| JSONL records | `data/{skill}/records.jsonl` (no person_id or person_id="self") | Same file, records tagged with `person_id` field |
| Daily memory | `memory/health/daily/` | `memory/health/persons/{id}/daily/` |
| Item memory | `memory/health/items/` | `memory/health/persons/{id}/items/` |
| Health profile | `memory/health/_health-profile.md` | `memory/health/persons/{id}/_health-profile.md` |
| Distillation | `memory/health/weekly/` etc. | `memory/health/persons/{id}/weekly/` etc. |
| Patient archive | `~/.openclaw/patients/{patient-id}/` | `~/.openclaw/patients/{person-patient-id}/` |

**Backward compatibility:** The default person ("self") keeps using existing paths. The `person_id` field in JSONL is optional -- records without it are treated as "self". This means zero migration needed for existing single-user data.

**Person registry:** A simple `memory/health/_family-registry.md` file maps person IDs to display names, relationships, and health profiles:

```markdown
## Family Members

| ID | Name | Relationship | Profile |
|----|------|-------------|---------|
| self | [user name] | self | memory/health/_health-profile.md |
| mom | [mom name] | mother | memory/health/persons/mom/_health-profile.md |
| dad | [dad name] | father | memory/health/persons/dad/_health-profile.md |
```

### 4. Visualization Flow

```
User asks: "Show me my blood pressure trend this month"
  |
  v
[Skill routes to visualization]
  |
  v
[HealthChartEngine.trend_chart(concept="blood-pressure", person_id="self", period="1M")]
  |
  |  1. Reads records via CrossSkillReader or HealthDataStore
  |  2. Filters by person_id, date range
  |  3. Generates matplotlib figure
  |  4. Saves PNG to data/{skill}/charts/{concept}_{period}_{timestamp}.png
  |  5. Returns file path for display
  |
  v
[Chart PNG file] → displayed in conversation or included in reports
```

**Chart types to support:**

| Chart Type | Use Case | Data Source |
|------------|----------|-------------|
| Single metric trend | BP over time, weight over time | One concept, time series |
| Dual-axis overlay | BP + medication changes | Two concepts, shared timeline |
| Correlation scatter | Sleep duration vs. blood glucose | Two concepts, paired by date |
| Dashboard (multi-panel) | Visit briefing, annual report | Multiple concepts, composite |

**Integration with existing features:**
- `generate_visit_briefing.py` can embed trend charts in briefing output
- Annual health report scenario can include dashboard charts
- Heartbeat can attach anomaly charts when alerting on threshold violations

## Patterns to Follow

### Pattern 1: Importer as Shared Module + CLI Script + Skill

Every data import capability follows a three-layer pattern established by Apple Health:

```
skills/_shared/{source}_bridge.py    # Shared module: parsing + mapping logic
scripts/import_{source}_health.py    # CLI entry point: argparse wrapper
skills/{source}-health-digest/       # Skill: SKILL.md for conversational access
```

**Why:** The shared module is testable and reusable. The CLI script enables automation. The skill enables conversational use. All three are needed.

### Pattern 2: Record Envelope Extension (not Replacement)

New fields (like `person_id`) are added to the JSONL record envelope as optional fields, never replacing existing ones:

```python
# Current envelope
{"id": "...", "type": "bp", "timestamp": "...", "skill": "blood-pressure-tracker", "data": {...}}

# Extended envelope (backward compatible)
{"id": "...", "type": "bp", "timestamp": "...", "skill": "blood-pressure-tracker",
 "person_id": "mom",  # NEW: optional, defaults to "self"
 "data": {...},
 "_meta": {"source": "ocr", "document_type": "lab_report", "original_file": "..."}}  # NEW: provenance
```

### Pattern 3: Confirm-Before-Write for OCR

OCR extraction is inherently error-prone. The pipeline must separate extraction from persistence:

```python
class OCRPipeline:
    def extract(self, image_path: str) -> dict:
        """Extract structured data. Returns draft, does NOT write."""
        ...

    def confirm_and_write(self, draft: dict, corrections: dict = None) -> dict:
        """User-confirmed data gets written to store."""
        ...
```

### Pattern 4: Person-Scoped Operations

All shared runtime modules that read or write data must accept an optional `person_id` parameter:

```python
# HealthDataStore
store.append(record_type, data, person_id="mom")
store.query(start=..., end=..., person_id="mom")

# CrossSkillReader
reader.read("blood-pressure", person_id="mom")

# HealthMemoryWriter
writer = HealthMemoryWriter(memory_dir=..., person_id="mom")
# Automatically scopes paths to persons/mom/
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Separate JSONL Files Per Person

**What:** Creating `data/{skill}/records-mom.jsonl`, `data/{skill}/records-dad.jsonl`
**Why bad:** Explodes the number of files. Every tool that reads data needs to discover which person files exist. Breaks existing glob patterns. Makes cross-person queries (family dashboard) harder.
**Instead:** Single `records.jsonl` per skill with `person_id` field in each record. Filter in code, not filesystem.

### Anti-Pattern 2: OCR Auto-Commit

**What:** OCR extracts values and immediately writes to HealthDataStore without user review.
**Why bad:** OCR errors (misread digits, wrong field mapping) become permanent health records. A systolic of 135 misread as 185 could trigger false alarms.
**Instead:** Extract -> present to user -> user confirms/corrects -> write.

### Anti-Pattern 3: Device-Specific Data Models

**What:** Each device importer stores data in its own format (Google Fit schema, Huawei schema).
**Why bad:** Downstream consumers (visualization, analysis, memory) must understand every device format. N devices x M consumers = N*M adapters.
**Instead:** All importers normalize to VitaClaw health concepts (`health-concepts.yaml`). Downstream consumers only understand one format.

### Anti-Pattern 4: Monolithic Visualization Module

**What:** One massive chart function that handles every chart type with conditionals.
**Why bad:** Unmaintainable. Hard to test. Hard to extend.
**Instead:** Small composable functions: `trend_chart()`, `correlation_chart()`, `dashboard()`. Each chart type is a separate method with a consistent signature.

## Component Dependencies and Build Order

The four capabilities have clear dependencies that dictate build order:

```
                    [Engineering Foundation]
                    (pyproject.toml, CI, migration tools)
                           |
                           v
            +----[Person Context Manager]----+
            |    (person_id threading)       |
            |              |                 |
            v              v                 v
    [HealthDataStore    [HealthMemory     [CrossSkillReader
     person_id support]  person scoping]   person filter]
            |              |                 |
            +------+-------+---------+------+
                   |                 |
          +--------+--------+       |
          |        |        |       |
          v        v        v       v
       [OCR     [Device  [Family  [Visualization
        Pipeline] Import]  UX]     Engine]
```

### Suggested Build Order

**Phase 1: Engineering Foundation** (no feature dependencies)
- `pyproject.toml`, CI, data migration tooling
- Rationale: Everything else builds on stable tooling

**Phase 2: Person Context + Data Layer Changes** (foundation for family support)
- `person_context.py`: person registry, resolution logic, path helpers
- `HealthDataStore`: add `person_id` to envelope, query filters
- `HealthMemoryWriter`: per-person memory paths
- `CrossSkillReader`: person_id filter
- Rationale: This is a cross-cutting change that affects nearly everything. Must be done early and carefully. All subsequent features (OCR, import, visualization) benefit from person_id support being in place.

**Phase 3: Device Importers** (builds on person_id support)
- `device_importer_base.py`: abstract base with dedup, concept mapping
- Google Fit, Huawei, Xiaomi importers (parallel work, independent of each other)
- Rationale: File import is straightforward once the base pattern exists. Apple Health is the reference implementation. Person_id support means imported data can be attributed to family members.

**Phase 4: OCR Pipeline** (builds on person_id, benefits from device importer patterns)
- Document type classifier
- Per-type field extractors (lab report, physical exam, prescription)
- Confirm-and-write workflow
- Integration with PatientArchiveBridge
- Rationale: OCR is the most complex new capability. Having person_id in place means OCR-extracted data can be attributed to the correct family member. Having device importers done first validates the data ingestion patterns.

**Phase 5: Visualization** (reads data written by all previous phases)
- `health_chart_engine.py`: trend, correlation, dashboard chart types
- Integration with visit briefing, annual report
- Rationale: Visualization is a pure consumer of data. More data sources (device imports, OCR) mean richer charts. Person_id support enables per-person and cross-person charts.

**Phase 6: Family UX + Polish** (ties everything together)
- Cold-start onboarding for family members
- Family dashboard scenario
- Visit briefing per family member
- Annual report per family member
- Rationale: The UX layer that makes multi-person feel natural. All infrastructure must be in place first.

### Dependency Matrix

| Component | Depends On | Blocks |
|-----------|-----------|--------|
| Engineering Foundation | Nothing | Everything |
| Person Context Manager | Engineering Foundation | All data layer changes |
| HealthDataStore person_id | Person Context Manager | OCR, Importers, Visualization, Family UX |
| HealthMemoryWriter person scoping | Person Context Manager | OCR, Family UX |
| Device Importer Base | HealthDataStore person_id | Individual importers |
| Google/Huawei/Xiaomi Importers | Device Importer Base | Visualization (more data) |
| OCR Pipeline | HealthDataStore person_id, PaddleOCR (existing) | Family UX (OCR for family members) |
| Visualization Engine | HealthDataStore (read), CrossSkillReader | Visit briefing enhancement, Annual report |
| Family UX | Person Context, all importers, OCR, visualization | Nothing (terminal) |

## Key Integration Points with Existing Architecture

### health-concepts.yaml Extensions

The concept registry must be extended with:
- **OCR-sourced lab concepts:** ALT, AST, creatinine, uric acid, cholesterol panel, CBC items, urinalysis items -- each with LOINC codes, normal ranges, and units
- **Device-specific mappings:** Google Fit activity types to VitaClaw concepts, Huawei sleep stages to VitaClaw sleep model

### Config Changes (openclaw.health.json5)

- Route table additions for OCR skill, device import skills, visualization skill
- Person context resolution rules for the chief-of-staff router
- New role or extended permissions for family-scoped operations

### Template Changes

- `templates/openclaw-health-family-agent/` needs `memory/health/persons/` directory structure
- Family template BOOTSTRAP.md needs person context initialization step

## Sources

- Existing codebase analysis (HIGH confidence): `skills/_shared/health_data_store.py`, `skills/_shared/apple_health_bridge.py`, `skills/_shared/patient_archive_bridge.py`, `privacy_desensitize.py`, `skills/medical-record-organizer/scripts/redact_ocr.py`
- PROJECT.md key decisions (HIGH confidence): OCR confirm-before-write, family single-workspace isolation, file-based device import
- Templates analysis (HIGH confidence): `templates/openclaw-health-family-agent/AGENTS.md`

---

*Architecture analysis: 2026-03-26*
