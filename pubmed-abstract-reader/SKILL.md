---
name: pubmed-abstract-reader
description: "Retrieves PubMed article abstracts, authors, journal, and metadata in batch by PMID via the NCBI E-utilities API. Also supports keyword-based search. Use when the user has PMIDs to look up or needs article details from PubMed."
version: 1.0.0
user-invocable: true
argument-hint: "[pmid1,pmid2,... | keyword-query]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📄","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# PubMed Abstract Reader

## Instructions

This skill retrieves detailed PubMed article information via the NCBI E-utilities API, including title, authors, journal, year, abstract, and publication types.

### Features

1. **Batch Abstract Retrieval by PMID** — Provide a set of PMIDs and receive complete metadata and abstracts for each article.
2. **Keyword Search** — Enter search terms (supporting Boolean operators) and receive a list of matching articles, with optional time-window filtering.

### Usage

```bash
# Retrieve by PMID (comma-separated)
python3 pubmed_abstract.py 33012899,29625055,28228467

# Run default search example (EGFR L858R osimertinib) when no arguments are provided
python3 pubmed_abstract.py
```

### Environment Variables (Optional)

- `NCBI_API_KEY` — NCBI API Key; when configured, the rate limit increases from 3 requests/sec to 10 requests/sec.
- `NCBI_EMAIL` — Contact email; NCBI recommends providing one so they can reach you if issues arise.

### Output Format

Each article returns the following fields:

| Field | Description |
|-------|-------------|
| `pmid` | PubMed ID |
| `title` | Article title |
| `authors` | Author list |
| `journal` | Journal name |
| `year` | Publication year |
| `abstract` | Full abstract text |
| `publication_types` | List of publication types (e.g., Journal Article, Review, etc.) |

### Agent Guidelines

Use this skill when the user provides PMIDs or needs to retrieve PubMed article abstracts:

1. Run `python3 pubmed_abstract.py <pmid1>,<pmid2>,...` to fetch article information.
2. Present the returned JSON results to the user, highlighting the title, authors, journal, year, and abstract.
3. If the user provides keywords instead of PMIDs, call the `search_pubmed()` method within the script to perform a search.
4. Respect NCBI rate limits: no more than 3 requests/sec without an API key, and no more than 10 requests/sec with an API key.
