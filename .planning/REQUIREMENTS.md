# Requirements: VitaClaw v1.1 Agent-First Governance

**Defined:** 2026-03-26
**Core Value:** 比用户记得更全、追得更连续、整理得更系统——在需要就医或决策时，能快速调出完整上下文。

## v1.1 Requirements

### Skill Governance

- [x] **GOV-01**: Skill structure linter validates every SKILL.md has valid YAML frontmatter matching skill-frontmatter.schema.json
- [x] **GOV-02**: Skill structure linter validates import directions (skills depend on _shared/, _shared/ does not depend on individual skills)
- [x] **GOV-03**: Skill quality scoring system assigns a health grade (A-F) to each of 222 skills based on frontmatter completeness, test coverage, code quality, and documentation
- [x] **GOV-04**: Quality score report is generated as a single markdown file showing all skills with grades, sortable by worst-first
- [x] **GOV-05**: Stale SKILL.md scanner detects when a skill's description does not match its Python implementation and generates fix suggestions

### Data Observability

- [ ] **OBS-01**: HealthDataStore.stats() returns per-skill record count, last update timestamp, and data time span
- [ ] **OBS-02**: HealthDataStore.stats() supports person_id filtering to show per-person data overview
- [ ] **OBS-03**: CLI script exposes stats as a health data dashboard (markdown table of all tracked metrics with counts and freshness)

### Safety Testing

- [x] **SAFE-01**: Test suite verifies that any output containing red-flag vital signs includes a "必须就医" layer
- [x] **SAFE-02**: Test suite verifies that group/public context does not auto-load MEMORY.md
- [x] **SAFE-03**: Test suite verifies that no skill output contains explicit diagnostic conclusions (per SOUL.md prohibition)
- [x] **SAFE-04**: Test suite verifies that high-risk escalation paths interrupt normal flow

### AI-Assisted OCR

- [ ] **AOCR-01**: OCR pipeline can use LLM post-processing to improve field extraction accuracy for ambiguous medical documents
- [ ] **AOCR-02**: Extracted lab items are automatically mapped to LOINC codes via ConceptResolver and health-concepts.yaml
- [ ] **AOCR-03**: OCR field extraction auto-suggests which VitaClaw skill should track each extracted metric

### Proactive Alerts

- [ ] **ALRT-01**: Heartbeat integrates with CorrelationEngine to auto-detect statistically significant cross-metric patterns
- [ ] **ALRT-02**: Proactive alerts include natural language explanation, statistical evidence (r, p, n), and actionable advice
- [ ] **ALRT-03**: Alert frequency is controlled to avoid fatigue (max 1 correlation alert per week per metric pair, only p<0.01)

## Future Requirements

### Advanced Governance
- **GOV-V2-01**: Auto-fix PRs for common skill issues (missing frontmatter fields, bare except clauses)
- **GOV-V2-02**: License audit automation (detect conflicting copyright headers)

### Conversational Profiling
- **ONBD-V2-01**: Onboarding uses AI-driven conversational flow with adaptive follow-up questions

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web dashboard for quality scores | VitaClaw is CLI/Agent-based, not a web app |
| Real-time alert streaming | Heartbeat runs on schedule, not real-time |
| Automated skill refactoring | v1.1 detects issues; auto-fix is v2 |
| Cross-repo skill dependency analysis | Single repo architecture |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GOV-01 | Phase 5 | Complete |
| GOV-02 | Phase 5 | Complete |
| GOV-03 | Phase 5 | Complete |
| GOV-04 | Phase 5 | Complete |
| GOV-05 | Phase 5 | Complete |
| SAFE-01 | Phase 5 | Complete |
| SAFE-02 | Phase 5 | Complete |
| SAFE-03 | Phase 5 | Complete |
| SAFE-04 | Phase 5 | Complete |
| OBS-01 | Phase 6 | Pending |
| OBS-02 | Phase 6 | Pending |
| OBS-03 | Phase 6 | Pending |
| AOCR-01 | Phase 6 | Pending |
| AOCR-02 | Phase 6 | Pending |
| AOCR-03 | Phase 6 | Pending |
| ALRT-01 | Phase 7 | Pending |
| ALRT-02 | Phase 7 | Pending |
| ALRT-03 | Phase 7 | Pending |

**Coverage:**
- v1.1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-26*
*Last updated: 2026-03-26 after roadmap creation*
