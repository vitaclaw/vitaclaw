---
name: clinical-trial-search
description: "Searches ClinicalTrials.gov for clinical trials with multi-dimensional filtering by disease, intervention, location, and trial status. Retrieves trial details by NCT ID and formats results as structured Markdown. Use when the user wants to find relevant clinical trials."
version: 1.0.0
user-invocable: true
argument-hint: "[condition | nct-id | condition intervention location]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🔬","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# Clinical Trial Search Skill

## Overview

This skill searches global clinical trials via the ClinicalTrials.gov API v2, supporting the following capabilities:

1. **Multi-Dimensional Search**: Filter by disease/condition, intervention (drug), location, and trial status
2. **Trial Detail Lookup**: Retrieve complete information for a single trial by NCT ID
3. **Formatted Output**: Format search results into a structured Markdown report

## Usage

### Command Line

```bash
# Default search for NSCLC EGFR-related trials
python clinical_trial_search.py

# Search by specified disease condition
python clinical_trial_search.py "breast cancer HER2"
```

### As a Module

```python
from clinical_trial_search import ClinicalTrialSearch, format_results

# Create client
client = ClinicalTrialSearch()

# Search trials
results = client.search(
    condition="EGFR mutation non-small cell lung cancer",
    intervention="osimertinib",
    location="China",
    status="RECRUITING",
    max_results=10
)

# Format output
print(format_results(results, location="China"))

# Get single trial details
detail = client.get_details("NCT04532463")
```

## Parameters

### search() Method

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `condition` | str | (required) | Disease/condition, e.g., `"NSCLC"`, `"EGFR mutation lung cancer"` |
| `intervention` | str | None | Intervention/drug, e.g., `"osimertinib"` |
| `location` | str | `"China"` | Location filter; set to `None` or empty string for global search |
| `status` | str | `"RECRUITING"` | Trial status; supports comma-separated multiple values |
| `max_results` | int | 20 | Maximum number of results to return |

### Trial Status Values

- `RECRUITING` - Currently recruiting
- `NOT_YET_RECRUITING` - Not yet recruiting
- `ACTIVE_NOT_RECRUITING` - Active, not recruiting
- `COMPLETED` - Completed
- `TERMINATED` - Terminated
- `WITHDRAWN` - Withdrawn
- `SUSPENDED` - Suspended

Multiple values can be combined, e.g., `"RECRUITING,NOT_YET_RECRUITING"`.

### get_details() Method

| Parameter | Type | Description |
|-----------|------|-------------|
| `nct_id` | str | NCT ID, e.g., `"NCT04532463"` |

## Return Data Structure

Each trial result contains the following fields:

```python
{
    "nct_id": "NCT04532463",
    "brief_title": "Brief trial title",
    "official_title": "Full official trial title",
    "phase": "PHASE3",
    "status": "RECRUITING",
    "enrollment": 500,
    "start_date": "2021-01-15",
    "completion_date": "2025-06-30",
    "conditions": ["Non-small Cell Lung Cancer"],
    "interventions": [{"name": "Osimertinib", "type": "DRUG"}],
    "locations": [{"facility": "Hospital name", "city": "City", "country": "China"}],
    "sponsor": "Sponsor name",
    "eligibility_criteria": "Full eligibility criteria text",
    "url": "https://clinicaltrials.gov/study/NCT04532463"
}
```

## Notes

- Search terms should be entered in English (e.g., `"NSCLC"` rather than the Chinese equivalent) for better matching results
- By default, results are filtered to trials in China; set `location` to `None` for a global search
- Results reflect real-time data; actual enrollment requires contacting each site's PI to confirm eligibility
- The API includes a built-in automatic retry mechanism (up to 3 retries) for 429/5xx errors
