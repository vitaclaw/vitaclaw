---
name: pubmed-search
description: "Performs intelligent PubMed literature search using a 3-layer LLM progressive query architecture with evidence bucketing and stratified sampling, returning high-quality clinical literature. Use when the user needs to find research papers on a biomedical topic."
version: 1.0.0
user-invocable: true
argument-hint: "[search-query]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🔍","category":"health","requires":{"bins":["python3"]},"install":[{"kind":"uv","package":"requests"}]}}
---

# PubMed Intelligent Literature Search

This skill provides intelligent PubMed searching based on a 3-layer LLM progressive architecture that automatically optimizes query strategies, evaluates literature quality, and performs stratified sampling by evidence level.

## Full Capability Chain

```
User natural-language query
  → [Layer 1 LLM] High-precision [tiab]-only query → PubMed API
  → [Layer 2 LLM] Expanded recall with MeSH+TIAB+synonyms → PubMed API (carries L1 failure info)
  → [Layer 3 LLM] Minimal fallback disease+gene → PubMed API (carries L1+L2 failure info)
  → [Regex Fallback] Best single-concept extraction (no LLM) → PubMed API
  → [XML Bucketing] PubMed PublicationType → 6 evidence buckets
  → [LLM Batch Scoring] Parallel 20 articles/batch relevance+evidence quality scoring
  → [LLM Re-bucketing] Uncategorized articles backfill study_type
  → [Stratified Sampling] By evidence bucket quota + empty-bucket reallocation → final results
```

## Usage

### As a Python Module

```python
from pubmed_search import SmartPubMedSearch

searcher = SmartPubMedSearch()
results, query_used = searcher.search("EGFR L858R osimertinib resistance", max_results=20)

for article in results:
    print(f"PMID {article['pmid']}: {article['title']}")
    print(f"  Evidence bucket: {article.get('mtb_bucket')}, Relevance: {article.get('relevance_score')}")
```

### Command Line

```bash
python pubmed_search.py "KRAS G12C colorectal cancer cetuximab"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key (used for LLM query optimization and literature scoring) |
| `OPENROUTER_BASE_URL` | No | OpenRouter API URL; defaults to `https://openrouter.ai/api/v1/chat/completions` |
| `LLM_MODEL` | No | LLM model name; defaults to `google/gemini-2.5-flash` |
| `LLM_MAX_TOKENS` | No | LLM maximum output tokens; defaults to `65536` |
| `NCBI_API_KEY` | No | NCBI API Key (increases rate limit to 10 requests/sec) |
| `NCBI_EMAIL` | No | NCBI contact email |

## Evidence Buckets

Literature is classified into the following 6 evidence buckets (ordered by priority):

| Bucket | Description | Default Quota |
|--------|-------------|---------------|
| guideline | Clinical guidelines, consensus statements | 3 |
| rct | Randomized controlled trials, clinical trials | 6 |
| systematic_review | Systematic reviews, meta-analyses | 4 |
| observational | Observational studies, cohort studies | 4 |
| case_report | Case reports | 2 |
| preclinical | Preclinical studies | 1 |

## Notes

- `OPENROUTER_API_KEY` is required for full LLM query optimization and literature scoring functionality
- If no LLM API key is available, set `skip_filtering=True` to skip LLM scoring and use only XML metadata bucketing
- By default, searches literature from the past 10 years; adjustable via the `year_window` parameter
- Broad search fetches up to 200 articles by default, which are then filtered by LLM and sampled by quota
