---
name: checkup-report-interpreter
description: "Interprets physical examination reports by parsing PDF files into structured data, identifying abnormalities with severity grading, and generating clinical explanations with health recommendations. Supports year-over-year comparison of two reports. Use when the user uploads a checkup report or asks for help understanding lab results."
version: 1.0.0
user-invocable: true
argument-hint: "[report <pdf> | parse <pdf> | extract <pdf> | compare <pdf1> <pdf2>]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏥","category":"health-scenario"}}
---

# Checkup Report Interpreter

Automatically parses physical examination report PDFs into structured data, then uses LLM for abnormality identification, clinical interpretation, and health recommendation generation.

## Features

- **Smart PDF Parsing**: Uses PyMuPDF to extract text from checkup reports, supporting multi-page reports
- **Structured Extraction**: LLM identifies all examination items (laboratory tests, imaging findings, physical examination), returning standardized JSON
- **Abnormality Grading**: Automatically determines abnormality severity based on reference ranges (urgent / important / moderate / minor), with 40+ built-in common indicator reference values
- **Clinical Interpretation**: Groups abnormal indicators by organ system and explains their clinical significance in plain language
- **Health Recommendations**: Generates personalized health recommendations and suggested follow-up items
- **Annual Comparison**: Supports item-by-item comparison of two reports, highlighting new abnormalities, worsening trends, and improvements

## Usage

```bash
# Full report interpretation
python checkup_report_interpreter.py report checkup_report.pdf

# Parse PDF text only
python checkup_report_interpreter.py parse checkup_report.pdf

# Extract structured examination items
python checkup_report_interpreter.py extract checkup_report.pdf

# Compare two years of reports
python checkup_report_interpreter.py compare 2026_checkup.pdf 2025_checkup.pdf
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | API endpoint (default: `https://openrouter.ai/api/v1/chat/completions`) |
| `LLM_MODEL` | No | Model name (default: `google/gemini-2.5-flash`) |
