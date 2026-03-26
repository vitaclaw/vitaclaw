# Phase 1: Foundation + Multi-Person Architecture - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Engineering hardening (pyproject.toml, CI, ruff, sys.path cleanup, data migration) and threading person_id through the entire data layer (HealthDataStore, HealthMemoryWriter, CrossSkillReader) so every subsequent feature gets multi-person support for free.

</domain>

<decisions>
## Implementation Decisions

### Person Identity Model
- **D-01:** Person identifiers use a flexible slug scheme: `self` (default, for the primary user), plus user-defined slugs for family members (e.g., `mom`, `dad`, `child-1`, `wife`). Slugs are kebab-case, max 32 chars, unique within the workspace. The slug is stored as `person_id` field in JSONL records.
- **D-02:** Person resolution from natural language is handled at the AI prompt layer (SKILL.md), not in Python code. When a user says "record blood pressure for mom", the skill prompt extracts the person reference and passes `person_id=mom` to the Python runtime. No explicit "switch person" command needed.
- **D-03:** `FamilyManager` (already exists in `skills/_shared/family_manager.py`) is the registry of known persons. It stores person profiles (name, relationship, demographics) in `memory/health/_family.yaml`. HealthDataStore and HealthMemoryWriter read person_id from function arguments, not from FamilyManager directly — FamilyManager is for profile management, not data routing.

### Data Isolation Strategy
- **D-04:** Single JSONL file per skill with `person_id` field (not per-person directories). Records without `person_id` default to `"self"`. Query methods on HealthDataStore accept optional `person_id` filter parameter.
- **D-05:** Memory files remain under `memory/health/` with per-person subdirectories where needed: `memory/health/items/{person_id}/blood-pressure.md`. The `self` person uses the existing flat structure for backward compatibility (`memory/health/items/blood-pressure.md`).

### Data Migration
- **D-06:** Migration happens automatically on first access after upgrade. When HealthDataStore reads a JSONL file and finds records without `person_id`, it treats them as `person_id=self`. No rewrite of existing files — the absence of `person_id` field IS the "self" marker. Zero-cost migration.
- **D-07:** Memory files under `memory/health/items/` stay in their current location (implicitly belonging to "self"). New family member items go to `memory/health/items/{person_id}/`. This avoids touching any existing files.

### Engineering Foundation
- **D-08:** Create `pyproject.toml` with setuptools backend. Core dependencies: `requests`, `PyYAML`. Optional extras: `[viz]` (matplotlib, pandas), `[ocr]` (paddleocr, paddlepaddle), `[oncology]` (numpy, pandas), `[dev]` (pytest, ruff). Python requires `>=3.11`.
- **D-09:** Remove all `sys.path.insert` hacks from tests and scripts. Make `skills/_shared/` importable as `vitaclaw.shared` package (or similar). Add `__init__.py` files as needed.
- **D-10:** CI via GitHub Actions: run `pytest tests/` and `ruff check` on push. Fail on lint errors. No pre-commit hooks (keep simple).
- **D-11:** ruff configured in `pyproject.toml` with sensible defaults (line-length 120, select standard rules).

### Claude's Discretion
- Test framework: keep existing `unittest.TestCase` tests, add pytest as runner. No mass migration of test style — new tests can use either.
- CI additional checks: manifest validation and skill frontmatter check are nice-to-haves, Claude can include if straightforward.
- Package naming and import paths: Claude decides the best structure for making `skills/_shared/` importable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Data Layer
- `skills/_shared/health_data_store.py` — JSONL storage engine, must be modified to accept person_id
- `skills/_shared/health_memory.py` — Memory writer, must support per-person item paths
- `skills/_shared/cross_skill_reader.py` — Cross-skill data aggregation, must filter by person_id

### Family Management
- `skills/_shared/family_manager.py` — Existing FamilyManager class, registry of known persons
- `skills/_shared/twin_identity.py` — Digital twin identity, may need person_id awareness

### Research
- `.planning/research/ARCHITECTURE.md` — Component integration patterns and build order
- `.planning/research/PITFALLS.md` — Known pitfalls for person_id threading and migration
- `.planning/research/STACK.md` — Recommended tooling versions

### Existing Tests
- `tests/` — 25 test files with 30 sys.path.insert hacks to be cleaned up

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FamilyManager` (`skills/_shared/family_manager.py`): Already has person profile management, config loading, data directory resolution. Needs connection to data layer, not rewrite.
- `HealthDataStore._resolve_data_root()`: Already accepts `data_dir` parameter — can be extended with `person_id` parameter.
- `health-data-record.schema.json`: Existing record schema, needs `person_id` field added.

### Established Patterns
- All shared modules use `_repo_root() -> Path` helper for path resolution
- JSONL append with `fcntl` file locking in `HealthDataStore`
- Optional dependency pattern: `try: import X; HAS_X = True / except: HAS_X = False`
- CLI scripts use `argparse` with `--format markdown|json`

### Integration Points
- `HealthDataStore.__init__(skill_name, data_dir)` — add optional `person_id` parameter
- `HealthMemoryWriter` path construction — add person_id awareness for items/ subdirectories
- `CrossSkillReader.read()` — add person_id filter
- Every test file's `sys.path.insert` block — replace with standard import after packaging

</code_context>

<specifics>
## Specific Ideas

- Migration is zero-cost: absence of `person_id` field equals "self", no file rewriting needed
- Natural language person resolution stays in skill prompts, not Python code — keeps runtime simple
- Existing `memory/health/items/*.md` files stay in place (belong to "self"), new persons get subdirectories

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-multi-person-architecture*
*Context gathered: 2026-03-26*
