---
phase: 03-visualization-correlation-analysis
plan: 02
subsystem: health-analyzer
tags: [scipy, correlation, pearson, spearman, p-value, statistics, chinese-nlp]

# Dependency graph
requires:
  - phase: 01-engineering-foundation
    provides: "pyproject.toml, CrossSkillReader with person_id, ConceptResolver"
provides:
  - "Enhanced CorrelationEngine with scipy Pearson+Spearman, p-values, n>=14 minimum"
  - "CorrelationResult with is_significant(), to_natural_language(), updated to_dict()"
  - "health-correlation-analyzer SKILL.md (user-invocable)"
  - "CLI script analyze_health_correlations.py with markdown/JSON output"
  - "12 unit tests for correlation engine"
affects: [phase-04-annual-report, health-heartbeat, health-operations]

# Tech tracking
tech-stack:
  added: [scipy>=1.11]
  patterns: [scipy-stats-dual-correlation, chinese-nl-insight-generation, tdd-red-green]

key-files:
  created:
    - tests/test_correlation_engine.py
    - skills/health-correlation-analyzer/SKILL.md
    - scripts/analyze_health_correlations.py
  modified:
    - skills/_shared/correlation_engine.py
    - pyproject.toml

key-decisions:
  - "scipy added to viz extras (not separate analysis extra) since correlation is visualization-adjacent"
  - "matplotlib minimum lowered from >=3.10 to >=3.8 to match installed version"
  - "Best-method auto-selection: compute both Pearson and Spearman, pick the one with lower p-value"
  - "DEFAULT_PAIRS updated to use health-concepts.yaml canonical field names (total_min instead of score)"

patterns-established:
  - "Dual correlation method: compute both Pearson+Spearman, select more significant"
  - "Chinese NL insight template with strength/direction labels"
  - "n>=14 minimum sample size enforcement for statistical rigor"

requirements-completed: [CORR-01, CORR-02, CORR-03]

# Metrics
duration: 6min
completed: 2026-03-26
---

# Phase 03 Plan 02: Correlation Analysis Summary

**Enhanced correlation engine with scipy Pearson+Spearman p-values, n>=14 minimum, Chinese NL insights, and CLI/SKILL.md entry points**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-26T10:51:17Z
- **Completed:** 2026-03-26T10:57:15Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- CorrelationEngine now computes both Pearson and Spearman correlations via scipy.stats, automatically selecting the more significant method
- Minimum sample size raised from n>=3 to n>=14, eliminating spurious small-sample correlations
- Chinese natural language insights generated for all results (significant and non-significant)
- User-invocable health-correlation-analyzer SKILL.md and CLI script with markdown/JSON output

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Add failing tests** - `74db248` (test)
2. **Task 1 (GREEN): Enhance correlation engine** - `5d06daf` (feat)
3. **Task 2: SKILL.md and CLI script** - `a2afab3` (feat)

_TDD task had RED (failing tests) and GREEN (implementation) commits._

## Files Created/Modified
- `skills/_shared/correlation_engine.py` - Enhanced with scipy stats, p-values, Spearman, NL insights, person_id
- `tests/test_correlation_engine.py` - 12 comprehensive unit tests
- `skills/health-correlation-analyzer/SKILL.md` - User-invocable skill definition with Chinese documentation
- `scripts/analyze_health_correlations.py` - CLI entry point with argparse, markdown/JSON output
- `pyproject.toml` - Added scipy>=1.11 to viz extras, lowered matplotlib to >=3.8

## Decisions Made
- scipy added to existing `viz` extras group rather than creating a separate `analysis` extra, since correlation analysis is closely coupled with visualization
- matplotlib minimum lowered from >=3.10 to >=3.8 to match the actually installed and tested version (3.8.2)
- Dual correlation approach: compute both Pearson (linear) and Spearman (rank), automatically select the method with lower p-value for reporting
- DEFAULT_PAIRS updated from old field names (e.g., sleep "score") to health-concepts.yaml canonical names (e.g., sleep "total_min")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. scipy is already installed (1.11.4).

## Known Stubs
None - all functionality fully wired.

## Next Phase Readiness
- Correlation engine ready for use by Phase 4 annual health report
- SKILL.md can be invoked by health-chief-of-staff for user requests
- CLI script functional for batch analysis

---
*Phase: 03-visualization-correlation-analysis*
*Completed: 2026-03-26*
