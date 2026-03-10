---
name: blood-pressure-tracker
description: "Records and classifies blood pressure readings per ACC/AHA 2017 guidelines, detects morning surge, analyzes diurnal variation, and generates monthly statistics. Use when the user logs BP readings or asks about blood pressure trends."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"💓","category":"health"}}
---

# Blood Pressure Tracker

Records blood pressure readings with automatic classification (ACC/AHA 2017), tracks trends, detects morning surge and diurnal patterns, computes pulse pressure and heart rate analysis, and generates monthly statistics.

## Capabilities

### 1. Record Blood Pressure

Extract from natural-language input:

| Field | Required | Default |
|-------|----------|---------|
| SBP (mmHg) | Yes | -- |
| DBP (mmHg) | Yes | -- |
| Pulse (bpm) | No | omitted |
| Time (HH:MM) | No | current time |
| Period | Auto | derived from time |
| Position | No | seated |
| Arm | No | omitted |
| Notes | No | omitted |

### 2. BP Classification (ACC/AHA 2017)

| Category | SBP (mmHg) | | DBP (mmHg) |
|----------|-----------|---|-----------|
| Normal | < 120 | AND | < 80 |
| Elevated | 120-129 | AND | < 80 |
| Stage 1 HTN | 130-139 | OR | 80-89 |
| Stage 2 HTN | >= 140 | OR | >= 90 |
| Hypertensive Crisis | >= 180 | OR | >= 120 |

**Logic**: check crisis first, then descend. When SBP and DBP fall in different categories, use the higher one. Example: SBP 125 (Elevated) + DBP 85 (Stage 1) = Stage 1 HTN.

```
classify(sbp, dbp):
    if sbp >= 180 or dbp >= 120: return "Hypertensive Crisis"
    if sbp >= 140 or dbp >= 90:  return "Stage 2 HTN"
    if sbp >= 130 or dbp >= 80:  return "Stage 1 HTN"
    if sbp >= 120 and dbp < 80:  return "Elevated"
    return "Normal"
```

### 3. Pulse Pressure

**PP = SBP - DBP**

| PP (mmHg) | Assessment | Clinical Significance |
|-----------|------------|----------------------|
| < 30 | Low | May indicate low cardiac output |
| 30-40 | Normal | Ideal range |
| 41-60 | High | Possible reduced arterial elasticity |
| > 60 | Significantly high | Increased arteriosclerosis risk; recommend evaluation |

### 4. Heart Rate Classification

| HR (bpm) | Category | Notes |
|-----------|----------|-------|
| < 60 | Bradycardia | Normal in trained athletes |
| 60-100 | Normal | Resting range |
| > 100 | Tachycardia | If not post-exercise, investigate |

### 5. Time-of-Day Periods

| Period | Time Range | Notes |
|--------|-----------|-------|
| Morning | 06:00-10:00 | Key window for morning surge detection |
| Daytime | 10:00-18:00 | Active hours |
| Evening | 18:00-22:00 | Evening readings |
| Nighttime | 22:00-06:00 | Sleep-period readings |

### 6. Morning Surge Detection

**Definition**: morning SBP (max 06:00-10:00) minus nighttime SBP (min 22:00-06:00) >= 35 mmHg.

Requires at least 1 morning and 1 nighttime reading (same day or previous night). If no nighttime data, use previous evening's last reading as approximation.

```
morning_surge = max(morning_SBP) - min(night_SBP)
```

| Surge (mmHg) | Result | Action |
|--------------|--------|--------|
| < 35 | Normal | Continue monitoring |
| 35-55 | Positive | Recommend medical evaluation; may need medication timing adjustment |
| > 55 | Significant | Elevated stroke risk; seek medical attention promptly |

### 7. Monthly Statistics

Compute for all readings in a given month:

| Metric | Formula |
|--------|---------|
| Mean | mean(SBP), mean(DBP), mean(Pulse) |
| Max | max(SBP), max(DBP) |
| Min | min(SBP), min(DBP) |
| SD | sqrt((1/N) * SUM[(x_i - mean)^2]) |
| Control rate | (on-target count / total) * 100% |
| Measurement frequency | total readings / days in month |

**Control targets** (default; user-customizable):
- General: SBP < 140 AND DBP < 90
- Elderly (>= 65): SBP < 150 AND DBP < 90
- Diabetes/CKD: SBP < 130 AND DBP < 80

**SBP SD variability assessment**: < 10 stable, 10-15 mild, > 15 significant.

### 8. Trend Analysis

Linear regression on the last 7/14/30 days: `SBP = a + b * day_index`.
- b > 0.5: rising
- b < -0.5: declining
- otherwise: stable

## Input Format

Natural language, e.g.:
- "BP 135/85, pulse 72"
- "This morning 128/82"
- "Just measured 142/90 HR 78"

## Output Format

### Single Reading

```markdown
## Blood Pressure [blood-pressure-tracker · 08:30]

### Reading
- Value: 135/85 mmHg
- Pulse: 72 bpm
- Period: Morning
- Classification: **Stage 1 HTN**
- Pulse pressure: 50 mmHg (high)
- Heart rate: Normal

### Analysis
- SBP 135 falls in Stage 1 range (130-139)
- DBP 85 falls in Stage 1 range (80-89)
- Higher category taken -> Stage 1 HTN
- PP 50 mmHg is high; monitor arterial elasticity

### Morning Surge
- Morning SBP: 135 mmHg
- Previous night min SBP: 108 mmHg
- Surge: 27 mmHg -> Normal
```

### Monthly Report

```markdown
# Blood Pressure Monthly Report -- March 2026

## Summary
| Metric | SBP | DBP | Pulse |
|--------|-----|-----|-------|
| Mean | 132.5 | 84.2 | 73 |
| Max | 148 | 95 | 88 |
| Min | 118 | 72 | 65 |
| SD | 8.3 | 6.1 | 5.2 |
| Readings | 45 | 45 | 42 |

## Control Analysis
- Target: < 140/90 mmHg
- On-target: 38/45
- Control rate: 84.4%

## By Period
| Period | Avg SBP | Avg DBP | Count |
|--------|---------|---------|-------|
| Morning | 136.2 | 86.1 | 20 |
| Daytime | 130.5 | 83.0 | 10 |
| Evening | 128.8 | 82.5 | 12 |
| Nighttime | 122.0 | 78.0 | 3 |

## Trend
- SBP: slight decline (slope -0.3/day) -> stable-improving
- DBP: stable

## Morning Surge
- Positive detections: 2/15 days (13%)
- Average surge: 28 mmHg (normal)

## Pulse Pressure
- Average PP: 48.3 mmHg (high)
- Max PP: 58 mmHg

## Alerts This Month
- [Warning] Mar 5: 3 consecutive above target (142/92, 145/90, 140/88)
- [Notice] Mar 12: PP 58 mmHg
```

## Data Persistence

### Daily File (`memory/health/daily/YYYY-MM-DD.md`)

```markdown
## Blood Pressure [blood-pressure-tracker · 08:30]
- 135/85 mmHg, pulse 72
- Grade: Stage 1 HTN
- Pulse pressure: 50
- Morning surge: 27 mmHg (normal)
```

Multiple readings in one day -- list all:

```markdown
## Blood Pressure [blood-pressure-tracker · 20:15]
- 08:30: 135/85 mmHg, pulse 72 -- Stage 1 HTN
- 20:15: 128/82 mmHg, pulse 70 -- Elevated
- Daily average: 131.5/83.5 mmHg
```

### Item File (`memory/health/items/blood-pressure.md`)

```markdown
---
item: blood-pressure
unit: mmHg
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Blood Pressure Records

## Recent Status
- Latest: 135/85 mmHg, pulse 72 (YYYY-MM-DD 08:30)
- Grade: Stage 1 HTN
- 7-day average: 132/83 mmHg
- Trend: Stable
- Morning surge: Normal (avg 28 mmHg)

## History
| Date | Time | SBP | DBP | Pulse | Grade | PP | Notes |
|------|------|-----|-----|-------|-------|----|-------|
| 2026-03-10 | 08:30 | 135 | 85 | 72 | Stage 1 | 50 | Morning |
| 2026-03-10 | 20:15 | 128 | 82 | 70 | Elevated | 46 | Evening |
| 2026-03-09 | 08:15 | 130 | 84 | 74 | Stage 1 | 46 | Morning |
```

### Write Steps

1. Glob `memory/health/daily/` for today's file; create if absent.
2. Read the daily file.
3. Grep `## .* \[blood-pressure-tracker ·` for existing section.
4. Edit to replace (merge all same-day readings), or insert before `## Health Files` if new.
5. Update frontmatter `updated_at`.
6. Read `memory/health/items/blood-pressure.md` (create if absent).
7. Update `## Recent Status` (including 7-day average and trend).
8. Prepend new row to `## History` table.
9. Remove rows older than 90 days.
10. If alert triggered, prominently display in output.

## Alerts and Safety

### Alert Thresholds

| Condition | Level | Message |
|-----------|-------|---------|
| SBP >= 180 OR DBP >= 120 | URGENT | `[URGENT] BP at crisis level ({SBP}/{DBP}). Seek emergency care or call 120/911 immediately.` |
| 3 consecutive readings SBP >= 140 OR DBP >= 90 | Warning | `[Warning] 3 consecutive readings above target. Recommend medical review.` |
| Morning surge >= 35 mmHg | Warning | `[Warning] Morning surge detected ({X} mmHg). Recommend evaluation.` |
| PP > 60 mmHg | Notice | `[Notice] Pulse pressure {PP} mmHg is high. Monitor arteriosclerosis risk.` |
| Resting HR < 50 OR HR > 110 | Notice | `[Notice] Resting HR {HR} bpm abnormal. Recommend evaluation.` |

### Measurement Best Practices

- Rest quietly for 5 minutes before measuring.
- Sit with arm at heart level.
- Take 2-3 readings per session; use the average.
- Avoid measuring within 30 min of exercise, alcohol, or caffeine.
- Measure at consistent times daily (morning + before bed recommended).

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice. It does not diagnose hypertension, recommend or adjust antihypertensive medications, or replace 24-hour ambulatory blood pressure monitoring (ABPM).

**Seek emergency care if**: SBP >= 180 or DBP >= 120, especially with headache, blurred vision, chest pain, or dyspnea.

**See a doctor soon if**:
- BP above target (>= 140/90) for 1+ week
- Recurring positive morning surge
- Persistent PP > 60 mmHg
- Resting HR persistently < 50 or > 100
- On antihypertensive medication with inadequate control
