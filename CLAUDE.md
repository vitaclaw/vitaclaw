<!-- GSD:project-start source:PROJECT.md -->
## Project

**VitaClaw Iteration 2**

VitaClaw 是一个运行在 OpenClaw 平台上的模块化健康 AI 技能库，222+ 个 SKILL.md 技能覆盖日常健康追踪、主动提醒、就医支持和医学研究。Iteration 1 搭建了核心架构（chief-led 多 agent、JSONL 数据存储、markdown 记忆链、heartbeat 主动巡检）。Iteration 2 的目标是让数据流通更顺畅、让纵向价值真正被用户感知到、让工程基础能承载长期演进。

**Core Value:** 比用户记得更全、追得更连续、整理得更系统——在需要就医或决策时，能快速调出完整上下文。

### Constraints

- **本地优先**：所有数据必须存储在本地文件系统，不依赖云服务 — 这是 VitaClaw 的核心差异化
- **技能格式**：新能力必须以 SKILL.md + 可选 Python 的形式实现 — 保持与 OpenClaw 运行时的兼容性
- **隐私边界**：健康数据不得未经用户同意离开本地 — SOUL.md 安全边界
- **向后兼容**：Iteration 1 的数据格式和记忆结构必须能平滑迁移 — 避免用户数据丢失
- **Python only**：不引入新语言 — 保持贡献者门槛低
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3 - All scripts, shared runtime libraries, skill implementations, tests, and CLI tooling
- Shell (Bash/Zsh) - Bioinformatics workflow examples (`skills/variant-interpretation-acmg/bioSkills/*/examples/*.sh`), setup scripts (`scripts/setup_heartbeat_scheduler.sh`), web-access helpers (`skills/web-access/scripts/*.sh`)
- Markdown - Primary skill definition format (`SKILL.md` files), health memory storage, documentation
- JSON / JSON5 - Configuration (`configs/openclaw.health.json5`), manifests (`skills-manifest.json`), schemas (`schemas/*.schema.json`), package definitions (`packages/*.json`)
- YAML - Skill frontmatter inside `SKILL.md` files, parsed by `scripts/skill_catalog.py` using PyYAML
## Runtime
- Python 3 (standard CPython, no version pinning detected)
- macOS (primary development/deployment target based on launchd plist at `configs/com.vitaclaw.heartbeat.plist`)
- No project-level `requirements.txt`, `pyproject.toml`, or `setup.py` at the repo root
- Individual skills may declare their own dependency files within their directories
- Python dependencies are installed ad-hoc; the shared runtime (`skills/_shared/`) uses only stdlib + `requests` + `PyYAML` as hard dependencies
## Frameworks
- No web framework - This is not a web application. It is a skill library for the OpenClaw AI assistant platform
- OpenClaw Runtime - The host platform that discovers and executes `SKILL.md` files; VitaClaw is a plugin/skill library for it
- `unittest` (Python stdlib) - All tests in `tests/` use `unittest.TestCase`
- Custom Python scripts for build/release tooling:
## Key Dependencies
- `requests` - HTTP client for all external API calls (PubMed, FDA, ClinicalTrials.gov, Ensembl, KEGG, etc.)
- `PyYAML` (`yaml`) - Parsing SKILL.md frontmatter in `scripts/skill_catalog.py` and `skills/_shared/concept_resolver.py`
- `matplotlib` - Chart generation in `skills/caffeine-tracker/caffeine_tracker.py`, `skills/chemo-side-effect-tracker/`, `skills/post-surgery-recovery/`
- `pandas` - Data analysis in oncology agent skills (`skills/hemoglobinopathy-analysis-agent/`, `skills/mpn-progression-monitor-agent/`, etc.)
- `numpy` - Numeric computation in specialized bioinformatics agents (`skills/nk-cell-therapy-agent/`, `skills/hrd-analysis-agent/`, etc.)
- `Pillow` (PIL) - Image processing in `privacy_desensitize.py`
- `pillow-heif` - HEIC/HEIF image support in `privacy_desensitize.py`, `skills/medical-record-organizer/scripts/redact_ocr.py`
- `PyMuPDF` (`fitz`) - PDF processing in `privacy_desensitize.py`, `skills/medical-record-organizer/scripts/redact_ocr.py`
- `PaddleOCR` - OCR text detection in `privacy_desensitize.py` (referenced in docstring)
- `cryptography` - SMART Health Card JWS signing in `skills/_shared/smart_health_card.py` (optional, gracefully degrades)
- `python-jose` - JWS creation fallback in `skills/_shared/smart_health_card.py` (optional)
- `urllib3` - Retry strategy via `urllib3.util.retry.Retry`, used alongside `requests`
## Configuration
- `configs/openclaw.health.json5` - Master agent/team configuration (JSON5 format): defines agent roles, heartbeat intervals, team routing, privacy defaults, push delivery model
- `configs/com.vitaclaw.heartbeat.plist` - macOS launchd scheduled task for heartbeat (runs `scripts/run_health_heartbeat.py` every 7200 seconds)
- Environment variables used for API keys and push channel configuration (see INTEGRATIONS.md for full list)
- `VITACLAW_DATA_DIR` - Override for data storage root directory (defaults to `<repo>/data/`)
- `schemas/skill-frontmatter.schema.json` - JSON Schema for validating SKILL.md YAML frontmatter
- `schemas/health-data-record.schema.json` - JSON Schema for JSONL health data records
- `schemas/twin-knowledge-graph.schema.json` - JSON Schema for Digital Twin knowledge graph entries
- `packages/vitaclaw-core.json` - Core release package manifest (stable tier)
- `packages/vitaclaw-oncology.json` - Oncology release package manifest (restricted tier)
- `packages/vitaclaw-family-care.json` - Family care release package manifest
- `packages/vitaclaw-labs.json` - Experimental release package manifest (labs tier)
## Data Storage
- JSONL (JSON Lines) - Primary structured data format for health records, stored in `data/<skill-slug>/`
- Markdown files - Health memory (`memory/health/daily/*.md`, `memory/health/items/*.md`, `memory/health/weekly/*.md`, `memory/health/monthly/*.md`)
- JSON - Manifest, reports, schemas
- Patient archives stored at `~/.openclaw/patients/` (outside repo)
## Platform Requirements
- Python 3 with `requests` and `PyYAML` installed
- macOS recommended (launchd integration, osascript notifications)
- Git for version control of health data
- OpenClaw-compatible AI runtime (Claude, GPT, Gemini, Llama supported)
- Local filesystem for data persistence
- Optional: Feishu bot credentials for push notifications
- Optional: Bark app for iOS push notifications
- Optional: macOS for native notification support
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Languages
## Naming Patterns
- Python modules: `snake_case.py` (e.g., `health_data_store.py`, `blood_pressure_tracker.py`)
- Skill directories: `kebab-case` (e.g., `blood-pressure-tracker/`, `caffeine-tracker/`)
- Test files: `test_<module_name>.py` (e.g., `test_health_shared.py`, `test_flagship_scenarios.py`)
- Script entry points: `run_<workflow>.py` or `<verb>_<noun>.py` (e.g., `run_health_heartbeat.py`, `build_vitaclaw_release.py`)
- PascalCase: `HealthDataStore`, `BloodPressureTracker`, `HealthMemoryWriter`, `ConsentManager`
- Test classes: `<Feature>Test` with `unittest.TestCase` (e.g., `HealthDataStoreTest`, `FlagshipScenarioTest`)
- snake_case: `update_blood_pressure()`, `daily_entry()`, `run_health_heartbeat()`
- Private helpers: underscore prefix `_repo_root()`, `_resolve_data_root()`, `_normalize_timestamp()`
- Test methods: `test_<behavior_description>` with verbose names (e.g., `test_detects_missing_records_risk_and_digest_due`)
- snake_case: `data_dir`, `memory_dir`, `workspace_root`
- Constants: UPPER_SNAKE_CASE defined at module level (e.g., `VITAL_BOUNDS`, `ROLE_DEFINITIONS`, `DRINKS`)
- Use `from __future__ import annotations` at the top of every module
- Modern union syntax: `str | None` instead of `Optional[str]`
- Custom exception classes: `ConceptNotFoundError(KeyError)`, `FieldValidationError(ValueError)`
## Code Style
- No `.prettierrc`, `.eslintrc`, `ruff.toml`, or `pyproject.toml` detected -- no automated formatter enforced
- Consistent 4-space indentation throughout
- Line length generally kept under ~120 characters but no strict limit enforced
- `# noqa: E402` comments used on imports that follow `sys.path` manipulation
- No formal linter configuration files detected
- Code is clean of TODO/FIXME/HACK comments in the shared modules (`skills/_shared/`)
- PEP 8 conventions followed informally
- All Python modules begin with `#!/usr/bin/env python3`
- Module-level docstrings on every file: triple-quoted single-line or multi-line
- Class-level docstrings: brief description of responsibility
- Method docstrings: `Args:` block for complex parameters, Chinese docstrings in user-facing skills (e.g., `caffeine_tracker.py`)
- Example from `skills/_shared/health_data_store.py`:
## Import Organization
- Shared modules use `_repo_root()` helper: `Path(__file__).resolve().parents[2]`
- Skills add `_shared` to path: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))`
- Tests add shared dir: `ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SHARED_DIR))`
- No `setup.py`, `pyproject.toml`, or installable package -- all imports are path-based
- None. All imports use `sys.path.insert(0, ...)` for resolution.
## Error Handling
- Custom exception hierarchy: `ConceptNotFoundError(KeyError)`, `FieldValidationError(ValueError)` in `skills/_shared/concept_resolver.py`
- Input validation with `ValueError` for out-of-range health metrics:
- Graceful degradation for corrupted data: JSONL parsing skips bad lines with stderr warning:
- Optional dependency handling with try/except ImportError (e.g., `yaml` in `consent_manager.py`):
## Logging
- Informational output: `print()` to stdout
- Warnings: `print(f"[WARN] ...", file=sys.stderr)`
- Structured output: `json.dumps(result, ensure_ascii=False, indent=2)` for `--format json` CLI mode
- Script runners support `--format markdown|json` for output format switching
## Constructor / Initialization Pattern
## Data Patterns
- Each skill writes to `data/<skill-name>/records.jsonl`
- Records include `timestamp`, `type`, `data`, `note`, `_meta`
- File-level locking with `fcntl` for concurrent append safety
- Hash-based record IDs using `uuid` and `hashlib`
- Memory written as markdown files under `memory/health/`
- YAML frontmatter in memory item files (`---\nitem: medications\n---`)
- Daily snapshots, weekly digests, monthly digests
- No hardcoded mappings; all concept definitions in YAML
## CLI Pattern
## Bilingual Content
- Code identifiers and docstrings: English
- User-facing health content (blood pressure grades, recommendations, UI text): Chinese (Simplified)
- Test assertions check both English structural markers (`## Sources`, `## Evidence`) and Chinese content (`"高血压"`, `"血压连续偏高"`)
- Mixed-language support is explicit and tested (see `test_mixed_language_checkup_report_preserves_raw_evidence`)
## Module Design
- `health_data_store.py`: JSONL storage
- `health_memory.py`: Markdown memory writes
- `health_heartbeat.py`: Proactive health checks
- `consent_manager.py`: Data sharing authorization
- `source_tracer.py`: Data lineage
- `event_trigger.py`: Real-time alerting
- `correlation_engine.py`: Metric correlation detection
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Skill-based modular architecture: 222+ self-contained `SKILL.md` files, each defining a health domain capability
- Chief-led orchestration: a single entry agent (`health-chief-of-staff`) routes tasks to specialist agents
- Local-first, file-based: all data stored as markdown and JSONL on the local filesystem, no external database
- Layered memory system: daily -> weekly -> monthly -> quarterly -> MEMORY.md distillation chain
- Designed for OpenClaw runtime: skills are discovered and invoked by the OpenClaw platform, not by traditional API/HTTP calls
## Layers
- Purpose: Define agent identity, behavior, memory policy, and bootstrap sequence
- Location: project root (`AGENTS.md`, `BOOTSTRAP.md`, `SOUL.md`, `MEMORY.md`, `IDENTITY.md`, `HEARTBEAT.md`, `USER.md`)
- Contains: Agent roles, fixed read order, write-back boundaries, safety rules, proactive service triggers
- Depends on: Nothing
- Used by: OpenClaw runtime, all skills and scripts
- Purpose: Define multi-agent team topology, routing rules, privacy defaults, heartbeat cadence
- Location: `configs/openclaw.health.json5`
- Contains: Agent list (10 agents), route table mapping scenarios to specialist roles, privacy defaults, web-assist policy, package matrix
- Depends on: Workspace configuration layer
- Used by: OpenClaw runtime for agent dispatch and policy enforcement
- Purpose: Provide reusable Python classes that skills, scenarios, and scripts depend on
- Location: `skills/_shared/`
- Contains: 36 Python modules including data store, memory writer, heartbeat, scenario runtime, team runtime, cross-skill reader, reminder center, patient archive bridge, timeline builder, visit workflow, memory distiller
- Depends on: Workspace configuration (reads memory paths), data layer
- Used by: Individual skills, scenario scripts, operations scripts, tests
- `health_data_store.py` (HealthDataStore): JSONL-backed structured record storage with file locking, per-skill data directories under `data/`
- `health_memory.py` (HealthMemoryWriter): Writes skill outputs to shared markdown-based health memory under `memory/health/`
- `health_heartbeat.py` (HealthHeartbeat): Proactive missing-data checks and reminder generation
- `health_scenario_runtime.py` (HealthScenarioRuntime): Consistent scenario output rendering with six-layer output format
- `health_team_runtime.py`: Chief-led multi-agent orchestration with role definitions, privacy tiers, task dispatch
- `health_operations.py` (HealthOperationsRunner): Automation-oriented runner combining heartbeat, distiller, weekly digest, timeline builder
- `cross_skill_reader.py` (CrossSkillReader): Registry-driven read-through helper for aggregating data across skills
- `health_reminder_center.py` (HealthReminderCenter): Stateful task/reminder management with priority and follow-up cadence
- `health_flagship_scenarios.py`: Productized end-to-end scenario classes (HypertensionDailyCopilot, DiabetesControlHub, AnnualCheckupAdvisorWorkflow)
- `health_visit_workflow.py` (HealthVisitWorkflow): Pre-visit briefing and post-visit follow-up generation
- `health_timeline_builder.py` (HealthTimelineBuilder): Unified timeline merging archive, Apple Health, items, and digests
- `health_memory_distiller.py` (HealthMemoryDistiller): Summarizes recent health operations into long-term MEMORY.md
- `patient_archive_bridge.py` (PatientArchiveBridge): Bridges patient archives from `~/.openclaw/patients/` into workspace memory
- `concept_resolver.py` (ConceptResolver): Resolves health concepts via `schemas/health-concepts.yaml` registry
- Purpose: Self-contained health capabilities, each in its own directory with a `SKILL.md` prompt file
- Location: `skills/` (222 skill directories + `_shared/`)
- Contains: `SKILL.md` (prompt with YAML frontmatter), optional Python implementation, optional `scripts/`, optional `references/`
- Depends on: Shared runtime layer, data layer
- Used by: OpenClaw runtime (discovers and invokes skills based on user intent)
- `health` (37): Core trackers (blood-pressure, caffeine, sleep, weight, medications, supplements, etc.)
- `health-scenario` (15): Orchestrated multi-skill workflows (annual-checkup-advisor, diabetes-control-hub, hypertension-daily-copilot, etc.)
- `health-analyzer` (14): Data analysis and trend detection (fitness-analyzer, goal-analyzer, health-trend-analyzer, etc.)
- `medical-research` (9): Bioinformatics and clinical research tools
- `health-records` (2): Medical record management and timeline
- Out-of-scope (142): Biomedical databases, clinical tools, research utilities not governed in Iteration 1
- Purpose: Persistent structured health data and memory files
- Location: `data/` (JSONL per-skill), `memory/health/` (markdown)
- Contains: JSONL records under `data/{skill-name}/`, markdown daily logs, item files, weekly/monthly/quarterly digests, heartbeat state, team artifacts
- Depends on: Nothing (filesystem)
- Used by: All skills and scripts via HealthDataStore and HealthMemoryWriter
- Purpose: CLI entry points for automation, workspace initialization, operations, and build
- Location: `scripts/`
- Contains: 29 Python scripts and 1 shell script
- Depends on: Shared runtime layer
- Used by: Users, cron/automation, CI
- Purpose: Starter workspace configurations for different use cases
- Location: `templates/`
- Contains: 3 agent templates (health-agent, health-family-agent, health-research-agent) with pre-initialized memory directories
- Depends on: Workspace configuration conventions
- Used by: `scripts/init_health_workspace.py`
- Purpose: Package skill sets into distributable bundles
- Location: `packages/` (manifests), `dist/` (built output)
- Contains: 4 package manifests (vitaclaw-core, vitaclaw-family-care, vitaclaw-labs, vitaclaw-oncology) and corresponding built directories
- Depends on: All other layers
- Used by: `scripts/build_vitaclaw_release.py`
## Data Flow
- No in-memory state between sessions; all state persisted to filesystem
- JSONL files in `data/` for structured records (append-only with file locking via `fcntl`)
- Markdown files in `memory/health/` for human-readable longitudinal tracking
- Task state in `memory/health/heartbeat/` for proactive service continuity
## Key Abstractions
- Purpose: Self-contained prompt file defining one health capability
- Examples: `skills/blood-pressure-tracker/SKILL.md`, `skills/caffeine-tracker/SKILL.md`, `skills/annual-checkup-advisor/SKILL.md`
- Pattern: YAML frontmatter (name, description, version, user-invocable, allowed-tools, metadata) followed by markdown prompt body
- Purpose: JSONL-backed structured record storage with standard envelope format
- Examples: `skills/_shared/health_data_store.py`
- Pattern: Every record has `{id, type, timestamp, skill, data}` envelope. Records appended with file locking.
- Purpose: Write skill outputs into shared markdown-based health memory
- Examples: `skills/_shared/health_memory.py`
- Pattern: Manages paths for daily/, items/, files/, heartbeat/, team/ directories. Handles section insertion and update in markdown files.
- Purpose: Single source of truth mapping concept IDs to producer/consumer skills, LOINC codes, field schemas, and plausible ranges
- Examples: `schemas/health-concepts.yaml`
- Pattern: Registry-driven discovery. Adding a new concept to the YAML makes it automatically discoverable by `CrossSkillReader.read()`.
- Purpose: Standardized health-facing output structure
- Examples: `skills/_shared/health_scenario_runtime.py` (DEFAULT_SECTION_ORDER)
- Pattern: Every health output maps to: Record, Interpretation, Trend, Risk, Advice, Must-See-Doctor
- Purpose: Define specialist agent capabilities, permissions, and write boundaries
- Examples: `skills/_shared/health_team_runtime.py` (ROLE_DEFINITIONS)
- Pattern: Each role has label, package, tool_policy, sandbox, can_write list, long_term_memory access, tone
## Entry Points
- Location: `BOOTSTRAP.md`
- Triggers: Agent entering workspace
- Responsibilities: Load SOUL.md, MEMORY.md, health profile, recent daily files, determine proactive tasks
- Location: `scripts/run_health_chief_of_staff.py` - Chief-led team orchestration
- Location: `scripts/run_health_heartbeat.py` - Proactive health checks
- Location: `scripts/run_health_operations.py` - Automated maintenance (heartbeat + digest + distill + timeline)
- Location: `scripts/run_hypertension_daily_copilot.py` - Hypertension scenario
- Location: `scripts/run_diabetes_control_hub.py` - Diabetes scenario
- Location: `scripts/run_annual_checkup_advisor.py` - Annual checkup scenario
- Location: `scripts/init_health_workspace.py` - Workspace initialization from templates
- Location: `scripts/build_vitaclaw_release.py` - Package builder
- Location: `scripts/build_skills_manifest.py` - Generate `skills-manifest.json`
- Location: `configs/com.vitaclaw.heartbeat.plist` - macOS launchd plist for heartbeat scheduler
- Location: `scripts/setup_heartbeat_scheduler.sh` - Scheduler installation
## Error Handling
- Skills never make explicit diagnoses or direct prescription adjustments
- Six-layer output always includes "must-see-doctor" when red-flag signals detected
- `health-safety` role handles risk escalation and boundary control
- High-risk items (critical vitals, acute symptoms) force escalation regardless of normal flow
- Missing data results in explicit "insufficient to judge" statements rather than guesses
## Cross-Cutting Concerns
- `MEMORY.md` only loaded in direct chats
- `health-research` role cannot access MEMORY.md or raw patient archives
- Public agents cannot read patient archives
- Group/public contexts never auto-load long-term memory
- `privacy_desensitize.py` at project root for data desensitization
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
