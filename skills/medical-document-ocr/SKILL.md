---
name: medical-document-ocr
description: Extract structured health data from Chinese medical document photos/PDFs
version: 1.1.0
user-invocable: true
allowed-tools: [Bash, Read, Write, Edit]
metadata:
  category: health-records
  domain: health
  input: image/PDF of Chinese medical document
  output: structured health data records
---

# Medical Document OCR

Extract structured health data from photos or scans of Chinese medical documents.

## Supported Document Types

- **体检报告** (Physical exam report) -- table-heavy, most common
- **检验单** (Lab test results) -- structured tables
- **门诊病历** (Outpatient records) -- mixed text
- **处方单** (Prescriptions) -- medication lists

## Supported Input Formats

JPG, PNG, HEIC, PDF

## Workflow

### Step 1: Get document from user

Ask the user for the path to their medical document image or PDF.

### Step 2: Run OCR extraction

```bash
python skills/medical-document-ocr/scripts/ocr_pipeline.py "<path>" --format json
```

Parse the JSON output to get extracted fields.

### Step 3: Display extracted fields for confirmation

Show the user a clear table of ALL extracted fields:

| # | Item | Value | Unit | Reference | Concept | Confidence |
|---|------|-------|------|-----------|---------|------------|
| 1 | 血红蛋白 | 135 | g/L | 130-175 | hemoglobin | 92% |
| 2 | 白细胞 | 5.3 | 10^9/L | 3.5-9.5 | wbc | 88% |
| 3 | 血糖 | 5.1 | mmol/L | 3.9-6.1 | blood-sugar | 45% :warning: |

For each field, display:
- **Item name** (Chinese + English concept if available)
- **Value** with unit
- **Reference range** (if found)
- **Health concept** mapping (concept_id from OCR pipeline)
- **Confidence** score -- flag low-confidence fields (<60%) with a :warning: marker

### Step 4: Handle low confidence fields (<60%)

For fields with confidence below 60%, show the raw OCR text excerpt so the user can manually identify the correct value. Present it like this:

> :warning: Low confidence (45%) for item "血糖". The OCR may have misread this field.
> Here is the raw text from the document near this field:
> ```
> [raw text snippet from OCR output]
> ```
> Can you identify the correct value, or should I skip this field?

This ensures no data is silently dropped -- the user always has the chance to recover values that OCR could not reliably extract (per D-16).

### Step 5: Collect user confirmations

For each field (or all at once if all confidences are high), let the user:
- **Confirm** -- accept the extracted value as-is (set `status: "confirmed"`)
- **Edit** -- provide a corrected value (set `status: "edited"`, record `edited_value`)
- **Reject** -- skip this field entirely (set `status: "rejected"`)

If all fields have confidence >= 80%, you may offer a "confirm all" shortcut.

Build a confirmed fields list with each field's status before proceeding to storage.

### Step 6: Store confirmed fields via ocr_store

Once the user has confirmed/edited/rejected all fields, store them using the `ocr_store.py` module.

**Option A: Bash invocation** (for CLI-style use):

Save the confirmed fields to a temporary JSON file, then run:

```bash
python skills/medical-document-ocr/scripts/ocr_store.py confirmed.json --person-id <pid> --format json
```

The JSON file should have this structure:
```json
{
  "document_type": "lab_test",
  "archived_path": "memory/health/files/2026-03-26_ocr_abc12345.pdf",
  "confirmed_fields": [
    {
      "item_name": "...",
      "value": "135",
      "unit": "g/L",
      "reference_range": "130-175",
      "concept_id": "hemoglobin",
      "record_type": "lab_result",
      "confidence": 0.92,
      "status": "confirmed"
    }
  ]
}
```

**Option B: Inline Python** (for direct function call):

```python
from ocr_store import store_confirmed_fields

result = store_confirmed_fields(
    confirmed_fields=fields_with_status,
    document_type="lab_test",
    archived_path="memory/health/files/2026-03-26_ocr_abc12345.pdf",
    person_id="mom",  # or None for self
)
```

The `store_confirmed_fields` function:
- Routes each field to the correct HealthDataStore skill based on `concept_id`:
  - `blood-pressure` -> `blood-pressure-tracker`
  - `blood-sugar` -> `chronic-condition-monitor`
  - `liver-function`, `kidney-function`, `blood-lipids`, `tumor-markers` -> `lab-results`
  - Other/unknown -> `lab-results`
- Stores with provenance metadata: `source: "ocr"`, `document_type`, `archived_path`, `confidence`
- Uses `edited_value` when status is `"edited"`
- Skips fields where status is `"rejected"`
- Returns `{"stored": N, "skipped": N, "errors": [...], "records": [...]}`

### Step 7: Report storage summary

After storage completes, show the user a clear summary:

```
## Storage Complete

- **Stored:** 12 fields confirmed and saved
- **Skipped:** 2 fields rejected
- **Skills updated:** blood-pressure-tracker, lab-results, chronic-condition-monitor
- **Document archived:** memory/health/files/2026-03-26_ocr_abc12345.pdf

All confirmed data has been saved with source="ocr" provenance.
```

Include which skills received new records so the user knows where to find the data later.

## Important Notes

- **Never auto-store** -- always show extracted data and wait for user confirmation before writing to any HealthDataStore. OCR data ONLY reaches storage after explicit user confirmation.
- **Archive original** -- the OCR pipeline automatically archives the original document in `memory/health/files/` with metadata.
- **Low confidence warning** -- fields below 60% confidence must show raw text for manual identification (D-16). Never silently drop low-confidence fields.
- **Person ID** -- if managing multiple family members, ask which person this document belongs to and pass `--person-id` to both the pipeline and the store commands.
- **Provenance** -- every stored record carries `_meta.source = "ocr"` and `_meta.archived_path` linking back to the original document for audit and reference.
