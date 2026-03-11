---
name: caffeine-sleep-advisor
description: "Analyzes the relationship between caffeine consumption and sleep quality by coordinating caffeine tracking, sleep analysis, and trend correlation. Identifies personal sensitivity thresholds and optimal caffeine cutoff times. Use when the user wants to understand how coffee affects their sleep."
version: 1.0.0
user-invocable: true
argument-hint: "[log-beverage | sleep-report | weekly-analysis]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"☕","category":"health-scenario"}}
---

# Caffeine and Sleep Advisor

Analyzes the relationship between caffeine consumption and sleep quality for individuals who drink coffee or tea regularly and want to optimize both enjoyment and rest. Coordinates caffeine intake tracking with half-life decay modeling, sleep quality analysis, personalized improvement recommendations, trend correlation to identify sensitivity thresholds, optional CYP1A2 genotype analysis, and beverage hidden-calorie assessment.

## Skill Chain

| Step | Skill | Purpose | Trigger |
|------|-------|---------|---------|
| 1 | caffeine-tracker | Log beverages, compute residual caffeine via half-life decay, predict safe sleep time | Always |
| 2 | sleep-analyzer | Calculate sleep efficiency, sleep score, onset latency analysis, sleep stage breakdown | Always |
| 3 | sleep-optimizer | Generate personalized sleep improvement recommendations based on caffeine + sleep data | Always |
| 4 | health-trend-analyzer | Correlate caffeine intake vs sleep quality, identify personal sensitivity thresholds | Always |
| 5 | nutrigx_advisor | CYP1A2 genotype analysis to determine fast/intermediate/slow metabolizer status | When genetic data with CYP1A2 is provided |
| 6 | nutrition-analyzer | Analyze hidden calories and sugar in caffeinated beverages | Always |
| 7 | wearable-analysis-agent | Sleep staging (deep/light/REM/awake) and HRV analysis from wearable device data | When wearable sleep data is provided |
| 8 | health-memory | Persist caffeine and sleep data to memory files | Always |

## Workflow

### Mode 1: Log Beverage

- [ ] Step 1: Record all caffeinated beverages via `caffeine-tracker`. Apply half-life decay model (`C(t) = C0 * 0.5^(t/t_half)`, default t_half = 5.7h, adjustable by genotype from Step 5). Calculate residual caffeine at any time point. Predict safe sleep time (residual < 50mg). Compare daily total against WHO recommended limit (400 mg/day).
- [ ] Step 6: Analyze hidden calories and sugar in logged beverages via `nutrition-analyzer`. Calculate extra calories from sugary coffee drinks (mocha, frappuccino). Suggest low-calorie alternatives.
- [ ] Step 8: Persist caffeine intake data via `health-memory`.

### Mode 2: Sleep Report

- [ ] Step 2: Analyze last night's sleep via `sleep-analyzer`. Calculate sleep efficiency (actual sleep / time in bed * 100%). Compute composite sleep score (duration, efficiency, onset latency, night awakenings). Classify onset latency: < 15 min excellent, 15-30 min normal, 30-60 min prolonged, > 60 min difficulty. If device data available, analyze sleep stages (deep/light/REM/awake).
- [ ] Step 7 (optional): If wearable sleep data is provided, invoke `wearable-analysis-agent` for device-measured sleep staging (deep/light/REM/awake breakdown), heart rate variability during sleep, and resting heart rate. Feed processed sleep stages into Step 2's analysis to replace subjective estimates with objective device data.
- [ ] Step 3: Generate personalized improvement recommendations via `sleep-optimizer` based on caffeine and sleep data. Dimensions: personalized caffeine cutoff time (data-driven, not generic), alternative beverage suggestions (decaf, herbal tea, low-caffeine options), sleep hygiene habits (blue light, temperature, schedule regularity), bedtime ritual suggestions.
- [ ] Step 8: Persist sleep data via `health-memory`.

### Mode 3: Weekly Analysis

- [ ] Step 4: Run caffeine-sleep correlation analysis via `health-trend-analyzer`. Compute Pearson correlation: total caffeine vs sleep score, afternoon caffeine vs onset latency. Identify personal sensitivity thresholds (e.g., "> 200mg total intake correlates with significantly longer onset latency", "intake > 80mg after 14:00 correlates with > 15% sleep score decline"). Generate weekly correlation chart data.
- [ ] Step 5 (optional): If CYP1A2 genetic data is provided, analyze genotype via `nutrigx_advisor`. Determine rs762551 genotype: AA (fast metabolizer, ~4h half-life, higher tolerance), AC (intermediate metabolizer, ~5.5h half-life), CC (slow metabolizer, ~7h half-life, high sensitivity). Adjust half-life parameter in Step 1. Generate genotype-guided caffeine limits: fast 400mg/day cutoff 15:00, intermediate 300mg/day cutoff 14:00, slow 200mg/day cutoff 12:00.

### Common Beverage Caffeine Reference

| Beverage | Serving | Caffeine (mg) |
|----------|---------|---------------|
| Americano | 350ml | 150 |
| Latte / Cappuccino | 350ml | 75-80 |
| Espresso | 30ml | 63 |
| Black tea | 240ml | 47 |
| Green tea | 240ml | 28 |
| Cola | 330ml | 34 |
| Red Bull | 250ml | 80 |
| Matcha latte | 350ml | 70 |
| Decaf coffee | 350ml | 5-15 |

## Input Format

| Input | Required | Description |
|-------|----------|-------------|
| Daily beverage log | Yes | Beverage type, serving size, time consumed (e.g., "Americano 350ml 08:30") |
| Sleep data | Yes | Bedtime, wake time, subjective sleep quality (1-10) |
| Sleep device data | No | Auto-recorded sleep stage data from Apple Watch / Fitbit / Oura / smart band |
| Genetic test data | No | Report containing CYP1A2 genotype |

## Output Format

### Daily Report Template

```
# Caffeine and Sleep Daily Report -- YYYY-MM-DD

## Today's Caffeine Intake
| Time | Beverage | Caffeine (mg) |
| 08:30 | Americano 350ml | 150 |
| 14:00 | Latte 350ml | 80 |
| **Total** | | **230 mg** |

## Residual Caffeine Status
- Current residual: ~xxx mg (as of HH:MM)
- Estimated safe sleep time: **HH:MM** (residual < 50mg)
- Daily limit assessment: 230/400 mg (within safe range)

## Last Night's Sleep Review
- Duration: x hours xx minutes
- Sleep efficiency: xx%
- Onset latency: xx minutes
- Sleep score: xx/100

## Today's Recommendations
- No further caffeine recommended after current time
- Suggest starting bedtime routine at xx:xx
```

### Weekly Report Template

```
# Caffeine and Sleep Weekly Report -- Week xx

## Weekly Overview
| Date | Caffeine (mg) | Sleep Score | Onset Latency (min) |

## Correlation Analysis
- Total caffeine <-> Sleep score: r = -0.xx
- Afternoon caffeine <-> Onset latency: r = +0.xx
- Correlation strength: weak / moderate / strong

## Personal Sensitivity Findings
- Sensitivity threshold: sleep quality declines significantly when daily total > xxx mg
- Safe cutoff time: recommend no caffeine after HH:MM

## Weekly Recommendations
- 1-3 data-driven personalized recommendations
```

### Genotype Report Template (if genetic data available)

```
## CYP1A2 Caffeine Metabolism Gene Analysis
- Genotype: rs762551 -- AA / AC / CC
- Metabolizer type: Fast / Intermediate / Slow
- Estimated half-life: ~x.x hours
- Personalized recommendations:
  - Daily caffeine limit: xxx mg
  - Recommended cutoff time: HH:MM
  - Per-serving recommended limit: xxx mg
```

## Alert Rules

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Daily overconsumption | Total intake > 400mg | Important alert: exceeds WHO daily limit |
| High evening residual | Residual > 100mg after 18:00 | Reminder: likely to impair sleep |
| Poor sleep streak | Sleep score < 60 for 3 consecutive days | Important alert: evaluate caffeine and sleep hygiene |
| Onset difficulty | Onset latency > 45 minutes | Reminder: flag for potential intervention |
| Slow metabolizer overconsumption | CC genotype and intake > 200mg | Important alert: exceeds genotype-adjusted limit |

## Data Persistence

Managed via `health-memory`:

| File Path | Content |
|-----------|---------|
| `memory/health/daily/YYYY-MM-DD.md` | Daily caffeine intake + sleep data |
| `memory/health/items/caffeine.md` | Rolling 90-day daily caffeine intake record |
| `memory/health/items/sleep.md` | Rolling 90-day sleep score/efficiency/latency record |

## Medical Disclaimer

This skill provides guidance for health reference only and does not constitute medical advice. Caffeine sensitivity varies widely between individuals; threshold analysis is based on statistical correlation, not causal diagnosis. Genetic test results are reference information; actual metabolism is influenced by multiple factors (medications, liver function, age). The WHO-recommended caffeine limit for pregnant women is 200mg/day; this skill does not auto-adjust this parameter and requires user notification. Insomnia may have many causes (anxiety, pain, medication side effects) and should not be attributed solely to caffeine. Persistent severe insomnia (onset latency > 45 minutes for 2+ consecutive weeks) warrants medical attention, and this skill will proactively remind the user. Certain medications (e.g., fluvoxamine, ciprofloxacin) significantly inhibit CYP1A2, prolonging caffeine half-life; extra caution is advised during use of these medications.
