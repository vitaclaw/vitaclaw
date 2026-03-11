---
name: diabetes-control-hub
description: "Manages comprehensive diabetes control by coordinating blood glucose tracking, nutrition analysis, exercise correlation, kidney function monitoring, and complication risk assessment. Use when a diabetes patient logs blood sugar, meals, or exercise, or needs checkup interpretation."
version: 1.0.0
user-invocable: true
argument-hint: "[daily-log | weekly-review | checkup-report]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🩸","category":"health-scenario"}}
---

# Diabetes Control Hub

Scenario orchestration skill for comprehensive diabetes management. Coordinates blood glucose tracking, dietary GI/GL analysis, exercise correlation, weight/metabolic monitoring, kidney function surveillance, and complication risk assessment. Targets patients with type 1 or type 2 diabetes who want a unified daily management workflow.

This skill does not perform analysis directly. It orchestrates multiple sub-skills in sequence to form a closed-loop diabetes management pipeline.

## Medical Disclaimer

**This skill is for health management reference only and does not constitute medical diagnosis or treatment advice.**

- All glycemic control plans require confirmation by an endocrinologist before execution.
- Insulin dose adjustments must be guided by a physician. This skill does not provide dosing recommendations.
- Severe hypoglycemia (confusion, seizures): call 120 (China) / 911 (US) immediately.
- Diabetic ketoacidosis (DKA) symptoms (nausea, vomiting, abdominal pain, Kussmaul breathing): seek emergency care immediately.

## Blood Glucose Target Reference

| Metric | Target Range | Notes |
|--------|-------------|-------|
| Fasting glucose | 4.4 - 7.0 mmol/L | Individualize based on patient profile |
| 2h postprandial glucose | < 10.0 mmol/L | Measured 2 hours after eating |
| HbA1c | < 7.0% | May relax for elderly or patients with complications |
| TIR (Time in Range) | >= 70% | Percentage of readings within 3.9 - 10.0 mmol/L |

**Estimated HbA1c formula**: eHbA1c = (mean glucose mmol/L + 2.59) / 1.59

## Skill Chain

| Step | Skill | Trigger | Purpose |
|------|-------|---------|---------|
| 1 | `chronic-condition-monitor` | Daily | Blood glucose trends, eHbA1c, TIR calculation |
| 2 | `nutrition-analyzer` | Daily | Carb counting, macronutrient ratios |
| 3 | `food-database-query` | Daily | GI/GL lookup, low-GI alternatives |
| 4 | `fitness-analyzer` | Daily | Exercise-glucose correlation |
| 5 | `weightloss-analyzer` | Daily | BMR/TDEE, body composition tracking |
| 6 | `wearable-analysis-agent` | When wearable data is provided | Activity tracking for exercise-glucose correlation, resting HR trend |
| 7 | `health-trend-analyzer` | Weekly | Multi-metric joint trend analysis |
| 8 | `kidney-function-tracker` | Ongoing | Creatinine/eGFR/UACR tracking |
| 9 | `checkup-report-interpreter` | On checkup | Lab report interpretation |
| 10 | `lab-results` | On checkup | Abnormal indicator trend comparison |
| 11 | `drug-interaction-checker` | On medication change | DDI safety check |
| 12 | `gwas-prs` | Annual / optional | T2D genetic risk assessment |
| 13 | `health-memory` | Every session | Data persistence |

## Workflow

### Mode 1: Daily Log

- [ ] **Step 1a -- Blood glucose and chronic condition recording.** Invoke `chronic-condition-monitor`. Record fasting/postprandial glucose to `memory/health/items/blood-sugar.md`. Compute 7-day/14-day/30-day glucose averages, eHbA1c, and TIR (percentage of readings within 3.9-10.0 mmol/L). Detect outliers and trigger alerts.
- [ ] **Step 1b -- Dietary nutrition analysis.** Invoke `nutrition-analyzer`. Analyze total carbohydrates per meal, dietary fiber intake, and daily total calories with macronutrient ratios.
- [ ] **Step 1c -- Glycemic index lookup.** Invoke `food-database-query`. Query GI (glycemic index) and GL (glycemic load) for each food item. Flag high-GI foods (>70) and suggest low-GI alternatives. Compute composite GL score per meal.
- [ ] **Step 1d -- Exercise and glucose correlation.** Invoke `fitness-analyzer`. Record exercise type, duration, and intensity. Analyze the effect of exercise on postprandial glucose (pre- vs post-exercise glucose comparison). Evaluate whether weekly exercise meets the 150-minute moderate-intensity aerobic recommendation.
- [ ] **Step 1e -- Weight and metabolic analysis.** Invoke `weightloss-analyzer`. Calculate BMR (basal metabolic rate) and TDEE (total daily energy expenditure). Track weight trend. Assess body fat percentage and waist circumference if data is available. Analyze energy balance.
- [ ] **Step 1f (optional) -- Wearable device data integration.** Invoke `wearable-analysis-agent` (when wearable data is provided). Analyze device-measured activity data (steps, active minutes, METs) to enhance exercise-glucose correlation in Step 1d with precise calorie burn and activity intensity. Extract resting heart rate trend as a cardiovascular risk indicator for diabetic patients. If continuous heart rate data spans exercise periods, correlate HR response with post-exercise glucose changes.
- [ ] **Step 1g -- Persist data.** Invoke `health-memory`. Write all data to `memory/health/daily/{YYYY-MM-DD}.md`. Update `memory/health/items/blood-sugar.md` and `memory/health/items/weight.md`.

### Mode 2: Weekly Review

- [ ] **Step 2 -- Multi-metric joint trend analysis.** Invoke `health-trend-analyzer`. Analyze: glucose + weight joint trend (weight change impact on glycemic control); glucose + exercise joint trend (exercise frequency/intensity vs glucose improvement); glucose + HbA1c trend (eHbA1c trajectory over time); dietary GI/GL + postprandial glucose trend (high-GI days vs low-GI days comparison).

### Mode 3: Checkup Report

- [ ] **Step 3a -- Lab report interpretation.** Invoke `checkup-report-interpreter`. Interpret HbA1c actual vs target. Interpret microalbuminuria (early renal damage marker). Interpret fundoscopy results (diabetic retinopathy screening). Interpret lipid profile (cardiovascular risk for diabetic patients). Interpret liver and kidney function markers.
- [ ] **Step 3b -- Abnormal indicator trend comparison.** Invoke `lab-results`. Compare current results against historical data. Flag significantly worsening indicators. Generate trend descriptions.

### Complication Monitoring (Ongoing)

- [ ] **Step C1 -- Kidney function tracking.** Invoke `kidney-function-tracker`. Track creatinine and eGFR values. Calculate eGFR rate of change (annual decline). Track UACR (urine albumin-to-creatinine ratio). Assess diabetic nephropathy staging if sufficient data.

### Medication Change (Event-Triggered)

- [ ] **Step M1 -- Drug interaction check.** Invoke `drug-interaction-checker`. Check interactions between new medication and existing diabetes drugs. Evaluate hypoglycemia risk (sulfonylurea + other glucose-lowering combinations). Flag high-risk combinations requiring physician confirmation.

### Genetic Risk Assessment (Annual / Optional)

- [ ] **Step G1 -- T2D polygenic risk scoring.** Invoke `gwas-prs` (requires genetic data). Calculate T2D polygenic risk score (PRS). Evaluate key loci (TCF7L2, KCNJ11, PPARG, etc.). Combine with family history to provide genetic risk tier.

## Input Format

### Daily Log

The user provides any combination of the following in natural language:

```
Blood glucose: fasting 6.2, post-lunch 8.5, post-dinner 9.1
Diet: breakfast oatmeal + egg, lunch rice + stir-fried broccoli + chicken breast, dinner buckwheat noodles + tofu
Exercise: 30-min brisk walk after dinner
Medications: metformin 500mg x2, acarbose 50mg x3
Weight: 72.5kg
```

Optional: Wearable device data (Apple Watch / Fitbit / Garmin export with activity and heart rate data).

### Checkup Report (Event-Triggered)

The user uploads or describes lab results (HbA1c, microalbumin, creatinine, eGFR, fundoscopy, etc.).

### Medication Change (Event-Triggered)

The user reports a medication adjustment (new drug, discontinuation, or dose change).

## Output Format

### Daily Briefing Template

```markdown
# Blood Glucose Daily Briefing -- YYYY-MM-DD

## Today's Glucose
| Timepoint | Glucose (mmol/L) | Status |
|-----------|-----------------|--------|
| Fasting | 6.2 | In range |
| 2h post-lunch | 8.5 | In range |
| 2h post-dinner | 9.1 | In range |

- Daily mean: 7.9 mmol/L
- eHbA1c: 6.6% (in range)
- TIR (past 7 days): 78% (in range, target >= 70%)

## Dietary GI Score
| Meal | Composite GL | Assessment |
|------|-------------|------------|
| Breakfast | 18 (low) | Oatmeal + egg, glucose-friendly |
| Lunch | 42 (medium) | White rice has high GL; consider brown rice |
| Dinner | 22 (low) | Buckwheat noodles + tofu, excellent choice |

## Exercise Notes
- Today: 30-min brisk walk (on target)
- Post-dinner glucose 9.1 -- consider extending post-meal walk by 10 min
- Weekly total: 120/150 min (30 min remaining to meet target)

## Alerts
(No alerts)
```

### Weekly Report Template

```markdown
# Weekly Glycemic Analysis -- YYYY-MM-DD to YYYY-MM-DD

## Glucose Target Achievement
- Fasting in range (4.4-7.0): 6/7 days (85.7%)
- Postprandial in range (<10.0): 12/14 readings (85.7%)
- TIR (3.9-10.0): 76% (in range)

## Best Meals TOP 3
1. Wed breakfast: oatmeal + nuts + blueberries -- postprandial 6.8
2. Fri dinner: buckwheat noodles + steamed fish + spinach -- postprandial 7.2
3. Sun lunch: brown rice + chicken breast + broccoli -- postprandial 7.5

## Worst Meals (Needs Improvement)
1. Sat lunch: white rice + braised pork + soda -- postprandial 12.3
2. Thu dinner: noodles + fried sauce -- postprandial 11.1

## Exercise-Glucose Correlation
- Exercise-day avg postprandial: 7.8 mmol/L
- Rest-day avg postprandial: 9.5 mmol/L
- Exercise lowers postprandial glucose by avg 1.7 mmol/L

## Weight Trend
- This week avg: 72.3 kg (vs last week -0.4 kg)
- Trend: gradual decrease, favorable for glycemic control
```

### Checkup Interpretation Template

```markdown
# Checkup Interpretation -- YYYY-MM-DD

## Core Diabetes Indicators
| Indicator | Current | Previous | Change | Assessment |
|-----------|---------|----------|--------|------------|
| HbA1c | 6.8% | 7.2% | -0.4% | Improved, in range |
| Fasting glucose | 6.5 | 7.1 | -0.6 | Improved |

## Complication Screening
| Item | Result | Assessment |
|------|--------|------------|
| UACR | 18 mg/g | Normal (<30) |
| eGFR | 92 mL/min | Normal (>90) |
| Fundoscopy | No abnormality | No retinopathy |
| LDL-C | 2.8 mmol/L | Elevated (diabetes target <2.6) |

## Risk Assessment
- Diabetic nephropathy risk: Low (UACR normal, eGFR normal)
- Retinopathy risk: Low (fundoscopy normal)
- Cardiovascular risk: Moderate (LDL-C elevated, recommend follow-up)

## Recommendations
1. HbA1c well-controlled; continue current regimen
2. LDL-C elevated; intensify dietary control or consult physician regarding statin therapy
3. Recheck HbA1c + microalbumin in 6 months
```

## Alert Rules

Alerts are displayed at the top of the output when triggered:

| Severity | Condition | Action |
|----------|-----------|--------|
| **Emergency** | Glucose < 3.9 mmol/L (hypoglycemia) | Consume 15g fast-acting carbs (glucose tablets/juice) immediately; recheck in 15 min; call 120/911 if unconscious |
| **Emergency** | Glucose > 16.7 mmol/L with nausea/vomiting | Suspected DKA; seek emergency care immediately |
| **High** | Postprandial glucose > 10.0 mmol/L for 3+ consecutive days | Contact physician to adjust treatment plan |
| **High** | eGFR declined > 15% from previous value | Recheck renal function urgently |
| **Medium** | Fasting glucose > 7.0 mmol/L for 5+ consecutive days | Review recent diet, exercise, and medication adherence |
| **Medium** | TIR < 50% for 2+ weeks | Poor glycemic control; recommend clinical evaluation |
| **Low** | Weight increase > 2 kg/month | Monitor caloric intake; assess medication factors |

## Data Persistence

All data is stored via the `health-memory` skill following its format conventions:

- **Daily records**: `memory/health/daily/YYYY-MM-DD.md` -- daily summary of glucose, diet, exercise, weight
- **Glucose longitudinal**: `memory/health/items/blood-sugar.md` -- most recent 90 days
- **Weight longitudinal**: `memory/health/items/weight.md` -- most recent 90 days
- **Kidney function longitudinal**: `memory/health/items/kidney-function.md` -- creatinine, eGFR tracking
- **Medication records**: `memory/health/items/medications.md` -- current medication list and change history
