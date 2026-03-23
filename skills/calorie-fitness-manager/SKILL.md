---
name: calorie-fitness-manager
description: "Manages daily calorie balance and fitness tracking by coordinating BMR/TDEE calculation, nutrition analysis, food lookup, exercise stats, trend analysis, and SMART goal tracking. Use when the user wants to track calories, manage weight loss or gain, or optimize their fitness routine."
version: 1.0.0
user-invocable: true
argument-hint: "[daily-log | weekly-review | goal-setup]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🔥","category":"health-scenario"}}
---

# Calorie and Fitness Manager

Comprehensive calorie balance and fitness tracking skill for individuals managing weight loss, muscle gain, or general fitness optimization. Coordinates BMR/TDEE calculation, macronutrient analysis, food database lookup, exercise analysis, multi-dimensional trend correlation, SMART goal tracking, and optional wearable device integration to deliver daily, weekly, and monthly reports with an alert and milestone system.

## Skill Chain

| Step | Skill | Purpose | Trigger |
|------|-------|---------|---------|
| 1 | weightloss-analyzer | BMR/TDEE calculation, energy balance, weight prediction, plateau detection | Always |
| 2 | nutrition-analyzer | Macronutrient ratios, micronutrient RDA assessment, nutrition score | Always |
| 3 | food-database-query | Calorie/GI/nutrient lookup for logged foods | Always |
| 4 | fitness-analyzer | Exercise calorie burn (MET), training analysis, WHO/ACSM compliance | Always |
| 5 | health-trend-analyzer | Multi-dimensional correlation (calorie deficit vs weight, protein vs strength) | Always |
| 6 | goal-analyzer | SMART goal setting, progress tracking, habit assessment, motivation analysis | Always |
| 7 | wearable-analysis-agent | Integrate Apple Watch / Fitbit / Garmin data | When wearable data is provided |
| 8 | tcm-constitution-analyzer | TCM constitution-guided exercise and diet preferences | On first use or user request |
| 9 | health-memory | Persist daily data to memory files | Always |

## Workflow

### Mode 1: Daily Log

- [ ] Step 1: Calculate BMR (Mifflin-St Jeor) and TDEE via `weightloss-analyzer`. Track daily energy deficit/surplus. Predict weight change trajectory. Detect plateau (weight stagnant > 2 weeks despite calorie deficit).
- [ ] Step 2: Analyze macronutrient ratios (carbs/protein/fat) via `nutrition-analyzer`. Assess micronutrient intake against RDA. Generate nutrition score (0-100).
- [ ] Step 3: Look up calorie, GI, and nutrient details for each logged food via `food-database-query`. Fill in missing nutritional data.
- [ ] Step 4: Calculate exercise calorie burn using MET values via `fitness-analyzer`. Analyze training frequency/intensity/type distribution. Assess WHO/ACSM compliance (aerobic: 150-300 min/week moderate or 75-150 min/week vigorous; strength: 2+ sessions/week targeting major muscle groups). Track training progression (pace, weight, volume).
- [ ] Step 5: Run multi-dimensional trend correlation via `health-trend-analyzer`. Analyze calorie deficit vs weight change (Pearson), exercise volume vs body fat change, protein intake vs strength progression. Identify the most effective strategies for the user.
- [ ] Step 6: Track SMART goal progress via `goal-analyzer`. Assess completion percentage, on-track status, habit streak (consecutive logging days), consistency score, motivation curve. Identify obstacles and suggest countermeasures.
- [ ] Step 7 (optional): If wearable data is provided, integrate device data via `wearable-analysis-agent` for precise activity burn and heart rate data.
- [ ] Step 8 (optional): On first use or by request, perform TCM constitution assessment via `tcm-constitution-analyzer` to recommend suitable/unsuitable exercise types and dietary preferences.
- [ ] Step 9: Persist all daily data via `health-memory`. Write to `memory/health/daily/YYYY-MM-DD.md`. Update `memory/health/items/weight.md`, `memory/health/items/body-fat.md`, and `memory/health/items/calories.md`.

### Mode 2: Weekly Review

- [ ] Aggregate 7-day data: weight/body-fat trend table, average daily intake vs burn, cumulative weekly deficit, best training day analysis, training type distribution, nutrition score average, protein/fiber compliance rates, micronutrient gaps.
- [ ] Identify weekly patterns and generate improvement recommendations.

### Mode 3: Goal Setup

- [ ] Set or update SMART fitness goals via `goal-analyzer`: fat loss (target weight/body-fat + deadline), muscle gain (target measurements/strength + deadline).
- [ ] Validate goal feasibility (e.g., reject > 1 kg/week weight loss as unhealthy).
- [ ] Calculate required daily calorie deficit/surplus and macro targets.

## Input Format

| Input | Required | Description |
|-------|----------|-------------|
| Daily diet log | Yes | Three meals + snacks (food name, estimated portion) |
| Exercise log | Yes | Exercise type, duration, intensity |
| Body weight | Yes | Current weight in kg |
| Body fat percentage | No | Current body fat % (if scale supports it) |
| Body measurements | No | Waist/hip/arm circumference in cm |
| Wearable device data | No | Exported data from Apple Watch / Fitbit / Garmin |

## Output Format

### Daily Report Template

```
# Daily Calorie Balance Report -- YYYY-MM-DD

## Energy Balance
| Item | Value |
|------|-------|
| BMR (Basal Metabolic Rate) | xxxx kcal |
| Activity Burn | xxx kcal |
| TDEE (Total Daily Energy Expenditure) | xxxx kcal |
| Dietary Intake | xxxx kcal |
| **Net Deficit/Surplus** | **-xxx kcal** |

## Macronutrients
| Nutrient | Intake | Target | On Target |
|----------|--------|--------|-----------|
| Protein | xxg (xx%) | xxg | Yes/No |
| Carbohydrates | xxg (xx%) | xxg | Yes/No |
| Fat | xxg (xx%) | xxg | Yes/No |

## Exercise Summary
- Type: xxx, Duration: xx min, Burn: xxx kcal
- WHO guideline weekly cumulative: xx/150 min

## Today's Recommendations
- 1-2 specific, actionable recommendations based on today's data
```

### Weekly Report Template

```
# Weekly Report -- Week xx (MM-DD ~ MM-DD)

## Weight/Body Fat Trend
| Date | Weight (kg) | Body Fat (%) | Change |
| Weekly Avg | xx.x | xx.x | +/-x.x |

## Calorie Balance Summary
- Avg daily intake: xxxx kcal
- Avg daily burn: xxxx kcal
- Weekly cumulative deficit: -xxxx kcal (theoretical loss ~x.x kg)

## Best Training Day
- Day: xxx (burn xxx kcal, xx min)
- Type distribution: Aerobic xx% / Strength xx% / Flexibility xx%

## Nutrition Score: xx/100
- Protein compliance: xx%
- Dietary fiber compliance: xx%
- Micronutrient alert: xxx intake insufficient
```

### Monthly Report Template

```
# Monthly Report -- YYYY Month

## Goal Progress
- Goal: [fat loss / muscle gain] xx.x kg -> xx.x kg
- Progress: xx% (net +/-x.x kg)
- Predicted target date: YYYY-MM-DD
- Status: On Track / Needs Adjustment

## Body Composition Change
- Start -> End: xx.x kg -> xx.x kg (-x.x kg)
- Body fat: xx.x% -> xx.x%

## Strategy Adjustment Recommendations
- Personalized recommendations based on trend analysis
- Key improvement areas for next month
```

## Alert Rules

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Dangerously low calorie intake | Female < 1200 kcal/day or Male < 1500 kcal/day | Severe alert: recommend increasing intake immediately |
| Insufficient protein | < 0.8 g/kg body weight/day | Important alert: risk of muscle loss |
| Weight loss plateau | Weight stagnant > 2 weeks despite calorie deficit | Reminder: suggest strategy adjustment |
| Overtraining | 7 consecutive days of high-intensity exercise without rest | Important alert: recommend rest day |
| Rapid weight loss | > 1 kg/week | Important alert: may indicate unhealthy rate |
| Rapid weight gain | > 1.5 kg/week (not in bulking phase) | Reminder: review calorie surplus |

### Milestone Badges

Achievement system to motivate consistency:

- **First 5K**: First 5-kilometer run completed
- **Iron Week**: 5+ exercise days in one week
- **Protein Pro**: 7 consecutive days of protein target met
- **First Squat PR**: Personal record broken in strength training
- **Down 5kg**: Cumulative 5 kg weight loss achieved
- **100-Day Streak**: 100 consecutive days of logging
- **Nutrition Ace**: Single-day nutrition score of 90+

## Data Persistence

Managed via `health-memory`:

| File Path | Content |
|-----------|---------|
| `memory/health/daily/YYYY-MM-DD.md` | Daily diet/exercise/weight/calorie balance |
| `memory/health/items/weight.md` | Rolling 90-day weight record |
| `memory/health/items/body-fat.md` | Rolling 90-day body fat record |
| `memory/health/items/calories.md` | Rolling 90-day daily calorie balance |

## Medical Disclaimer

This skill provides guidance for health reference only and does not constitute medical or professional dietitian advice. Calorie intake must not fall below safety minimums (female 1200 kcal/day, male 1500 kcal/day). Extreme weight loss targets (> 1 kg/week) are flagged as unhealthy. If signs of eating disorder risk are detected (prolonged very low calorie intake, mention of purging), the skill immediately recommends professional help. Users with BMI < 18.5 are discouraged from fat loss goals. Exercise recommendations do not replace sports medicine evaluation; individuals with cardiovascular or joint conditions should consult a physician first. All nutritional calculations are database estimates with a potential 10-20% variance from actual values.
