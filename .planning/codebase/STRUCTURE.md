# Codebase Structure

**Analysis Date:** 2026-03-26

## Directory Layout

```
vitaclaw-main/
├── AGENTS.md               # Agent roles and fixed read order
├── BOOTSTRAP.md            # Bootstrap checklist for workspace entry
├── HEARTBEAT.md            # Proactive service triggers and output rules
├── IDENTITY.md             # Agent identity template (filled during onboarding)
├── MEMORY.md               # Long-term stable facts (user baseline, chronic conditions, preferences)
├── SOUL.md                 # Agent personality, safety boundaries, output format
├── USER.md                 # User identity template
├── README.md               # English documentation with generated skill catalog
├── README.zh.md            # Chinese documentation
├── privacy_desensitize.py  # Data desensitization utility
├── skills-manifest.json    # Generated manifest of all 222 skills
├── configs/                # Runtime configuration
│   ├── com.vitaclaw.heartbeat.plist   # macOS launchd scheduler config
│   └── openclaw.health.json5         # Agent team topology and routing
├── data/                   # JSONL structured data per skill
│   ├── blood-pressure-tracker/
│   ├── caffeine-tracker/
│   ├── chronic-condition-monitor/
│   ├── health-operations/
│   ├── medication-reminder/
│   ├── sleep-analyzer/
│   ├── supplement-manager/
│   └── weekly-health-digest/
├── dist/                   # Built release packages
│   ├── vitaclaw-core/
│   ├── vitaclaw-family-care/
│   ├── vitaclaw-labs/
│   └── vitaclaw-oncology/
├── docs/                   # Design documents and guides (17 files)
├── examples/               # Example workspace
│   └── workspace-health/
├── memory/                 # Shared health memory (markdown)
│   └── health/
│       ├── _health-profile.md
│       ├── daily/          # Per-day event logs
│       ├── files/          # Bridged summaries, briefings, timelines
│       ├── heartbeat/      # Task board, preferences, state
│       ├── items/          # Longitudinal per-metric tracking files
│       ├── monthly/        # Monthly digest summaries
│       ├── quarterly/      # Quarterly stability checkpoints
│       └── weekly/         # Weekly digest summaries
├── packages/               # Release package manifests
│   ├── vitaclaw-core.json
│   ├── vitaclaw-family-care.json
│   ├── vitaclaw-labs.json
│   └── vitaclaw-oncology.json
├── reports/                # Generated validation/governance reports
├── schemas/                # Data schemas and concept registry
│   ├── doctor-match/
│   ├── health-concepts.yaml
│   ├── health-data-record.schema.json
│   ├── skill-frontmatter.schema.json
│   └── twin-knowledge-graph.schema.json
├── scripts/                # CLI entry points (29 Python + 1 shell)
├── skills/                 # 222 skill directories + _shared/
│   ├── _shared/            # Shared Python runtime (36 modules)
│   ├── blood-pressure-tracker/
│   ├── annual-checkup-advisor/
│   ├── ... (222 total)
│   └── weightloss-analyzer/
├── templates/              # Workspace templates for init
│   ├── openclaw-health-agent/
│   ├── openclaw-health-family-agent/
│   └── openclaw-health-research-agent/
└── tests/                  # Test suite (28 test files + fixtures)
    ├── fixtures/
    └── test_*.py
```

## Directory Purposes

**`skills/`:**
- Purpose: Contains all 222 health AI skills plus shared runtime
- Contains: One subdirectory per skill, each with `SKILL.md` and optional Python/scripts
- Key files: `skills/_shared/*.py` (shared runtime), `skills/*/SKILL.md` (skill prompts)

**`skills/_shared/`:**
- Purpose: Shared Python runtime depended on by all skills and scripts
- Contains: 36 Python modules providing data storage, memory writing, scenario runtime, team orchestration, heartbeat, cross-skill reading, reminders, patient archive bridging, timeline building, visit workflows, memory distillation
- Key files:
  - `health_data_store.py`: JSONL record storage with file locking
  - `health_memory.py`: Markdown memory writer
  - `health_heartbeat.py`: Proactive health checks
  - `health_scenario_runtime.py`: Scenario output rendering
  - `health_team_runtime.py`: Multi-agent team orchestration
  - `health_operations.py`: Automation runner
  - `cross_skill_reader.py`: Registry-driven cross-skill data reader
  - `health_reminder_center.py`: Task/reminder management
  - `health_flagship_scenarios.py`: Productized scenario classes
  - `health_visit_workflow.py`: Visit briefing/follow-up
  - `health_timeline_builder.py`: Unified timeline builder
  - `health_memory_distiller.py`: Long-term memory distillation
  - `patient_archive_bridge.py`: Patient archive integration
  - `concept_resolver.py`: Health concept resolution from YAML registry

**`memory/health/`:**
- Purpose: Shared markdown-based health memory used across all skills
- Contains: Daily logs, per-item longitudinal files, digests, heartbeat state, team artifacts
- Key files:
  - `_health-profile.md`: Structured health baseline
  - `daily/YYYY-MM-DD.md`: Per-day event records
  - `items/blood-pressure.md`, `items/blood-sugar.md`, `items/weight.md`, etc.: Per-metric longitudinal tracking (17 core items)
  - `heartbeat/task-board.md`: Current task list
  - `heartbeat/preferences.md`: Reminder preferences
  - `weekly/`, `monthly/`, `quarterly/`: Distilled summaries
  - `files/patient-archive-summary.md`: Bridged patient data
  - `files/health-timeline.md`: Unified timeline

**`data/`:**
- Purpose: JSONL structured data storage for skills that produce quantitative records
- Contains: Subdirectory per skill with `{skill-name}.jsonl` and optional `charts/` directory
- Key files: `data/{skill-name}/{skill-name}.jsonl`

**`scripts/`:**
- Purpose: CLI entry points for running scenarios, automation, workspace init, and build
- Contains: 29 Python scripts and 1 shell script
- Key files:
  - `init_health_workspace.py`: Initialize workspace from templates
  - `run_health_chief_of_staff.py`: Run chief-led team orchestration
  - `run_health_heartbeat.py`: Run proactive health checks
  - `run_health_operations.py`: Run all due maintenance tasks
  - `run_hypertension_daily_copilot.py`: Run hypertension scenario
  - `run_diabetes_control_hub.py`: Run diabetes scenario
  - `run_annual_checkup_advisor.py`: Run annual checkup scenario
  - `build_vitaclaw_release.py`: Build release packages
  - `build_skills_manifest.py`: Generate skills-manifest.json
  - `validate_skill_frontmatter.py`: Validate skill YAML frontmatter
  - `smoke_test_skills.py`: Smoke test skill imports
  - `distill_health_memory.py`: Run memory distillation
  - `generate_health_timeline.py`: Generate unified timeline
  - `generate_visit_briefing.py`: Generate pre-visit briefing
  - `record_visit_followup.py`: Record post-visit follow-up
  - `sync_patient_archive.py`: Sync patient archive to workspace
  - `import_apple_health_export.py`: Import Apple Health data
  - `manage_health_tasks.py`: Task management (list/complete/snooze/reopen)

**`configs/`:**
- Purpose: Runtime configuration for OpenClaw platform and macOS scheduler
- Contains: Agent team config and launchd plist
- Key files:
  - `openclaw.health.json5`: Full agent topology (10 agents), route table, privacy defaults, heartbeat cadence, web-assist policy, package matrix
  - `com.vitaclaw.heartbeat.plist`: macOS launchd plist for scheduled heartbeat

**`schemas/`:**
- Purpose: Data validation schemas and health concept registry
- Contains: JSON Schema files and YAML concept definitions
- Key files:
  - `health-concepts.yaml`: Single source of truth for all health concepts (concept ID, LOINC codes, field schemas, producer/consumer skills, plausible ranges)
  - `skill-frontmatter.schema.json`: JSON Schema for SKILL.md frontmatter validation
  - `health-data-record.schema.json`: JSON Schema for JSONL record envelope
  - `twin-knowledge-graph.schema.json`: Knowledge graph schema

**`templates/`:**
- Purpose: Starter workspace configurations for different use cases
- Contains: 3 complete workspace templates with pre-initialized memory directories
- Key files:
  - `openclaw-health-agent/`: Personal health management template
  - `openclaw-health-family-agent/`: Family care coordination template
  - `openclaw-health-research-agent/`: Health research template

**`packages/`:**
- Purpose: Release package manifests defining which files belong in each distribution tier
- Contains: 4 JSON manifests
- Key files:
  - `vitaclaw-core.json`: Core package (shared runtime, templates, scripts, docs, config)
  - `vitaclaw-family-care.json`: Family care extension
  - `vitaclaw-labs.json`: Advanced/research skills
  - `vitaclaw-oncology.json`: Restricted oncology skills

**`docs/`:**
- Purpose: Design documents, architecture guides, and onboarding playbooks
- Contains: 17 markdown files (mostly Chinese)
- Key files:
  - `health-agent-architecture.zh.md`: Chief-led multi-agent architecture design
  - `health-memory-spec.zh.md`: Health memory contract specification
  - `health-data-contract.md`: Data contract (JSONL envelope, markdown memory, distillation chain)
  - `health-agent-quickstart.zh.md`: Quick start guide
  - `health-release-packages.zh.md`: Release package documentation
  - `skill-frontmatter-schema.md`: Frontmatter schema documentation

**`tests/`:**
- Purpose: Test suite for shared runtime, scenarios, and workspace initialization
- Contains: 28 test files and fixtures
- Key files: `test_health_memory_golden.py`, `test_flagship_scenarios.py`, `test_health_heartbeat.py`, `test_health_operations.py`, `test_health_team_runtime.py`, etc.
- Fixtures: `tests/fixtures/health_memory_golden/` (golden test data for memory operations)

**`reports/`:**
- Purpose: Generated validation and governance reports
- Contains: JSON reports from frontmatter validation, smoke tests, governance audit
- Key files: `skill-frontmatter-report.json`, `skill-governance-report.json`, `skill-smoke-report.json`

## Key File Locations

**Entry Points:**
- `BOOTSTRAP.md`: Agent workspace entry checklist
- `scripts/run_health_chief_of_staff.py`: Chief-led team CLI
- `scripts/run_health_operations.py`: Automated operations CLI
- `scripts/init_health_workspace.py`: Workspace initialization

**Configuration:**
- `configs/openclaw.health.json5`: Agent team topology and routing
- `schemas/health-concepts.yaml`: Health concept registry
- `schemas/skill-frontmatter.schema.json`: Skill frontmatter validation schema

**Core Logic:**
- `skills/_shared/health_data_store.py`: JSONL data storage
- `skills/_shared/health_memory.py`: Markdown memory writer
- `skills/_shared/health_heartbeat.py`: Proactive health checks
- `skills/_shared/health_scenario_runtime.py`: Scenario output rendering
- `skills/_shared/health_team_runtime.py`: Multi-agent orchestration
- `skills/_shared/health_operations.py`: Automation runner
- `skills/_shared/cross_skill_reader.py`: Cross-skill data aggregation
- `skills/_shared/health_flagship_scenarios.py`: Productized scenarios

**Testing:**
- `tests/test_*.py`: 28 test files
- `tests/fixtures/health_memory_golden/`: Golden test data

## Naming Conventions

**Files:**
- Skill directories: `kebab-case` (e.g., `blood-pressure-tracker`, `annual-checkup-advisor`)
- Python modules: `snake_case` (e.g., `health_data_store.py`, `blood_pressure_tracker.py`)
- Markdown skill files: Always `SKILL.md` (uppercase)
- Workspace config files: `UPPERCASE.md` (e.g., `AGENTS.md`, `BOOTSTRAP.md`, `SOUL.md`, `MEMORY.md`)
- Memory item files: `kebab-case.md` (e.g., `blood-pressure.md`, `blood-sugar.md`)
- Test files: `test_{module_name}.py`
- Daily logs: `YYYY-MM-DD.md`

**Directories:**
- Skill directories match skill name in frontmatter: `skills/{skill-name}/`
- Data directories mirror skill names: `data/{skill-name}/`
- Memory subdirectories: `daily/`, `items/`, `files/`, `heartbeat/`, `weekly/`, `monthly/`, `quarterly/`

**Python classes:**
- PascalCase with descriptive domain prefix: `HealthDataStore`, `HealthMemoryWriter`, `HealthHeartbeat`, `HealthScenarioRuntime`, `CrossSkillReader`

## Where to Add New Code

**New Health Skill:**
- Create directory: `skills/{skill-name}/`
- Create `skills/{skill-name}/SKILL.md` with YAML frontmatter (name, description, version, user-invocable, allowed-tools, metadata)
- Optional Python implementation: `skills/{skill-name}/{skill_name}.py`
- Register concept in `schemas/health-concepts.yaml` if the skill produces structured data
- Frontmatter must validate against `schemas/skill-frontmatter.schema.json`
- Run `scripts/validate_skill_frontmatter.py` to verify
- Run `scripts/build_skills_manifest.py` to regenerate `skills-manifest.json`

**New Shared Runtime Module:**
- Add to `skills/_shared/{module_name}.py`
- Follow existing pattern: class-based with `workspace_root`/`memory_dir`/`now_fn` constructor parameters
- Import from other shared modules using direct import (modules add `SHARED_DIR` to `sys.path`)

**New Scenario Workflow:**
- Add scenario class to `skills/_shared/health_flagship_scenarios.py` or create new file in `skills/_shared/`
- Create CLI entry point: `scripts/run_{scenario_name}.py`
- Add route table entry in `configs/openclaw.health.json5` under `vitaclaw.team.routeTable`
- Add test: `tests/test_{scenario_name}.py`

**New Health Memory Item:**
- Add item template to `scripts/init_health_workspace.py` (DEFAULT_CORE_ITEMS dict)
- Create file: `memory/health/items/{item-name}.md` with required sections (YAML frontmatter, `## Recent Status`, `## History`)
- Register in `docs/health-data-contract.md` and `docs/health-memory-spec.zh.md`

**New Test:**
- Add to `tests/test_{feature}.py`
- Use golden fixtures from `tests/fixtures/health_memory_golden/` for memory operation tests
- Follow existing pattern of injecting `now_fn` for deterministic time

**New CLI Script:**
- Add to `scripts/{script_name}.py`
- Follow existing pattern: argparse CLI, instantiate shared runtime classes, call methods

**New Workspace Template:**
- Add to `templates/{template-name}/`
- Include pre-initialized `memory/health/` directory structure
- Register in `scripts/init_health_workspace.py` TEMPLATES dict

**New Release Package:**
- Add manifest: `packages/{package-name}.json`
- Include file list of what belongs in the package
- `scripts/build_vitaclaw_release.py` will copy files to `dist/{package-name}/`

## Special Directories

**`skills/_shared/`:**
- Purpose: Shared Python runtime for all skills (not a skill itself)
- Generated: No
- Committed: Yes
- Note: All 36 modules are importable by skills via `sys.path` manipulation

**`dist/`:**
- Purpose: Built release packages for distribution
- Generated: Yes (by `scripts/build_vitaclaw_release.py`)
- Committed: Yes (contains distributable snapshots)

**`data/`:**
- Purpose: Per-skill JSONL structured data
- Generated: Yes (by skill execution)
- Committed: Partially (structure committed, data may vary per installation)

**`memory/health/`:**
- Purpose: Shared markdown health memory
- Generated: Yes (by workspace init and ongoing skill execution)
- Committed: Template structure committed; actual patient data is per-installation

**`reports/`:**
- Purpose: Generated validation and governance reports
- Generated: Yes (by validation/governance scripts)
- Committed: Yes

**`tests/fixtures/`:**
- Purpose: Golden test data for deterministic testing
- Generated: No (manually curated)
- Committed: Yes

---

*Structure analysis: 2026-03-26*
