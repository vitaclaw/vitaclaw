---
name: drug-adverse-event-query
description: "Queries drug adverse event reports from the openFDA FAERS API, including frequency, severity, and outcome distributions. Use when the user wants to understand reported side effects for a medication."
version: 1.0.0
user-invocable: true
argument-hint: "[drug-name]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🚨","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# Drug Adverse Event Query

This skill queries drug adverse event report data through the openFDA FAERS (FDA Adverse Event Reporting System) API.

## Overview

FAERS is the FDA's adverse event reporting system that collects spontaneous reports of post-marketing drug adverse reactions. This skill provides the following query capabilities:

1. **Adverse Event Frequency Query** (`search_adverse_events`): Retrieves the most frequently reported adverse reactions for a drug along with report counts
2. **Serious Adverse Event Query** (`search_serious_events`): Retrieves only events flagged as "serious"
3. **Outcome Distribution Query** (`search_outcomes`): Retrieves the ratio of serious vs. non-serious adverse events
4. **Comprehensive Report** (`get_full_report`): Combines all three queries above to generate a complete adverse reaction profile

## Usage

```bash
python drug_adverse_event.py <drug-name>
```

Examples:

```bash
python drug_adverse_event.py osimertinib
python drug_adverse_event.py pembrolizumab
python drug_adverse_event.py metformin
```

## API Details

- **Data Source**: openFDA Drug Adverse Events API (`https://api.fda.gov/drug/event.json`)
- **API Key**: Optional. Setting the `OPENFDA_API_KEY` environment variable increases rate limits (40 requests/min without a key, 240 requests/min with a key)
- **Drug Name**: Supports queries by generic_name and brand_name

## Important Disclaimers

FAERS is a spontaneous reporting system with the following limitations:

- Report counts do not equal adverse reaction incidence rates
- Reporting bias exists (serious events are more likely to be reported)
- Cannot be used to directly compare the safety profiles of different drugs
- Causal relationships in reports have not been confirmed

Query results are for reference only. Clinical decisions should be based on a comprehensive evaluation of drug labels, clinical trial data, and guideline recommendations.
