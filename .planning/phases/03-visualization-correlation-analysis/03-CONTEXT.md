# Phase 3: Visualization + Correlation Analysis - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Health trend visualization (blood pressure, blood glucose, weight, sleep) with clinical reference bands and CJK support, plus cross-metric correlation analysis that discovers patterns and presents them as natural language insights with statistical confidence.

</domain>

<decisions>
## Implementation Decisions

### Chart Engine
- **D-01:** Chart engine is a shared module `skills/_shared/health_chart_engine.py` that wraps matplotlib. It provides per-metric chart generators with pre-configured clinical reference bands, axis labels, and styling.
- **D-02:** CJK font configuration: detect system CJK fonts at runtime (SimHei, STHeiti, PingFang SC, Noto Sans CJK). Fall back to matplotlib's default if no CJK font found, with a warning. Font config is set once at module import via `matplotlib.rcParams`.
- **D-03:** Clinical reference range bands: Blood pressure (normal <120/80, elevated 120-129/<80, stage 1 130-139/80-89, stage 2 ≥140/≥90), Blood glucose fasting (normal 3.9-6.1 mmol/L, pre-diabetic 6.1-7.0, diabetic >7.0), Weight (no fixed band — show trend only), Sleep (7-9h recommended range band).
- **D-04:** Time range support: 7d, 30d, 90d, 1y. The engine accepts a `days` parameter and queries HealthDataStore accordingly. Default is 30d.
- **D-05:** Output: PNG files saved to `data/{skill-name}/charts/` directory. File naming: `{metric}_{person_id}_{days}d_{date}.png`. Charts are also displayable inline by the AI runtime.
- **D-06:** Blood pressure chart uses dual-line (systolic + diastolic) with shaded reference bands. Blood glucose uses single line with horizontal band. Sleep uses bar chart (duration per day). Weight uses line chart with trend line (moving average).

### Correlation Analysis
- **D-07:** Correlation engine enhances the existing `skills/_shared/correlation_engine.py`. It computes both Pearson (linear) and Spearman (rank) correlations between metric pairs.
- **D-08:** Minimum requirements: n ≥ 14 data points for both metrics in the analysis window. Significance threshold: p < 0.05. Results with p ≥ 0.05 are reported as "no significant correlation found."
- **D-09:** Natural language insight generation: template-based. Example: "过去90天，当睡眠时间 < 6小时时，次日空腹血糖平均升高 15%（p=0.03, n=42）". Insights are in Chinese, matching VitaClaw's user-facing language.
- **D-10:** Supported correlation pairs (pre-defined, not exhaustive): sleep↔blood_glucose, medication_timing↔blood_pressure, exercise↔weight, sleep↔blood_pressure, caffeine↔sleep. Users can also request custom pairs.
- **D-11:** Correlation results include: metric pair, correlation coefficient (r), p-value, sample size (n), direction (positive/negative), and a natural language summary. Output as both structured JSON and markdown.

### Skill Integration
- **D-12:** Visualization exposed as `skills/health-trend-chart/SKILL.md`. Correlation exposed as `skills/health-correlation-analyzer/SKILL.md`. Both are user-invocable.
- **D-13:** CLI scripts: `scripts/generate_health_chart.py` and `scripts/analyze_health_correlations.py` with argparse and --format markdown|json support.

### Claude's Discretion
- Exact matplotlib styling (colors, line widths, grid, margins)
- Whether to use scipy.stats or numpy for correlation computation
- Chart DPI and figure size defaults
- Whether correlation_engine.py needs refactoring or can be extended in place
- How to handle metrics with sparse data points (interpolation vs gaps)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Code
- `skills/_shared/correlation_engine.py` — Existing correlation engine to enhance
- `skills/_shared/health_data_store.py` — Data source for chart/correlation queries (person_id aware)
- `skills/caffeine-tracker/caffeine_tracker.py` — Existing matplotlib chart usage in VitaClaw

### Data Layer
- `schemas/health-concepts.yaml` — Health concept registry for metric names
- `data/blood-pressure-tracker/` — Example data directory with charts/ subdirectory pattern

### Research
- `.planning/research/STACK.md` — matplotlib recommendations, CJK font notes
- `.planning/research/PITFALLS.md` — CJK rendering pitfall, spurious correlation warnings

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `correlation_engine.py`: Already exists with basic correlation detection. Needs enhancement with statistical rigor (p-values, confidence levels).
- `caffeine_tracker.py`: Has matplotlib chart generation code — reference for styling patterns.
- `HealthDataStore.query()`: Accepts person_id and can filter by date range — direct data source for charts.

### Established Patterns
- Charts directories: `data/{skill-name}/charts/` already used by some skills
- CLI pattern: argparse with --format markdown|json
- Six-layer output applies to correlation insights (Record → Interpretation → Trend → Risk → Advice)

### Integration Points
- Chart engine reads from HealthDataStore via query()
- Correlation engine reads from HealthDataStore via query() for multiple metrics
- Both respect person_id for family member isolation
- Generated charts can be embedded in visit summaries (Phase 4)

</code_context>

<specifics>
## Specific Ideas

- Charts must work on macOS (primary platform) with CJK fonts — PingFang SC or STHeiti
- Correlation insights in Chinese, matching SOUL.md output conventions
- Pre-defined correlation pairs cover the most clinically meaningful relationships
- Blood pressure always dual-line (systolic/diastolic), never averaged

</specifics>

<deferred>
## Deferred Ideas

- **Proactive correlation alerts** (D7 from FEATURES.md) — v2, needs mature correlation engine first
- **Interactive chart exploration** — anti-feature, matplotlib static charts are sufficient

</deferred>

---

*Phase: 03-visualization-correlation-analysis*
*Context gathered: 2026-03-26*
