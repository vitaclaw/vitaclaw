# External Integrations

**Analysis Date:** 2026-03-26

## AI / LLM Services

**OpenRouter (primary LLM gateway):**
- Used by: `skills/research-lookup/research_lookup.py`, `skills/cancer-nutrition-coach/cancer_nutrition_coach.py`, `skills/weekly-health-digest/weekly_health_digest.py`
- Models accessed: `perplexity/sonar-pro-search`, `perplexity/sonar-reasoning-pro`
- Auth: `OPENROUTER_API_KEY` env var
- Base URL: `https://openrouter.ai/api/v1/chat/completions`

**Local LLM (privacy desensitization):**
- Used by: `privacy_desensitize.py`
- Default endpoint: `http://localhost:8000/v1` (OpenAI-compatible)
- Model: `Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit` (default, configurable)
- Auth: `LLM_API_KEY` env var (default: hardcoded fallback)
- Config: `LLM_API_BASE`, `LLM_MODEL` env vars

**OpenClaw Runtime (host platform):**
- VitaClaw runs inside OpenClaw as a skill library
- Default model: `anthropic/claude-sonnet-4-5` with fallback `openai/gpt-5.2` (configured in `configs/openclaw.health.json5`)
- Agent tools: Read, Edit, Write, Bash, Glob, Grep, WebFetch, WebSearch, Task

## Biomedical & Clinical APIs

**NCBI / PubMed (E-utilities):**
- Used by: `skills/pubmed-abstract-reader/pubmed_abstract.py`, `skills/citation-management/scripts/search_pubmed.py`
- Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- Auth: `NCBI_API_KEY` (optional, increases rate limit to 10/sec)
- Also: `NCBI_EMAIL` env var (recommended by NCBI)

**NCBI Datasets API:**
- Used by: `skills/gene-database/scripts/fetch_gene_data.py`
- Base URL: `https://api.ncbi.nlm.nih.gov/datasets/v2alpha/gene`
- Auth: None required (public API)

**ClinicalTrials.gov API v2:**
- Used by: `skills/clinical-trial-search/clinical_trial_search.py`
- Base URL: `https://clinicaltrials.gov/api/v2/studies`
- Auth: None required (public API)

**RxNorm (NLM):**
- Used by: `skills/drug-interaction-checker/drug_interaction.py`
- Base URLs: `https://rxnav.nlm.nih.gov/REST`, `https://rxnav.nlm.nih.gov/REST/interaction`
- Auth: None required (public API)

**openFDA:**
- Used by: `skills/drug-interaction-checker/drug_interaction.py` (drug labels), `skills/drug-adverse-event-query/drug_adverse_event.py` (FAERS), `skills/drug-label-lookup/drug_label.py`, `skills/fda-database/scripts/fda_query.py`
- Base URLs: `https://api.fda.gov/drug/label.json`, `https://api.fda.gov/drug/event.json`
- Auth: `OPENFDA_API_KEY` (optional, increases rate limit)

**Ensembl REST API:**
- Used by: `skills/ensembl-database/scripts/ensembl_query.py`
- Base URL: `https://rest.ensembl.org`
- Auth: None required (rate limit: 15 req/sec anonymous)

**KEGG REST API:**
- Used by: `skills/kegg-database/scripts/kegg_api.py`
- Base URL: `https://rest.kegg.jp`
- Auth: None (academic use only)

**PGS Catalog:**
- Used by: `skills/gwas-prs/gwas_prs.py`
- Purpose: Polygenic Risk Score data lookup
- Auth: None required

**bioRxiv API:**
- Used by: `skills/biorxiv-database/scripts/biorxiv_search.py`
- Purpose: Preprint literature search

**PubChem API:**
- Used by: `skills/pubchem-database/scripts/compound_search.py`, `skills/pubchem-database/scripts/bioactivity_query.py`
- Purpose: Chemical compound and bioactivity data

**UniProt API:**
- Used by: `skills/uniprot-database/scripts/uniprot_client.py`
- Purpose: Protein sequence and function data

**Reactome API:**
- Used by: `skills/reactome-database/scripts/reactome_query.py`
- Purpose: Biological pathway data

**DrugBank:**
- Used by: `skills/drugbank-database/scripts/drugbank_helper.py`
- Purpose: Drug data reference

**COSMIC Database:**
- Used by: `skills/cosmic-database/scripts/download_cosmic.py`
- Purpose: Cancer mutation data

**ClinPGx:**
- Used by: `skills/clinpgx-database/scripts/query_clinpgx.py`
- Purpose: Clinical pharmacogenomics data

**ClinVar / dbSNP / gnomAD / MyVariant:**
- Used by: `skills/bio-clinical-databases-clinvar-lookup/`, `skills/bio-clinical-databases-dbsnp-queries/`, `skills/bio-clinical-databases-gnomad-frequencies/`, `skills/bio-clinical-databases-myvariant-queries/`
- Purpose: Variant annotation and population frequency data

## Data Storage

**Databases:**
- None. All data is file-based (JSONL + Markdown).
- JSONL files stored in `data/<skill-slug>/` directories
- Health memory as Markdown in `memory/health/`
- Patient archives at `~/.openclaw/patients/` (structured Markdown + files)

**File Storage:**
- Local filesystem only
- Charts generated as PNG in `data/<skill-slug>/charts/`
- Health data records follow `schemas/health-data-record.schema.json`

**Caching:**
- None (no Redis, no memcached, no in-memory cache layer)

## Data Exchange Standards

**FHIR R4:**
- Bidirectional mapper: `skills/_shared/fhir_mapper.py`
- Maps VitaClaw records to/from FHIR R4 Observation, MedicationStatement, Condition resources
- Uses LOINC coding via `skills/_shared/concept_resolver.py`

**OMOP CDM:**
- Export script: `scripts/export_omop.py`
- Generates person.jsonl, observation.jsonl, drug_exposure.jsonl
- Consent-controlled via `skills/_shared/consent_manager.py`

**SMART Health Cards:**
- Generator/verifier: `skills/_shared/smart_health_card.py`
- Wraps FHIR Bundle into JWS per SHC specification
- Optional dependencies: `cryptography`, `python-jose`

## Push Notifications & Messaging

**Feishu (Lark) Bot:**
- Used by: `skills/_shared/push_dispatcher.py`, `scripts/apple_health_feishu_bridge.py`
- API: `https://open.feishu.cn/open-apis/`
- Auth: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_RECEIVE_USER_ID` env vars
- Purpose: Health notifications, daily health digests

**Bark (iOS Push):**
- Used by: `skills/_shared/push_dispatcher.py`
- Auth: `BARK_URL` env var (e.g. `https://api.day.app/YOUR_KEY`)
- Purpose: iOS push notifications for health alerts

**macOS Native Notifications:**
- Used by: `skills/_shared/push_dispatcher.py`
- Method: `osascript` / `terminal-notifier`
- Purpose: Desktop health alerts

**Generic Webhook:**
- Used by: `skills/_shared/push_dispatcher.py`
- Auth: `VITACLAW_WEBHOOK_URL` env var
- Purpose: Custom integration endpoint

**Push Channel Configuration:**
- `VITACLAW_PUSH_CHANNEL` - comma-separated channels: `"feishu,macos"` | `"none"` (default: `"none"`)
- `VITACLAW_PUSH_ROUTING` - priority-based routing config
- Priority levels: high (all channels), medium (first channel), low (task board only)

## Apple Health Integration

**Apple Health Export:**
- Import script: `scripts/import_apple_health_export.py`
- Bridge runtime: `skills/_shared/apple_health_bridge.py`
- Parses Apple Health `export.xml` files
- Syncs data into VitaClaw patient archive and workspace

**iOS Shortcut Bridge Server:**
- Server script: `scripts/apple_health_feishu_bridge.py`
- Receives HTTP POST from iOS Shortcuts containing daily Apple Health data
- Writes to VitaClaw data layer and forwards via Feishu bot
- Runs as a local HTTP server (`http.server`)

## Scheduled Tasks

**macOS launchd:**
- Plist: `configs/com.vitaclaw.heartbeat.plist`
- Runs `scripts/run_health_heartbeat.py` every 7200 seconds (2 hours)
- Setup: `scripts/setup_heartbeat_scheduler.sh`
- Logs to `<repo>/logs/heartbeat.log`

## Web Access (Controlled)

**Web Access Runtime:**
- Implementation: `skills/_shared/web_access_runtime.py`
- Policy: `public-health-pages-only` (configured in `configs/openclaw.health.json5`)
- Blocked domains: social media, search engines, e-commerce (see comprehensive blocklist in source)
- Used by: doctor profile harvesting (`skills/_shared/doctor_profile_harvester.py`)
- Browser fallback support for dynamic pages

## Authentication & Identity

**Auth Provider:**
- No centralized auth system. This is a local-first tool.
- API keys managed via environment variables per service
- Patient identity via `skills/_shared/twin_identity.py` (Digital Twin identity management)
- Consent management via `skills/_shared/consent_manager.py` (controls data export and sharing)

## Environment Configuration

**Required env vars (minimum for core functionality):**
- None strictly required for basic operation

**Optional env vars by feature:**
- `OPENROUTER_API_KEY` - Research lookup, LLM-powered skills
- `NCBI_API_KEY` / `NCBI_EMAIL` - PubMed higher rate limits
- `OPENFDA_API_KEY` - FDA API higher rate limits
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` / `FEISHU_RECEIVE_USER_ID` - Feishu push notifications
- `BARK_URL` - Bark iOS push
- `VITACLAW_PUSH_CHANNEL` - Push channel selection
- `VITACLAW_WEBHOOK_URL` - Generic webhook push
- `VITACLAW_DATA_DIR` - Custom data directory override
- `LLM_API_BASE` / `LLM_API_KEY` / `LLM_MODEL` - Local LLM for privacy desensitization

**Secrets location:**
- Environment variables only. No `.env` file checked into repo.
- No secrets management service detected.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, no external error tracking)

**Logs:**
- Python `logging` module used in individual skill scripts
- Heartbeat logs to `<repo>/logs/heartbeat.log` via launchd
- Write audit trail at `memory/health/files/write-audit.md`

**Health Operations Reports:**
- Generated by `scripts/run_health_operations.py`
- Stored in `data/health-operations/`
- Governance reports in `reports/` directory

## CI/CD & Deployment

**Hosting:**
- Local machine (no cloud deployment)
- Distributed as release packages via `scripts/build_vitaclaw_release.py` to `dist/`

**CI Pipeline:**
- No CI/CD pipeline detected (no `.github/workflows/`, no `.gitlab-ci.yml`, etc.)
- Manual quality gates: `scripts/smoke_test_skills.py`, `scripts/validate_skill_frontmatter.py`, `scripts/build_skill_governance_report.py`

## Webhooks & Callbacks

**Incoming:**
- Apple Health bridge server at `scripts/apple_health_feishu_bridge.py` (local HTTP POST endpoint for iOS Shortcuts)

**Outgoing:**
- Feishu bot messages via Open API
- Bark push notifications
- Generic webhook POST to `VITACLAW_WEBHOOK_URL`

---

*Integration audit: 2026-03-26*
