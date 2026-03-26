# Project Research Summary

**Project:** VitaClaw Iteration 2
**Domain:** Personal health record / AI-native health skill library
**Researched:** 2026-03-26
**Confidence:** MEDIUM-HIGH

## Executive Summary

VitaClaw Iteration 2 extends an existing 222-skill health AI system with four major capabilities: medical document OCR, multi-device wearable data import, health visualization with cross-metric correlation, and family multi-person support. The existing architecture -- a file-based, local-first skill library running on OpenClaw with JSONL data storage and markdown memory -- is sound and extensible. The recommended approach is to build on the existing patterns (especially the Apple Health importer as a reference implementation) rather than introduce new frameworks or paradigms.

The most impactful architectural decision is threading `person_id` through the entire data layer early. This cross-cutting change affects HealthDataStore, HealthMemoryWriter, CrossSkillReader, and all 36+ shared modules. Doing it late means a painful retrofit; doing it early means every subsequent feature (OCR, device import, visualization) gets multi-person support for free. The second critical decision is enforcing a confirm-before-write contract for OCR -- medical data accuracy is non-negotiable, and auto-committing misread lab values is a safety risk.

The primary risks are: (1) Chinese medical document OCR accuracy on tables and handwriting, which requires PP-StructureV2 table recognition beyond basic text OCR; (2) cross-device data deduplication, where fuzzy matching is needed instead of exact hash comparison; and (3) spurious correlations in cross-metric analysis that could lead to harmful health conclusions. All three are solvable with the identified mitigations but require deliberate engineering -- they will not work correctly with naive implementations.

## Key Findings

### Recommended Stack

The stack is conservative by design: extend existing dependencies rather than introduce new ones. Python >= 3.11 is recommended (up from 3.10+) because Python 3.10 hits EOL in October 2026 and pandas 3.x requires 3.11. No new heavy dependencies are needed -- PaddleOCR, matplotlib, pandas, and scipy cover all requirements.

**Core technologies:**
- **PaddleOCR >= 3.4.0**: Medical document OCR with PP-OCRv5 and PP-StructureV2 table extraction -- already a project dependency, best-in-class for Chinese medical documents
- **pandas >= 2.2.3**: Time series normalization, resampling, and correlation -- already a dependency, handles all multi-device data alignment
- **matplotlib >= 3.10**: Static trend charts (PNG/SVG) for terminal/markdown output -- already a dependency, no browser runtime needed
- **scipy >= 1.13**: Statistical correlation with p-values -- lightweight addition for correlation analysis confidence scoring
- **pytest >= 8.0 + ruff >= 0.9**: Engineering foundation -- pytest replaces unittest (backward compatible), ruff replaces flake8+black+isort at 100x speed

**Key exclusions:** No Plotly/Seaborn (browser dependency), no cloud OCR APIs (violates local-first), no OAuth sync (complexity, deprecated APIs), no statsmodels (30MB for one function), no polars (migration cost exceeds performance benefit at this data scale).

### Expected Features

**Must have (table stakes):**
- T1: Medical document OCR (photo to structured data) -- every PHR competitor supports scan-and-store
- T2: OCR result confirmation before storage -- safety-critical, no health app auto-commits OCR results
- T3: Google Fit data import (file-based) -- establishes the multi-device import pattern
- T4: Health trend visualization (BP, glucose, weight, sleep charts) -- users need to see their data
- T5: Doctor-ready visit summary (Markdown + HTML + optional PDF) -- direct user-facing value before every visit
- T6: User onboarding / cold start profile -- without guided setup, 222 skills are overwhelming
- T7: Multi-person data isolation -- family health managers need strict per-person separation

**Should have (differentiators):**
- D1: Cross-metric correlation analysis -- VitaClaw's biggest differentiator vs. single-metric apps
- D2: Annual health report ("Health Wrapped") -- emerging category, no established competitor
- D3: AI-powered OCR field extraction with medical concept mapping -- no consumer PHR does concept-level medical OCR
- D4/D5: Huawei + Xiaomi import -- expands Chinese user coverage using the same import architecture

**Defer (v2+):**
- D6: Conversational profiling -- nice polish, but structured onboarding is sufficient
- D7: Proactive correlation alerts -- needs mature correlation engine and alert fatigue tuning

### Architecture Approach

The four new capabilities slot into the existing layered architecture without structural rewrites. New shared modules go in `skills/_shared/`, new skills in `skills/`, new CLI scripts in `scripts/`. The critical structural change is a `PersonContext` abstraction that threads through all data-accessing code. Data isolation uses a `person_id` field in JSONL records (not separate files per person) with per-person memory subdirectories. The default "self" person keeps existing paths for zero-migration backward compatibility.

**Major components:**
1. **OCR Pipeline** (`health_ocr_pipeline.py`) -- Document type classification, PaddleOCR extraction, field structuring, confirm-before-write workflow
2. **Device Importer Base** (`device_importer_base.py`) -- Abstract base class with dedup, concept mapping, and JSONL output following the Apple Health importer pattern
3. **Person Context Manager** (`person_context.py`) -- Person registry, context resolution from conversation, path helpers for per-person data/memory
4. **Visualization Engine** (`health_chart_engine.py`) -- Composable chart functions (trend, correlation, dashboard) with per-metric clinical configurations
5. **HealthDataStore** (modified) -- `person_id` in record envelope, fuzzy dedup for cross-device imports

### Critical Pitfalls

1. **OCR auto-commit without confirmation** -- Misread lab values silently corrupt the health store. Prevention: staging records with confidence scores, mandatory user confirmation step, confidence threshold warnings below 0.85.
2. **Cross-device deduplication false negatives** -- Same metric from Apple Watch and Mi Band creates doubled entries (timestamps differ by seconds, values by noise). Prevention: fuzzy dedup with configurable time window (5 min) and value margin, `source_device` field, time-range overlap detection for sleep/workout.
3. **Family member data leaks** -- 36 shared modules have no person context; data gets written to wrong person's directory. Prevention: `PersonContext` abstraction threaded through all data accessors, error on missing context when family mode is enabled, integration tests for data isolation.
4. **Chinese medical document table extraction failure** -- PaddleOCR text mode returns flat text without table structure; lab results lose key-value pairing. Prevention: PP-StructureV2 for table detection, template matching for common Chinese lab report formats, handwriting flagged for manual entry.
5. **Visualization with wrong clinical context** -- Auto-scaled axes make normal fluctuations look alarming or concerning trends look flat. Prevention: per-metric chart configs with fixed y-axis ranges, normal range bands, CJK font configuration.

## Implications for Roadmap

Based on combined research, six phases are recommended. The ordering is driven by: (a) the `person_id` threading must happen before any feature that writes data, (b) device importers are simpler than OCR and validate data ingestion patterns, (c) visualization is a pure data consumer and benefits from more data sources being available.

### Phase 1: Engineering Foundation
**Rationale:** Everything else builds on stable tooling and centralized path management. The `pyproject.toml` migration, CI pipeline, and path centralization in `health_memory.py` / `health_heartbeat.py` must happen first. Without centralized paths, multi-person support becomes a rewrite.
**Delivers:** `pyproject.toml` with optional dependency groups, pytest + ruff + pre-commit configuration, CI via GitHub Actions, centralized path construction in shared modules.
**Addresses:** Engineering prerequisites for all features.
**Avoids:** Pitfall 8 (memory/heartbeat path breakage), Pitfall 12 (JSONL performance -- partition structure).

### Phase 2: Person Context + Data Layer
**Rationale:** Cross-cutting concern that affects every subsequent phase. Threading `person_id` through HealthDataStore, HealthMemoryWriter, and CrossSkillReader early means OCR, importers, and visualization all get multi-person support automatically. Retrofitting this later touches 36+ shared modules.
**Delivers:** PersonContextManager, modified HealthDataStore with `person_id` envelope field, per-person memory paths, backward-compatible "self" default, family registry.
**Addresses:** T7 (multi-person data isolation -- infrastructure layer).
**Avoids:** Pitfall 3 (data leaks through shared code paths), Pitfall 8 (memory path breakage).

### Phase 3: Onboarding + Device Importers
**Rationale:** Onboarding (T6) gives new users a starting point. Google Fit import (T3) establishes the importer pattern that Huawei/Xiaomi reuse. These are medium-complexity features with well-understood file formats that validate the data layer changes from Phase 2.
**Delivers:** Cold-start onboarding flow, DeviceImporterBase, Google Fit importer (CLI + skill), Huawei importer, Xiaomi importer, fuzzy cross-device deduplication.
**Addresses:** T6 (onboarding), T3 (Google Fit), D4 (Huawei), D5 (Xiaomi).
**Avoids:** Pitfall 2 (dedup false negatives -- fuzzy dedup designed before second importer), Pitfall 5 (format changes -- schema version detection from day one).

### Phase 4: OCR Pipeline
**Rationale:** OCR is the most complex new capability. Building it after device importers means the data ingestion patterns (concept mapping, dedup, person_id attribution) are proven. PaddleOCR is already a dependency; the gap is the end-to-end pipeline with table extraction and confirmation workflow.
**Delivers:** Document type classifier, PP-StructureV2 table extraction, per-type field extractors (lab report, physical exam, prescription), confirm-before-write workflow, image preprocessing (deskew, contrast, resize), OCR confidence scoring.
**Addresses:** T1 (OCR basic), T2 (OCR confirmation), D3 (AI-powered field extraction with concept mapping).
**Avoids:** Pitfall 1 (OCR auto-commit), Pitfall 4 (table extraction failure), Pitfall 9 (preprocessing ignored).

### Phase 5: Visualization + Visit Summaries
**Rationale:** Pure data consumer. More data sources from Phases 3-4 mean richer charts. Per-metric clinical configurations (axis ranges, normal bands) are critical for medical correctness. Visit summaries embed charts, so visualization must be ready first.
**Delivers:** HealthChartEngine with trend/correlation/dashboard chart types, per-metric clinical configs, CJK font handling, enhanced visit briefing (Markdown + HTML + PDF), chart embedding in briefings.
**Addresses:** T4 (trend visualization), T5 (visit summary), D1 (cross-metric correlation).
**Avoids:** Pitfall 6 (wrong clinical context in charts), Pitfall 7 (spurious correlations -- minimum sample sizes, clinical plausibility filter, causation disclaimers).

### Phase 6: Advanced Features + Family UX
**Rationale:** Requires stable single-user experience and mature data layer. Annual reports need 6+ months of data. Proactive alerts need tuned correlation engine. Family UX ties all infrastructure together with per-person onboarding, dashboards, and briefings.
**Delivers:** Annual health report (HTML), family onboarding flow, family dashboard, proactive correlation alerts (integrated with heartbeat), per-person visit briefings.
**Addresses:** T7 (family UX layer), D2 (annual report), D7 (proactive alerts).
**Avoids:** Pitfall 10 (misleading year-over-year comparisons -- sample size disclosure), Pitfall 11 (irrelevant visit briefing data -- department filtering).

### Phase Ordering Rationale

- **Engineering Foundation first** because path centralization and CI prevent cascading breakage in all subsequent phases.
- **Person Context before features** because it is a cross-cutting concern. Every data-writing feature benefits from `person_id` being in place. The alternative -- adding person support after features are built -- means rewriting every feature.
- **Device importers before OCR** because importers are simpler (well-defined file formats vs. computer vision) and validate the data ingestion architecture. OCR can then reuse proven patterns.
- **Visualization after data sources** because charts are more useful with more data. Building charts first means testing with limited data.
- **Family UX last** because it is a composition layer. It combines person context + importers + OCR + visualization into a cohesive multi-person experience. All building blocks must exist first.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (OCR Pipeline):** Chinese medical document table extraction with PP-StructureV2 needs hands-on testing with real documents. Template matching for common lab report formats requires sample collection. PaddleOCR installation on Apple Silicon needs verification.
- **Phase 5 (Visualization -- correlation):** Cross-metric correlation analysis is statistically nuanced. Determining clinically meaningful metric pairs, appropriate lag windows, and minimum sample sizes needs domain research. Risk of shipping misleading analysis is high.
- **Phase 3 (Device Importers -- Huawei/Xiaomi):** Export formats are poorly documented and change without warning. Need real export files from each platform for parser development and testing.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Engineering Foundation):** pyproject.toml, pytest, ruff, CI are thoroughly documented. No unknowns.
- **Phase 2 (Person Context):** Architecture is fully specified in ARCHITECTURE.md. Implementation is straightforward file-system organization + parameter threading.
- **Phase 5 (Visualization -- charting):** matplotlib time-series charting is well-documented. The main risk (CJK fonts, clinical ranges) is addressed in pitfalls research.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies already in project or have verified PyPI versions. No speculative choices. |
| Features | HIGH | Table stakes validated against 6+ competitor apps. Feature dependencies mapped clearly. |
| Architecture | HIGH | Based on direct codebase analysis. Patterns follow existing Apple Health importer reference. |
| Pitfalls | MEDIUM-HIGH | Critical pitfalls identified from codebase inspection and domain literature. Medical document OCR accuracy needs real-world validation. |

**Overall confidence:** MEDIUM-HIGH. Stack and architecture are well-grounded in existing code. Features are validated against competitors. The main uncertainty is in OCR accuracy on real Chinese medical documents and the stability of third-party device export formats.

### Gaps to Address

- **Chinese medical document samples:** Need 5+ real document types (blood test, imaging, prescription, outpatient summary, discharge summary) for OCR pipeline testing. Cannot validate table extraction without real samples.
- **Huawei/Xiaomi export format verification:** Documented formats may differ from actual exports by region and app version. Need real export files from Chinese-region devices.
- **Cross-metric clinical plausibility:** Which metric pairs have clinically meaningful correlations? What lag windows are appropriate? Needs domain expert input or medical literature review during Phase 5 planning.
- **PaddleOCR Apple Silicon installation:** PaddlePaddle ARM64 wheels may lag behind. Need early testing on macOS ARM64 to catch installation issues before OCR phase begins.
- **JSONL performance at scale:** The performance impact of 2.7M+ records with multi-person, multi-device data is theoretical. May need benchmarking during Phase 2 to validate partitioning strategy.

## Sources

### Primary (HIGH confidence)
- PaddleOCR GitHub releases and PyPI -- OCR capabilities, PP-OCRv5, version compatibility
- pandas/matplotlib/scipy PyPI -- version requirements, Python compatibility
- Existing codebase analysis -- `health_data_store.py`, `apple_health_bridge.py`, `health_memory.py`, `family_manager.py`, `redact_ocr.py`
- PROJECT.md key decisions -- OCR confirm-before-write, family single-workspace isolation, file-based import
- Python Packaging User Guide -- pyproject.toml best practices

### Secondary (MEDIUM confidence)
- Google Fit Takeout, Huawei Health, Xiaomi Mi Fitness export documentation -- formats verified via official docs but may vary by region/version
- Competitor app analysis (CareClinic, MediTrack, SmartBP, FAMHLTH) -- feature validation
- PaddleOCR table recognition discussions -- PP-StructureV2 capability assessment
- Healthcare data visualization best practices (PMC, KMS Technology)

### Tertiary (LOW confidence)
- Annual health report ("Health Wrapped") category -- emerging, no established best practices
- Cross-metric correlation clinical significance thresholds -- needs domain expert validation
- Xiaomi/Huawei export format stability -- anecdotal evidence of format changes

---
*Research completed: 2026-03-26*
*Ready for roadmap: yes*
