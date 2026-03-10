---
name: weekly-health-digest
description: "Aggregates the past 7 days of health data from health-memory into a narrative weekly report with a composite health score (0-100), per-domain summaries, cross-domain correlations, and actionable next-week suggestions. Use at the end of each week or when the user asks for a health summary."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📊","category":"health"}}
---

# Weekly Health Digest

Aggregate the past 7 days of daily logs and longitudinal indicator files from health-memory. Produce a narrative weekly report with a composite health score, per-domain summaries, cross-domain correlations, highlights, and actionable next-week suggestions.

## Capabilities

### 1. Data Aggregation

**Data sources**:
- `memory/health/daily/*.md` -- last 7 days of daily logs
- `memory/health/items/*.md` -- all longitudinal indicator files
- `memory/health/_health-profile.md` -- health baseline profile

**Steps**:
1. Determine target week range: Monday to Sunday (ISO week), default is the most recent complete week
2. Glob `memory/health/daily/*.md`, filter to the 7 target days
3. Read each daily file, extract data from each skill section
4. Glob `memory/health/items/*.md`, read each file, extract `## Recent Status` and `## History` rows within the target week
5. Read `memory/health/_health-profile.md` for baseline info

**Data completeness check**: Record which days and which domains have data vs. are missing. Clearly note missing data in the report. Do not impute missing values.

### 2. Health Score Calculation (0-100)

Composite score from all tracked domains' control rates.

**Formula**: Total = sum of (domain compliance rate * domain weight * 100)

**Domain weights** (sum = 1.0):

| Domain | Weight | Compliance calculation |
|--------|--------|----------------------|
| Blood pressure | 0.20 | This-week BP on-target count / measurements (target: < 140/90) |
| Blood glucose | 0.20 | This-week FPG on-target count / measurements (target: < 7.0 mmol/L) |
| Weight management | 0.10 | BMI 18.5-24 = 100%; each BMI point beyond deducts 10% |
| Exercise | 0.15 | This-week total exercise minutes / 150 (WHO recommendation), cap at 100% |
| Nutrition | 0.10 | This-week average calorie compliance (within +/-10% of target = on-target) |
| Sleep quality | 0.10 | This-week average sleep score / 100 (from sleep-analyzer) |
| Caffeine control | 0.05 | This-week caffeine cutoff-compliant days / 7 (from caffeine-tracker) |
| Medication adherence | 0.10 | This-week medication adherence rate (from medication-reminder) |

**When a domain has no data**: Exclude it and redistribute its weight proportionally among domains with data, keeping total weight = 1.0.

**Score grades**:

| Score | Grade | Description |
|-------|-------|-------------|
| 90-100 | Excellent | All indicators well controlled |
| 75-89 | Good | Most on-target, a few need attention |
| 60-74 | Fair | Multiple areas need improvement |
| < 60 | Needs attention | Overall control is poor, recommend medical consultation |

### 3. Per-Domain Weekly Summaries

Generate a structured summary for each domain with data:

**Blood Pressure**: Measurement count, average SBP/DBP, max/min, on-target rate (< 140/90), week-over-week change.

**Blood Glucose**: FPG average/max/min, postprandial average/max/min, latest HbA1c (if available), hypoglycemia events (< 3.9 mmol/L).

**Weight**: Start-of-week vs. end-of-week weight, weekly change (kg), distance to target weight, trend direction.

**Exercise**: Total minutes, active days, WHO compliance (>= 150 min moderate/week), exercise type distribution.

**Nutrition**: Average daily calories, macronutrient ratio (protein/carb/fat), deviation from calorie target.

**Sleep**: Average duration, average score, sleep efficiency, week-over-week comparison.

**Caffeine**: Average daily intake (mg), peak single-day intake, cutoff-time compliant days.

**Medication**: Weekly adherence rate, missed doses count and drugs, week-over-week comparison.

### 4. Cross-Domain Correlation Discovery

Analyze correlations between health domains:

| Pair | Analysis | Method |
|------|----------|--------|
| Exercise <-> Blood Pressure | BP on exercise days vs. rest days | Compare group means |
| Diet <-> Blood Glucose | Postprandial glucose on high-cal vs. low-cal days | Compare group means |
| Caffeine <-> Sleep | Sleep score on high-caffeine vs. low-caffeine days | Compare group means |
| Exercise <-> Sleep | Sleep quality on exercise vs. rest days | Compare group means |
| Sleep <-> Blood Pressure | Next-day BP after good vs. poor sleep | Compare group means |
| Medication <-> Blood Pressure | BP on missed-dose days vs. adherent days | Compare group means |

**Method** (no statistics library required):
1. Split 7 days into two groups by condition (e.g., exercise days vs. rest days)
2. Compute mean of the related indicator for each group
3. If difference > 10%, note as "possible correlation"
4. Describe findings in narrative language; avoid statistical terms like "significant"

Note: 7 days of data is limited. Correlations are observational, not causal.

### 5. Highlights and Milestones

**Best day**: The day with the most on-target indicators.

**Areas needing improvement**: The domain with the lowest compliance rate, with specific improvement direction.

**Milestone detection**:
- Consecutive N days BP on-target (N >= 7)
- Weight crosses a stage goal
- Exercise on-target for N consecutive weeks
- Medication adherence upgraded from "Fair" to "Good"
- Other quantifiable progress

### 6. Next-Week Action Suggestions

Generate 3-5 specific, actionable suggestions based on this week's data:
- Each suggestion must be concrete (not "watch your diet" but "keep lunch carbs under 100g")
- Each must have a clear action item
- Based on specific problems found in this week's data
- Ordered by priority
- Prioritize worsening trends and low-compliance domains

## Narrative Writing Rules

The core value of the digest is turning data into readable narrative, not just listing numbers.

- Use natural language to describe trends; do not only list tables
- Lead with conclusions, then provide supporting data
- Connect findings across domains to tell a "story"
- Offer possible explanations for anomalies
- Make suggestions specific and actionable

Good example:
> Blood pressure control was generally acceptable this week, averaging 132/85 mmHg, but readings spiked on Wednesday and Saturday. Notably, both were rest days -- exercise-day average was 128/82, while rest-day average rose to 138/90, suggesting regular exercise helps with BP control.

## Output Format

### Weekly Report Template

```markdown
# Weekly Health Digest

## Period
YYYY-Wnn (YYYY-MM-DD to YYYY-MM-DD)

## Health Score: NN/100 (Grade)

### Score Breakdown
| Domain | Weight | Compliance | Points |
|--------|--------|-----------|--------|
| Blood pressure | 20% | N% | N.N |
| Blood glucose | 20% | N% | N.N |
| Weight management | 10% | N% | N.N |
| Exercise | 15% | N% | N.N |
| Nutrition | 10% | N% | N.N |
| Sleep quality | 10% | N% | N.N |
| Caffeine control | 5% | N% | N.N |
| Medication adherence | 10% | N% | N.N |
| **Total** | **100%** | | **NN.N** |

---

## Weekly Overview
[Narrative paragraph summarizing the week]

---

## Domain Details

### Blood Pressure
[Narrative summary with data]

### Blood Glucose
[Narrative summary with data]

### [Other domains...]

---

## Correlations
1. **[Pair]**: [narrative finding]

---

## Highlights
- **Best day**: [day and why]
- **Milestone**: [if any]
- **Progress**: [if any]

## Areas to Improve
- **[Domain]** (compliance N%): [specific issue]

---

## Next-Week Action Plan
1. **[Action]**: [rationale from this week's data]

---

## Data Completeness

| Date | BP | Glucose | Exercise | Nutrition | Sleep | Caffeine | Meds |
|------|----|---------|---------|-----------| ------|----------|------|
| MM-DD Day | v/- | v/- | v/- | v/- | v/- | v/- | v/- |

Missing: [summary of gaps]
```

## Execution Flow

1. **Determine target week**: Default = last complete Mon-Sun. User may specify e.g. `2026-W10`.
2. **Collect data**: Glob + Read daily files and items files for the target week.
3. **Completeness check**: Note missing days and domains.
4. **Calculate health score**: Per-domain compliance, redistribute weight for missing domains, compute weighted total.
5. **Generate domain summaries**: Structured summary per domain with week-over-week comparison.
6. **Correlation analysis**: For pairs with sufficient data, compare group means, describe findings narratively.
7. **Highlights and suggestions**: Identify best day, milestones, areas to improve, 3-5 action items.
8. **Generate narrative overview**: Synthesize into readable narrative paragraph.
9. **Write output**: Write report to `memory/health/weekly/YYYY-Wnn.md`. Edit Sunday's daily file to add digest section.

## Data Persistence

1. **Weekly report file**: `memory/health/weekly/YYYY-Wnn.md` (create directory if needed; overwrite if regenerating)
2. **Daily file update**: Add/replace section in Sunday's daily file:

```markdown
## Weekly Digest [weekly-health-digest · HH:MM]
- Health Score: NN/100 (Grade)
- Highlights: [key achievement]
- Action items: [top priorities]
- Full report: memory/health/weekly/YYYY-Wnn.md
```

## Alerts and Safety

### Medical Disclaimer

This skill generates weekly health digests for personal health management reference only. It does not constitute medical advice. It does not diagnose diseases, recommend treatments, adjust medications, or replace regular medical checkups.

The health score is a composite reference metric, not a medical assessment. Correlations are based on limited data (7 days) and are observational only. When the score is < 60 or multiple abnormal trends are detected, recommend medical consultation. The digest can serve as reference material for physician visits but does not replace medical examination.
