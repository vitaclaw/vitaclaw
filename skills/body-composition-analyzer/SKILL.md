---
name: body-composition-analyzer
description: "Analyzes body composition metrics including body fat percentage, muscle mass, visceral fat, and BMI. Tracks trends over time and provides training and nutrition recommendations based on body composition goals. Use when the user logs body measurements, DEXA/BIA results, or asks about body composition."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📊","category":"health"}}
---

# Body Composition Analyzer

Analyzes body composition metrics, classifies results, tracks trends over time, and provides evidence-based training and nutrition recommendations based on body composition goals.

## Capabilities

### 1. Measurement Recording

Record and store body composition measurements with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| date | ISO date | Date of measurement (YYYY-MM-DD) |
| weight_kg | float | Body weight in kilograms |
| body_fat_pct | float | Body fat percentage |
| muscle_mass_kg | float | Skeletal muscle mass in kilograms |
| visceral_fat_level | int | Visceral fat level (1-59 scale, varies by device) |
| bone_mass_kg | float | Estimated bone mineral content in kilograms |
| water_pct | float | Total body water percentage |
| BMI | float | Body Mass Index (auto-calculated if height is known) |
| waist_circumference_cm | float | Waist circumference in centimeters |
| hip_circumference_cm | float | Hip circumference in centimeters |
| measurement_method | enum | One of: scale, DEXA, BIA, caliper, tape |
| notes | string | Free-text notes (e.g., fasted, post-workout, dehydrated) |

When the user provides a measurement:

1. Parse the values from user input (accept metric or imperial, convert internally to metric).
2. Validate ranges (e.g., body fat 2-60%, weight 20-300 kg, visceral fat 1-59).
3. Flag any values that seem out of range and confirm with the user before saving.
4. Store the entry in the daily file and append to the longitudinal tracker.

### 2. Body Fat Classification

Classify the user's body fat percentage using the American Council on Exercise (ACE) categories:

| Category | Men | Women |
|----------|-----|-------|
| Essential fat | 2-5% | 10-13% |
| Athletic | 6-13% | 14-20% |
| Fitness | 14-17% | 21-24% |
| Average | 18-24% | 25-31% |
| Obese | >25% | >32% |

When reporting body fat classification:

- Always specify which category the user falls into.
- Show how far the user is from adjacent category boundaries.
- Note that these ranges are general guidelines and individual variation exists.
- If sex is not known, present both columns and ask the user to confirm.

### 3. BMI Calculation & Context

Calculate BMI using the standard formula:

```
BMI = weight(kg) / height(m)^2
```

Classify results using the WHO categories:

| Category | BMI Range |
|----------|-----------|
| Underweight | <18.5 |
| Normal weight | 18.5-24.9 |
| Overweight | 25-29.9 |
| Obese Class I | 30-34.9 |
| Obese Class II | 35-39.9 |
| Obese Class III | >=40 |

**Important BMI limitations to always communicate:**

- BMI does not distinguish between muscle mass and fat mass. A muscular individual may have a high BMI but low body fat.
- BMI thresholds vary by ethnicity. For example, Asian populations may have higher health risks at lower BMI values (WHO suggests overweight at >=23 for Asian populations).
- BMI is a population-level screening tool, not a diagnostic measure for individuals.
- Always present BMI alongside body fat percentage and waist-to-hip ratio for a more complete picture.

### 4. Waist-to-Hip Ratio (WHR)

Calculate WHR:

```
WHR = waist_circumference_cm / hip_circumference_cm
```

Classify cardiovascular and metabolic risk:

| Risk Level | Men | Women |
|------------|-----|-------|
| Low | <0.90 | <0.80 |
| Moderate | 0.90-0.99 | 0.80-0.85 |
| High | >=1.0 | >0.85 |

Additional context:

- Waist circumference alone is also a useful metric: >102 cm (men) or >88 cm (women) indicates elevated risk (WHO).
- WHR is a stronger predictor of cardiovascular disease risk than BMI alone.
- Measure waist at the narrowest point between the lowest rib and the iliac crest.

### 5. Body Fat Estimation Methods

#### Navy Method

Estimate body fat from circumference measurements using the U.S. Navy formula:

**Men:**
```
%BF = 86.010 * log10(waist_cm - neck_cm) - 70.041 * log10(height_cm) + 36.76
```

**Women:**
```
%BF = 163.205 * log10(waist_cm + hip_cm - neck_cm) - 97.684 * log10(height_cm) - 78.387
```

Required measurements: waist, neck, height (and hip for women). Accuracy: +/- 3-4%.

#### DEXA Scan Interpretation Guide

- DEXA (Dual-Energy X-ray Absorptiometry) is the gold standard for body composition.
- Reports regional fat distribution (android vs gynoid), total body fat %, lean mass, and bone mineral density.
- Typical accuracy: +/- 1-2%.
- Compare DEXA results only with other DEXA results (not with BIA or caliper readings).
- Android/Gynoid ratio > 1.0 suggests central adiposity and elevated metabolic risk.

#### BIA Scale Accuracy Notes

- Bioelectrical Impedance Analysis (BIA) accuracy is heavily influenced by hydration status.
- Best practices for consistent BIA readings:
  - Measure at the same time of day (ideally morning).
  - Avoid eating or drinking 2-4 hours before measurement.
  - Avoid exercise 12 hours before measurement.
  - Avoid alcohol 24 hours before measurement.
  - Ensure consistent hydration day-to-day.
- BIA can vary by 3-5% based on hydration alone. Treat trends as more meaningful than individual readings.
- Multi-frequency BIA devices are more accurate than single-frequency.

#### Skinfold Caliper Methods

**3-Site Method (Jackson-Pollock):**
- Men: chest, abdomen, thigh
- Women: triceps, suprailiac, thigh

**7-Site Method (Jackson-Pollock):**
- Sites: chest, midaxillary, triceps, subscapular, abdomen, suprailiac, thigh
- More accurate than 3-site but requires experienced technician.
- Accuracy: +/- 3-4% with skilled measurer.
- Always take measurements on the right side of the body.
- Take 2-3 readings at each site and average them.

### 6. Trend Analysis

When analyzing body composition trends over time:

#### Weight Change Rate
- Healthy fat loss rate: 0.5-1% of body weight per week (e.g., 0.4-0.8 kg/week for an 80 kg person).
- Faster rates increase risk of muscle loss, metabolic adaptation, and rebound.
- Weight gain for muscle building: 0.25-0.5% of body weight per week to minimize fat gain.

#### Body Fat Trajectory
- Track body fat percentage change over 4-week rolling windows.
- A decrease of 0.5-1% body fat per month is a good rate for most people.
- Plateau detection: flag if body fat has not changed by more than 0.3% over 6+ weeks.

#### Lean Mass Preservation During Cuts
- During a caloric deficit, monitor the ratio of weight lost from fat vs lean mass.
- **Alert**: Flag if more than 25% of total weight loss is coming from lean mass.
- Recommendations if lean mass loss is excessive:
  - Increase protein intake (target 2.0-2.4 g/kg).
  - Reduce caloric deficit (no more than 500 kcal/day).
  - Ensure resistance training volume is maintained or increased.
  - Consider diet breaks (1-2 weeks at maintenance every 8-12 weeks).

#### Recomposition Tracking
- Simultaneous fat loss and muscle gain (body recomposition) is possible, especially for:
  - Beginners (first 1-2 years of training).
  - Returning trainees (muscle memory effect).
  - Individuals with higher body fat (>20% men, >30% women).
  - Those on optimized protein intake and training programs.
- Track by monitoring body fat % decrease AND lean mass increase over the same period.
- Scale weight may remain stable during recomposition; this is expected and not a sign of failure.

#### Seasonal Patterns
- Identify recurring patterns (e.g., holiday weight gain, summer cut cycles).
- Use year-over-year comparisons when data is available.
- Help the user plan around known seasonal challenges.

### 7. Goal-Based Recommendations

Provide tailored recommendations based on the user's stated goal:

| Goal | Caloric Target | Protein | Training Focus |
|------|---------------|---------|----------------|
| Fat loss | -300 to -500 kcal deficit | 1.6-2.2 g/kg body weight | Resistance training + moderate cardio |
| Muscle gain | +200 to +400 kcal surplus | 1.6-2.2 g/kg body weight | Progressive overload, compound lifts |
| Recomposition | ~maintenance calories | 2.0-2.4 g/kg body weight | Resistance training priority |
| Maintenance | TDEE | 1.2-1.6 g/kg body weight | Mixed training modalities |

Additional guidance per goal:

- **Fat loss**: Prioritize resistance training to preserve lean mass. Cardio should supplement, not replace, strength training. Aim for 3-5 resistance sessions and 2-3 moderate cardio sessions per week. Consider refeed days at maintenance calories 1x per week if deficit is aggressive.
- **Muscle gain**: Focus on progressive overload (increasing weight, reps, or sets over time). Ensure adequate sleep (7-9 hours) for recovery. A slight caloric surplus minimizes fat gain compared to aggressive bulking.
- **Recomposition**: Most effective with higher protein intake and well-periodized resistance training. Progress will be slower on the scale but visible in body composition metrics. Patience is key; expect meaningful changes over 3-6 months.
- **Maintenance**: Focus on sustainability. Adjust caloric intake seasonally or based on activity level changes. Continue training to prevent age-related muscle loss (sarcopenia).

### 8. Body Composition Score (0-100)

Calculate a composite body composition health score using the following weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Body Fat Range | 30% | How close body fat % is to optimal range for age and sex |
| Muscle Mass | 25% | Skeletal muscle mass relative to height and sex norms |
| Visceral Fat | 20% | Visceral fat level (lower is better; <10 is healthy) |
| WHR | 15% | Waist-to-hip ratio relative to low-risk thresholds |
| Trend Direction | 10% | Whether metrics are moving toward or away from goals |

Scoring methodology:

- Each component is scored 0-100 individually.
- **Body Fat Range**: 100 if within the "Fitness" range, scaled down proportionally as it moves toward "Essential" or "Obese" ranges.
- **Muscle Mass**: 100 if at or above the 75th percentile for age/sex, scaled down for lower values.
- **Visceral Fat**: 100 if level 1-5, 80 if 6-9, 60 if 10-14, 40 if 15-19, 20 if 20+.
- **WHR**: 100 if in "Low" risk, 60 if "Moderate", 20 if "High".
- **Trend Direction**: 100 if all metrics moving toward goals, 50 if stable, 0 if moving away from goals.

The final score is the weighted sum. Present alongside a brief interpretation:

- 85-100: Excellent body composition
- 70-84: Good body composition
- 55-69: Average body composition
- 40-54: Below average, recommend focused attention
- <40: Significant room for improvement, consider professional guidance

### 9. Measurement Consistency Guide

To ensure reliable and comparable measurements over time, advise the user to follow these standardization practices:

#### Timing
- **Time of day**: Measure first thing in the morning.
- **Fasting state**: Before eating or drinking anything.
- **Post-bathroom**: After using the restroom.
- **Pre-exercise**: Before any physical activity.

#### Conditions
- **Same scale**: Always use the same device.
- **Same clothing**: Minimal clothing or nude; consistent each time.
- **Same hydration state**: Avoid measuring after heavy alcohol consumption, illness, or unusual fluid intake.
- **Surface**: Place scale on hard, flat surface (not carpet).

#### Frequency
- **Weight**: Weekly (same day each week). Optionally daily, using a 7-day rolling average to smooth fluctuations.
- **Body fat (BIA/caliper)**: Monthly at most. More frequent measurements introduce noise.
- **DEXA scan**: Quarterly (every 3 months) for precise tracking. More frequent is unnecessary and costly.
- **Circumference measurements**: Bi-weekly or monthly. Mark measurement sites with a washable marker for consistency.

## Output Format

### Measurement Entry Response

When a user logs a new measurement, respond with:

```
## Body Composition Entry - [DATE]

**Measurements:**
- Weight: [X] kg ([change from last] kg)
- Body Fat: [X]% ([classification]) ([change from last]%)
- Muscle Mass: [X] kg ([change from last] kg)
- Visceral Fat: Level [X] ([risk level])
- BMI: [X] ([classification])
- WHR: [X] ([risk level])

**Composition Score:** [X]/100 ([interpretation])

**Trend (last [N] entries):**
- Weight: [direction] ([rate]/week)
- Body Fat: [direction] ([rate]/month)
- Lean Mass: [preserved/declining]

**Notes:** [any flags, alerts, or observations]
```

### Progress Report

When the user requests a progress report, provide:

```
## Body Composition Progress Report
**Period:** [start date] to [end date]

### Summary
- Starting weight: [X] kg -> Current: [X] kg (net: [+/-X] kg)
- Starting body fat: [X]% -> Current: [X]% (net: [+/-X]%)
- Starting muscle mass: [X] kg -> Current: [X] kg (net: [+/-X] kg)
- Composition Score: [start] -> [current]

### Analysis
[Narrative analysis of trends, rate of change, lean mass preservation, etc.]

### Recommendations
[Goal-specific recommendations based on current trajectory]
```

### Goal Tracking

When tracking toward a specific goal:

```
## Goal Progress: [Goal Name]
**Target:** [specific target, e.g., 15% body fat]
**Current:** [current value]
**Gap:** [difference]
**Estimated time to goal:** [weeks/months at current rate]
**On track:** [Yes/No/Needs adjustment]
```

## Data Persistence

### Daily File

Store each measurement entry in the user's daily file at the standard daily file path, under a `## Body Composition` section.

### Longitudinal Tracker

Maintain a persistent body composition tracking file at `items/body-composition.md` with the following structure:

```markdown
# Body Composition Tracker

## Profile
- Height: [X] cm
- Sex: [M/F]
- Age: [X]
- Activity level: [sedentary/lightly active/moderately active/very active/extremely active]

## Current Goals
- Primary: [goal]
- Target body fat: [X]%
- Target weight: [X] kg

## Measurement History

| Date | Weight (kg) | BF% | Muscle (kg) | Visceral | BMI | WHR | Method | Score | Notes |
|------|-------------|-----|-------------|----------|-----|-----|--------|-------|-------|
| [date] | [val] | [val] | [val] | [val] | [val] | [val] | [method] | [score] | [notes] |

## Milestones
- [date]: [milestone achieved, e.g., "Reached 'Fitness' body fat range"]
```

When writing to this file:

1. Read the existing file first to preserve previous entries.
2. Append new measurement rows to the history table.
3. Update the "Current Goals" section if the user changes goals.
4. Add milestones when the user crosses a classification boundary or reaches a target.

## Alerts and Safety

### Body Dysmorphia Awareness
- Focus language on health, performance, and how the user feels rather than appearance.
- If the user sets goals that are in the "Essential fat" range or below, gently note the health risks and suggest consulting a healthcare provider.
- Avoid language that could reinforce unhealthy relationships with body image.
- Celebrate non-scale victories (strength gains, energy levels, sleep quality).

### Extremely Low Body Fat Warning
- Men below 5% or women below 12% body fat face serious health consequences including hormonal disruption, immune suppression, bone density loss, and organ damage.
- If a user's body fat approaches these levels, provide a clear warning and recommend medical supervision.
- Competitive bodybuilders and athletes who intentionally reach very low body fat should be reminded this is a temporary state and not sustainable long-term.

### Rapid Weight Loss Alert
- Flag if the user is losing more than 1% of body weight per week consistently (over 2+ weeks).
- Potential causes: excessive caloric deficit, muscle loss, dehydration, or underlying medical issue.
- Recommend slowing the rate of loss, increasing protein, and consulting a healthcare provider if the cause is unclear.

### Muscle Loss During Deficit
- If lean mass is decreasing and accounts for more than 25% of total weight lost, alert the user.
- Provide specific corrective actions: increase protein, reduce deficit, maintain or increase resistance training volume.

### Medical Disclaimer
- Body composition analysis provided here is for informational and educational purposes only.
- It is not a substitute for professional medical body composition assessment, diagnosis, or treatment.
- Users with medical conditions, eating disorders, or those on medication that affects body composition should consult their healthcare provider.
- DEXA scan results should be interpreted by a qualified professional for clinical decision-making.
- Recommend annual check-ups and professional body composition assessments for baseline comparisons.
