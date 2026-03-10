---
name: drug-label-lookup
description: "Retrieves FDA-approved drug label information via the openFDA API, including indications, dosage, warnings, contraindications, adverse reactions, and drug interactions. Use when the user needs official prescribing information for a medication."
version: 1.0.0
user-invocable: true
argument-hint: "[drug-name]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📋","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# Drug Label Lookup Skill

## Overview

This skill queries complete label information for FDA-approved drugs via the openFDA API, including:

- **Indications and Usage**
- **Dosage and Administration**
- **Boxed Warning**
- **Warnings and Precautions**
- **Contraindications**
- **Adverse Reactions**
- **Drug Interactions**
- **Pregnancy / Use in Specific Populations**
- **Clinical Pharmacology**

## Usage

Run `drug_label.py` with a drug name (generic or brand name, in English):

```bash
python drug_label.py osimertinib
python drug_label.py pembrolizumab
python drug_label.py Keytruda
```

If no drug name is provided, the default query is `osimertinib`.

## Output Format

- The `lookup(drug_name)` method returns a raw dictionary containing all label fields
- The `format_label(drug_name, label)` function returns a human-readable Markdown-formatted text

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENFDA_API_KEY` | No | openFDA API Key; increases rate limits (works without a key, but subject to rate limiting) |

## Notes

- Only queries drugs approved by the U.S. FDA; drugs exclusive to other markets (e.g., per Chinese clinical guidelines) may not be available
- Drug names should be entered in English (either generic or brand names)
- API responses are returned in the original English text without translation
- Built-in automatic retry mechanism (up to 3 retries on 429/5xx errors)
