# Architecture

**Analysis Date:** 2026-03-26

## Pattern Overview

**Overall:** Chief-led multi-agent skill library with markdown-based memory and JSONL data storage

**Key Characteristics:**
- Skill-based modular architecture: 222+ self-contained `SKILL.md` files, each defining a health domain capability
- Chief-led orchestration: a single entry agent (`health-chief-of-staff`) routes tasks to specialist agents
- Local-first, file-based: all data stored as markdown and JSONL on the local filesystem, no external database
- Layered memory system: daily -> weekly -> monthly -> quarterly -> MEMORY.md distillation chain
- Designed for OpenClaw runtime: skills are discovered and invoked by the OpenClaw platform, not by traditional API/HTTP calls

## Layers

**Workspace Configuration Layer:**
- Purpose: Define agent identity, behavior, memory policy, and bootstrap sequence
- Location: project root (`AGENTS.md`, `BOOTSTRAP.md`, `SOUL.md`, `MEMORY.md`, `IDENTITY.md`, `HEARTBEAT.md`, `USER.md`)
- Contains: Agent roles, fixed read order, write-back boundaries, safety rules, proactive service triggers
- Depends on: Nothing
- Used by: OpenClaw runtime, all skills and scripts

**Agent Configuration Layer:**
- Purpose: Define multi-agent team topology, routing rules, privacy defaults, heartbeat cadence
- Location: `configs/openclaw.health.json5`
- Contains: Agent list (10 agents), route table mapping scenarios to specialist roles, privacy defaults, web-assist policy, package matrix
- Depends on: Workspace configuration layer
- Used by: OpenClaw runtime for agent dispatch and policy enforcement

**Shared Runtime Layer:**
- Purpose: Provide reusable Python classes that skills, scenarios, and scripts depend on
- Location: `skills/_shared/`
- Contains: 36 Python modules including data store, memory writer, heartbeat, scenario runtime, team runtime, cross-skill reader, reminder center, patient archive bridge, timeline builder, visit workflow, memory distiller
- Depends on: Workspace configuration (reads memory paths), data layer
- Used by: Individual skills, scenario scripts, operations scripts, tests

**Key shared modules:**
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

**Skills Layer:**
- Purpose: Self-contained health capabilities, each in its own directory with a `SKILL.md` prompt file
- Location: `skills/` (222 skill directories + `_shared/`)
- Contains: `SKILL.md` (prompt with YAML frontmatter), optional Python implementation, optional `scripts/`, optional `references/`
- Depends on: Shared runtime layer, data layer
- Used by: OpenClaw runtime (discovers and invokes skills based on user intent)

**Skill categories:**
- `health` (37): Core trackers (blood-pressure, caffeine, sleep, weight, medications, supplements, etc.)
- `health-scenario` (15): Orchestrated multi-skill workflows (annual-checkup-advisor, diabetes-control-hub, hypertension-daily-copilot, etc.)
- `health-analyzer` (14): Data analysis and trend detection (fitness-analyzer, goal-analyzer, health-trend-analyzer, etc.)
- `medical-research` (9): Bioinformatics and clinical research tools
- `health-records` (2): Medical record management and timeline
- Out-of-scope (142): Biomedical databases, clinical tools, research utilities not governed in Iteration 1

**Data Layer:**
- Purpose: Persistent structured health data and memory files
- Location: `data/` (JSONL per-skill), `memory/health/` (markdown)
- Contains: JSONL records under `data/{skill-name}/`, markdown daily logs, item files, weekly/monthly/quarterly digests, heartbeat state, team artifacts
- Depends on: Nothing (filesystem)
- Used by: All skills and scripts via HealthDataStore and HealthMemoryWriter

**Scripts Layer:**
- Purpose: CLI entry points for automation, workspace initialization, operations, and build
- Location: `scripts/`
- Contains: 29 Python scripts and 1 shell script
- Depends on: Shared runtime layer
- Used by: Users, cron/automation, CI

**Templates Layer:**
- Purpose: Starter workspace configurations for different use cases
- Location: `templates/`
- Contains: 3 agent templates (health-agent, health-family-agent, health-research-agent) with pre-initialized memory directories
- Depends on: Workspace configuration conventions
- Used by: `scripts/init_health_workspace.py`

**Release/Distribution Layer:**
- Purpose: Package skill sets into distributable bundles
- Location: `packages/` (manifests), `dist/` (built output)
- Contains: 4 package manifests (vitaclaw-core, vitaclaw-family-care, vitaclaw-labs, vitaclaw-oncology) and corresponding built directories
- Depends on: All other layers
- Used by: `scripts/build_vitaclaw_release.py`

## Data Flow

**Health Data Recording Flow:**

1. User provides health data (e.g., blood pressure reading) via conversation
2. OpenClaw runtime matches intent to a skill (e.g., `skills/blood-pressure-tracker/`)
3. Skill's Python implementation (e.g., `blood_pressure_tracker.py`) processes input
4. `HealthDataStore.append()` writes a JSONL record to `data/{skill-name}/{skill-name}.jsonl`
5. `HealthMemoryWriter` updates markdown in `memory/health/daily/YYYY-MM-DD.md` and `memory/health/items/{item}.md`

**Scenario Orchestration Flow:**

1. User triggers a scenario (e.g., "hypertension daily copilot")
2. `health-chief-of-staff` routes to specialist roles via route table in `configs/openclaw.health.json5`
3. `HealthScenarioRuntime` coordinates multiple skills (e.g., BP tracker + medication + DASH diet + exercise)
4. Each skill reads via `CrossSkillReader` and writes via `HealthDataStore`
5. Scenario produces six-layer output (record, interpretation, trend, risk, advice, must-see-doctor)
6. Follow-up tasks written to `memory/health/heartbeat/task-board.md`

**Heartbeat / Proactive Service Flow:**

1. Heartbeat triggers on schedule (configurable per-role, e.g., every 30m for chief)
2. `HealthHeartbeat.run()` checks for missing daily records, overdue appointments, threshold violations
3. `HealthReminderCenter` manages task state with priority and deduplication
4. Missing/urgent items surface as tasks on `memory/health/heartbeat/task-board.md`
5. High-priority items trigger isolated sessions; low-priority items wait for next check

**Memory Distillation Flow:**

1. Daily logs accumulate in `memory/health/daily/`
2. `WeeklyHealthDigest` summarizes weekly trends into `memory/health/weekly/`
3. Monthly and quarterly summaries roll up further
4. `HealthMemoryDistiller` promotes stable conclusions to `MEMORY.md`
5. Behavior plans and execution barriers must pass through weekly/monthly before reaching MEMORY.md

**Patient Archive Bridge Flow:**

1. Patient medical records stored in `~/.openclaw/patients/{patient-id}/`
2. `PatientArchiveBridge` reads archive INDEX.md, timeline.md, and structured files
3. Minimal summaries synced to `memory/health/files/patient-archive-summary.md`
4. `HealthTimelineBuilder` merges archive data with workspace items and Apple Health data into unified timeline

**State Management:**
- No in-memory state between sessions; all state persisted to filesystem
- JSONL files in `data/` for structured records (append-only with file locking via `fcntl`)
- Markdown files in `memory/health/` for human-readable longitudinal tracking
- Task state in `memory/health/heartbeat/` for proactive service continuity

## Key Abstractions

**SKILL.md:**
- Purpose: Self-contained prompt file defining one health capability
- Examples: `skills/blood-pressure-tracker/SKILL.md`, `skills/caffeine-tracker/SKILL.md`, `skills/annual-checkup-advisor/SKILL.md`
- Pattern: YAML frontmatter (name, description, version, user-invocable, allowed-tools, metadata) followed by markdown prompt body

**HealthDataStore:**
- Purpose: JSONL-backed structured record storage with standard envelope format
- Examples: `skills/_shared/health_data_store.py`
- Pattern: Every record has `{id, type, timestamp, skill, data}` envelope. Records appended with file locking.

**HealthMemoryWriter:**
- Purpose: Write skill outputs into shared markdown-based health memory
- Examples: `skills/_shared/health_memory.py`
- Pattern: Manages paths for daily/, items/, files/, heartbeat/, team/ directories. Handles section insertion and update in markdown files.

**Health Concepts Registry:**
- Purpose: Single source of truth mapping concept IDs to producer/consumer skills, LOINC codes, field schemas, and plausible ranges
- Examples: `schemas/health-concepts.yaml`
- Pattern: Registry-driven discovery. Adding a new concept to the YAML makes it automatically discoverable by `CrossSkillReader.read()`.

**Six-Layer Output:**
- Purpose: Standardized health-facing output structure
- Examples: `skills/_shared/health_scenario_runtime.py` (DEFAULT_SECTION_ORDER)
- Pattern: Every health output maps to: Record, Interpretation, Trend, Risk, Advice, Must-See-Doctor

**Role Definitions:**
- Purpose: Define specialist agent capabilities, permissions, and write boundaries
- Examples: `skills/_shared/health_team_runtime.py` (ROLE_DEFINITIONS)
- Pattern: Each role has label, package, tool_policy, sandbox, can_write list, long_term_memory access, tone

## Entry Points

**Workspace Bootstrap:**
- Location: `BOOTSTRAP.md`
- Triggers: Agent entering workspace
- Responsibilities: Load SOUL.md, MEMORY.md, health profile, recent daily files, determine proactive tasks

**CLI Scripts:**
- Location: `scripts/run_health_chief_of_staff.py` - Chief-led team orchestration
- Location: `scripts/run_health_heartbeat.py` - Proactive health checks
- Location: `scripts/run_health_operations.py` - Automated maintenance (heartbeat + digest + distill + timeline)
- Location: `scripts/run_hypertension_daily_copilot.py` - Hypertension scenario
- Location: `scripts/run_diabetes_control_hub.py` - Diabetes scenario
- Location: `scripts/run_annual_checkup_advisor.py` - Annual checkup scenario
- Location: `scripts/init_health_workspace.py` - Workspace initialization from templates
- Location: `scripts/build_vitaclaw_release.py` - Package builder
- Location: `scripts/build_skills_manifest.py` - Generate `skills-manifest.json`

**Scheduled Automation:**
- Location: `configs/com.vitaclaw.heartbeat.plist` - macOS launchd plist for heartbeat scheduler
- Location: `scripts/setup_heartbeat_scheduler.sh` - Scheduler installation

## Error Handling

**Strategy:** Conservative, fail-safe approach aligned with medical safety

**Patterns:**
- Skills never make explicit diagnoses or direct prescription adjustments
- Six-layer output always includes "must-see-doctor" when red-flag signals detected
- `health-safety` role handles risk escalation and boundary control
- High-risk items (critical vitals, acute symptoms) force escalation regardless of normal flow
- Missing data results in explicit "insufficient to judge" statements rather than guesses

## Cross-Cutting Concerns

**Logging:** No centralized logging framework. Audit trail maintained via `memory/health/team/audit/dispatch-log.jsonl` and `memory/health/files/write-audit.md`.

**Validation:** Skill frontmatter validated against `schemas/skill-frontmatter.schema.json`. Health data validated against plausible ranges in `schemas/health-concepts.yaml`. Script: `scripts/validate_skill_frontmatter.py`.

**Authentication:** No authentication system. Local-first design. Privacy enforced by role-level read/write permissions defined in `ROLE_DEFINITIONS` and `configs/openclaw.health.json5`.

**Privacy:** Multi-tier privacy model:
- `MEMORY.md` only loaded in direct chats
- `health-research` role cannot access MEMORY.md or raw patient archives
- Public agents cannot read patient archives
- Group/public contexts never auto-load long-term memory
- `privacy_desensitize.py` at project root for data desensitization

**Internationalization:** Bilingual (Chinese primary, English secondary). Output layers use Chinese labels. Documentation exists in both languages.

---

*Architecture analysis: 2026-03-26*
