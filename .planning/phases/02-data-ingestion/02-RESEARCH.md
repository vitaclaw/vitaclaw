# Phase 2: Data Ingestion - Research

**Researched:** 2026-03-26
**Domain:** Health data ingestion -- onboarding, wearable import, OCR pipeline
**Confidence:** HIGH

## Summary

Phase 2 covers three data ingestion channels: (1) a conversational onboarding SKILL.md that populates USER.md, IDENTITY.md, and _health-profile.md; (2) file-based wearable data importers for Google Fit, Huawei Health, and Xiaomi/Mi Fitness following the established Apple Health import pattern; and (3) an OCR pipeline for Chinese medical documents using PaddleOCR with table extraction for lab reports.

The project already has strong foundations: PaddleOCR 3.4.0 is installed and working on macOS, the Apple Health importer provides a clear reference pattern, HealthDataStore supports person_id threading from Phase 1, and the health-concepts.yaml registry provides the mapping layer for OCR-extracted fields. The main technical risks are: (a) PaddleOCR's table recognition pipeline (PPStructureV3/TableRecognitionPipelineV2) needs verification for Chinese medical table layouts, (b) Huawei and Xiaomi export formats are poorly documented and may vary by region/version, and (c) the fuzzy dedup algorithm (60s window, 5% tolerance) is new functionality not present in the existing exact-match dedup.

**Primary recommendation:** Build the shared `HealthImporterBase` class first, then implement importers in parallel. Build OCR as a separate workstream. Onboarding is the simplest channel and should land first.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Onboarding is a SKILL.md with structured prompt for conversational flow, not Python UI
- **D-02:** Onboarding collects: demographics (age, sex, height), chronic conditions, medications + dosages, supplements, health goals, reminder cadence, care team
- **D-03:** Output populates USER.md, IDENTITY.md, _health-profile.md; registers person in _family.yaml if family mode active
- **D-04:** Re-running onboarding merges updates, does not overwrite
- **D-05:** All importers follow Apple Health import pattern: Python script in scripts/ that reads export file, parses, maps to JSONL, appends with dedup
- **D-06:** Separate scripts: import_google_fit_export.py, import_huawei_health_export.py, import_xiaomi_health_export.py + corresponding SKILL.md each
- **D-07:** Shared base class HealthImporterBase in skills/_shared/health_importer_base.py with: file discovery (ZIP extraction), record mapping, fuzzy dedup (60s/5%), progress reporting, person_id passthrough
- **D-08:** Metrics: heart rate, steps, sleep (duration + stages), weight, blood pressure, activities (type + duration + calories). Unknown types logged as warnings.
- **D-09:** Google Fit: Takeout ZIP with CSV + TCX. Huawei: Settings export ZIP with CSV/JSON + GPX. Xiaomi: Account data export ZIP with CSV.
- **D-10:** Fuzzy dedup across devices: 60s timestamp window, 5% value tolerance, first-imported wins
- **D-11:** OCR pipeline as SKILL.md + Python: classify doc type, extract via PaddleOCR PP-StructureV2, structured field extraction, display for confirmation, store on confirmation
- **D-12:** Supported types: 体检报告, 检验单, 门诊病历, 处方单. System auto-detects type.
- **D-13:** Table extraction (PPStructureV2) for lab/exam reports; raw text OCR (PP-OCRv5) for prescriptions/outpatient records
- **D-14:** Confirmation UI shows: extracted value, unit, reference range, health concept mapping. User confirms/edits/rejects each field.
- **D-15:** Confirmed fields stored as HealthDataStore records mapped to appropriate skills + original document archived in memory/health/files/
- **D-16:** Low confidence (<60%) shows raw text and asks user to manually identify values
- **D-17:** Accepts JPG, PNG, HEIC, PDF. HEIC via pillow-heif.

### Claude's Discretion
- Exact Google Fit / Huawei / Xiaomi CSV field name mappings (discover defensively from actual exports)
- PaddleOCR model selection and initialization parameters
- Whether to use LLM post-processing for field extraction
- Onboarding question phrasing and conversation flow design
- Progress reporting format during import

### Deferred Ideas (OUT OF SCOPE)
- AI-powered field extraction with LOINC mapping (OCR-V2-01, OCR-V2-02)
- Conversational profiling (ONBD-V2-01, ONBD-V2-02)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ONBD-01 | Guided health profile setup through conversational flow | SKILL.md pattern verified from blood-pressure-tracker; USER.md/IDENTITY.md/_health-profile.md templates exist with "pending" placeholders ready for population |
| ONBD-02 | Populates USER.md, IDENTITY.md, _health-profile.md | All three files exist with known structure (see Code Examples section); merge-update pattern needed for D-04 |
| ONBD-03 | Re-run onboarding to update profile | Merge-update pattern: read existing file, parse sections, update only changed fields, write back. Markdown section-based parsing already used in HealthMemoryWriter |
| IMPT-01 | Google Fit import from Takeout CSV + TCX | Google Takeout produces dated CSVs + Daily Summaries + TCX activities. stdlib csv + xml.etree sufficient. |
| IMPT-02 | Huawei Health import from data export | ZIP with CSV/JSON + GPX. Format poorly documented -- parser must be defensive with field name discovery. |
| IMPT-03 | Xiaomi/Mi Fitness import from account export | ZIP with CSV files from account.xiaomi.com. Format varies by region. |
| IMPT-04 | Shared base class with fuzzy dedup | HealthImporterBase provides ZIP extraction, record mapping, fuzzy dedup (60s/5%), person_id threading. Not in existing codebase -- must be built new. |
| IMPT-05 | Maps to HealthDataStore JSONL format | health-concepts.yaml defines canonical types (heart_rate, sleep_session, bp, weight). HealthDataStore.append() with _meta for provenance. |
| OCR-01 | Photo/PDF to structured data for 4 Chinese document types | PaddleOCR 3.4.0 installed. PPStructureV3 and TableRecognitionPipelineV2 available for table extraction. PP-OCRv5 for text. |
| OCR-02 | Extracted fields displayed for confirmation before storage | Must implement staging buffer -- OCR output is NOT written to HealthDataStore until user confirms |
| OCR-03 | Confirmed data auto-stored into HealthDataStore records | ConceptResolver maps extracted lab items to concept IDs; HealthDataStore.append() with source="ocr" meta |
| OCR-04 | PP-StructureV2 table extraction for Chinese medical tables | **CORRECTION:** PaddleOCR 3.4.0 ships PPStructureV3 (not V2). TableRecognitionPipelineV2 is the table-specific pipeline. Both verified available. |
| OCR-05 | Original document archived in patient records | memory/health/files/ directory exists via HealthMemoryWriter. Copy original file + metadata JSON. |
</phase_requirements>

## Standard Stack

### Core (already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PaddleOCR | 3.4.0 (installed) | OCR text detection + table extraction | Already in project, PP-OCRv5 for text, PPStructureV3 for tables |
| PyMuPDF (fitz) | installed | PDF to image rendering | Already used in privacy_desensitize.py and redact_ocr.py |
| Pillow | installed | Image preprocessing | Already a dependency |
| pillow-heif | installed | HEIC support | Already a dependency |
| PyYAML | installed | _family.yaml parsing, health-concepts.yaml | Core dependency |

### Supporting (stdlib, no install needed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| csv | stdlib | Google Fit CSV parsing | All importers |
| json | stdlib | Huawei JSON export parsing | Huawei importer |
| zipfile | stdlib | ZIP extraction for all platforms | All importers |
| xml.etree.ElementTree | stdlib | TCX activity file parsing | Google Fit activities |
| argparse | stdlib | CLI argument parsing | All import scripts |
| hashlib | stdlib | Data hashing for dedup | Fuzzy dedup in base class |

### Key Existing Components to Use

| Component | Location | Purpose in Phase 2 |
|-----------|----------|-------------------|
| HealthDataStore | skills/_shared/health_data_store.py | Write imported/OCR records with person_id |
| HealthMemoryWriter | skills/_shared/health_memory.py | Write onboarding profile, archive OCR docs |
| ConceptResolver | skills/_shared/concept_resolver.py | Map OCR lab items to health concepts |
| FamilyManager | skills/_shared/family_manager.py | Register person during onboarding |
| health-concepts.yaml | schemas/health-concepts.yaml | Canonical field definitions, ranges, LOINC codes |
| AppleHealthImporter | skills/_shared/apple_health_bridge.py | Reference pattern for new importers |

**Installation:** No new packages needed. All dependencies are already installed.

## Architecture Patterns

### Project Structure for Phase 2

```
skills/
  _shared/
    health_importer_base.py          # NEW: shared base class for all importers
    health_data_store.py             # EXISTING: append records
    health_memory.py                 # EXISTING: write profiles
    concept_resolver.py              # EXISTING: map OCR fields
  health-onboarding/
    SKILL.md                         # NEW: conversational onboarding skill
  google-fit-import/
    SKILL.md                         # NEW: skill for AI to invoke import
  huawei-health-import/
    SKILL.md                         # NEW: skill for AI to invoke import
  xiaomi-health-import/
    SKILL.md                         # NEW: skill for AI to invoke import
  medical-document-ocr/
    SKILL.md                         # NEW: OCR pipeline skill
    scripts/
      ocr_pipeline.py               # NEW: main OCR extraction logic
      ocr_table_extractor.py         # NEW: table-specific extraction
      ocr_text_extractor.py          # NEW: text-specific extraction
scripts/
  import_google_fit_export.py        # NEW: CLI entry point
  import_huawei_health_export.py     # NEW: CLI entry point
  import_xiaomi_health_export.py     # NEW: CLI entry point
```

### Pattern 1: Importer Base Class (HealthImporterBase)

**What:** Abstract base class providing ZIP extraction, record mapping, fuzzy dedup, and progress reporting. Each platform subclass implements only the format-specific parsing.

**When to use:** All new device importers MUST inherit from this.

**Key design:**
```python
# skills/_shared/health_importer_base.py
class HealthImporterBase:
    """Base class for health data importers."""

    def __init__(self, data_dir=None, person_id=None):
        self.person_id = person_id
        self._data_dir = data_dir

    def import_export(self, export_path: str, start_date=None, end_date=None) -> dict:
        """Main entry: extract ZIP -> discover files -> parse -> dedup -> store."""
        ...

    def _extract_zip(self, zip_path: str) -> Path:
        """Extract ZIP to temp dir, return extraction root."""
        ...

    def _discover_files(self, extracted_dir: Path) -> list[Path]:
        """Subclass: return list of data files to process."""
        raise NotImplementedError

    def _parse_records(self, data_file: Path) -> list[dict]:
        """Subclass: parse file into list of {type, timestamp, data, _meta}."""
        raise NotImplementedError

    def _fuzzy_dedup(self, new_record: dict, existing_records: list[dict]) -> bool:
        """Return True if new_record is a fuzzy duplicate of any existing."""
        # Timestamp within 60s AND value within 5% = duplicate
        ...

    def _store_records(self, records: list[dict], skill_name: str) -> dict:
        """Write records via HealthDataStore with dedup."""
        ...
```

### Pattern 2: OCR Pipeline (extract -> classify -> confirm -> store)

**What:** Multi-stage pipeline that never auto-commits to HealthDataStore.

**Stages:**
1. **Input handling:** Accept image/PDF path, convert HEIC if needed, render PDF pages to images
2. **Document classification:** Detect document type (体检报告/检验单/门诊病历/处方单) from layout and keywords
3. **Extraction:** For table docs (体检报告, 检验单) use PPStructureV3/TableRecognitionPipelineV2. For text docs (门诊病历, 处方单) use PaddleOCR text recognition.
4. **Field mapping:** Map extracted items to health concepts via ConceptResolver. Attach confidence scores.
5. **Staging output:** Return structured JSON with extracted fields for the AI to display to user
6. **Confirmation:** AI shows fields, user confirms/edits/rejects. Only confirmed fields proceed.
7. **Storage:** Write confirmed records via HealthDataStore.append() with meta.source="ocr"

**Critical:** Steps 1-5 are Python. Steps 6-7 happen in the AI conversation guided by SKILL.md.

### Pattern 3: Onboarding as Pure SKILL.md

**What:** A SKILL.md file that instructs the AI runtime to conduct a conversational health profile setup. No Python script runs during the conversation -- the AI reads/writes markdown files directly.

**Flow:**
1. AI reads existing USER.md, IDENTITY.md, _health-profile.md
2. AI identifies which fields are still "pending" or need update
3. AI asks questions conversationally (not a form)
4. AI writes updated content to the three files using Edit tool
5. If family mode: AI registers person in _family.yaml via FamilyManager

### Anti-Patterns to Avoid

- **Auto-committing OCR results:** NEVER call HealthDataStore.append() from OCR extraction code. Extraction produces staging output only.
- **Hardcoded CSV field names:** Huawei/Xiaomi formats change between versions. Always discover field names from headers, not hardcoded constants.
- **Exact dedup for cross-device:** The existing HealthDataStore dedup uses exact hash matching. Cross-device dedup MUST use the fuzzy algorithm (60s/5%).
- **Single monolithic OCR script:** Split table extraction and text extraction into separate modules. They use different PaddleOCR pipelines.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ZIP extraction | Custom unzip logic | zipfile stdlib | Handles nested ZIPs, encoding issues, path traversal safety |
| HEIC conversion | Custom converter | pillow-heif + sips fallback | Already implemented in redact_ocr.py (_ensure_processable) |
| PDF to image | Custom renderer | PyMuPDF (fitz) | Already implemented in privacy_desensitize.py (pdf_to_images) |
| Health concept mapping | Hardcoded field-to-concept maps | ConceptResolver + health-concepts.yaml | Registry-driven, extensible, already has LOINC codes |
| Markdown section parsing | Custom parser | HealthMemoryWriter patterns | Already handles YAML frontmatter, section insertion/update |
| Person-scoped data paths | Manual path construction | HealthDataStore(person_id=...) + HealthMemoryWriter(person_id=...) | Phase 1 already threaded person_id through these |

**Key insight:** The project already has significant infrastructure from Phase 1 and Iteration 1. The importers are primarily format-parsing code on top of existing storage APIs. The OCR pipeline is primarily PaddleOCR orchestration on top of existing concept resolution.

## Common Pitfalls

### Pitfall 1: PaddleOCR PPStructureV3 vs PP-StructureV2 Naming

**What goes wrong:** CONTEXT.md says "PP-StructureV2" but PaddleOCR 3.4.0 ships PPStructureV3 (not V2). Code targeting V2 API will fail with ImportError.
**Why it happens:** The PP-Structure naming evolved across PaddleOCR versions. V2 was in PaddleOCR 2.x, V3 is in 3.x.
**How to avoid:** Use `from paddleocr import PPStructureV3` or `TableRecognitionPipelineV2` for table-specific extraction. Both are verified available in the installed PaddleOCR 3.4.0.
**Warning signs:** ImportError on `PPStructureV2`.

### Pitfall 2: OCR Table Results Lose Key-Value Association

**What goes wrong:** Table extraction returns cells but loses the relationship between test name and result value. "血红蛋白" and "135" appear as separate cells with no linking.
**Why it happens:** Table recognition returns cell positions but the semantic meaning (which column is "item name" vs "result" vs "reference range") requires post-processing.
**How to avoid:** After table extraction, apply column role classification: first column = item name, second = result, third = unit, fourth = reference range. This works for 80%+ of Chinese lab reports which follow a standard 4-column layout.
**Warning signs:** Extracted values with no item names attached.

### Pitfall 3: Fuzzy Dedup Performance on Large Datasets

**What goes wrong:** Fuzzy dedup compares each new record against ALL existing records (O(n*m) complexity). With 10,000+ existing records and 5,000 new records, import takes minutes.
**Why it happens:** Naive implementation scans all records for each new record.
**How to avoid:** Pre-filter by record_type and timestamp range (same day +/- 1 day) before fuzzy comparison. This reduces the comparison set by 95%+.
**Warning signs:** Import script hangs or takes >30 seconds for moderate datasets.

### Pitfall 4: Timezone Mismatches Between Devices

**What goes wrong:** Apple Health uses UTC internally, Google Fit uses local time, Xiaomi uses local time, Huawei varies. Importing from multiple devices produces duplicate records because the "same" event has different timestamps.
**Why it happens:** Each platform has its own timestamp convention.
**How to avoid:** Each importer must normalize timestamps to ISO 8601 with timezone offset. Store timezone in _meta. When comparing for fuzzy dedup, convert both timestamps to UTC first.
**Warning signs:** Duplicate records appearing for the same timeframe from different devices.

### Pitfall 5: Onboarding Overwrites Existing Profile Data

**What goes wrong:** User re-runs onboarding (ONBD-03) and the AI writes a fresh _health-profile.md, destroying the conditions and medications that were carefully entered months ago.
**Why it happens:** The AI uses Write tool to create the file from scratch instead of Edit tool to update specific sections.
**How to avoid:** The SKILL.md must explicitly instruct the AI to: (1) Read existing file first, (2) Only update fields the user explicitly mentioned, (3) Use Edit tool for targeted section updates, not Write for full replacement.
**Warning signs:** _health-profile.md losing previously entered data after re-onboarding.

### Pitfall 6: Large Image OOM During OCR

**What goes wrong:** Phone cameras produce 4000x3000+ images. PaddleOCR loads the full image into memory for processing, potentially causing OOM on machines with limited RAM.
**Why it happens:** No image resizing before OCR input.
**How to avoid:** Resize images to max 2048px on the longest side before OCR. This matches PaddleOCR's internal processing resolution and prevents OOM with negligible accuracy loss.
**Warning signs:** Python process killed during OCR, or extremely slow processing.

## Code Examples

### OCR Pipeline Initialization (PPStructureV3)

```python
# Verified against PaddleOCR 3.4.0 installed API
import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# For table-heavy documents (体检报告, 检验单):
from paddleocr import TableRecognitionPipelineV2
table_pipeline = TableRecognitionPipelineV2(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)
# table_pipeline.predict(image_path) returns table structure + cell text

# For text-heavy documents (门诊病历, 处方单):
from paddleocr import PaddleOCR
text_ocr = PaddleOCR(lang="ch")
# Use the .predict() API (PaddleOCR 3.x)
results = list(text_ocr.predict(image_path))
for page in results:
    texts = page["rec_texts"]
    scores = page["rec_scores"]
    polys = page["dt_polys"]
```

### Fuzzy Dedup Algorithm

```python
from datetime import datetime, timedelta

def is_fuzzy_duplicate(
    new_record: dict,
    existing: dict,
    time_window_seconds: int = 60,
    value_tolerance: float = 0.05,
) -> bool:
    """Check if two records are fuzzy duplicates."""
    # Must be same record type
    if new_record.get("type") != existing.get("type"):
        return False

    # Must be same person
    if new_record.get("person_id") != existing.get("person_id"):
        return False

    # Timestamp within window
    ts_new = datetime.fromisoformat(new_record["timestamp"])
    ts_existing = datetime.fromisoformat(existing["timestamp"])
    if abs((ts_new - ts_existing).total_seconds()) > time_window_seconds:
        return False

    # Numeric values within tolerance
    new_data = new_record.get("data", {})
    existing_data = existing.get("data", {})
    for key in new_data:
        new_val = new_data[key]
        existing_val = existing_data.get(key)
        if isinstance(new_val, (int, float)) and isinstance(existing_val, (int, float)):
            if existing_val == 0:
                if new_val != 0:
                    return False
            elif abs(new_val - existing_val) / abs(existing_val) > value_tolerance:
                return False

    return True
```

### Onboarding Profile Merge Pattern

```python
# The AI runtime handles this via SKILL.md instructions, but the pattern is:
# 1. Read existing _health-profile.md
# 2. Parse YAML frontmatter + markdown sections
# 3. For each field user provides, update only that field
# 4. Write back with preserved structure

# Example _health-profile.md after onboarding:
"""
---
updated_at: 2026-03-26T10:00:00
---

# Health Profile

## Baseline

- Name: John
- Date of birth: 1985-03-15
- Sex: Male
- Height: 178cm
- Weight baseline: 75kg

## Conditions

- Hypertension (diagnosed 2020, managed with medication)

## Medications

- Amlodipine 5mg, once daily, morning

## Supplements

- Vitamin D3 2000IU, once daily

## Allergies

- None documented yet

## Risk Thresholds

- Blood pressure escalation: SBP > 140 or DBP > 90
- Blood glucose escalation: pending
- Sleep / stress escalation: pending

## Care Plan

- Track blood pressure daily (morning + evening)
- Monthly medication review
- Quarterly lab work
"""
```

### HEIC Conversion (reuse existing pattern)

```python
# From redact_ocr.py -- already implemented, reuse directly
def _ensure_processable(image_path: str) -> tuple[str, bool]:
    """Convert HEIC/HEIF to temporary JPG. Returns (processable_path, is_temp)."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in (".heic", ".heif"):
        return (image_path, False)
    # Try macOS sips first, fallback to pillow-heif
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PP-StructureV2 (PaddleOCR 2.x) | PPStructureV3 (PaddleOCR 3.x) | PaddleOCR 3.0 (2025-05) | V3 has better table detection, supports wired and wireless table structure recognition |
| PaddleOCR `ocr.ocr()` API | PaddleOCR `ocr.predict()` API | PaddleOCR 3.x | New predict API returns structured dict with rec_texts, rec_scores, dt_polys |
| Google Fit API (OAuth) | Google Takeout file export | Google Fit API deprecated 2024 | File-based export is now the only option; aligns with local-first architecture |
| Mi Fit app | Mi Fitness / Zepp Life | 2023 | Data export format may differ between old and new app versions |

**Critical note:** The CONTEXT.md references "PP-StructureV2" but the installed PaddleOCR 3.4.0 exposes `PPStructureV3` and `TableRecognitionPipelineV2`. Implementation should use the V3/PipelineV2 APIs that are actually available.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All | Yes | 3.11.4 | -- |
| PaddleOCR | OCR pipeline | Yes | 3.4.0 | -- |
| PyMuPDF | PDF processing | Yes | installed | -- |
| Pillow | Image processing | Yes | installed | -- |
| pillow-heif | HEIC support | Yes | installed | macOS sips command |
| PyYAML | Family config | Yes | installed | JSON fallback in FamilyManager |
| PPStructureV3 | Table extraction | Yes | bundled in paddleocr 3.4.0 | -- |
| TableRecognitionPipelineV2 | Table-specific OCR | Yes | bundled in paddleocr 3.4.0 | -- |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Open Questions

1. **PaddleOCR PPStructureV3 table output format for Chinese lab reports**
   - What we know: PPStructureV3 and TableRecognitionPipelineV2 are importable and have rich initialization parameters (wired/wireless table models, cell detection)
   - What's unclear: Exact output format of table extraction (HTML table? Cell coordinates? Structured dict?) and how well it handles merged cells in Chinese lab reports
   - Recommendation: Build a small test script as the first OCR task to validate the table extraction output format against a real Chinese lab report image

2. **Huawei Health export file structure**
   - What we know: ZIP archive with CSV/JSON + GPX files
   - What's unclear: Exact CSV column names, JSON schema, whether format varies by Huawei Health app version or phone model
   - Recommendation: Parse defensively -- discover columns from headers, skip unrecognized fields, log warnings for unexpected formats. Per D decision: Claude's discretion on field mappings.

3. **Xiaomi/Mi Fitness export structure**
   - What we know: ZIP from account.xiaomi.com with CSV files
   - What's unclear: Exact CSV structure, whether legacy Mi Fit vs new Mi Fitness exports differ
   - Recommendation: Same defensive parsing approach as Huawei. Build with auto-detection of CSV column meanings.

## Project Constraints (from CLAUDE.md)

- **Local-first:** All data must stay on local filesystem, no cloud OCR APIs
- **Skill format:** New capabilities as SKILL.md + optional Python
- **Privacy boundary:** Health data never leaves local without user consent
- **Backward compatible:** Iteration 1 data formats must be preserved
- **Python only:** No new languages
- **Bilingual content:** Code identifiers in English, user-facing health content in Chinese
- **CLI pattern:** Scripts use argparse with --format markdown|json
- **Import organization:** sys.path.insert for shared module access
- **Error handling:** Custom exceptions, graceful degradation for corrupted data
- **Logging:** print() for info, print(file=sys.stderr) for warnings
- **Module convention:** `from __future__ import annotations` at top of every module

## Sources

### Primary (HIGH confidence)
- PaddleOCR 3.4.0 installed locally -- API verified via direct import and inspection
- Existing codebase: apple_health_bridge.py, health_data_store.py, health_memory.py, redact_ocr.py, privacy_desensitize.py, concept_resolver.py
- health-concepts.yaml registry -- field schemas, ranges, LOINC codes verified
- USER.md, IDENTITY.md, _health-profile.md templates -- current structure inspected
- pyproject.toml -- dependency groups verified

### Secondary (MEDIUM confidence)
- .planning/research/STACK.md -- PaddleOCR version recommendations, import format notes
- .planning/research/PITFALLS.md -- OCR table extraction, cross-device dedup, timezone pitfalls
- .planning/research/FEATURES.md -- Feature dependencies and format notes

### Tertiary (LOW confidence)
- Huawei Health export format specifics -- documented in FEATURES.md but exact field schemas unverified against real exports
- Xiaomi/Mi Fitness export format -- same limitation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all dependencies already installed and verified
- Architecture: HIGH - patterns established by existing Apple Health importer and OCR infrastructure
- Pitfalls: HIGH - documented from existing codebase analysis and research phase
- OCR table extraction: MEDIUM - API available but output format for Chinese medical tables unverified against real documents
- Wearable export formats: MEDIUM - Huawei/Xiaomi formats not verified against real export files

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain, PaddleOCR version pinned)
