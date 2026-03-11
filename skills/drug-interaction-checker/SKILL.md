---
name: drug-interaction-checker
description: "Checks drug-drug interactions via the RxNorm API with automatic fallback to openFDA drug labels when RxNorm data is unavailable. Supports single-drug lookup, multi-drug batch checking, and FDA label retrieval. Use when the user wants to verify whether their medications interact."
version: 1.0.0
user-invocable: true
argument-hint: "[single-drug | multi-drug-check | fda-fallback]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"⚠️","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# Drug Interaction Checker Skill

## Overview

This skill checks drug-drug interactions through the RxNorm Interaction API and automatically falls back to the openFDA drug label for interaction information when RxNorm has no data. It supports the following three query modes:

### 1. Single-Drug Interaction Query

Enter a single drug name to retrieve all known drug interactions for that drug, including the drugs involved, severity, and detailed descriptions.

### 2. Multi-Drug Interaction Check

Enter multiple drug names (2 or more) to check whether interactions exist among them. The system resolves each drug name to an RxCUI and then calls the RxNorm multi-drug interaction endpoint for batch checking.

### 3. FDA Label Fallback

When RxNorm does not contain interaction data for a given drug, the system automatically queries the Drug Interactions section of the openFDA drug label as a supplementary information source.

## Usage

Run `drug_interaction.py` with one or more drug names (in English):

```bash
# Single-drug query
python drug_interaction.py osimertinib

# Multi-drug interaction check
python drug_interaction.py osimertinib rifampin ketoconazole
```

If no drug names are provided, the default query checks interactions among `osimertinib`, `rifampin`, and `ketoconazole`.

## Output Format

- The `check(drug_name, other_drugs)` method returns formatted Markdown text containing:
  - Basic drug information (RxCUI)
  - List of major drug interactions (source labeled as RxNorm or FDA label)
  - Multi-drug interaction check results (if multiple drugs are provided)
  - RxNorm reference links
- The `DrugInteractionChecker` class also exposes lower-level methods for programmatic use:
  - `get_single_drug_interactions(drug_name)` — returns a list of interaction dictionaries
  - `check_multi_drug_interactions(drug_names)` — returns a list of multi-drug interaction dictionaries

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENFDA_API_KEY` | No | openFDA API Key; increases rate limits (works without a key as well) |

## Notes

- RxNorm is a free public API maintained by the U.S. National Library of Medicine (NLM); no API key is required
- Drug names should be entered as English generic names (e.g., osimertinib, not the Chinese name)
- When an exact match fails, the system automatically attempts approximate term matching
- Built-in automatic retry mechanism (up to 3 retries on 429/5xx errors)
- Interaction severity is provided by the RxNorm data source; common values include high, low, N/A, etc.
