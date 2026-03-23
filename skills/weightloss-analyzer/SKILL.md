---
name: weightloss-analyzer
description: "Analyzes weight loss data, calculates metabolic rates (BMR/TDEE), tracks energy deficits, and manages weight loss phases including plateau detection. Provides body composition analysis and personalized calorie targets. Use when the user wants to set up a weight loss plan, calculate metabolism, or track their deficit progress."
version: 1.0.0
user-invocable: true
argument-hint: "[setup | bmr | track | report | plateau-check]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"⚖️","category":"health-analyzer"}}
---

# Weight Loss Analyzer Skill

Analyzes weight loss data, calculates metabolic rates, tracks energy deficits, and manages weight loss phases.

## Features

### 1. Body Composition Analysis

**BMI Calculation and Classification**
- BMI = weight (kg) / height (m)^2
- Classification criteria (per WHO Asian standards, per Chinese clinical guidelines):
  - Underweight: BMI < 18.5
  - Normal: 18.5 <= BMI < 24
  - Overweight: 24 <= BMI < 28
  - Obese: BMI >= 28

**Body Fat Percentage Assessment**
- Male: 15-20% (normal), 20-25% (slightly high), >25% (obese)
- Female: 20-25% (normal), 25-30% (slightly high), >30% (obese)

**Circumference Analysis**
- Waist circumference assessment
  - Male: < 90 cm (normal), >= 90 cm (abdominal obesity)
  - Female: < 85 cm (normal), >= 85 cm (abdominal obesity)
- Waist-to-hip ratio
  - Male: < 0.9 (normal), >= 0.9 (abdominal obesity)
  - Female: < 0.85 (normal), >= 0.85 (abdominal obesity)

**Ideal Weight Calculation**
- BMI method: ideal weight = height (m)^2 x 22
- Modified Broca formula: ideal weight = (height in cm - 100) x 0.9

### 2. Metabolic Rate Calculation

**Harris-Benedict Equation (1919 Original)**
- Male: BMR = 88.362 + (13.397 x weight kg) + (4.799 x height cm) - (5.677 x age)
- Female: BMR = 447.593 + (9.247 x weight kg) + (3.098 x height cm) - (4.330 x age)

**Mifflin-St Jeor Equation (recommended, more accurate)**
- Male: BMR = (10 x weight kg) + (6.25 x height cm) - (5 x age) + 5
- Female: BMR = (10 x weight kg) + (6.25 x height cm) - (5 x age) - 161

**Katch-McArdle Equation (based on lean body mass)**
- BMR = 370 + (21.6 x lean body mass kg)
- Lean body mass = weight kg x (1 - body fat percentage)

**TDEE Calculation**
- TDEE = BMR x activity factor
- Activity factors:
  - Sedentary: 1.2
  - Lightly active: 1.375
  - Moderately active: 1.55
  - Highly active: 1.725
  - Very highly active: 1.9

### 3. Energy Deficit Management

**Daily Energy Deficit Tracking**
- Deficit = TDEE - actual intake + exercise expenditure
- Deficit target analysis: actual deficit vs. target deficit

**Weight Loss Estimation**
- 1 kg of fat ~ 7700 kcal
- Estimated weekly weight loss = daily deficit x 7 / 7700
- Safe weight loss rate: 0.5-1 kg/week (deficit 500-1000 kcal/day)

**Calorie Safety Thresholds**
- Minimum calorie for males: 1500 kcal/day
- Minimum calorie for females: 1200 kcal/day
- Absolute minimum: BMR x 1.2

### 4. Phase Management

**Weight Loss Phase**
- Track weight changes
- Calculate weight loss progress
- Monitor weight loss rate

**Plateau Detection**
- Definition: No significant weight change for 2+ weeks (fluctuation < 0.5 kg)
- Cause analysis: Metabolic adaptation, water retention, muscle gain
- Breakthrough methods: Adjust calories, change exercise routine, intermittent fasting

**Maintenance Phase**
- Within target weight +/- 2 kg range
- Regular weight monitoring
- Timely plan adjustments

## Data Sources

### Primary Data Sources

1. **Fitness tracker**
   - Path: `data/fitness-tracker.json`
   - Content: Weight records, body composition, metabolic rates, phase management

2. **Nutrition tracker**
   - Path: `data/nutrition-tracker.json`
   - Content: Calorie intake, energy deficit, meal plans

3. **Health logs**
   - Path: `data/health-logs/YYYY-MM/YYYY-MM-DD.json`
   - Content: Daily weight, diet records

## Output Format

### Body Composition Analysis Report

```markdown
# Body Composition Analysis Report

## Basic Information
- Gender: Male
- Age: 52
- Height: 175 cm
- Weight: 75 kg

## Body Metrics

### BMI
- Current BMI: 24.5
- Classification: Overweight
- Ideal weight: 67 kg (BMI=22)
- Weight to lose: 8 kg

### Body Fat Percentage
- Current body fat: 25%
- Classification: Slightly high
- Target body fat: 15-20%

### Circumference Analysis
- Waist: 92 cm (abdominal obesity risk)
- Hip: 98 cm
- Waist-to-hip ratio: 0.94 (abdominal obesity)

## Recommendations
1. Target weight loss of 0.5-1 kg/week
2. Target weight loss duration: 8-16 weeks
3. Combined intervention: diet + exercise
```

### Metabolic Rate Analysis Report

```markdown
# Metabolic Rate Analysis Report

## BMR Calculation

| Formula | BMR | Notes |
|---------|-----|-------|
| Harris-Benedict | 1650 | 1919 original formula |
| Mifflin-St Jeor | 1620 | Recommended |
| Katch-McArdle | 1700 | Based on body fat percentage |

**Recommended BMR: 1620 kcal/day**

## TDEE Calculation

- Activity level: Moderately active
- Activity factor: 1.55
- TDEE: 1620 x 1.55 = **2511 kcal/day**

### Calorie Distribution
- BMR basal metabolism: 65% ~ 1632 kcal
- Exercise expenditure: 20% ~ 502 kcal
- NEAT daily activity: 15% ~ 377 kcal

## Weight Loss Calorie Targets

### Moderate Weight Loss Plan
- Daily deficit: 500 kcal
- Target intake: 2011 kcal/day
- Estimated weight loss: 0.5 kg/week

### Aggressive Weight Loss Plan
- Daily deficit: 750 kcal
- Target intake: 1761 kcal/day
- Estimated weight loss: 0.75 kg/week

### Rapid Weight Loss Plan
- Daily deficit: 1000 kcal
- Target intake: 1511 kcal/day
- Estimated weight loss: 1 kg/week
- Warning: Short-term use only

## Safety Check
- Minimum calorie requirement: 1500 kcal/day (male)
- Rapid plan calories: 1511 kcal/day (passes)
- Recommended choice: Moderate or aggressive plan
```

### Energy Deficit Tracking Report

```markdown
# Energy Deficit Tracking Report

## Weekly Summary (2025-06-16 to 2025-06-22)

| Day | Intake | Exercise Burn | NEAT | Deficit | On Target |
|-----|--------|--------------|------|---------|-----------|
| Mon | 1800 | 350 | 300 | 961 | Yes |
| Tue | 2100 | 200 | 250 | 461 | No |
| Wed | 1750 | 400 | 300 | 1061 | Yes |
| Thu | 1950 | 300 | 280 | 741 | Yes |
| Fri | 2200 | 150 | 200 | 261 | No |
| Sat | 2400 | 100 | 150 | -89 | No |
| Sun | 1850 | 350 | 300 | 911 | Yes |

**Target deficit: 500 kcal/day**

## Statistical Analysis
- Average deficit: 642 kcal/day
- Days on target: 5/7 (71%)
- Total deficit: 4494 kcal
- Estimated weight loss: 0.58 kg

## Trend Analysis
- Weekend deficit tends to be smaller (increased social activities)
- Recommendation: Plan weekend meals in advance

## Next Week Goals
- Days on target: 7/7
- Average deficit: 700 kcal/day
- Estimated weight loss: 0.64 kg
```

### Phase Management Report

```markdown
# Weight Loss Phase Management Report

## Current Phase: Weight Loss Phase

### Progress Tracking
- Start date: 2025-01-01
- Initial weight: 82 kg
- Current weight: 75 kg
- Target weight: 67 kg
- Weight lost: 7 kg
- Remaining: 8 kg
- Progress: 47%

### Weight Loss Rate
- Total weeks: 24
- Average weight loss: 0.29 kg/week
- Last 4 weeks: 0.35 kg/week (accelerating)

## Status Analysis

### Current Status: Good
- Weight loss rate within healthy range (0.5-1 kg/week)
- Metabolic rate stable
- Muscle mass well maintained

### Plateau Monitoring
- Last 2-week change: -0.8 kg
- Status: Not in plateau

## Next Steps
1. Continue current calorie plan
2. Increase strength training frequency
3. Monitor body composition weekly
```

## Usage

Invoked via `/fitness:weightloss-*` and `/nutrition:weightloss-*` commands.

### Example Commands

```bash
# Set up weight loss plan
/fitness:weightloss-setup --weight 75 --height 175 --age 52 --gender male

# Calculate metabolic rate
/fitness:weightloss-bmr --formula mifflin

# Track energy deficit
/nutrition:weightloss-track --intake 1800 --exercise 350

# Generate phase report
/fitness:weightloss-report

# Check for plateau
/fitness:weightloss-plateau-check
```

## Safety Principles

### Calorie Safety Thresholds
- Not recommended < 1200 kcal/day (female)
- Not recommended < 1500 kcal/day (male)
- Absolute minimum no lower than BMR x 1.2

### Weight Loss Rate Control
- Safe range: 0.5-1 kg/week
- Maximum: 1.5 kg/week
- Long-term average: 0.5-0.8 kg/week

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice.

Consult a physician in the following situations:
- BMI > 35
- Have chronic conditions such as heart disease, hypertension, or diabetes
- Taking prescription medications
- Women who are pregnant or breastfeeding
- Any uncertain health conditions
