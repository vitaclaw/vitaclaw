---
name: sleep-analyzer
description: "Analyzes sleep data to compute efficiency, quality score (0-100), and stage distribution. Detects patterns like irregular schedules, chronic short sleep, and weekend oversleep. Use when the user provides sleep records, imports Apple Health data, or asks about sleep quality."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"😴","category":"health"}}
---

# Sleep Analyzer

Records and analyzes sleep data: computes sleep efficiency and a composite quality score (0-100), evaluates stage distribution, detects multi-day patterns, cross-references caffeine data, and supports Apple Health CSV import.

## Capabilities

### 1. Sleep Data Recording

Extract from natural-language input:

| Field | Required | Default if missing |
|-------|----------|--------------------|
| bedtime | Yes | -- |
| sleep_onset | No | bedtime + 15 min |
| waketime | Yes | -- |
| awakenings (count) | No | 0 |
| waso (wake-after-sleep-onset, min) | No | 0 |
| stages (light/deep/REM/awake) | No | omitted |
| subjective quality (1-5) | No | omitted |
| notes | No | omitted |

### 2. Sleep Efficiency

```
Sleep Efficiency = (TST / TIB) * 100%
```

- **TIB** (Time In Bed) = waketime - bedtime (minutes)
- **SOL** (Sleep Onset Latency) = sleep_onset - bedtime (default 15 min)
- **TST** (Total Sleep Time) = TIB - SOL - WASO

| Efficiency | Rating |
|------------|--------|
| >= 90% | Excellent |
| 85-89% | Good |
| 80-84% | Fair |
| < 80% | Poor |

### 3. Composite Sleep Score (0-100)

```
Score = Efficiency(40%) + Duration(30%) + Consistency(20%) + Latency(10%)
```

#### 3.1 Efficiency Sub-score (weight 40%)

| Efficiency | Points |
|------------|--------|
| >= 95% | 100 |
| 90-94% | 90 |
| 85-89% | 80 |
| 80-84% | 60 |
| 75-79% | 40 |
| < 75% | 20 |

Use linear interpolation within adjacent bands.

#### 3.2 Duration Sub-score (weight 30%)

| TST | Points | Notes |
|-----|--------|-------|
| 7-9 h | 100 | NSF recommended (adults) |
| 6-7 h | 70 | Slightly short |
| 5-6 h | 40 | Insufficient |
| < 5 h | 10 | Severely insufficient |
| > 9 h | 60 | Excess; may indicate health issue |

#### 3.3 Consistency Sub-score (weight 20%)

Standard deviation of bedtime and waketime over the last 7 days:

| SD (minutes) | Points |
|--------------|--------|
| < 30 | 100 |
| 30-60 | 80 |
| 60-90 | 50 |
| > 90 | 20 |

**Time-to-minutes conversion**: use midnight (00:00) as zero; times before midnight are negative (e.g. 23:00 = -60). Average the bedtime SD and waketime SD. If fewer than 7 days available, compute on existing data and note the limitation.

#### 3.4 Latency Sub-score (weight 10%)

| SOL | Points |
|-----|--------|
| < 15 min | 100 |
| 15-30 min | 70 |
| 30-60 min | 40 |
| > 60 min | 10 |

### 4. Sleep Stage Analysis

**Normal ranges** (adult, 8 h sleep):

| Stage | Normal % | Normal Duration | Function |
|-------|----------|-----------------|----------|
| Light (N1+N2) | 50-60% | 4-4.8 h | Basic restoration |
| Deep (N3) | 13-23% | 1-1.8 h | Physical recovery, immune repair |
| REM | 20-25% | 1.6-2 h | Memory consolidation, mood regulation |
| Awake | < 5% | < 24 min | -- |

**Flags**: Deep < 13%, REM < 20%, Awake > 10%, Light > 65%.

### 5. Pattern Detection (7-30 days)

| Pattern | Condition | Suggestion |
|---------|-----------|------------|
| Irregular schedule | bedtime SD > 60 min | Fix bedtime and waketime |
| Chronic short sleep | TST < 6 h for 5+ consecutive days | Increase sleep time; consult doctor if persistent |
| Weekend oversleep | Weekend TST > weekday TST + 2 h | Reduce weekday sleep debt |
| Fragmented sleep | awakenings >= 3 or WASO > 30 min | Investigate cause (environment/health/stress) |
| Difficulty falling asleep | SOL > 30 min for 3+ consecutive days | Try relaxation techniques; consult doctor |
| Early awakening | wakes > 1 h before planned time, cannot fall back asleep | May relate to mood or light exposure |
| Delayed phase | bedtime consistently > 01:00 | Gradual phase advance needed |

### 6. Caffeine Correlation

Read caffeine-tracker data from health-memory. Analyze:
- Bedtime residual vs. sleep onset latency
- Daily total caffeine vs. sleep efficiency
- Last caffeine time vs. sleep quality
- Describe correlation direction (positive/negative/none).

### 7. Apple Health CSV Import

**Required columns** (case-insensitive): `bedtime`, `waketime`.
**Optional columns**: `duration`, `deep`, `rem`, `light`, `awake`.

Steps: read CSV, compute efficiency and score per row, batch-write to health-memory, output summary (count, date range, average score).

## Output Format

### Single-Night Report

```markdown
## Sleep [sleep-analyzer · HH:MM]

### Overview
- Bedtime: 23:00 -> Waketime: 07:00
- Time in bed: 8h 0min
- Sleep onset latency: ~20 min
- Total sleep time: 7h 25min
- Awakenings: 1 (15 min)

### Efficiency
- Efficiency: 92.7%
- Rating: Excellent

### Sleep Score: 83 / 100
| Dimension | Raw | Sub-score | Weight | Weighted |
|-----------|-----|-----------|--------|----------|
| Efficiency | 92.7% | 90 | 40% | 36.0 |
| Duration | 7h25min | 100 | 30% | 30.0 |
| Consistency | SD=45min | 50 | 20% | 10.0 |
| Latency | 20min | 70 | 10% | 7.0 |
| **Total** | | | | **83.0** |

### Stages (if available)
| Stage | Duration | % | Normal Range | Status |
|-------|----------|---|-------------|--------|
| Light | 3h 55min | 53% | 50-60% | Normal |
| Deep | 1h 20min | 18% | 13-23% | Normal |
| REM | 1h 45min | 24% | 20-25% | Normal |
| Awake | 25min | 5% | <5% | Slightly high |

### Insights
- Excellent efficiency; fell asleep quickly
- Schedule consistency needs improvement (SD 45 min)
- Recommend fixing bedtime around 23:00
```

### Weekly Summary

```markdown
## Weekly Sleep Summary (MM-DD ~ MM-DD)

### Key Metrics
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Score | 78 | 72 | +6 |
| Duration | 7h 10min | 6h 45min | +25min |
| Efficiency | 89% | 86% | +3% |
| Latency | 18min | 25min | -7min |

### Daily Detail
| Date | Bedtime | Waketime | Duration | Efficiency | Score |
|------|---------|----------|----------|------------|-------|
| Mon | 23:15 | 07:00 | 7h15min | 91% | 85 |
| Tue | 00:30 | 07:30 | 6h30min | 84% | 68 |
| ... | | | | | |

### Patterns
- [Notice] Late bedtimes on Tue and Fri (>00:00) lowered consistency score
- [Good] Average deep sleep 17%, within normal range
- [Suggestion] Fix bedtime at 23:00 to improve consistency

### Caffeine Correlation (if data available)
- Average daily caffeine: 220 mg
- Average last-caffeine time: 15:30
- High-caffeine days (>300 mg) avg score: 71 vs low-caffeine days: 82
```

## Data Persistence

### Daily File (`memory/health/daily/YYYY-MM-DD.md`)

```markdown
## Sleep [sleep-analyzer · HH:MM]
- Score: 83/100
- Duration: 7h 25min (23:00-07:00)
- Efficiency: 92.7%
- Latency: 20min
- Awakenings: 1 (15min)
- Stages: Light 53%, Deep 18%, REM 24%, Awake 5%
```

### Item File (`memory/health/items/sleep.md`)

```markdown
---
item: sleep
unit: score (0-100)
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Sleep Records

## Recent Status
- Latest: Score 83, 7h25min, Efficiency 92.7% (YYYY-MM-DD)
- 7-day average score: 78
- 7-day average duration: 7h 10min
- Trend: Improving

## History
| Date | Score | Duration | Efficiency | Latency | Bedtime | Waketime | Notes |
|------|-------|----------|------------|---------|---------|----------|-------|
| 2026-03-10 | 83 | 7h25min | 92.7% | 20min | 23:00 | 07:00 | |
| 2026-03-09 | 71 | 6h30min | 85.4% | 25min | 00:15 | 07:00 | Late night |
```

### Write Steps

1. Glob `memory/health/daily/` for the target date file; create if absent.
2. Read the daily file.
3. Grep `## .* \[sleep-analyzer ·` for existing section.
4. Edit to replace existing section, or insert before `## Health Files` if new.
5. Update frontmatter `updated_at`.
6. Read `memory/health/items/sleep.md` (create if absent).
7. Update `## Recent Status` (including 7-day averages) and prepend new row to `## History`.
8. Remove rows older than 90 days.

## Formulas and Reference Data

### Trend Determination

Linear regression on last 7 days of scores:
- Slope > 1: Improving
- Slope < -1: Declining
- Otherwise: Stable

### Standard Deviation (Consistency)

```
SD = sqrt( (1/N) * SUM[(x_i - mean)^2] )
```

## Alerts and Safety

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice. It does not diagnose sleep disorders or replace polysomnography (PSG).

**Consult a doctor if**:
- Sleep onset latency consistently > 45 min
- Frequent awakenings (>= 5 per night)
- Partner reports loud snoring or breathing pauses
- Severe daytime sleepiness affecting work or driving safety
- Sleep problems persist > 1 month without improvement
