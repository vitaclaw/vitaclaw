# Coding Conventions

**Analysis Date:** 2026-03-26

## Languages

**Primary:** Python 3.10+ (type hints with `X | None` union syntax used throughout)

**Secondary:** Shell (bash scripts in `scripts/setup_heartbeat_scheduler.sh`, skill-level example scripts)

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `health_data_store.py`, `blood_pressure_tracker.py`)
- Skill directories: `kebab-case` (e.g., `blood-pressure-tracker/`, `caffeine-tracker/`)
- Test files: `test_<module_name>.py` (e.g., `test_health_shared.py`, `test_flagship_scenarios.py`)
- Script entry points: `run_<workflow>.py` or `<verb>_<noun>.py` (e.g., `run_health_heartbeat.py`, `build_vitaclaw_release.py`)

**Classes:**
- PascalCase: `HealthDataStore`, `BloodPressureTracker`, `HealthMemoryWriter`, `ConsentManager`
- Test classes: `<Feature>Test` with `unittest.TestCase` (e.g., `HealthDataStoreTest`, `FlagshipScenarioTest`)

**Functions/Methods:**
- snake_case: `update_blood_pressure()`, `daily_entry()`, `run_health_heartbeat()`
- Private helpers: underscore prefix `_repo_root()`, `_resolve_data_root()`, `_normalize_timestamp()`
- Test methods: `test_<behavior_description>` with verbose names (e.g., `test_detects_missing_records_risk_and_digest_due`)

**Variables:**
- snake_case: `data_dir`, `memory_dir`, `workspace_root`
- Constants: UPPER_SNAKE_CASE defined at module level (e.g., `VITAL_BOUNDS`, `ROLE_DEFINITIONS`, `DRINKS`)

**Types:**
- Use `from __future__ import annotations` at the top of every module
- Modern union syntax: `str | None` instead of `Optional[str]`
- Custom exception classes: `ConceptNotFoundError(KeyError)`, `FieldValidationError(ValueError)`

## Code Style

**Formatting:**
- No `.prettierrc`, `.eslintrc`, `ruff.toml`, or `pyproject.toml` detected -- no automated formatter enforced
- Consistent 4-space indentation throughout
- Line length generally kept under ~120 characters but no strict limit enforced
- `# noqa: E402` comments used on imports that follow `sys.path` manipulation

**Linting:**
- No formal linter configuration files detected
- Code is clean of TODO/FIXME/HACK comments in the shared modules (`skills/_shared/`)
- PEP 8 conventions followed informally

**Shebang:**
- All Python modules begin with `#!/usr/bin/env python3`

**Docstrings:**
- Module-level docstrings on every file: triple-quoted single-line or multi-line
- Class-level docstrings: brief description of responsibility
- Method docstrings: `Args:` block for complex parameters, Chinese docstrings in user-facing skills (e.g., `caffeine_tracker.py`)
- Example from `skills/_shared/health_data_store.py`:
  ```python
  def append(self, record_type: str, data: dict, note: str = "",
             timestamp=None, meta: dict | None = None, sign: bool = False) -> dict:
      """Append a health record.

      Args:
          record_type: The record type (e.g. "bp", "glucose").
          data: Metric-specific payload.
          ...
      """
  ```

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first)
2. Standard library imports (`json`, `sys`, `tempfile`, `pathlib`, etc.)
3. `sys.path` manipulation to add shared/skill directories
4. Local project imports (with `# noqa: E402` when path was modified above)

**Path Resolution Pattern:**
- Shared modules use `_repo_root()` helper: `Path(__file__).resolve().parents[2]`
- Skills add `_shared` to path: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))`
- Tests add shared dir: `ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SHARED_DIR))`
- No `setup.py`, `pyproject.toml`, or installable package -- all imports are path-based

**Path Aliases:**
- None. All imports use `sys.path.insert(0, ...)` for resolution.

## Error Handling

**Patterns:**
- Custom exception hierarchy: `ConceptNotFoundError(KeyError)`, `FieldValidationError(ValueError)` in `skills/_shared/concept_resolver.py`
- Input validation with `ValueError` for out-of-range health metrics:
  ```python
  if isinstance(val, (int, float)) and not (lo <= val <= hi):
      raise ValueError(f"Value out of plausible range for {key}: {val} (expected {lo}-{hi})")
  ```
- Graceful degradation for corrupted data: JSONL parsing skips bad lines with stderr warning:
  ```python
  except json.JSONDecodeError:
      print(f"[WARN] Skipping corrupted JSONL line in {self.data_file}: {line[:80]}", file=sys.stderr)
  ```
- Optional dependency handling with try/except ImportError (e.g., `yaml` in `consent_manager.py`):
  ```python
  try:
      import yaml
      HAS_YAML = True
  except ImportError:
      HAS_YAML = False
  ```

## Logging

**Framework:** `print()` to stdout/stderr (no logging framework)

**Patterns:**
- Informational output: `print()` to stdout
- Warnings: `print(f"[WARN] ...", file=sys.stderr)`
- Structured output: `json.dumps(result, ensure_ascii=False, indent=2)` for `--format json` CLI mode
- Script runners support `--format markdown|json` for output format switching

## Constructor / Initialization Pattern

**Dependency injection with sensible defaults:**

All major classes follow a consistent constructor pattern:

```python
class SomeComponent:
    def __init__(
        self,
        data_dir: str | None = None,
        memory_dir: str | None = None,
        workspace_root: str | None = None,
        now_fn=None,
    ):
```

Resolution order for directories:
1. Explicit parameter
2. Environment variable (`VITACLAW_DATA_DIR`, `VITACLAW_MEMORY_DIR`, `OPENCLAW_WORKSPACE`)
3. Repo-relative default (via `_repo_root()`)

`now_fn` parameter enables deterministic time in tests (e.g., `lambda: datetime(2026, 3, 15, 21, 0, 0)`).

## Data Patterns

**JSONL append-only storage:** `skills/_shared/health_data_store.py`
- Each skill writes to `data/<skill-name>/records.jsonl`
- Records include `timestamp`, `type`, `data`, `note`, `_meta`
- File-level locking with `fcntl` for concurrent append safety
- Hash-based record IDs using `uuid` and `hashlib`

**Markdown-based memory:** `skills/_shared/health_memory.py`
- Memory written as markdown files under `memory/health/`
- YAML frontmatter in memory item files (`---\nitem: medications\n---`)
- Daily snapshots, weekly digests, monthly digests

**Schema-driven concepts:** `schemas/health-concepts.yaml` drives `ConceptResolver`
- No hardcoded mappings; all concept definitions in YAML

## CLI Pattern

**Standard `argparse` entry point:**

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--data-dir", default=None, help="Data directory")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    # ... instantiate and run ...

if __name__ == "__main__":
    main()
```

Scripts in `scripts/` follow this pattern consistently. Skills in `skills/<name>/` also use `argparse` with `--help` support.

## Bilingual Content

- Code identifiers and docstrings: English
- User-facing health content (blood pressure grades, recommendations, UI text): Chinese (Simplified)
- Test assertions check both English structural markers (`## Sources`, `## Evidence`) and Chinese content (`"高血压"`, `"血压连续偏高"`)
- Mixed-language support is explicit and tested (see `test_mixed_language_checkup_report_preserves_raw_evidence`)

## Module Design

**Exports:** No `__all__` declarations. Classes and functions are imported directly by name.

**Barrel Files:** Not used. No `__init__.py` files in skill directories.

**Single-responsibility modules:** Each module in `skills/_shared/` handles one concern:
- `health_data_store.py`: JSONL storage
- `health_memory.py`: Markdown memory writes
- `health_heartbeat.py`: Proactive health checks
- `consent_manager.py`: Data sharing authorization
- `source_tracer.py`: Data lineage
- `event_trigger.py`: Real-time alerting
- `correlation_engine.py`: Metric correlation detection

---

*Convention analysis: 2026-03-26*
