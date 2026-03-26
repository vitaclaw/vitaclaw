# Testing Patterns

**Analysis Date:** 2026-03-26

## Test Framework

**Runner:**
- `unittest` (stdlib) -- primary framework for `tests/` directory
- `pytest` -- used in skill-level tests (`skills/gwas-prs/tests/`, `skills/nutrigx_advisor/tests/`, `skills/gwas-lookup/tests/`)
- No `pytest.ini`, `conftest.py`, or `pyproject.toml` with pytest config detected

**Assertion Library:**
- `unittest.TestCase` assertions: `self.assertEqual`, `self.assertTrue`, `self.assertIn`, `self.assertIsNotNone`, `self.assertGreaterEqual`
- `pytest` plain `assert` in skill-level tests

**Run Commands:**
```bash
python -m pytest tests/ -v              # Run all core tests
python -m unittest tests/test_health_shared.py   # Run single test file
python -m pytest skills/gwas-prs/tests/ -v       # Run skill-specific tests
python -m pytest skills/nutrigx_advisor/tests/test_nutrigx.py -v  # Individual skill test
```

## Test File Organization

**Location:**
- Core tests: `tests/` directory at project root (centralized)
- Skill-specific tests: `skills/<skill-name>/tests/` (co-located with skill)
- Some skills have test files at skill root: `skills/tooluniverse-*/test_*.py`

**Naming:**
- `test_<feature>.py` for all test files
- Test classes: `<Feature>Test(unittest.TestCase)` in core tests
- Pytest-style classes: `class Test<Feature>:` in skill tests (no TestCase inheritance)
- Pytest-style functions: `def test_<behavior>():` at module level in skill tests

**Structure:**
```
tests/
    fixtures/
        health_memory_golden/       # Golden files for snapshot testing
    test_health_shared.py           # 1692 lines -- largest test file, covers all shared modules
    test_health_heartbeat.py        # Proactive health check tests
    test_flagship_scenarios.py      # Integration tests for productized workflows
    test_health_operations.py       # Automated operations runner tests
    test_health_memory_golden.py    # Golden/snapshot tests for markdown output
    test_health_team_runtime.py     # Multi-agent orchestration tests
    test_iteration3_safety_contracts.py  # Safety and anti-hallucination tests
    test_skill_governance.py        # Governance metadata validation
    test_smoke_test_skills.py       # Smoke test command map tests
    test_release_builder.py         # Package building tests
    test_readme_render.py           # README rendering tests
    test_init_health_workspace.py   # Workspace initialization tests
    test_apple_health_bridge.py     # Apple Health import tests
    test_doctor_matching.py         # Doctor matching workflow tests
    test_annual_checkup_memory.py
    test_diabetes_workflow.py
    test_hypertension_workflow.py
    test_health_visit_workflow.py
    test_health_timeline_builder.py
    test_health_reminder_center.py
    test_health_memory_distiller.py
    test_iteration2_active_service.py
    test_monthly_digest_fallback.py
    test_weekly_digest_fallback.py
    test_patient_archive_bridge.py
    test_medical_record_organizer_privacy.py

skills/gwas-prs/tests/
    fixtures/                       # JSON mock API responses
    test_gwas_prs.py                # pytest-based

skills/nutrigx_advisor/tests/
    test_nutrigx.py                 # pytest-based with synthetic patient data

skills/gwas-lookup/tests/
    fixtures/                       # JSON fixtures per API source
    test_gwas_lookup.py             # pytest-based
```

## Test Structure

**Core test pattern (unittest):**
```python
#!/usr/bin/env python3
"""Tests for <feature description>."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from health_data_store import HealthDataStore  # noqa: E402
from health_memory import HealthMemoryWriter  # noqa: E402


class FeatureTest(unittest.TestCase):
    def test_behavior_description(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Arrange
            component = SomeComponent(data_dir=tmp_dir)

            # Act
            result = component.do_something()

            # Assert
            self.assertTrue(result["output_path"])
            self.assertIn("expected text", result["markdown"])


if __name__ == "__main__":
    unittest.main()
```

**Skill test pattern (pytest):**
```python
"""Tests for <skill name>.
Run with: pytest skills/<skill>/tests/test_<skill>.py -v
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from module import function_under_test

FIXTURES = Path(__file__).parent / "fixtures"


def test_behavior_description():
    result = function_under_test(input_data)
    assert len(result) > 0
    assert result["key"] == expected_value
```

**Patterns:**
- Setup: `tempfile.TemporaryDirectory()` as context manager for isolated filesystem
- Time injection: `now_fn=lambda: datetime(2026, 3, 15, 21, 0, 0)` for deterministic timestamps
- No `setUp`/`tearDown` methods -- each test is self-contained via `with tempfile.TemporaryDirectory()`
- `setUpClass` used sparingly (e.g., `SkillGovernanceTest` to build manifest records once)

## Mocking

**Framework:** `unittest.mock` (used in `skills/gwas-prs/tests/test_gwas_prs.py`)

**Patterns:**
```python
from unittest.mock import MagicMock, patch

@patch("gwas_prs.fetch_score_metadata")
def test_api_call(self, mock_fetch):
    mock_fetch.return_value = load_fixture("mock_score_metadata.json")
    result = gwas_prs.process(...)
    assert result is not None
```

**What to Mock:**
- External API calls (GWAS Catalog, PGS Catalog, etc.)
- Network requests in bioinformatics skills

**What NOT to Mock:**
- File system operations (use `tempfile.TemporaryDirectory()` instead)
- Shared library code (`HealthDataStore`, `HealthMemoryWriter`)
- Time (inject via `now_fn` parameter instead of mocking `datetime`)

## Fixtures and Factories

**Test Data:**

1. **JSON fixtures** for API response mocking:
   ```
   skills/gwas-prs/tests/fixtures/mock_trait_search.json
   skills/gwas-prs/tests/fixtures/mock_score_metadata.json
   skills/gwas-prs/tests/fixtures/mock_scores_by_trait.json
   skills/gwas-lookup/tests/fixtures/gwas_catalog.json
   skills/gwas-lookup/tests/fixtures/ensembl_variation.json
   skills/gwas-lookup/tests/fixtures/pheweb_ukb.json
   ```

2. **Golden files** for markdown output snapshot testing:
   ```
   tests/fixtures/health_memory_golden/
   ```

3. **Synthetic data files** for deterministic genomics tests:
   ```
   skills/nutrigx_advisor/tests/synthetic_patient.csv
   ```

4. **Inline test data** for health scenarios:
   ```python
   items = [
       {"category": "血糖", "item": "空腹血糖", "value": "6.4", "unit": "mmol/L",
        "reference_range": "3.9-6.1", "status": "偏高"},
   ]
   ```

5. **Helper methods** for writing markdown fixture files in tests:
   ```python
   def _write_item_file(self, memory_dir: str, slug: str, body: str) -> None:
       path = Path(memory_dir) / "items" / f"{slug}.md"
       path.parent.mkdir(parents=True, exist_ok=True)
       path.write_text(body.strip() + "\n", encoding="utf-8")
   ```

**Location:**
- `tests/fixtures/` for core test fixtures
- `skills/<skill>/tests/fixtures/` for skill-specific fixtures

## Coverage

**Requirements:** No coverage requirements enforced. No `.coveragerc` or coverage configuration detected.

**View Coverage:**
```bash
python -m pytest tests/ --cov=skills/_shared --cov-report=term  # If pytest-cov installed
```

## Test Types

**Unit Tests:**
- `tests/test_health_shared.py` (1692 lines): Comprehensive unit tests for all shared modules
  - `HealthDataStoreTest`: append, query, trend, config, vital bounds validation
  - `ConceptResolverTest`: concept lookup, field normalization, LOINC codes
  - `CorrelationEngineTest`: metric correlation detection
  - `ConsentManagerTest`: data sharing authorization
  - `FamilyManagerTest`: family member management
  - `FHIRMapperTest`: FHIR resource mapping
  - `MemoryEditorTest`: memory editing operations
  - `MemoryLifecycleTest`: fact lifecycle management
  - `SourceTracerTest`: data lineage tracing
  - `TwinIdentityTest`: digital twin identity
  - `EventTriggerTest`: real-time alerting rules
  - `PushDispatcherTest`: notification formatting

**Integration Tests:**
- `tests/test_flagship_scenarios.py`: End-to-end productized health workflows
  - Hypertension daily copilot: input -> output file + audit + behavior plan
  - Diabetes control hub: glucose entries -> recommendations + task board
  - Annual checkup advisor: lab results -> follow-up tasks
- `tests/test_health_operations.py`: Automated operations (weekly/monthly digest generation)
- `tests/test_health_heartbeat.py`: Proactive monitoring (missing records, upcoming appointments, refill alerts)

**Safety/Contract Tests:**
- `tests/test_iteration3_safety_contracts.py`: Anti-hallucination and access control tests
  - Mixed-language input preserves raw evidence
  - Ambiguous input does not write to MEMORY.md directly
  - Group context keeps public agents off patient archive
  - Family member context boundaries enforced

**Golden/Snapshot Tests:**
- `tests/test_health_memory_golden.py`: Compares markdown output against golden files in `tests/fixtures/health_memory_golden/`

**Governance Tests:**
- `tests/test_skill_governance.py`: Validates skill metadata (frontmatter, distribution tier, audit status)
- `tests/test_smoke_test_skills.py`: Validates smoke test command map includes compile and help checks

**Smoke Tests:**
- `scripts/smoke_test_skills.py`: Generates `py_compile` and `--help` commands for each health-core skill
- Tested by `tests/test_smoke_test_skills.py`

**Skill-Level Tests (pytest-based):**
- `skills/gwas-prs/tests/test_gwas_prs.py`: Genotype parsing, score calculation, API mocking
- `skills/nutrigx_advisor/tests/test_nutrigx.py`: Genetic file parsing, SNP extraction, risk scoring
- `skills/gwas-lookup/tests/test_gwas_lookup.py`: GWAS data normalization, PheWAS merging
- `skills/pharmgx-reporter/tests/test_pharmgx.py`: Pharmacogenomics reporting

**E2E Tests:**
- Not automated. Manual testing via CLI scripts (`scripts/run_*.py`).

## Common Patterns

**Deterministic Time Testing:**
```python
def test_something(self):
    fixed_now = lambda: datetime(2026, 3, 15, 21, 0, 0)  # Sunday

    with tempfile.TemporaryDirectory() as data_dir:
        component = SomeComponent(data_dir=data_dir, now_fn=fixed_now)
        result = component.run()
        self.assertIn("2026-03-15", result["markdown"])
```

**File System Isolation:**
```python
def test_output_files_created(self):
    with tempfile.TemporaryDirectory() as data_dir, \
         tempfile.TemporaryDirectory() as memory_dir:
        result = Workflow(data_dir=data_dir, memory_dir=memory_dir).run()

        output_path = Path(result["output_path"])
        self.assertTrue(output_path.exists())
        markdown = output_path.read_text(encoding="utf-8")
        self.assertIn("## Expected Section", markdown)
```

**Testing Chinese Content:**
```python
self.assertIn("高血压", markdown)
self.assertIn("血压连续偏高", result["markdown"])
self.assertIn("本周周报待生成", result["markdown"])
```

**Fixture-Based API Testing (no network):**
```python
FIXTURES = Path(__file__).parent / "fixtures"

def load_fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    return json.loads(path.read_text())

def test_merge_gwas_sorts_by_pval():
    gwas_catalog = load_fixture("gwas_catalog")
    credsets = load_fixture("open_targets_credsets")
    merged = merge_gwas(gwas_catalog, credsets)
    assert len(merged) > 0
```

**Error/Validation Testing:**
```python
def test_vital_bounds_reject_out_of_range(self):
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = HealthDataStore("test", data_dir=tmp_dir)
        with self.assertRaises(ValueError):
            store.append("bp", {"systolic": 500})
```

## CI/CD Integration

**CI Pipeline:** No CI/CD configuration detected (no `.github/workflows/`, no `Jenkinsfile`, no `.gitlab-ci.yml`).

**Smoke test infrastructure exists** in `scripts/smoke_test_skills.py` which generates per-skill compile and help commands, suitable for integration into a CI pipeline.

## Adding New Tests

**For shared module changes:**
- Add test class/methods to `tests/test_health_shared.py`
- Follow `<Module>Test(unittest.TestCase)` naming pattern
- Use `tempfile.TemporaryDirectory()` for isolation
- Inject time with `now_fn=lambda: datetime(...)`

**For new flagship scenarios:**
- Add to `tests/test_flagship_scenarios.py` or create `tests/test_<scenario>.py`
- Test full data flow: input -> output files + memory writebacks + task board

**For new skills with Python code:**
- Create `skills/<skill-name>/tests/test_<skill>.py`
- Use pytest-style functions (no TestCase needed)
- Add JSON fixtures for any API responses in `skills/<skill-name>/tests/fixtures/`
- Document run command in module docstring: `Run with: pytest skills/<skill>/tests/test_<skill>.py -v`

**For safety/contract tests:**
- Add to `tests/test_iteration3_safety_contracts.py`
- Focus on: data boundary enforcement, hallucination prevention, access control

---

*Testing analysis: 2026-03-26*
