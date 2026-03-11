---
name: hypertension-daily-copilot
description: "Provides comprehensive daily hypertension management by coordinating blood pressure tracking, medication adherence, DASH diet scoring, exercise monitoring, and trend analysis. Use when a hypertension patient wants daily BP management, weekly health reports, or medication reviews."
version: 1.0.0
user-invocable: true
argument-hint: "[daily-entry | weekly-review | medication-review]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🫀","category":"health-scenario"}}
---

# Hypertension Daily Copilot

Comprehensive daily hypertension management skill for patients living with high blood pressure who need structured BP tracking, medication adherence monitoring, DASH diet scoring, exercise compliance assessment, and multi-dimensional trend analysis. Coordinates blood pressure tracking, medication reminders, nutrition analysis, fitness analysis, trend correlation, weekly health digests, monthly drug interaction reviews, and emergency card updates to deliver daily briefings, weekly reports, and proactive alerts.

## Skill Chain

| Step | Skill | Purpose | Trigger |
|------|-------|---------|---------|
| 1 | blood-pressure-tracker | Record BP readings, classify grade, detect morning surge, analyze diurnal variation | Daily |
| 2 | medication-reminder | Track medication adherence, calculate compliance rate, flag missed doses | Daily |
| 3 | nutrition-analyzer | DASH diet scoring (sodium/potassium analysis, Na/K ratio, whole grains, fruits/vegetables) | Daily |
| 4 | fitness-analyzer | Exercise compliance (WHO hypertension guidelines), weekly cumulative tracking | Daily |
| 5 | health-trend-analyzer | Multi-dimensional correlation (BP vs sodium, exercise, weight, medication adherence) | Daily |
| 6 | wearable-analysis-agent | Continuous HR/HRV analysis, resting HR trend, activity tracking from wearable device data | When wearable data is provided |
| 7 | health-memory | Persist BP, medication, diet, and exercise data | Daily |
| 8 | weekly-health-digest | Weekly BP control rate, DASH score average, exercise/medication compliance summary | Weekly (weekend or on request) |
| 9 | drug-interaction-checker | Drug-drug interaction (DDI) review for all current medications | Monthly or on medication change |
| 10 | emergency-card | Update emergency information card with current diagnosis and medication regimen | On medication change |

## Workflow

### Mode 1: Daily Entry

- [ ] Step 1: Record BP readings via `blood-pressure-tracker` (supports multiple daily measurements). Analyze morning surge (morning BP minus overnight nadir; > 35 mmHg = morning surge hypertension with elevated cardiovascular risk). Analyze diurnal variation: dipper (night drop 10-20%, normal), non-dipper (< 10%, concerning), extreme dipper (> 20%, concerning), reverse dipper (night rise, high risk). Classify BP grade: normal (< 120/80), high-normal (120-139/80-89), grade 1 (140-159/90-99), grade 2 (160-179/100-109), grade 3 (>= 180/110).
- [ ] Step 2: Record medication intake via `medication-reminder`. Calculate adherence rate (7-day and 30-day on-time dosing percentage). Flag missed medications and assess impact. Classify adherence: >= 90% excellent, 70-89% good, 50-69% needs improvement, < 50% dangerous.
- [ ] Step 3: Score DASH diet compliance via `nutrition-analyzer`. Evaluate sodium intake (target: < 2300mg/day, ideal: < 1500mg/day), potassium intake (target: > 3500mg/day), Na/K ratio (target: < 1.0), whole grain/fruit/vegetable/low-fat dairy intake. Generate DASH score (0-100).
- [ ] Step 4: Assess exercise compliance via `fitness-analyzer`. Evaluate against WHO hypertension exercise guidelines: aerobic 150-300 min/week moderate intensity (brisk walking, swimming, cycling), resistance training 2-3 sessions/week moderate load, avoid prolonged isometric exercises (e.g., extended planking), breath-holding exercises, and sudden explosive movements. Calculate weekly cumulative volume.
- [ ] Step 5: Run multi-dimensional trend correlation via `health-trend-analyzer`. Analyze BP vs dietary sodium, BP vs exercise volume, BP vs weight change, BP vs medication adherence. Identify the most impactful modifiable factor for the user's BP.
- [ ] Step 6 (optional): If wearable data is provided, invoke `wearable-analysis-agent`. Extract resting heart rate trend (cardiovascular health indicator). Analyze HRV metrics (SDNN, RMSSD) as indicators of autonomic nervous system function and medication response. Validate exercise compliance using device-measured activity data (steps, active minutes, METs). If overnight HR data is available, enrich morning surge analysis from Step 1 with device-measured overnight HR nadir.
- [ ] Step 7: Persist all daily data via `health-memory`. Write to `memory/health/daily/YYYY-MM-DD.md`. Update `memory/health/items/blood-pressure.md` and `memory/health/items/medications.md`.

### Mode 2: Weekly Review

- [ ] Step 8: Generate weekly health summary via `weekly-health-digest`. Aggregate BP control rate (days < 140/90 as percentage), weekly DASH score average, exercise compliance, medication adherence. Generate trend chart data. Summarize weekly correlation findings. Produce improvement recommendations.

### Mode 3: Medication Review

- [ ] Step 9: Run drug-drug interaction (DDI) review via `drug-interaction-checker`. Audit all current medications for interactions. Focus areas: antihypertensive-antihypertensive interactions, antihypertensive interactions with other chronic disease medications (antidiabetics, lipid-lowering agents, anticoagulants), NSAID effects on antihypertensive efficacy. Classify by severity (severe/moderate/mild).
- [ ] Step 10: If medication regimen has changed, update emergency card via `emergency-card`. Include current diagnoses (hypertension + comorbidities), current medication regimen (drug/dose/frequency), allergy information, emergency contacts, and attending physician contact information.

## Input Format

### Daily Input

| Input | Required | Description |
|-------|----------|-------------|
| BP readings | Yes | Systolic/diastolic mmHg, pulse, measurement time (recommend morning + bedtime) |
| Medication log | Yes | Drug name, dose, time taken (e.g., "Amlodipine 5mg 08:00") |
| Diet summary | Yes | Meal overview (focus on high-sodium / high-potassium foods) |
| Exercise log | Yes | Exercise type, duration, intensity |
| Body weight | No | Recommend at least weekly |
| Symptoms/notes | No | Dizziness, headache, palpitations, or other symptoms |
| Wearable device data | No | Exported data from Apple Watch / Fitbit / Garmin (heart rate, HRV, activity) |

### Event-Triggered Input

| Event | Description |
|-------|-------------|
| Medication change | Triggers emergency card update |
| Weekend | Triggers weekly health summary |
| Month-end | Triggers monthly DDI review |

## Output Format

### Daily Briefing Template

```
# BP Management Daily Briefing -- YYYY-MM-DD

## Today's Blood Pressure
| Time | Systolic | Diastolic | Pulse | Grade |
| 07:00 (morning) | 135 | 85 | 72 | High-normal |
| 22:00 (bedtime) | 128 | 80 | 68 | High-normal |

- Morning surge: +xx mmHg (normal / elevated)
- Diurnal variation: dipper / non-dipper

## Medication Status
| Drug | Dose | Scheduled | Actual | Status |
| Amlodipine | 5mg | 08:00 | 08:15 | Taken |
| Valsartan | 80mg | 08:00 | 08:15 | Taken |
- 7-day adherence: xx%

## Diet Score
- DASH score: xx/100
- Sodium: ~xxxx mg (target < 2300 mg)
- Potassium: ~xxxx mg (target > 3500 mg)
- Na/K ratio: x.x (target < 1.0)

## Exercise Assessment
- Today: xxx, xx min, moderate intensity
- Weekly cumulative: xx/150 min (aerobic)

## Today's Recommendations
- 1-2 specific recommendations based on today's data
```

### Weekly Report Template

```
# Hypertension Management Weekly Report -- Week xx (MM-DD ~ MM-DD)

## BP Control Rate
- Days at target: x/7 (xx%)
- Mean systolic: xxx mmHg (target < 140)
- Mean diastolic: xx mmHg (target < 90)
- Trend: improving / stable / worsening

## Weekly BP Trend
| Date | Morning SBP/DBP | Bedtime SBP/DBP | Grade |

## Composite Scores
| Dimension | Score | Rating |
|-----------|-------|--------|
| BP control | xx/100 | Excellent/Good/Fair/Poor |
| Medication adherence | xx% | Excellent/Good/Needs improvement |
| DASH diet | xx/100 | Excellent/Good/Fair/Poor |
| Exercise compliance | xx/150 min | On target / Below target |

## Correlation Findings
- Significant associations found between BP and diet/exercise/weight this week
- Most impactful modifiable factor for BP

## Next Week Recommendations
- Specific improvement recommendations based on trend analysis
```

### Monthly DDI Review Template

```
# Monthly Drug Interaction Review -- YYYY Month

## Current Medication Regimen
| Drug | Dose | Frequency | Indication |

## DDI Review Results
| Drug Pair | Severity | Mechanism | Recommendation |

## Conclusion
- Current regimen safety assessment
- Interactions requiring monitoring
```

## Alert Rules

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Persistently elevated BP | > 140/90 for 3 consecutive days | Severe: recommend physician visit for regimen adjustment |
| Hypertensive crisis | Single reading >= 180/110 | Urgent: seek immediate medical attention |
| Morning surge hypertension | Morning surge > 35 mmHg | Important: inform physician, may need dosing time adjustment |
| Non-dipper pattern | Nighttime drop < 10% | Important: recommend 24-hour ambulatory BP monitoring |
| Low medication adherence | 7-day adherence < 70% | Important: analyze missed-dose reasons, adjust reminder strategy |
| Excessive sodium intake | Single day > 3000 mg | Reminder: identify high-sodium foods, suggest alternatives |
| Severe DDI detected | Severe drug-drug interaction found | Urgent: consult physician immediately |

## Data Persistence

Managed via `health-memory`:

| File Path | Content |
|-----------|---------|
| `memory/health/daily/YYYY-MM-DD.md` | Daily BP/medication/diet score/exercise |
| `memory/health/items/blood-pressure.md` | Rolling 90-day BP record |
| `memory/health/items/medications.md` | Medication record and adherence tracking |

## Medical Disclaimer

This skill is a supplementary tool for blood pressure management and does not replace physician care. Hypertensive crisis (>= 180/110 mmHg) triggers an urgent alert recommending immediate medical attention; no self-management advice is provided. This skill does not recommend adding, reducing, or switching medications; all medication adjustments must be decided by a physician. DDI reviews are supplementary references and do not replace pharmacist or physician professional judgment. If BP exceeds 140/90 for 3 consecutive days, seek medical attention rather than waiting. New symptoms such as dizziness, headache, chest tightness, or blurred vision require immediate medical attention and should not be attributed solely to BP fluctuation. Antihypertensive medications must not be self-discontinued even if BP normalizes. Improper measurement technique (e.g., measuring immediately after exercise, loose cuff) produces inaccurate readings that this skill cannot detect. DASH diet scores are based on self-reported intake; actual sodium consumption may be underestimated.
