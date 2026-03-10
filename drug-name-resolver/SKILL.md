---
name: drug-name-resolver
description: "Resolves drug names (generic, brand, or development codes) to standardized RxNorm RxCUI identifiers and retrieves drug classification information. Use when the user needs to normalize a medication name or look up its drug class."
version: 1.0.0
user-invocable: true
argument-hint: "[drug-name | brand-name | development-code]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"💊","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# Drug Name Resolver

## Overview

This skill uses the RxNorm REST API to resolve drug names (generic names, brand names, development codes, etc.) to standardized RxCUI (RxNorm Concept Unique Identifier) values and retrieves drug classification information.

Supported input formats:
- Generic name (e.g., `osimertinib`)
- Brand name (e.g., `Tagrisso`)
- Development code (e.g., `AZD9291`)

## Usage

### As a Python Module

```python
from drug_name_resolver import DrugNameResolver

resolver = DrugNameResolver()

# Shortcut method: get complete info in one step
result = resolver.resolve("osimertinib")
print(result)
# {
#     "rxcui": "1860477",
#     "name": "osimertinib",
#     "properties": { ... },
#     "drug_class": ["Protein Kinase Inhibitors", ...]
# }

# Step-by-step calls
rxcui = resolver.get_rxcui("Tagrisso")
info = resolver.get_drug_info("Tagrisso")
classes = resolver.get_drug_class(rxcui)
```

### Command Line

```bash
python drug_name_resolver.py osimertinib
python drug_name_resolver.py Tagrisso
python drug_name_resolver.py      # defaults to querying osimertinib
```

## Return Structure

The `resolve()` method returns a dictionary with the following structure:

| Field | Type | Description |
|-------|------|-------------|
| `rxcui` | `str` | RxNorm unique identifier |
| `name` | `str` | Input drug name |
| `properties` | `dict` | Drug properties (name-related) |
| `drug_class` | `list[str]` | List of drug classifications |

If the drug is not found, a dictionary containing only `name` and `error` fields is returned.

## Notes

- The RxNorm API is a free public endpoint; no API key is required
- When an exact match fails, approximate term search is used automatically
- Drug classification results return a maximum of 50 entries
- Network requests include an automatic retry mechanism (3 retries with exponential backoff)
