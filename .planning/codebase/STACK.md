# Technology Stack

**Analysis Date:** 2026-03-26

## Languages

**Primary:**
- Python 3 - All scripts, shared runtime libraries, skill implementations, tests, and CLI tooling

**Secondary:**
- Shell (Bash/Zsh) - Bioinformatics workflow examples (`skills/variant-interpretation-acmg/bioSkills/*/examples/*.sh`), setup scripts (`scripts/setup_heartbeat_scheduler.sh`), web-access helpers (`skills/web-access/scripts/*.sh`)
- Markdown - Primary skill definition format (`SKILL.md` files), health memory storage, documentation
- JSON / JSON5 - Configuration (`configs/openclaw.health.json5`), manifests (`skills-manifest.json`), schemas (`schemas/*.schema.json`), package definitions (`packages/*.json`)
- YAML - Skill frontmatter inside `SKILL.md` files, parsed by `scripts/skill_catalog.py` using PyYAML

## Runtime

**Environment:**
- Python 3 (standard CPython, no version pinning detected)
- macOS (primary development/deployment target based on launchd plist at `configs/com.vitaclaw.heartbeat.plist`)

**Package Manager:**
- No project-level `requirements.txt`, `pyproject.toml`, or `setup.py` at the repo root
- Individual skills may declare their own dependency files within their directories
- Python dependencies are installed ad-hoc; the shared runtime (`skills/_shared/`) uses only stdlib + `requests` + `PyYAML` as hard dependencies

## Frameworks

**Core:**
- No web framework - This is not a web application. It is a skill library for the OpenClaw AI assistant platform
- OpenClaw Runtime - The host platform that discovers and executes `SKILL.md` files; VitaClaw is a plugin/skill library for it

**Testing:**
- `unittest` (Python stdlib) - All tests in `tests/` use `unittest.TestCase`

**Build/Dev:**
- Custom Python scripts for build/release tooling:
  - `scripts/build_skills_manifest.py` - Generates `skills-manifest.json` catalog
  - `scripts/build_vitaclaw_release.py` - Builds distributable release packages to `dist/`
  - `scripts/validate_skill_frontmatter.py` - Validates YAML frontmatter in `SKILL.md` files
  - `scripts/render_readme_catalog.py` - Generates README skill catalog sections
  - `scripts/smoke_test_skills.py` - Smoke tests across skills
  - `scripts/build_skill_governance_report.py` - Governance audit reporting

## Key Dependencies

**Critical (used across shared runtime):**
- `requests` - HTTP client for all external API calls (PubMed, FDA, ClinicalTrials.gov, Ensembl, KEGG, etc.)
- `PyYAML` (`yaml`) - Parsing SKILL.md frontmatter in `scripts/skill_catalog.py` and `skills/_shared/concept_resolver.py`

**Used by specific skills (optional, lazy-imported):**
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

**Environment:**
- `configs/openclaw.health.json5` - Master agent/team configuration (JSON5 format): defines agent roles, heartbeat intervals, team routing, privacy defaults, push delivery model
- `configs/com.vitaclaw.heartbeat.plist` - macOS launchd scheduled task for heartbeat (runs `scripts/run_health_heartbeat.py` every 7200 seconds)
- Environment variables used for API keys and push channel configuration (see INTEGRATIONS.md for full list)
- `VITACLAW_DATA_DIR` - Override for data storage root directory (defaults to `<repo>/data/`)

**Build:**
- `schemas/skill-frontmatter.schema.json` - JSON Schema for validating SKILL.md YAML frontmatter
- `schemas/health-data-record.schema.json` - JSON Schema for JSONL health data records
- `schemas/twin-knowledge-graph.schema.json` - JSON Schema for Digital Twin knowledge graph entries
- `packages/vitaclaw-core.json` - Core release package manifest (stable tier)
- `packages/vitaclaw-oncology.json` - Oncology release package manifest (restricted tier)
- `packages/vitaclaw-family-care.json` - Family care release package manifest
- `packages/vitaclaw-labs.json` - Experimental release package manifest (labs tier)

## Data Storage

**Format:**
- JSONL (JSON Lines) - Primary structured data format for health records, stored in `data/<skill-slug>/`
- Markdown files - Health memory (`memory/health/daily/*.md`, `memory/health/items/*.md`, `memory/health/weekly/*.md`, `memory/health/monthly/*.md`)
- JSON - Manifest, reports, schemas
- Patient archives stored at `~/.openclaw/patients/` (outside repo)

**No database required.** All data is file-based, local-first, and git-versioned.

## Platform Requirements

**Development:**
- Python 3 with `requests` and `PyYAML` installed
- macOS recommended (launchd integration, osascript notifications)
- Git for version control of health data

**Production:**
- OpenClaw-compatible AI runtime (Claude, GPT, Gemini, Llama supported)
- Local filesystem for data persistence
- Optional: Feishu bot credentials for push notifications
- Optional: Bark app for iOS push notifications
- Optional: macOS for native notification support

---

*Stack analysis: 2026-03-26*
