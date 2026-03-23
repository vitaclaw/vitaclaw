---
name: chronic-condition-monitor
description: "Monitors multiple chronic disease indicators (BP, glucose, HbA1c, lipids, uric acid, creatinine, eGFR, liver function) against Chinese clinical guidelines. Detects abnormal trends, metabolic syndrome, and generates visit summaries. Use when the user tracks lab results or manages multiple chronic conditions."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏥","category":"health"}}
---

# Chronic Condition Monitor

Record and track multiple chronic disease indicators, detect abnormal trends, perform cross-indicator analysis, assess severity, and generate visit summaries.

## Capabilities

### 1. Multi-Indicator Recording

Track the following chronic disease indicators:

**Blood Pressure**: SBP / DBP (mmHg), pulse (bpm)

**Blood Glucose**: Fasting plasma glucose FPG (mmol/L), 2-hour postprandial glucose 2hPG (mmol/L), HbA1c (%)

**Weight & BMI**: Weight (kg), height (cm), BMI = weight(kg) / height(m)^2, waist circumference (cm)

**Uric Acid**: umol/L

**Kidney Function**: Serum creatinine Scr (umol/L), eGFR (mL/min/1.73m^2) via CKD-EPI 2021

**Lipid Panel**: Total cholesterol TC, triglycerides TG, LDL-C, HDL-C (all mmol/L)

**Liver Function**: ALT, AST (U/L)

### 2. Reference Ranges and Classification

> For complete reference ranges and classification thresholds, see [references/ranges.md](references/ranges.md)

Classification logic:
- Within normal range -> Normal
- Within caution range -> Elevated/Low, needs attention
- Reaches critical value -> Immediate alert, advise medical attention

### 3. Abnormal Trend Detection

**Consecutive Out-of-Range**:
- Check last N readings for each indicator
- 3+ consecutive readings above upper normal limit -> "Persistent elevation" alert
- 3+ consecutive readings below lower normal limit -> "Persistent low" alert

**Progressive Worsening**:
- Check whether last 3 readings show progressive deterioration
- Worsening = each reading worse than the previous (for rising-type indicators: each higher; for falling-type like HDL-C, eGFR: each lower)
- Progressive worsening -> "Progressive deterioration" alert

**Rate of Change**:
- Calculate change rate between last two readings
- Single change exceeding 20% of normal range -> "Rapid change" alert

**Detection Steps**:
1. Glob `memory/health/items/` to read indicator files
2. Extract last 5-10 records from `## History` table
3. Apply all three detection algorithms per indicator
4. Aggregate all alerts

### 4. Cross-Indicator Analysis

#### Metabolic Syndrome Detection

Diagnose metabolic syndrome when 3 of 5 criteria are met:

| # | Criterion | Threshold |
|---|-----------|-----------|
| 1 | Central obesity | Waist: male >= 90 cm, female >= 85 cm |
| 2 | Elevated triglycerides | TG >= 1.7 mmol/L |
| 3 | Low HDL-C | Male < 1.0 mmol/L, female < 1.3 mmol/L |
| 4 | Elevated blood pressure | SBP >= 130 or DBP >= 85 mmHg |
| 5 | Elevated fasting glucose | FPG >= 6.1 mmol/L |

Check each criterion against the most recent reading. >= 3 triggers metabolic syndrome warning.

#### Diabetes + Hypertension Comorbidity Alert

Trigger when both are met:
- FPG >= 7.0 mmol/L or HbA1c >= 6.5% (diabetes diagnostic criteria)
- SBP >= 140 or DBP >= 90 mmHg (hypertension diagnostic criteria)

Alert content:
- Diabetes combined with hypertension significantly increases cardiovascular risk
- Recommend stricter BP target: < 130/80 mmHg
- Recommend ACEI/ARB class antihypertensives (renal protective benefit)

#### CKD Progression Markers

Trigger CKD progression alert on any of:
- eGFR drops to a new CKD stage (e.g., G2 to G3a)
- eGFR annual decline rate > 5 mL/min/1.73m^2
- Creatinine rising for 3 consecutive readings

CKD staging reference (see kidney-function-tracker):
- G1: >= 90, G2: 60-89, G3a: 45-59, G3b: 30-44, G4: 15-29, G5: < 15

#### Hepatorenal Combined Abnormality

When ALT or AST is elevated AND creatinine is elevated or eGFR is decreased:
- Suggest possible drug-induced hepatorenal injury
- Recommend medication review
- Recommend prompt medical evaluation

### 5. Severity Grading

**Level 1 (Mild)**:
- Only 1 indicator mildly out of range (within caution range)
- No progressive worsening trend
- Recommendation: Continue monitoring, lifestyle adjustments

**Level 2 (Moderate)**:
- 2+ indicators out of normal range
- OR 1 indicator significantly elevated (beyond caution but below critical)
- OR progressive worsening trend detected
- Recommendation: Increase monitoring frequency, consider medical consultation

**Level 3 (Severe)**:
- Any indicator reaches critical value
- OR 3+ indicators simultaneously out of range
- OR rapid change detected (single change > 20%)
- OR metabolic syndrome detected
- Recommendation: **Seek immediate medical attention**, bring monitoring records

### 6. Visit Summary Generation

Generate a structured visit summary covering the last 3-6 months.

Steps:
1. Glob `memory/health/items/*.md` for all indicator files
2. Read each file, extract `## History` table data
3. Filter records from the last 3-6 months
4. Per indicator: compute latest, average, max, min, trend
5. Run trend detection and cross-indicator analysis
6. Read `memory/health/_health-profile.md` for baseline health info
7. Read `memory/health/items/medications.md` for current medications
8. Compile visit summary report

## eGFR Calculation (CKD-EPI 2021, Race-Free)

Auto-calculate eGFR when creatinine is recorded.

**Female**:
- Scr <= 0.7 mg/dL: eGFR = 142 * (Scr/0.7)^(-0.241) * 0.9938^age
- Scr > 0.7 mg/dL: eGFR = 142 * (Scr/0.7)^(-1.200) * 0.9938^age

**Male**:
- Scr <= 0.9 mg/dL: eGFR = 142 * (Scr/0.9)^(-0.302) * 0.9938^age
- Scr > 0.9 mg/dL: eGFR = 142 * (Scr/0.9)^(-1.200) * 0.9938^age

**Unit conversion**: Chinese labs report creatinine in umol/L. Convert first:
- Scr (mg/dL) = Scr (umol/L) / 88.4

## Input Format

User provides indicator values in natural language. Parse and match to known indicators. Examples:
- "BP 135/88, fasting glucose 6.8, uric acid 398"
- "Lab results: creatinine 95, TC 5.5, TG 1.9, LDL 3.6, HDL 1.15, ALT 35, AST 28"
- "Generate visit summary"
- "Show 3-month glucose trend"

## Output Format

### Indicator Dashboard

```markdown
# Chronic Condition Monitoring Report

## Date
YYYY-MM-DD

## Indicator Dashboard

| Indicator | Latest | Reference | Status | Trend |
|-----------|--------|-----------|--------|-------|
| Blood Pressure | 135/88 mmHg | < 120/80 | Elevated | Stable |
| Fasting Glucose | 6.8 mmol/L | 3.9-6.1 | Elevated | Rising |
| ... | ... | ... | ... | ... |

## Trend Alerts

### Persistent Elevation
- Fasting glucose: last 4 readings all above normal (6.5, 6.6, 6.7, 6.8)

### Progressive Deterioration
- Fasting glucose: 4 consecutive increases

### Rapid Change
- None

## Cross-Indicator Analysis

### Metabolic Syndrome Assessment
- [criteria evaluation, count met/5]
- **Result: meets N/5 criteria, [diagnosis or not]**

### Comorbidity Alerts
- [if applicable]

## Severity Assessment

**Overall Level: Level N (Mild/Moderate/Severe)**
- Abnormal indicators: N items
- Worsening trends: [details]
- Combined abnormalities: [details]
- **Recommendation: [action]**
```

### Visit Summary

```markdown
# Visit Summary

## Generated
YYYY-MM-DD (covering YYYY-MM-DD to YYYY-MM-DD)

## Basic Information
- Sex, Age, Height, Weight, BMI

## Current Medications
- [medication list with doses]

## Indicator Summary
### Blood Pressure (N readings)
| Stat | SBP | DBP |
|------|-----|-----|
| Latest / Average / Max / Min / Trend / Target rate |

### [Other indicators with similar tables]

## Issues Requiring Attention
1. [prioritized list]

## Suggested Discussion Topics
1. [for physician consultation]
```

## Data Persistence

Follow health-memory write protocol:

1. **Update daily file**: Insert/replace section `## Chronic Indicators [chronic-condition-monitor · HH:MM]`
2. **Update items files**: Update `## Recent Status`, prepend row to `## History` table, trim rows older than 90 days

Daily section format:
```markdown
## Chronic Indicators [chronic-condition-monitor · 09:30]
- Blood Pressure: 135/88 mmHg, pulse 75 -> Elevated
- Fasting Glucose: 6.8 mmol/L -> Impaired fasting glucose
- Severity: Level 2 (Moderate)
- Alerts: Progressive FPG increase, Metabolic syndrome risk
```

Data files:
- Daily logs: `memory/health/daily/YYYY-MM-DD.md`
- Indicator files: `memory/health/items/blood-pressure.md`, `blood-sugar.md`, `weight.md`, `uric-acid.md`, `kidney-function.md`, `blood-lipids.md`, `liver-function.md`
- Health profile: `memory/health/_health-profile.md`

## Alerts and Safety

### Critical Value Thresholds

Emit **immediate emergency alert** when any of the following are detected:
- SBP >= 180 mmHg or DBP >= 110 mmHg (hypertensive crisis)
- Blood glucose >= 16.7 mmol/L or <= 2.8 mmol/L
- eGFR < 15 mL/min/1.73m^2
- ALT or AST > 200 U/L

Alert message: **Seek immediate medical attention or call emergency services. This skill cannot replace emergency medical care.**

### Consult a Physician When

- Any indicator is abnormal for the first time
- An indicator shows persistent worsening
- Multiple indicators are simultaneously abnormal
- Metabolic syndrome screening is positive
- Medication adjustment is needed

### Medical Disclaimer

This skill is for health monitoring reference only. It does not constitute medical diagnosis or treatment advice. It does not diagnose diseases, formulate treatment plans, recommend medications, or replace physician consultations.
