# Roadmap: VitaClaw

## Milestones

- ✅ **v1.0 Iteration 2** - Phases 1-4 (shipped 2026-03-26)
- 🚧 **v1.1 Agent-First Governance** - Phases 5-7 (in progress)

## Phases

<details>
<summary>✅ v1.0 Iteration 2 (Phases 1-4) - SHIPPED 2026-03-26</summary>

- [x] **Phase 1: Foundation + Multi-Person Architecture** - Engineering hardening (pyproject.toml, CI, migration) and person_id threading through the entire data layer
- [x] **Phase 2: Data Ingestion** - Onboarding flow, device importers (Google Fit, Huawei, Xiaomi), and OCR pipeline for medical documents
- [x] **Phase 3: Visualization + Correlation Analysis** - Trend charts with clinical context and cross-metric correlation insights
- [x] **Phase 4: Clinical Output** - Doctor-ready visit summaries and annual health reports

</details>

- [ ] **Phase 5: Governance & Safety** - Skill structure linting, quality scoring, stale doc detection, and SOUL.md safety boundary test suite
- [ ] **Phase 6: Data Observability & AI-Assisted OCR** - HealthDataStore stats API, data dashboard CLI, LLM-enhanced OCR with LOINC mapping
- [ ] **Phase 7: Proactive Correlation Alerts** - Heartbeat-integrated correlation detection with throttled natural language alerts

## Phase Details

<details>
<summary>✅ v1.0 Iteration 2 (Phases 1-4) - SHIPPED 2026-03-26</summary>

### Phase 1: Foundation + Multi-Person Architecture
**Goal**: The codebase has modern packaging, automated quality gates, data migration capability, and a person_id abstraction threaded through all data-accessing code
**Depends on**: Nothing (first phase)
**Requirements**: ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, FAM-01, FAM-02, FAM-03, FAM-04, FAM-05
**Success Criteria** (what must be TRUE):
  1. Running `pip install -e .` installs VitaClaw with all core dependencies resolved from pyproject.toml
  2. Pushing code triggers CI that runs tests and linting, blocking merge on failure
  3. A user with existing Iteration 1 data can run the migration tool and continue using all skills without data loss
  4. User can create family member profiles and switch between them; each person's health data is fully isolated
  5. All existing skills (tracking, heartbeat, memory) work correctly in per-person context without code changes to individual skills
**Plans:** 3/3 complete

Plans:
- [x] 01-01-PLAN.md -- Engineering foundation: pyproject.toml, package structure, ruff, sys.path cleanup
- [x] 01-02-PLAN.md -- person_id threading through HealthDataStore, HealthMemoryWriter, CrossSkillReader
- [x] 01-03-PLAN.md -- GitHub Actions CI pipeline

### Phase 2: Data Ingestion
**Goal**: Users can populate their health record through three channels -- guided onboarding for profile setup, file-based wearable data import, and photo/PDF OCR for medical documents
**Depends on**: Phase 1
**Requirements**: ONBD-01, ONBD-02, ONBD-03, IMPT-01, IMPT-02, IMPT-03, IMPT-04, IMPT-05, OCR-01, OCR-02, OCR-03, OCR-04, OCR-05
**Success Criteria** (what must be TRUE):
  1. A new user can complete a conversational onboarding flow and find their demographics, conditions, medications, and goals populated in their profile files
  2. User can import Google Fit, Huawei Health, and Xiaomi exports using the same workflow pattern without duplicates
  3. User can photograph a Chinese medical document and see structured fields extracted for confirmation before storage
**Plans:** 5/5 complete

Plans:
- [x] 02-01-PLAN.md -- Onboarding SKILL.md with conversational health profile setup
- [x] 02-02-PLAN.md -- HealthImporterBase shared class + Google Fit importer
- [x] 02-03-PLAN.md -- Huawei Health + Xiaomi/Mi Fitness importers
- [x] 02-04-PLAN.md -- OCR pipeline core: table + text extraction with PaddleOCR
- [x] 02-05-PLAN.md -- OCR confirmation-to-storage bridge

### Phase 3: Visualization + Correlation Analysis
**Goal**: Users can see their health data as trend charts with clinical context and discover cross-metric patterns
**Depends on**: Phase 2
**Requirements**: VIZ-01, VIZ-02, VIZ-03, VIZ-04, CORR-01, CORR-02, CORR-03
**Success Criteria** (what must be TRUE):
  1. User can generate trend charts for blood pressure, blood glucose, weight, and sleep with clinically meaningful reference range bands
  2. User can request cross-metric correlation analysis and receive natural language insights with statistical confidence levels
**Plans:** 2/2 complete

Plans:
- [x] 03-01-PLAN.md -- Health chart engine: trend charts with clinical reference bands and CJK support
- [x] 03-02-PLAN.md -- Correlation engine enhancement: scipy stats, p-values, Spearman, Chinese NL insights

### Phase 4: Clinical Output
**Goal**: Users can produce doctor-ready visit summaries and comprehensive annual reports
**Depends on**: Phase 3
**Requirements**: VISIT-01, VISIT-02, VISIT-03, VISIT-04, ARPT-01, ARPT-02, ARPT-03
**Success Criteria** (what must be TRUE):
  1. User can generate a visit summary with recent vitals, medications, lab results, and concerns as Markdown/HTML/PDF with embedded trend charts
  2. User can generate a year-in-review health report as styled HTML with embedded charts
**Plans:** 2/2 complete

Plans:
- [x] 04-01-PLAN.md -- Doctor-ready visit summary with Markdown/HTML/PDF output and embedded trend charts
- [x] 04-02-PLAN.md -- Annual health report with year-in-review HTML

</details>

### Phase 5: Governance & Safety
**Goal**: Agent and human operators can verify skill quality and safety boundaries mechanically
**Depends on**: Phase 4 (v1.0 complete)
**Requirements**: GOV-01, GOV-02, GOV-03, GOV-04, GOV-05, SAFE-01, SAFE-02, SAFE-03, SAFE-04
**Success Criteria** (what must be TRUE):
  1. Running the skill linter on any SKILL.md reports whether its YAML frontmatter is valid against the schema and whether import directions are correct (skills depend on _shared, not vice versa)
  2. A single markdown report shows all 222 skills with A-F health grades sorted worst-first, based on frontmatter completeness, test coverage, code quality, and documentation
  3. Stale SKILL.md files where the description has drifted from the Python implementation are detected with actionable fix suggestions
  4. A test suite catches: (a) outputs missing "必须就医" for red-flag vitals, (b) diagnostic conclusions in skill output, (c) MEMORY.md auto-loading in group/public contexts, (d) high-risk escalation paths interrupting normal flow
**Plans:** 3 plans

Plans:
- [x] 05-01-PLAN.md -- Skill structure linter: frontmatter validation + import direction checks with pytest CI wrapper
- [x] 05-02-PLAN.md -- Quality scoring (A-F grades) + stale SKILL.md detection scanner
- [x] 05-03-PLAN.md -- SOUL.md safety boundary test suite (red-flag vitals, memory privacy, diagnostic prohibition, escalation)

### Phase 6: Data Observability & AI-Assisted OCR
**Goal**: Users can inspect data health at a glance and get higher-accuracy OCR extraction with standardized medical coding
**Depends on**: Phase 5
**Requirements**: OBS-01, OBS-02, OBS-03, AOCR-01, AOCR-02, AOCR-03
**Success Criteria** (what must be TRUE):
  1. Calling HealthDataStore.stats() returns per-skill record counts, last update timestamps, and data time spans, filterable by person_id
  2. A CLI command outputs a markdown dashboard table showing all tracked metrics with record counts and data freshness
  3. OCR pipeline uses LLM post-processing to extract fields from ambiguous medical documents with higher accuracy than raw PaddleOCR alone
  4. Extracted lab items are automatically mapped to LOINC codes via ConceptResolver and the system suggests which VitaClaw skill should track each metric
**Plans:** 2 plans

Plans:
- [ ] 06-01-PLAN.md -- Data observability: HealthDataStore.stats() + global_stats() + CLI dashboard
- [ ] 06-02-PLAN.md -- AI-assisted OCR: LLM enhancer with LOINC mapping and skill routing

### Phase 7: Proactive Correlation Alerts
**Goal**: Users receive timely, actionable alerts when VitaClaw discovers significant cross-metric patterns in their health data
**Depends on**: Phase 6
**Requirements**: ALRT-01, ALRT-02, ALRT-03
**Success Criteria** (what must be TRUE):
  1. Heartbeat automatically runs CorrelationEngine and detects statistically significant cross-metric patterns without user intervention
  2. Each correlation alert includes natural language explanation, statistical evidence (r, p, n), and actionable advice
  3. Alert frequency is throttled to max 1 per week per metric pair with only p<0.01 significance level to prevent fatigue
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 5 -> 6 -> 7

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation + Multi-Person Architecture | v1.0 | 3/3 | Complete | 2026-03-26 |
| 2. Data Ingestion | v1.0 | 5/5 | Complete | 2026-03-26 |
| 3. Visualization + Correlation Analysis | v1.0 | 2/2 | Complete | 2026-03-26 |
| 4. Clinical Output | v1.0 | 2/2 | Complete | 2026-03-26 |
| 5. Governance & Safety | v1.1 | 1/3 | In progress | - |
| 6. Data Observability & AI-Assisted OCR | v1.1 | 0/2 | Not started | - |
| 7. Proactive Correlation Alerts | v1.1 | 0/? | Not started | - |
