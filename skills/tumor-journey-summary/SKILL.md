---
name: tumor-journey-summary
description: "Builds a structured timeline of a cancer patient's treatment journey by scanning patient file directories and using LLM to extract clinical events. Supports manual event entry, automatic extraction from free text, and narrative summaries highlighting key treatment decisions. Use when the user wants to organize or review their cancer treatment history."
version: 1.0.0
user-invocable: true
argument-hint: "[add | list | scan <dir> | extract | summary | timeline]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📋","category":"health-scenario"}}
---

# Tumor Journey Timeline Summary

Helps build a structured timeline of a cancer patient's treatment journey.

## Features

- **Manual Event Entry**: Supports 16 event types including diagnosis, surgery, chemotherapy, radiotherapy, targeted therapy, immunotherapy, and imaging studies
- **Directory Scanning**: Scans patient file directories to discover medical documents in PDF/TXT/DOCX/MD formats
- **LLM Smart Extraction**: Automatically extracts structured clinical events from free text (date, type, description, details)
- **Timeline Export**: Generates a chronologically sorted Markdown-format treatment timeline
- **Journey Summary**: Uses LLM to generate a narrative treatment summary highlighting key treatment decisions and turning points

## Usage Examples

```bash
# Add events
python tumor_journey_summary.py add --type diagnosis --date 2025-01-15 --desc "Colonoscopy found ascending colon mass, biopsy confirmed adenocarcinoma"
python tumor_journey_summary.py add --type surgery --date 2025-02-01 --desc "Right hemicolectomy" --details '{"surgeon":"Dr. Zhang"}'

# View events
python tumor_journey_summary.py list
python tumor_journey_summary.py list --type chemotherapy

# Scan patient directory
python tumor_journey_summary.py scan /path/to/patient/dir

# Extract events from text
python tumor_journey_summary.py extract --text "Patient diagnosed with colon cancer in January 2025..."
python tumor_journey_summary.py extract --file /path/to/report.txt

# Generate summary and timeline
python tumor_journey_summary.py summary
python tumor_journey_summary.py timeline
```
