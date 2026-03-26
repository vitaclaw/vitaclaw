# Milestones

## v1.0 Iteration 2 (Shipped: 2026-03-26)

**Phases completed:** 4 phases, 12 plans, 23 tasks

**Key accomplishments:**

- pyproject.toml with setuptools editable install, relative imports in skills/_shared/, package imports in tests, ruff passing
- person_id threaded through HealthDataStore, HealthMemoryWriter, CrossSkillReader with zero-cost migration and 31 comprehensive tests
- GitHub Actions CI workflow with pytest + ruff on push/PR, testing Python 3.11 and 3.12 matrix
- Conversational health onboarding SKILL.md that guides profile setup across USER.md, IDENTITY.md, and _health-profile.md with merge-update preservation
- HealthImporterBase with fuzzy dedup (60s/5%) and GoogleFitImporter parsing Takeout CSV + TCX into HealthDataStore JSONL
- Huawei Health (CSV/JSON/GPX) and Xiaomi/Mi Fitness (CSV) importers with defensive parsing, fuzzy dedup, and sleep stage breakdown
- OCR extraction pipeline for Chinese medical documents with PPStructureV3 table extraction, PP-OCRv5 text extraction, concept mapping, and staging-only output
- store_confirmed_fields() routes confirmed OCR fields to HealthDataStore with concept-based skill routing, provenance meta (source=ocr, archived_path), and confirm/edit/reject status handling
- Shared matplotlib chart engine generating clinically contextualized PNG trend charts for blood pressure (dual-line), blood glucose, weight (with moving average), and sleep (bar chart) with CJK font support
- Enhanced correlation engine with scipy Pearson+Spearman p-values, n>=14 minimum, Chinese NL insights, and CLI/SKILL.md entry points
- Doctor-ready visit summary generator with Jinja2 HTML template, base64 chart embedding, and MD/HTML/PDF multi-format output
- HealthAnnualReport class generating self-contained HTML year-in-review with 7 sections: metric trajectories (base64 charts), medication adherence heatmaps, event timeline from daily logs, Q1-vs-Q4 improvement analysis, correlation insights, and goals review

---
