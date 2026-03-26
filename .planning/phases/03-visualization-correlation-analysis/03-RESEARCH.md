# Phase 3: Visualization + Correlation Analysis - Research

**Researched:** 2026-03-26
**Domain:** Health data visualization (matplotlib) + statistical correlation analysis (scipy)
**Confidence:** HIGH

## Summary

Phase 3 builds two interconnected capabilities: (1) a shared health chart engine that generates clinically contextualized trend charts for blood pressure, blood glucose, weight, and sleep, and (2) an enhanced correlation engine that computes statistically rigorous cross-metric correlations with natural language insight generation in Chinese.

The existing codebase provides strong foundations. `correlation_engine.py` already has Pearson correlation and daily value aggregation via `CrossSkillReader`, but lacks p-values, Spearman rank correlation, minimum sample enforcement (currently n >= 3, needs n >= 14), and natural language output. The `caffeine_tracker.py` demonstrates the established matplotlib charting pattern (Agg backend, figure creation, PNG save to `charts_dir`), which the new chart engine should follow. `HealthDataStore` already creates `charts/` subdirectories and supports `person_id` filtering.

**Primary recommendation:** Build `skills/_shared/health_chart_engine.py` as a module with per-metric chart generators, and enhance the existing `skills/_shared/correlation_engine.py` in place with scipy.stats for p-values. Use scipy.stats (already installed at 1.11.4) rather than hand-rolling statistical tests.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Chart engine is a shared module `skills/_shared/health_chart_engine.py` that wraps matplotlib. It provides per-metric chart generators with pre-configured clinical reference bands, axis labels, and styling.
- **D-02:** CJK font configuration: detect system CJK fonts at runtime (SimHei, STHeiti, PingFang SC, Noto Sans CJK). Fall back to matplotlib's default if no CJK font found, with a warning. Font config is set once at module import via `matplotlib.rcParams`.
- **D-03:** Clinical reference range bands: Blood pressure (normal <120/80, elevated 120-129/<80, stage 1 130-139/80-89, stage 2 >=140/>=90), Blood glucose fasting (normal 3.9-6.1 mmol/L, pre-diabetic 6.1-7.0, diabetic >7.0), Weight (no fixed band -- show trend only), Sleep (7-9h recommended range band).
- **D-04:** Time range support: 7d, 30d, 90d, 1y. The engine accepts a `days` parameter and queries HealthDataStore accordingly. Default is 30d.
- **D-05:** Output: PNG files saved to `data/{skill-name}/charts/` directory. File naming: `{metric}_{person_id}_{days}d_{date}.png`. Charts are also displayable inline by the AI runtime.
- **D-06:** Blood pressure chart uses dual-line (systolic + diastolic) with shaded reference bands. Blood glucose uses single line with horizontal band. Sleep uses bar chart (duration per day). Weight uses line chart with trend line (moving average).
- **D-07:** Correlation engine enhances the existing `skills/_shared/correlation_engine.py`. It computes both Pearson (linear) and Spearman (rank) correlations between metric pairs.
- **D-08:** Minimum requirements: n >= 14 data points for both metrics in the analysis window. Significance threshold: p < 0.05. Results with p >= 0.05 are reported as "no significant correlation found."
- **D-09:** Natural language insight generation: template-based. Example: "Past 90 days, when sleep < 6h, next-day fasting glucose averages 15% higher (p=0.03, n=42)". Insights are in Chinese, matching VitaClaw's user-facing language.
- **D-10:** Supported correlation pairs (pre-defined, not exhaustive): sleep<->blood_glucose, medication_timing<->blood_pressure, exercise<->weight, sleep<->blood_pressure, caffeine<->sleep. Users can also request custom pairs.
- **D-11:** Correlation results include: metric pair, correlation coefficient (r), p-value, sample size (n), direction (positive/negative), and a natural language summary. Output as both structured JSON and markdown.
- **D-12:** Visualization exposed as `skills/health-trend-chart/SKILL.md`. Correlation exposed as `skills/health-correlation-analyzer/SKILL.md`. Both are user-invocable.
- **D-13:** CLI scripts: `scripts/generate_health_chart.py` and `scripts/analyze_health_correlations.py` with argparse and --format markdown|json support.

### Claude's Discretion
- Exact matplotlib styling (colors, line widths, grid, margins)
- Whether to use scipy.stats or numpy for correlation computation
- Chart DPI and figure size defaults
- Whether correlation_engine.py needs refactoring or can be extended in place
- How to handle metrics with sparse data points (interpolation vs gaps)

### Deferred Ideas (OUT OF SCOPE)
- Proactive correlation alerts (D7 from FEATURES.md) -- v2, needs mature correlation engine first
- Interactive chart exploration -- anti-feature, matplotlib static charts are sufficient

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VIZ-01 | Trend charts for BP (dual-line), glucose, weight, sleep | Chart engine module with per-metric generators; caffeine_tracker.py as pattern reference |
| VIZ-02 | Clinically meaningful reference range bands | D-03 defines exact ranges; matplotlib `axhspan()` for shaded bands |
| VIZ-03 | CJK character rendering | D-02 font detection; PingFang HK and Heiti TC confirmed available on target macOS |
| VIZ-04 | Configurable time ranges (7d, 30d, 90d, 1y) | D-04; HealthDataStore.query() already supports start/end date filtering |
| CORR-01 | Cross-metric correlation analysis | Existing correlation_engine.py enhanced with scipy.stats; CrossSkillReader for data access |
| CORR-02 | Statistical confidence level and sample size | scipy.stats.pearsonr/spearmanr return (r, p-value); D-08 n>=14 threshold |
| CORR-03 | Natural language insights | D-09 template-based Chinese insight generation; template strings with f-string formatting |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| matplotlib | >= 3.8 (installed: 3.8.2, latest: 3.10.8) | Static chart generation | Already a project dependency. Agg backend for headless PNG generation. Established pattern in caffeine_tracker.py. |
| scipy | >= 1.11 (installed: 1.11.4, latest: 1.17.1) | Statistical correlation with p-values | `scipy.stats.pearsonr()` and `scipy.stats.spearmanr()` return (correlation, p-value) tuple. Already installed. |
| numpy | >= 1.26 (installed: 1.26.4) | Array operations, NaN handling | Indirect dependency via matplotlib/scipy. Used for moving averages in weight trend line. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | >= 2.2 (installed: 2.2.2) | Time series resampling, date alignment | Align irregular measurement timestamps to daily aggregates for correlation. Optional -- can use dict-based aggregation from existing correlation_engine.py. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scipy.stats | numpy manual Pearson + t-distribution | Loses p-value calculation; would need to hand-roll significance testing. Use scipy. |
| scipy.stats | pandas DataFrame.corr() | No p-values from pandas.corr(). Still need scipy for significance. |
| matplotlib | seaborn | Overkill for 4 chart types. Adds dependency for marginal styling benefit. |

**Installation:**
```bash
# Already in pyproject.toml [project.optional-dependencies] viz group
pip install "vitaclaw[viz]"
# scipy needs to be added to pyproject.toml
pip install scipy>=1.11
```

**Version note:** The installed matplotlib 3.8.2 is below the pyproject.toml spec (>=3.10). The code will work on 3.8.2, but consider upgrading. The pyproject.toml minimum should match what is actually tested -- recommend lowering to >=3.8 or upgrading the install.

## Architecture Patterns

### Recommended Project Structure
```
skills/
  _shared/
    health_chart_engine.py     # NEW: shared chart generation module
    correlation_engine.py      # ENHANCED: add scipy stats, p-values, NL insights
  health-trend-chart/
    SKILL.md                   # NEW: user-invocable skill definition
  health-correlation-analyzer/
    SKILL.md                   # NEW: user-invocable skill definition
scripts/
  generate_health_chart.py     # NEW: CLI for chart generation
  analyze_health_correlations.py  # NEW: CLI for correlation analysis
```

### Pattern 1: Chart Engine Module Design
**What:** A single Python module with a `HealthChartEngine` class providing per-metric chart methods.
**When to use:** Always -- this is the locked decision (D-01).

```python
# Source: Pattern derived from caffeine_tracker.py lines 263-350
import matplotlib
matplotlib.use("Agg")  # Must be before pyplot import
import matplotlib.pyplot as plt

class HealthChartEngine:
    """Shared chart engine for health metric visualization."""

    # CJK font detection at module level (D-02)
    _CJK_FONTS = ["PingFang HK", "Heiti TC", "Hiragino Sans GB",
                   "SimHei", "STHeiti", "PingFang SC", "Noto Sans CJK SC"]

    def __init__(self, data_dir: str | None = None, person_id: str | None = None):
        self.data_dir = data_dir
        self.person_id = person_id
        self._configure_fonts()

    def _configure_fonts(self):
        """Detect and configure CJK font. Called once."""
        import matplotlib.font_manager as fm
        available = {f.name for f in fm.fontManager.ttflist}
        for font in self._CJK_FONTS:
            if font in available:
                plt.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                return
        import sys
        print("[WARN] No CJK font found. Chinese labels may not render.", file=sys.stderr)

    def generate_blood_pressure_chart(self, days: int = 30) -> str:
        """Generate dual-line BP chart with reference bands."""
        ...

    def generate_blood_glucose_chart(self, days: int = 30) -> str:
        ...

    def generate_weight_chart(self, days: int = 30) -> str:
        ...

    def generate_sleep_chart(self, days: int = 30) -> str:
        ...
```

### Pattern 2: Clinical Reference Bands with axhspan
**What:** Shaded horizontal bands showing normal/elevated/concerning ranges.
**When to use:** Blood pressure, blood glucose, and sleep charts (D-03, D-06).

```python
# Blood pressure reference bands (D-03)
def _draw_bp_reference_bands(self, ax):
    ax.axhspan(0, 120, alpha=0.08, color="green", label="Normal (<120)")
    ax.axhspan(120, 130, alpha=0.08, color="gold", label="Elevated (120-129)")
    ax.axhspan(130, 140, alpha=0.08, color="orange", label="Stage 1 (130-139)")
    ax.axhspan(140, 300, alpha=0.08, color="red", label="Stage 2 (>=140)")
```

### Pattern 3: Correlation Engine Enhancement (In-Place)
**What:** Extend existing `CorrelationResult` and `CorrelationEngine` classes with p-values, Spearman, and NL insights.
**When to use:** Recommended approach -- existing code structure is clean enough to extend.

```python
# Enhancement to existing CorrelationResult
class CorrelationResult:
    def __init__(self, ..., p_value: float = 1.0, method: str = "pearson"):
        ...
        self.p_value = p_value
        self.method = method

    def is_significant(self) -> bool:
        return self.p_value < 0.05 and self.sample_count >= 14

    def to_natural_language(self) -> str:
        """Generate Chinese natural language insight (D-09)."""
        if not self.is_significant():
            return f"{self.concept_a} 与 {self.concept_b} 之间未发现显著相关性（p={self.p_value:.3f}, n={self.sample_count}）"
        direction_zh = "正相关" if self.direction == "positive" else "负相关"
        return (
            f"过去分析期间，{self.concept_a} 与 {self.concept_b} 存在{self.strength_zh}{direction_zh}"
            f"（r={self.correlation:.3f}, p={self.p_value:.3f}, n={self.sample_count}）"
        )
```

### Pattern 4: CLI Script Pattern (Established)
**What:** argparse with --format markdown|json, --data-dir, --person-id flags.
**When to use:** Both new CLI scripts (D-13).

```python
# Source: Established pattern from caffeine_tracker.py and existing CLI scripts
parser = argparse.ArgumentParser(description="Generate health trend charts")
parser.add_argument("--metric", required=True, choices=["bp", "glucose", "weight", "sleep"])
parser.add_argument("--days", type=int, default=30, choices=[7, 30, 90, 365])
parser.add_argument("--person-id", default=None)
parser.add_argument("--data-dir", default=None)
parser.add_argument("--format", default="markdown", choices=["markdown", "json"])
```

### Anti-Patterns to Avoid
- **Global rcParams mutation without reset:** `plt.rcParams` is global state. The chart engine should set CJK fonts once at init, not per-chart. If other matplotlib code runs in the same process, test that font settings don't conflict.
- **Auto-scaling y-axis for clinical metrics:** Blood pressure and glucose charts must have clinically meaningful y-axis ranges (see Pitfall 6 from PITFALLS.md). Never rely on matplotlib auto-scale for these metrics.
- **Correlating everything with everything:** Only compute pre-defined clinically plausible pairs (D-10). Computing all-pairs correlation on N metrics produces O(N^2) results with many spurious findings.
- **Interpolating across large data gaps:** If a metric has no data for >3 days, do not interpolate. Show a gap in the chart line. For correlation, exclude windows with >30% missing days.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pearson correlation with p-value | Manual t-distribution calculation | `scipy.stats.pearsonr(x, y)` | Returns (r, p-value) in one call. Handles edge cases (constant arrays, NaN). |
| Spearman rank correlation | Manual rank sorting + Pearson on ranks | `scipy.stats.spearmanr(x, y)` | Handles tied ranks correctly. Returns (rho, p-value). |
| Moving average for weight trend | Manual sliding window with list slicing | `numpy.convolve(values, kernel, mode='valid')` or `pandas.Series.rolling().mean()` | Handles edge cases at series boundaries. |
| CJK font detection | Hard-coded font paths | `matplotlib.font_manager.fontManager.ttflist` | Cross-platform. Discovers all installed fonts dynamically. |

**Key insight:** The statistical significance testing (p-values) is the critical piece that the existing correlation_engine.py lacks. scipy.stats handles this correctly including edge cases like very small samples, tied values, and constant series. Hand-rolling p-value calculation from the t-distribution is error-prone and unnecessary.

## Common Pitfalls

### Pitfall 1: CJK Font Not Found -- Tofu Boxes in Charts
**What goes wrong:** Chinese axis labels, titles, and annotations render as empty rectangles ("tofu") because matplotlib cannot find a CJK-capable font.
**Why it happens:** matplotlib's default font (DejaVu Sans) has no CJK glyphs. On macOS, CJK fonts exist but matplotlib doesn't auto-discover them for `sans-serif` family.
**How to avoid:** Set `rcParams["font.sans-serif"]` to include a CJK font at module import. The target macOS system has `PingFang HK`, `Heiti TC`, `Hiragino Sans GB`, and `Songti SC` available. Also set `rcParams["axes.unicode_minus"] = False` to prevent minus sign rendering issues.
**Warning signs:** Chart PNG files show square boxes where Chinese text should be.

### Pitfall 2: matplotlib Not Thread-Safe
**What goes wrong:** If heartbeat or batch processing generates charts for multiple family members concurrently, matplotlib's global state (rcParams, current figure) causes garbled output.
**Why it happens:** `plt.plot()` and similar functions operate on implicit global state.
**How to avoid:** Always use the OO API (`fig, ax = plt.subplots()`), never the stateful `plt.plot()` API. Always `plt.close(fig)` after saving. The caffeine_tracker.py already follows this pattern correctly.
**Warning signs:** Charts appear blank, have wrong labels, or crash with "figure already closed" errors during batch processing.

### Pitfall 3: Y-Axis Auto-Scale Hides Clinical Context
**What goes wrong:** A blood pressure chart with values 125-135 gets auto-scaled to that range, making a 10-point fluctuation look dramatic. Or values 120-200 get scaled to 0-300, making a dangerous spike look flat.
**Why it happens:** matplotlib auto-scales by default.
**How to avoid:** Set explicit y-axis ranges per metric type. Blood pressure: 40-200 mmHg. Glucose: 2-15 mmol/L. Sleep: 0-14 hours. Weight: auto with 10% padding around data range.
**Warning signs:** Users misinterpret stable values as alarming or ignore genuinely concerning trends.

### Pitfall 4: Spurious Correlations from Small Samples
**What goes wrong:** System reports "strong correlation r=0.85" between sleep and glucose based on 5 data points. This is statistically meaningless.
**Why it happens:** Pearson r can be very high with few points even for random data. The existing correlation_engine.py uses n >= 3 as minimum -- far too low.
**How to avoid:** Enforce D-08: n >= 14 minimum. Always report p-value. If p >= 0.05, state "no significant correlation found" regardless of r value. The existing `pearson_correlation()` method returns r without p-value -- this must be replaced with scipy.stats.pearsonr().
**Warning signs:** Correlations reported with n < 14, or correlations reported without p-values.

### Pitfall 5: Correlation Engine Data Access Mismatch
**What goes wrong:** The existing `CorrelationEngine._get_daily_values()` uses `CrossSkillReader.read()` which queries by concept name. But the DEFAULT_PAIRS use different field names than what HealthDataStore stores. For example, sleep data may use `total_min` (as per health-concepts.yaml) but the correlation engine looks for `score`.
**Why it happens:** The DEFAULT_PAIRS were defined when the correlation engine was first built and may not match current data schemas.
**How to avoid:** Align correlation pair definitions with health-concepts.yaml field names. For sleep duration correlation, use `total_min` (aliased as `duration_min`, `sleep_duration`). For blood glucose, use `value` (aliased as `glucose`, `blood_sugar`). Verify against actual data in `data/` directories.
**Warning signs:** Correlation analysis returns all results with sample_count=0 despite data existing.

### Pitfall 6: File Naming with person_id=None
**What goes wrong:** D-05 specifies file naming as `{metric}_{person_id}_{days}d_{date}.png`. When person_id is None (default/self user), the filename becomes `bp_None_30d_2026-03-26.png`.
**Why it happens:** String formatting with None value.
**How to avoid:** Use `person_id or "self"` in filename construction. Example: `bp_self_30d_20260326.png`.
**Warning signs:** Files with "None" in their names appearing in charts directories.

## Code Examples

### Blood Pressure Dual-Line Chart with Reference Bands
```python
# Source: Pattern from caffeine_tracker.py + D-03/D-06 requirements
def generate_blood_pressure_chart(self, days: int = 30) -> str:
    store = HealthDataStore("blood-pressure-tracker", data_dir=self.data_dir)
    start = (datetime.now() - timedelta(days=days)).isoformat()[:10]
    records = store.query(record_type="bp", start=start, person_id=self.person_id)

    if not records:
        return ""

    dates = [r["timestamp"][:10] for r in records]
    systolic = [r["data"]["systolic"] for r in records]
    diastolic = [r["data"]["diastolic"] for r in records]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Reference bands (D-03)
    ax.axhspan(0, 80, alpha=0.06, color="green")      # Normal diastolic zone
    ax.axhspan(80, 90, alpha=0.06, color="gold")       # Elevated diastolic
    ax.axhspan(90, 200, alpha=0.06, color="red")       # High diastolic
    ax.axhspan(0, 120, alpha=0.04, color="green")      # Normal systolic zone
    ax.axhspan(120, 130, alpha=0.06, color="gold")     # Elevated systolic
    ax.axhspan(130, 140, alpha=0.06, color="orange")   # Stage 1
    ax.axhspan(140, 200, alpha=0.06, color="red")      # Stage 2

    ax.plot(dates, systolic, "o-", color="#E74C3C", linewidth=2, markersize=4, label="收缩压")
    ax.plot(dates, diastolic, "s-", color="#3498DB", linewidth=2, markersize=4, label="舒张压")

    ax.set_title(f"血压趋势 (近{days}天)", fontsize=14)
    ax.set_ylabel("mmHg")
    ax.set_ylim(40, 200)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()

    pid = self.person_id or "self"
    date_str = datetime.now().strftime("%Y%m%d")
    path = Path(store.charts_dir) / f"bp_{pid}_{days}d_{date_str}.png"
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path)
```

### Correlation with scipy.stats
```python
# Source: scipy.stats API documentation
from scipy.stats import pearsonr, spearmanr

def correlate(self, concept_a, field_a, concept_b, field_b, window_days=30):
    values_a = self._get_daily_values(concept_a, field_a, window_days)
    values_b = self._get_daily_values(concept_b, field_b, window_days)
    common_dates = sorted(set(values_a.keys()) & set(values_b.keys()))

    if len(common_dates) < 14:  # D-08: minimum n=14
        return CorrelationResult(
            concept_a=concept_a, concept_b=concept_b,
            field_a=field_a, field_b=field_b,
            correlation=0.0, p_value=1.0,
            sample_count=len(common_dates),
            direction="none", strength="none",
            method="insufficient_data",
        )

    x = [values_a[d] for d in common_dates]
    y = [values_b[d] for d in common_dates]

    r_pearson, p_pearson = pearsonr(x, y)
    r_spearman, p_spearman = spearmanr(x, y)

    # Use the method with lower p-value (more significant)
    if p_spearman < p_pearson:
        r, p, method = r_spearman, p_spearman, "spearman"
    else:
        r, p, method = r_pearson, p_pearson, "pearson"

    return CorrelationResult(
        concept_a=concept_a, concept_b=concept_b,
        field_a=field_a, field_b=field_b,
        correlation=r, p_value=p,
        sample_count=len(common_dates),
        direction="positive" if r > 0 else "negative",
        strength=self._classify_strength(abs(r)),
        method=method,
    )
```

### CJK Font Detection
```python
# Source: matplotlib.font_manager API
def _configure_cjk_fonts():
    """Configure matplotlib for CJK rendering. Call once at module import."""
    import matplotlib.font_manager as fm

    CJK_PREFERENCE = [
        "PingFang HK", "PingFang SC", "Heiti TC",
        "Hiragino Sans GB", "Hiragino Sans",
        "STHeiti", "SimHei", "Noto Sans CJK SC",
        "Arial Unicode MS",
    ]

    available_fonts = {f.name for f in fm.fontManager.ttflist}
    for font_name in CJK_PREFERENCE:
        if font_name in available_fonts:
            plt.rcParams["font.sans-serif"] = [font_name] + plt.rcParams.get("font.sans-serif", [])
            plt.rcParams["axes.unicode_minus"] = False
            return font_name

    import sys
    print("[WARN] No CJK font found for matplotlib. Chinese labels will not render correctly.", file=sys.stderr)
    return None

# Call at module level
_configured_cjk_font = _configure_cjk_fonts()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-rolled Pearson only (current correlation_engine.py) | scipy.stats.pearsonr + spearmanr with p-values | Always available | Proper statistical significance testing |
| n >= 3 minimum (current code) | n >= 14 minimum (D-08) | This phase | Prevents spurious correlations from tiny samples |
| No natural language output | Template-based Chinese insights | This phase | User-facing value from correlation analysis |
| Per-skill chart code (caffeine_tracker) | Shared chart engine module | This phase | Consistent styling, reusable across skills and Phase 4 visit summaries |

**Deprecated/outdated:**
- The existing `correlation_engine.py` `pearson_correlation()` method (hand-rolled, no p-value) should be replaced by scipy.stats calls but kept as a fallback if scipy is not installed.

## Project Constraints (from CLAUDE.md)

- **GSD workflow enforcement:** All code changes must go through GSD workflow -- no direct repo edits outside GSD
- **Python only:** No new languages (confirmed -- matplotlib + scipy are Python)
- **Local-first:** All data stays on local filesystem (charts saved as PNG files locally)
- **Skill format:** New capabilities as SKILL.md + optional Python
- **from __future__ import annotations** at top of every module
- **Modern union syntax:** `str | None` not `Optional[str]`
- **4-space indentation, ~120 char line length**
- **Naming:** PascalCase classes, snake_case functions, kebab-case skill dirs
- **CLI pattern:** argparse with --format markdown|json
- **Error output:** `print(f"[WARN] ...", file=sys.stderr)` for warnings

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| matplotlib | Chart generation | Yes | 3.8.2 | -- |
| scipy | Correlation p-values | Yes | 1.11.4 | Hand-rolled Pearson (no p-value, degraded) |
| numpy | Array ops, moving average | Yes | 1.26.4 | -- |
| pandas | Time series resampling | Yes | 2.2.2 | Dict-based aggregation (already used) |
| CJK font (PingFang HK) | Chinese chart labels | Yes | System font | Heiti TC, Hiragino Sans GB also available |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None -- all required packages are installed.

**Note:** matplotlib 3.8.2 is installed but pyproject.toml specifies >=3.10. Either upgrade matplotlib or adjust pyproject.toml minimum. For Phase 3, 3.8.2 is functionally sufficient -- all required APIs (subplots, axhspan, savefig) are available.

**Note:** scipy is not currently in pyproject.toml. Must add to `[project.optional-dependencies]` -- recommend adding an `analysis` extra or extending the existing `viz` extra.

## Open Questions

1. **Correlation field name alignment**
   - What we know: The existing DEFAULT_PAIRS in correlation_engine.py reference fields like `("sleep", "score")` but health-concepts.yaml defines `total_min` as the primary sleep duration field and `score` as sleep quality score.
   - What's unclear: Which existing data records actually use which field names -- depends on which importers/trackers wrote the data.
   - Recommendation: Update DEFAULT_PAIRS to match health-concepts.yaml canonical field names. Add aliases via ConceptResolver for backward compatibility.

2. **matplotlib version mismatch**
   - What we know: Installed 3.8.2, pyproject.toml says >=3.10, latest is 3.10.8.
   - What's unclear: Whether to upgrade during this phase or just adjust the spec.
   - Recommendation: Lower pyproject.toml minimum to >=3.8 since no 3.10-specific features are needed. Upgrading is optional.

3. **Sparse data handling for charts**
   - What we know: Users may have only a few measurements per month. Line charts with 3 data points over 90 days look odd.
   - What's unclear: Best UX for sparse data -- connect points with lines? Show only markers? Show data density indicator?
   - Recommendation: Show data points as markers always. Connect with lines only when gap between consecutive points is <= 3 days. For larger gaps, break the line. Add subtitle showing "N data points in period."

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `correlation_engine.py`, `caffeine_tracker.py`, `health_data_store.py`, `cross_skill_reader.py`, `health-concepts.yaml` -- direct source inspection
- matplotlib 3.8.2 installed -- API verified locally
- scipy 1.11.4 installed -- `scipy.stats.pearsonr` and `spearmanr` API verified
- CJK fonts verified on target macOS: PingFang HK, Heiti TC, Hiragino Sans GB, Songti SC, Hiragino Sans, Arial Unicode MS

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` -- matplotlib and scipy recommendations from prior research
- `.planning/research/PITFALLS.md` -- CJK font pitfall (Pitfall 6) and spurious correlation pitfall (Pitfall 7)

### Tertiary (LOW confidence)
- None -- all findings verified against installed packages and codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and used in project
- Architecture: HIGH -- follows established patterns from caffeine_tracker.py and existing correlation_engine.py
- Pitfalls: HIGH -- CJK font availability confirmed on target system; correlation statistics well-understood domain

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain, no fast-moving dependencies)
