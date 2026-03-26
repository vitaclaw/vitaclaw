# Phase 1: Foundation + Multi-Person Architecture - Research

**Researched:** 2026-03-26
**Domain:** Python packaging, CI/CD, linting, data layer refactoring (person_id threading)
**Confidence:** HIGH

## Summary

Phase 1 combines two tightly coupled concerns: (1) engineering hardening (pyproject.toml, CI, ruff, sys.path cleanup) and (2) threading a `person_id` abstraction through the entire data layer (HealthDataStore, HealthMemoryWriter, CrossSkillReader). These must land together because the packaging work makes the data layer importable cleanly, and the person_id threading is a cross-cutting change that every subsequent feature phase depends on.

The codebase currently has 35 Python modules in `skills/_shared/` with no `__init__.py`, no `pyproject.toml`, and 30 `sys.path.insert` hacks across 25 test files. The data layer (HealthDataStore, HealthMemoryWriter, CrossSkillReader) has no concept of person identity -- all records are implicitly single-user. FamilyManager exists but is isolated from the data flow.

**Primary recommendation:** Build in strict order: (1) pyproject.toml + package structure, (2) ruff configuration + fix lint errors, (3) sys.path cleanup in tests, (4) CI pipeline, (5) person_id threading through HealthDataStore, (6) person_id threading through HealthMemoryWriter, (7) person_id threading through CrossSkillReader, (8) schema update + integration tests.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Person identifiers use a flexible slug scheme: `self` (default, for the primary user), plus user-defined slugs for family members (e.g., `mom`, `dad`, `child-1`, `wife`). Slugs are kebab-case, max 32 chars, unique within the workspace. The slug is stored as `person_id` field in JSONL records.
- **D-02:** Person resolution from natural language is handled at the AI prompt layer (SKILL.md), not in Python code. When a user says "record blood pressure for mom", the skill prompt extracts the person reference and passes `person_id=mom` to the Python runtime. No explicit "switch person" command needed.
- **D-03:** `FamilyManager` (already exists in `skills/_shared/family_manager.py`) is the registry of known persons. It stores person profiles (name, relationship, demographics) in `memory/health/_family.yaml`. HealthDataStore and HealthMemoryWriter read person_id from function arguments, not from FamilyManager directly -- FamilyManager is for profile management, not data routing.
- **D-04:** Single JSONL file per skill with `person_id` field (not per-person directories). Records without `person_id` default to `"self"`. Query methods on HealthDataStore accept optional `person_id` filter parameter.
- **D-05:** Memory files remain under `memory/health/` with per-person subdirectories where needed: `memory/health/items/{person_id}/blood-pressure.md`. The `self` person uses the existing flat structure for backward compatibility (`memory/health/items/blood-pressure.md`).
- **D-06:** Migration happens automatically on first access after upgrade. When HealthDataStore reads a JSONL file and finds records without `person_id`, it treats them as `person_id=self`. No rewrite of existing files -- the absence of `person_id` field IS the "self" marker. Zero-cost migration.
- **D-07:** Memory files under `memory/health/items/` stay in their current location (implicitly belonging to "self"). New family member items go to `memory/health/items/{person_id}/`. This avoids touching any existing files.
- **D-08:** Create `pyproject.toml` with setuptools backend. Core dependencies: `requests`, `PyYAML`. Optional extras: `[viz]` (matplotlib, pandas), `[ocr]` (paddleocr, paddlepaddle), `[oncology]` (numpy, pandas), `[dev]` (pytest, ruff). Python requires `>=3.11`.
- **D-09:** Remove all `sys.path.insert` hacks from tests and scripts. Make `skills/_shared/` importable as `vitaclaw.shared` package (or similar). Add `__init__.py` files as needed.
- **D-10:** CI via GitHub Actions: run `pytest tests/` and `ruff check` on push. Fail on lint errors. No pre-commit hooks (keep simple).
- **D-11:** ruff configured in `pyproject.toml` with sensible defaults (line-length 120, select standard rules).

### Claude's Discretion
- Test framework: keep existing `unittest.TestCase` tests, add pytest as runner. No mass migration of test style -- new tests can use either.
- CI additional checks: manifest validation and skill frontmatter check are nice-to-haves, Claude can include if straightforward.
- Package naming and import paths: Claude decides the best structure for making `skills/_shared/` importable.

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENG-01 | Project has pyproject.toml with core dependencies and optional extras per skill group | Standard Stack section: pyproject.toml skeleton with verified versions |
| ENG-02 | All shared modules can be imported via standard `import` without sys.path hacks | Architecture Patterns: package structure with `__init__.py` files |
| ENG-03 | CI pipeline runs pytest on push and reports test results | Architecture Patterns: GitHub Actions workflow |
| ENG-04 | ruff linter configured and passing on all shared modules | Standard Stack: ruff 0.15.x configuration in pyproject.toml |
| ENG-05 | Data migration tool can detect format version and migrate existing health data forward | Architecture Patterns: zero-cost migration via absent person_id = "self" |
| FAM-01 | User can create and switch between family member profiles | Code Examples: FamilyManager already supports add_member/get_member |
| FAM-02 | Each person's health data is isolated in per-person data directories | Architecture Patterns: person_id field filtering in HealthDataStore |
| FAM-03 | Existing single-user data auto-migrates to "self" profile without data loss | Architecture Patterns: D-06 zero-cost migration, no file rewriting |
| FAM-04 | All skills (tracking, OCR, import, visualization) work in per-person context | Architecture Patterns: person_id parameter threaded through data layer |
| FAM-05 | person_id field is threaded through HealthDataStore, HealthMemoryWriter, and CrossSkillReader | Code Examples: exact API changes for each module |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| setuptools | >=75.0 (latest 82.0.1) | Build backend for pyproject.toml | Most widely adopted Python build backend. Project is a skill library, not a PyPI package -- setuptools is simplest. |
| pytest | >=8.0 (latest 9.0.2) | Test runner | Runs existing unittest.TestCase tests without modification. Adds fixtures, parametrize. 52%+ Python developer adoption. |
| ruff | >=0.9 (latest 0.15.7) | Linting + formatting | Replaces flake8+isort+black. 10-100x faster (Rust-based). Single config in pyproject.toml. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | >=2.31 | HTTP client | Core dependency, already used throughout |
| PyYAML | >=6.0 | YAML parsing | Core dependency, used by FamilyManager, ConceptResolver |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| setuptools | Poetry | Adds complexity (poetry.lock, venv management) for a non-PyPI library |
| setuptools | Hatch | Less ecosystem adoption, no compelling advantage here |
| ruff | flake8+black+isort | Three tools doing what one does, 100x slower |

**Installation:**
```bash
pip install -e ".[dev]"
```

**Version verification:** All versions verified via `pip3 index versions` on 2026-03-26:
- setuptools: 82.0.1 (specify >=75.0)
- pytest: 9.0.2 (specify >=8.0)
- ruff: 0.15.7 (specify >=0.9)

## Architecture Patterns

### Recommended Package Structure

```
vitaclaw-main/
├── pyproject.toml                    # NEW: build config, deps, tool config
├── skills/
│   ├── __init__.py                   # NEW: empty, makes skills a package
│   └── _shared/
│       ├── __init__.py               # NEW: empty, makes _shared importable
│       ├── health_data_store.py      # MODIFIED: add person_id parameter
│       ├── health_memory.py          # MODIFIED: per-person memory paths
│       ├── cross_skill_reader.py     # MODIFIED: person_id filter
│       ├── family_manager.py         # EXISTS: person registry
│       └── ... (32 other modules)
├── scripts/                          # Unchanged
├── tests/
│   ├── __init__.py                   # NEW: makes tests a package
│   ├── conftest.py                   # NEW: shared fixtures
│   └── test_*.py                     # MODIFIED: remove sys.path.insert
├── schemas/
│   └── health-data-record.schema.json # MODIFIED: add person_id field
└── .github/
    └── workflows/
        └── ci.yml                    # NEW: GitHub Actions CI
```

### Pattern 1: Package Discovery via pyproject.toml

**What:** Use setuptools `packages.find` with `where` to discover `skills._shared` as an importable package. Install in editable mode (`pip install -e .`) so that `from skills._shared.health_data_store import HealthDataStore` works everywhere.

**When to use:** All imports of shared modules -- in tests, scripts, and other shared modules.

**Configuration:**
```toml
[tool.setuptools.packages.find]
include = ["skills*"]
```

**Import transformation:**
```python
# BEFORE (in tests):
ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
from health_data_store import HealthDataStore  # noqa: E402

# AFTER (in tests):
from skills._shared.health_data_store import HealthDataStore
```

**CRITICAL DETAIL:** The shared modules currently import each other with bare module names (e.g., `from health_data_store import HealthDataStore` inside `cross_skill_reader.py`). These internal imports MUST also be updated to use the package path (`from skills._shared.health_data_store import HealthDataStore`) or relative imports (`from .health_data_store import HealthDataStore`).

**Recommendation:** Use relative imports within `skills/_shared/` (shorter, no coupling to package name) and absolute imports from tests/scripts.

### Pattern 2: person_id as Optional Parameter (Backward Compatible)

**What:** Add `person_id: str | None = None` to HealthDataStore.append(), HealthDataStore.query(), CrossSkillReader.read(), and HealthMemoryWriter constructor. When None or "self", use existing paths/behavior.

**When to use:** Every data-accessing call.

**Key rules:**
1. `person_id=None` and `person_id="self"` are equivalent -- both mean the default user
2. Records without `person_id` field in JSONL are treated as belonging to "self"
3. Query with `person_id=None` returns ALL records (no filter) for backward compatibility
4. Query with `person_id="self"` returns records where person_id is absent OR "self"
5. Query with `person_id="mom"` returns ONLY records with person_id="mom"

### Pattern 3: Memory Path Resolution for person_id

**What:** HealthMemoryWriter resolves item paths based on person_id.

```python
# self (or None): memory/health/items/blood-pressure.md  (backward compat)
# "mom":          memory/health/items/mom/blood-pressure.md
# "dad":          memory/health/items/dad/blood-pressure.md
```

**Critical:** The `self` person MUST continue using the existing flat path structure. Only non-self persons get subdirectories. This is the zero-cost migration strategy from D-05/D-07.

### Pattern 4: Schema Extension (not Replacement)

**What:** Add `person_id` as an optional field to `health-data-record.schema.json`. The field is NOT required -- existing records without it are valid.

```json
"person_id": {
  "type": "string",
  "pattern": "^[a-z0-9][a-z0-9-]*$",
  "maxLength": 32,
  "description": "Person slug. Absent or 'self' means the primary user."
}
```

### Anti-Patterns to Avoid

- **Separate JSONL files per person:** D-04 explicitly forbids this. Single file with person_id field, filter in code.
- **Making person_id required in schema:** Breaks all existing data. The field MUST be optional.
- **Using FamilyManager for data routing:** D-03 says FamilyManager is for profile management. HealthDataStore reads person_id from function arguments.
- **Rewriting existing JSONL files to add person_id:** D-06 says absence of field IS the "self" marker. Zero-cost migration.
- **Moving existing memory files to `items/self/`:** D-07 says existing files stay in place.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python packaging | Custom import machinery | pyproject.toml + setuptools | Standard, well-documented, handles edge cases |
| Linting | Custom style checks | ruff | 500+ rules, auto-fix, Rust-speed |
| CI pipeline | Shell scripts for testing | GitHub Actions | Industry standard, free for public repos |
| Test runner | Custom test harness | pytest | Discovers and runs unittest.TestCase tests natively |

## Common Pitfalls

### Pitfall 1: Internal Import Breakage During sys.path Cleanup

**What goes wrong:** After adding `__init__.py` and switching tests to `from skills._shared.X import Y`, the shared modules themselves still use bare `from health_data_store import HealthDataStore`. This works in tests (because `skills/_shared/` is no longer on sys.path) only if relative imports are used within the package.

**Why it happens:** There are 17 internal cross-imports between shared modules (grep found them above). If you update tests but not internal imports, everything breaks.

**How to avoid:** Update internal imports FIRST (to relative imports within `_shared/`), then update test imports, then remove sys.path hacks.

**Warning signs:** ImportError on any shared module after removing sys.path.insert.

### Pitfall 2: person_id Query Semantics Ambiguity

**What goes wrong:** Code passes `person_id=None` expecting "all records" but gets only "self" records, or vice versa.

**Why it happens:** The semantics of None vs "self" vs absent are subtly different (see Pattern 2 above). Without clear convention, callers make wrong assumptions.

**How to avoid:** Document and test these three cases explicitly:
- `person_id=None` -> no filter (all persons) -- for backward compat with existing callers
- `person_id="self"` -> records with absent or "self" person_id
- `person_id="mom"` -> records with exactly "mom"

### Pitfall 3: HealthMemoryWriter Path Construction Scattered

**What goes wrong:** HealthMemoryWriter (1,814 lines) constructs paths to daily/, items/, weekly/, monthly/, files/ directories in many places. Adding person_id awareness requires modifying every path construction site.

**Why it happens:** The current code builds paths like `self.items_dir / f"{item_name}.md"` in dozens of methods. Each needs person_id-aware path logic.

**How to avoid:** Centralize path resolution into a single method (e.g., `_resolve_item_path(item_name, person_id)`) and route ALL path construction through it. Do NOT add person_id logic to each individual method.

### Pitfall 4: ruff Lint Errors Cascade

**What goes wrong:** Running `ruff check` for the first time on 35 modules produces hundreds of errors. Fixing them all at once creates a massive diff that's hard to review and may introduce bugs.

**Why it happens:** The codebase has never had a linter. Common issues: unused imports, f-string without placeholders, bare except, comparison to None with ==.

**How to avoid:** Start with a narrow rule set (E, F only), fix those, then expand to I (isort) and UP (pyupgrade). Use `ruff check --fix` for auto-fixable issues. Run tests after each batch of fixes.

### Pitfall 5: Dedup Logic Ignores person_id

**What goes wrong:** HealthDataStore.append() dedup check (line 183-195) compares `(type, timestamp, data_hash)` but not person_id. Two different people recording the same blood pressure at the same time would be falsely deduplicated.

**Why it happens:** Dedup was designed for single-user. Adding person_id to the record but not updating the dedup check creates a subtle data loss bug.

**How to avoid:** Include person_id in the dedup key: `(type, timestamp, data_hash, person_id)`.

### Pitfall 6: conftest.py Must Handle Both Import Styles During Transition

**What goes wrong:** During the transition, some tests may still use old sys.path imports while new tests use package imports. If both styles coexist, Python may import the same module twice under different names, causing `isinstance()` checks to fail.

**How to avoid:** Do the migration atomically -- update ALL tests in a single pass. Add a `conftest.py` at the tests root that ensures correct import paths. Run the full test suite after migration.

## Code Examples

### pyproject.toml (Complete)

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "vitaclaw"
version = "2.0.0"
description = "Modular health AI skill library for OpenClaw"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
viz = [
    "matplotlib>=3.10",
    "pandas>=2.2.3",
]
ocr = [
    "paddleocr>=3.4.0",
    "paddlepaddle>=3.0",
]
oncology = [
    "numpy>=1.26",
    "pandas>=2.2.3",
]
dev = [
    "pytest>=8.0",
    "ruff>=0.9",
]

[tool.setuptools.packages.find]
include = ["skills*"]

[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### HealthDataStore person_id Changes

```python
# Source: Derived from existing health_data_store.py (lines 81-240)

class HealthDataStore:
    def __init__(self, skill_name: str, data_dir: str | None = None):
        # ... existing init unchanged ...
        pass

    def append(
        self,
        record_type: str,
        data: dict,
        note: str = "",
        timestamp=None,
        meta: dict | None = None,
        sign: bool = False,
        person_id: str | None = None,  # NEW
    ) -> dict:
        # ... existing validation ...

        # Normalize person_id
        effective_pid = person_id if person_id and person_id != "self" else None

        # Dedup must include person_id
        for existing in self._iter_records():
            existing_pid = existing.get("person_id")
            if (
                existing.get("type") == record_type
                and existing.get("timestamp") == timestamp
                and existing_pid == effective_pid  # NEW: include in dedup
                and data_hash_matches(existing, data)
            ):
                return existing

        record = {
            "id": "...",
            "type": record_type,
            "timestamp": timestamp,
            "skill": self.skill_name,
            "note": note,
            "data": data,
        }

        # Only add person_id to record if not "self"
        if effective_pid:
            record["person_id"] = person_id

        # ... rest of append logic ...
        return record

    def query(
        self,
        record_type: str | None = None,
        start=None,
        end=None,
        person_id: str | None = None,  # NEW
    ) -> list[dict]:
        # ... existing filter logic ...
        result = []
        for record in self._read_all_records():
            # ... existing type/date filters ...

            # NEW: person_id filter
            if person_id is not None:
                record_pid = record.get("person_id")
                if person_id == "self":
                    # "self" matches records with no person_id or person_id="self"
                    if record_pid is not None and record_pid != "self":
                        continue
                else:
                    if record_pid != person_id:
                        continue

            result.append(record)
        return result
```

### HealthMemoryWriter person_id Changes

```python
# Source: Derived from existing health_memory.py (lines 78-100)

class HealthMemoryWriter:
    def __init__(
        self,
        workspace_root: str | None = None,
        memory_root: str | None = None,
        now_fn=None,
        person_id: str | None = None,  # NEW
    ):
        self._person_id = person_id
        # ... existing init ...
        self.base_dir = _resolve_memory_root(workspace_root=workspace_root, memory_root=memory_root)
        # ... existing dir setup ...

    def _resolve_items_path(self, item_name: str) -> Path:
        """Resolve item file path, scoped by person_id."""
        if self._person_id and self._person_id != "self":
            return self.items_dir / self._person_id / f"{item_name}.md"
        return self.items_dir / f"{item_name}.md"
```

### CrossSkillReader person_id Changes

```python
# Source: Derived from existing cross_skill_reader.py (lines 48-80)

class CrossSkillReader:
    def read(self, concept: str, start=None, end=None, person_id: str | None = None) -> list[dict]:
        # ... existing concept resolution ...
        merged: list[dict] = []
        for producer in producers:
            skill = producer.get("skill", "")
            record_type = producer.get("record_type", "")
            if skill and record_type:
                records = self._store(skill).query(
                    record_type, start=start, end=end,
                    person_id=person_id,  # NEW: pass through
                )
                merged.extend(records)
        merged.sort(key=lambda r: r.get("timestamp", ""))
        return merged
```

### GitHub Actions CI Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest tests/ -v
```

### Internal Import Migration (within skills/_shared/)

```python
# BEFORE (cross_skill_reader.py):
from health_data_store import HealthDataStore

# AFTER (cross_skill_reader.py):
from .health_data_store import HealthDataStore
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| setup.py + requirements.txt | pyproject.toml (PEP 621) | 2022 (PEP 621 standardized) | Single config file for build, deps, tools |
| flake8 + black + isort | ruff | 2023+ | Single tool, 100x faster |
| unittest only | pytest as runner + unittest compat | Long-standing | pytest runs unittest tests natively |
| sys.path manipulation | editable install (`pip install -e .`) | Standard practice | Clean imports, IDE support |

## Open Questions

1. **Package name for skills._shared imports**
   - What we know: D-09 says "Make skills/_shared/ importable as vitaclaw.shared package (or similar)"
   - What's unclear: Whether to use `skills._shared` (matching filesystem) or create an alias like `vitaclaw.shared`
   - Recommendation: Use `skills._shared` directly (matches filesystem, no indirection). The underscore prefix is fine for a package name. Simpler than creating an alias mapping.

2. **Should person_id=None return all records or raise?**
   - What we know: D-04 says query methods accept "optional person_id filter parameter"
   - What's unclear: Whether existing callers that pass no person_id expect to see all records
   - Recommendation: person_id=None means no filter (backward compat). person_id="self" means self-only. This preserves existing behavior.

3. **How to handle ruff errors in non-shared modules (scripts/, skills/\*/)**
   - What we know: D-04 says "ruff linter configured and passing on all shared modules"
   - What's unclear: Whether to enforce ruff on the entire repo or just skills/_shared/
   - Recommendation: Configure ruff for the entire repo but start by only fixing `skills/_shared/` and `tests/`. Use `extend-exclude` for other directories initially.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Everything | Yes | 3.11.4 | -- |
| pip | Package install | Yes | 23.2.1 | -- |
| pytest | Testing (installed) | Yes | 7.4.4 (needs upgrade to >=8.0) | Install via pip |
| setuptools | Build backend (installed) | Yes | 68.0.0 (needs upgrade to >=75.0) | Install via pip |
| ruff | Linting | No | -- | Install via pip |
| GitHub Actions | CI | N/A (cloud) | -- | -- |

**Missing dependencies with no fallback:**
- None -- all dependencies are pip-installable

**Missing dependencies with fallback:**
- ruff: not installed locally, install via `pip install ruff>=0.9`
- pytest needs upgrade from 7.4.4 to >=8.0 (will happen via `pip install -e ".[dev]"`)
- setuptools needs upgrade from 68.0.0 to >=75.0

## Project Constraints (from CLAUDE.md)

Extracted from CLAUDE.md:

- **Local-first:** All data must be stored on local filesystem, no cloud services
- **Skill format:** New capabilities as SKILL.md + optional Python
- **Privacy boundary:** Health data must not leave local without user consent
- **Backward compatible:** Iteration 1 data formats must migrate smoothly
- **Python only:** No new languages
- **GSD workflow:** Use GSD commands for code changes, not direct edits
- **Naming conventions:** snake_case for modules, kebab-case for directories, PascalCase for classes
- **`from __future__ import annotations`** at top of every module
- **Modern union syntax:** `str | None` not `Optional[str]`
- **4-space indentation**, line length ~120 chars
- **Bilingual:** Code identifiers in English, user-facing health content in Chinese

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `health_data_store.py` (350 lines), `health_memory.py` (1814 lines), `cross_skill_reader.py`, `family_manager.py` -- direct source inspection
- `schemas/health-data-record.schema.json` -- existing schema, verified structure
- 25 test files with 30 sys.path.insert occurrences -- verified via grep
- 35 shared modules in `skills/_shared/` -- verified via ls
- 17 internal cross-imports between shared modules -- verified via grep

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` -- pyproject.toml skeleton and version recommendations (pre-researched)
- `.planning/research/PITFALLS.md` -- person_id threading pitfalls (pre-researched)
- `.planning/research/ARCHITECTURE.md` -- data flow patterns (pre-researched)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all versions verified via pip index, tools are industry standard
- Architecture: HIGH - based on direct codebase inspection and locked user decisions
- Pitfalls: HIGH - identified from actual code patterns (17 cross-imports, dedup logic, 1814-line memory writer)

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain, no fast-moving dependencies)
