---
phase: 05-governance-safety
plan: 02
subsystem: governance
tags: [quality-scoring, staleness-detection, skill-health, ruff, keyword-matching]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Skill linter with frontmatter validation and import direction checks"
provides:
  - "A-F quality scoring for all 236 skills across 7 weighted dimensions"
  - "Stale SKILL.md detection scanner with keyword matching"
  - "Markdown quality report sorted worst-first with grade distribution"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "7-dimension quality scoring with N/A handling for prompt-only skills"
    - "Keyword extraction with stop word filtering for staleness detection"
    - "Proportional reweighting when dimensions are N/A"

key-files:
  created:
    - reports/skill-quality-scores.md
    - scripts/skill_staleness_scanner.py
  modified:
    - scripts/build_skill_governance_report.py

key-decisions:
  - "Prompt-only skills score code/test/lint/bare-except as N/A with proportional reweighting, not zero"
  - "Staleness uses simple keyword overlap (not TF-IDF) for fast deterministic results"
  - "Staleness scanner skips test files to avoid false positive keyword matches"

patterns-established:
  - "Quality scores use weighted dimensions with N/A exclusion for fair grading"
  - "Staleness threshold configurable via CLI (default 50%)"

requirements-completed: [GOV-03, GOV-04, GOV-05]

# Metrics
duration: 3min
completed: 2026-03-26
---

# Phase 05 Plan 02: Skill Quality & Staleness Summary

**A-F quality scoring across 7 dimensions for 236 skills plus keyword-based stale SKILL.md detection scanner**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T13:50:31Z
- **Completed:** 2026-03-26T13:54:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended governance report with `compute_quality_score()` scoring 7 dimensions: frontmatter, code, tests, ruff lint, docs length, bare excepts, license
- Prompt-only skills (no Python) correctly score code-related dimensions as N/A with proportional reweighting
- Generated quality report showing 236 skills: 48 A, 8 B, 50 C, 88 D, 42 F grades
- Created staleness scanner detecting 50 out of 92 scanned skills with description-implementation drift below 50% keyword match
- Both tools support --format markdown|json CLI flags following project conventions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add A-F quality scoring to governance report** - `ed1db6b` (feat)
2. **Task 2: Create stale SKILL.md detection scanner** - `82a0a31` (feat)

## Files Created/Modified
- `scripts/build_skill_governance_report.py` - Extended with compute_quality_score(), --quality-report flag, markdown report generation
- `scripts/skill_staleness_scanner.py` - New scanner with extract_keywords(), check_staleness(), CLI with --threshold/--format/--output
- `reports/skill-quality-scores.md` - Generated markdown report with A-F grades for all 236 skills

## Decisions Made
- Prompt-only skills (no Python) have code, tests, lint, and bare-except dimensions scored as N/A. Remaining dimensions are reweighted proportionally so prompt-only skills are not unfairly penalized.
- Staleness scanner uses simple word overlap (regex-based keyword extraction + stop word filtering) rather than TF-IDF, keeping it fast, deterministic, and dependency-free.
- Test files are excluded from staleness code scanning to avoid false positive keyword matches from test fixtures.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Quality scoring and staleness detection infrastructure complete
- Both tools ready for CI integration if desired
- Reports available for operator review of skill health across all 236 skills

---
*Phase: 05-governance-safety*
*Completed: 2026-03-26*
