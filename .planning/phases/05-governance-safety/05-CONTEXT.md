# Phase 5: Governance & Safety - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Mechanical verification infrastructure: skill structure linter (YAML frontmatter + import direction), skill quality scoring system (A-F grades for 222 skills), stale SKILL.md detection, and SOUL.md safety boundary test suite. All tools enforce rules that were previously documented but not mechanically checked.

</domain>

<decisions>
## Implementation Decisions

### Skill Structure Linter
- **D-01:** Extend existing `scripts/validate_skill_frontmatter.py` rather than creating a new tool. Add import direction validation and data layer usage checks.
- **D-02:** Linter runs as a standalone script AND as a pytest test (so CI catches violations). Output: pass/fail per skill with structured error messages that include remediation instructions (per Harness Engineering pattern — error messages become agent context).
- **D-03:** Import direction rule: files under `skills/{name}/` may import from `skills/_shared/` but `skills/_shared/` must NOT import from any specific skill directory. Validated by scanning Python files for import statements.
- **D-04:** Frontmatter validation uses existing `schemas/skill-frontmatter.schema.json`. Checks: required fields present (name, description, version, category), values match allowed enums, no unknown fields.

### Skill Quality Scoring
- **D-05:** Extend existing `scripts/build_skill_governance_report.py` to produce A-F grades. Scoring dimensions: (1) frontmatter completeness (20%), (2) has Python implementation (15%), (3) has tests (20%), (4) code passes ruff (15%), (5) SKILL.md description length >50 chars (10%), (6) no bare except clauses (10%), (7) no proprietary copyright conflicts (10%).
- **D-06:** Output: `reports/skill-quality-scores.md` — markdown table with columns: Skill, Grade, Frontmatter, Code, Tests, Lint, Docs, Issues. Sorted worst-first.
- **D-07:** Grade thresholds: A (≥90%), B (≥75%), C (≥60%), D (≥40%), F (<40%). Percentages based on weighted dimension scores.

### Stale SKILL.md Detection
- **D-08:** Scanner compares SKILL.md description against Python implementation. Uses keyword extraction (not LLM) — checks whether key terms in the SKILL.md (tool names, data types, output formats) appear in the Python code. Skills with <50% keyword match are flagged as potentially stale.
- **D-09:** Output: list of flagged skills with mismatch details and suggested actions (update description, review implementation, or mark as prompt-only skill).

### Safety Boundary Tests
- **D-10:** Safety tests are pytest tests in `tests/test_safety_boundaries.py`. They test the shared runtime modules, not individual skills.
- **D-11:** Red-flag vital signs test: feed HealthScenarioRuntime extreme values (e.g., systolic >180, glucose >20 mmol/L) and verify output contains "必须就医" section.
- **D-12:** Memory privacy test: verify HealthMemoryWriter refuses to auto-load MEMORY.md when context indicates group/public scenario.
- **D-13:** Diagnostic prohibition test: verify HealthScenarioRuntime output never contains diagnostic-conclusion patterns (e.g., "确诊", "诊断为", "你患有").
- **D-14:** Escalation test: verify HealthHeartbeat flags critical vitals with high-priority escalation that interrupts normal advice flow.

### Claude's Discretion
- Exact keyword extraction algorithm for stale detection (TF-IDF vs simple word overlap)
- How to handle skills that are prompt-only (no Python) in quality scoring — they should still get a grade but code/test/lint dimensions score N/A
- Whether to add the linter to CI immediately or as a separate follow-up
- Exact red-flag thresholds for safety tests (use clinical guidelines)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Governance Tools
- `scripts/validate_skill_frontmatter.py` — Existing frontmatter validator to extend
- `scripts/build_skill_governance_report.py` — Existing governance report to extend
- `scripts/smoke_test_skills.py` — Existing smoke test runner
- `scripts/skill_catalog.py` — Skill catalog parser (YAML frontmatter extraction)
- `schemas/skill-frontmatter.schema.json` — Frontmatter schema for validation

### Safety References
- `SOUL.md` — Safety boundaries and output rules
- `skills/_shared/health_scenario_runtime.py` — Six-layer output format implementation
- `skills/_shared/health_heartbeat.py` — Proactive checks and escalation
- `skills/_shared/health_memory.py` — Memory loading with privacy controls

### Quality Context
- `.planning/codebase/CONCERNS.md` — Known issues (bare except, copyright conflicts, etc.)
- `reports/` — Existing report output directory

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `validate_skill_frontmatter.py`: Already validates frontmatter against schema. Needs import direction checks added.
- `build_skill_governance_report.py`: Already generates governance reports. Needs quality scoring added.
- `skill_catalog.py`: Parses SKILL.md YAML frontmatter — used by multiple scripts.
- `HealthScenarioRuntime.DEFAULT_SECTION_ORDER`: Defines the six-layer output format including "必须就医".

### Established Patterns
- Scripts in `scripts/` use argparse with --format markdown|json
- Reports go to `reports/` directory
- Tests in `tests/test_*.py` using unittest.TestCase

### Integration Points
- Linter integrates with CI (`.github/workflows/ci.yml`) as additional test
- Quality scorer reads from skill_catalog and existing validators
- Safety tests import from `skills._shared` modules directly

</code_context>

<specifics>
## Specific Ideas

- Error messages in linter should include remediation instructions (Harness Engineering insight: lint error messages ARE agent context)
- Quality scoring for prompt-only skills (no Python) should score code/test/lint as N/A, not 0
- Safety tests should use real clinical thresholds, not arbitrary numbers
- Stale detection uses keyword matching, not LLM (fast, deterministic, no API dependency)

</specifics>

<deferred>
## Deferred Ideas

- **Auto-fix PRs** (GOV-V2-01) — v1.1 detects, v2 auto-fixes
- **License audit automation** (GOV-V2-02) — separate concern, not in this phase

</deferred>

---

*Phase: 05-governance-safety*
*Context gathered: 2026-03-26*
