---
phase: 02-data-ingestion
plan: 02
subsystem: data-ingestion
tags: [google-fit, csv, tcx, fuzzy-dedup, importer, health-data]

# Dependency graph
requires:
  - phase: 01-engineering-foundation
    provides: "HealthDataStore with person_id, package imports, pyproject.toml"
provides:
  - "HealthImporterBase shared base class for all device importers"
  - "GoogleFitImporter for Takeout ZIP (CSV + TCX) import"
  - "CLI script import_google_fit_export.py"
  - "google-fit-import SKILL.md for AI-invocable import"
affects: [02-03-huawei-xiaomi-import, future-device-importers]

# Tech tracking
tech-stack:
  added: []
  patterns: ["HealthImporterBase inheritance for device importers", "fuzzy dedup (60s/5%)", "defensive CSV column discovery"]

key-files:
  created:
    - skills/_shared/health_importer_base.py
    - skills/_shared/google_fit_importer.py
    - scripts/import_google_fit_export.py
    - skills/google-fit-import/SKILL.md
    - tests/test_health_importer_base.py
    - tests/test_google_fit_import.py
  modified: []

key-decisions:
  - "GoogleFitImporter placed in skills/_shared/ as a separate module rather than embedded in CLI script -- enables reuse and testing"
  - "CSV column names discovered defensively from headers, not hardcoded -- handles Google Fit format variations"
  - "CLI script uses package-style import (skills._shared.google_fit_importer) to work with relative imports in _shared"

patterns-established:
  - "HealthImporterBase: subclass pattern with _discover_files and _parse_records hooks"
  - "Fuzzy dedup: 60s timestamp window + 5% value tolerance, pre-filtered by type and day range"
  - "Type-to-skill mapping: canonical record types map to skill data directories"

requirements-completed: [IMPT-04, IMPT-05, IMPT-01]

# Metrics
duration: 6min
completed: 2026-03-26
---

# Phase 02 Plan 02: Google Fit Import Summary

**HealthImporterBase with fuzzy dedup (60s/5%) and GoogleFitImporter parsing Takeout CSV + TCX into HealthDataStore JSONL**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-26T10:05:25Z
- **Completed:** 2026-03-26T10:11:53Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- HealthImporterBase established as the reusable base class that Huawei and Xiaomi importers will inherit
- Google Fit importer handles CSV (heart rate, daily activity, sleep) and TCX (activities) from Takeout ZIP
- Fuzzy dedup prevents duplicate records across devices with 60s timestamp window and 5% value tolerance
- All 21 tests pass (14 base class + 7 Google Fit)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create HealthImporterBase with fuzzy dedup and tests**
   - `0e32ea9` (test: add failing tests for HealthImporterBase)
   - `afb2a6d` (feat: implement HealthImporterBase with fuzzy dedup)
2. **Task 2: Create Google Fit importer + CLI script + SKILL.md**
   - `925f590` (test: add failing tests for GoogleFitImporter)
   - `12bba2b` (feat: implement Google Fit importer with CLI and SKILL.md)

_Note: TDD tasks have multiple commits (test -> feat)_

## Files Created/Modified
- `skills/_shared/health_importer_base.py` - Base class with ZIP extraction, fuzzy dedup, record mapping, person_id passthrough
- `skills/_shared/google_fit_importer.py` - Google Fit CSV + TCX parser inheriting HealthImporterBase
- `scripts/import_google_fit_export.py` - CLI entry point with argparse (--person-id, --start-date, --end-date, --format)
- `skills/google-fit-import/SKILL.md` - AI-invocable skill with usage instructions
- `tests/test_health_importer_base.py` - 14 tests covering fuzzy dedup, ZIP extraction, store records, orchestration
- `tests/test_google_fit_import.py` - 7 tests covering file discovery, CSV/TCX parsing, full import flow

## Decisions Made
- GoogleFitImporter placed in `skills/_shared/` as a separate module for reuse and testability
- CSV column names discovered defensively from headers (not hardcoded indices) per Claude's discretion
- CLI uses package-style import (`skills._shared.google_fit_importer`) instead of sys.path + bare import to work with relative imports in _shared

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed import path for CLI script**
- **Found during:** Task 2 (CLI script verification)
- **Issue:** CLI script used `sys.path.insert(0, SHARED_DIR)` + `from google_fit_importer import GoogleFitImporter` which fails because google_fit_importer.py uses relative imports (`from .health_importer_base import ...`)
- **Fix:** Changed to `sys.path.insert(0, ROOT)` + `from skills._shared.google_fit_importer import GoogleFitImporter` (package-style import)
- **Files modified:** scripts/import_google_fit_export.py
- **Verification:** `python scripts/import_google_fit_export.py --help` exits 0
- **Committed in:** 12bba2b (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Import path fix necessary for CLI to work. No scope creep.

## Issues Encountered
None beyond the import path fix documented above.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all data paths are fully wired.

## Next Phase Readiness
- HealthImporterBase is ready for Huawei and Xiaomi importers to inherit
- Pattern established: subclass only needs to implement `_discover_files` and `_parse_records`
- Fuzzy dedup works across devices (tested with synthetic data)

---
*Phase: 02-data-ingestion*
*Completed: 2026-03-26*

## Self-Check: PASSED

All 7 files verified present. All 4 commits verified in git log.
