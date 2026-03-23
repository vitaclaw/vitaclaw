---
name: hydration-tracker
description: "Tracks daily water intake, calculates personalized hydration targets based on body weight, activity level, and weather conditions, and provides reminders. Use when the user logs water intake, asks about hydration needs, or wants to analyze drinking patterns."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"💧","category":"health"}}
---

# Hydration Tracker

Tracks daily water intake, calculates personalized hydration targets based on body weight, activity level, and weather conditions, computes a hydration score (0-100), detects multi-day drinking patterns, evaluates beverage hydration equivalency, and provides dehydration warnings.

## Capabilities

### 1. Water Intake Recording

Extract from natural-language input (e.g., "drank 500ml water", "had 2 glasses of water", "finished a bottle of green tea"):

| Field | Required | Default if missing |
|-------|----------|--------------------|
| timestamp | Yes | current time |
| amount (ml) | Yes | see defaults below |
| beverage_type | No | water |
| temperature (hot/cold/room) | No | room |
| notes | No | omitted |

**Volume defaults**:

| Container | Default Volume |
|-----------|---------------|
| Glass | 250ml |
| Bottle | 500ml |
| Cup | 200ml |
| Mug | 300ml |
| Sip | 50ml |
| Large bottle | 750ml |

When the user says a number of glasses/bottles without specifying ml, multiply the count by the default volume.

### 2. Personalized Daily Target Calculation

```
Base Target = body_weight_kg × 30ml
```

If body weight is unknown, use 2000ml as the default base target and note the limitation.

**Adjustment factors** (additive):

| Factor | Adjustment |
|--------|-----------|
| Light exercise (30-60 min) | +500ml |
| Moderate exercise (60-90 min) | +750ml |
| Intense exercise (>90 min) | +1000ml |
| Hot weather (>30°C) | +500ml |
| Very hot weather (>35°C) | +750ml |
| Dry climate (<30% humidity) | +250ml |
| Caffeine (per 100mg consumed) | +150ml (compensate diuretic effect) |
| Alcohol consumption | +250ml per standard drink |
| Illness / fever | +500ml |
| Pregnancy | +300ml |
| Breastfeeding | +700ml |

```
Daily Target = Base Target + SUM(applicable adjustments)
```

For caffeine adjustment, read caffeine-tracker data from health-memory if available. Weather adjustments require user input or stored location/climate preferences.

### 3. Hydration Score (0-100)

```
Score = Intake_Ratio(50%) + Consistency(25%) + Timing_Distribution(25%)
```

#### 3.1 Intake Ratio Sub-score (weight 50%)

Ratio = actual effective intake / daily target (after applying beverage hydration factors from Section 4).

| Ratio | Points |
|-------|--------|
| 100-110% | 100 |
| 90-99% | 85 |
| 80-89% | 70 |
| 70-79% | 50 |
| 60-69% | 30 |
| < 60% | 10 |
| > 120% | 80 (overhydration concern) |
| > 150% | 50 (significant overhydration risk) |

Use linear interpolation within adjacent bands.

#### 3.2 Consistency Sub-score (weight 25%)

Standard deviation of daily effective intake over the last 7 days:

| SD (ml) | Points |
|---------|--------|
| < 200 | 100 |
| 200-400 | 80 |
| 400-600 | 50 |
| > 600 | 20 |

If fewer than 7 days available, compute on existing data and note the limitation.

#### 3.3 Timing Distribution Sub-score (weight 25%)

Measures how evenly spaced intake is throughout waking hours. Divide the waking day (assume 16 hours or use sleep data if available) into 4 equal blocks.

| Distribution | Points |
|--------------|--------|
| Each block has 20-30% of total | 100 |
| One block has 30-40% | 80 |
| One block has 40-50% | 50 |
| One block has >50% | 20 |

**Penalty**: If any single intake event exceeds 30% of the daily total, subtract 10 points from this sub-score (floor at 0). Large bolus intake is less effective for hydration.

### 4. Beverage Hydration Equivalency

Effective hydration = volume × hydration factor.

| Beverage | Hydration Factor | Notes |
|----------|-----------------|-------|
| Water | 1.0 | Gold standard |
| Herbal tea | 0.95 | Minimal diuretic effect |
| Green/black tea | 0.85 | Mild caffeine content |
| Coffee | 0.80 | Moderate diuretic effect |
| Juice | 0.85 | High sugar reduces absorption |
| Milk | 0.90 | Good hydration, contains electrolytes |
| Sports drink | 0.95 | Designed for rehydration |
| Coconut water | 0.95 | Natural electrolytes |
| Soda | 0.70 | Sugar and caffeine reduce effectiveness |
| Alcohol (beer) | 0.60 | Mild diuretic |
| Alcohol (wine) | -0.10 | Net dehydrating effect |
| Alcohol (spirits) | -0.20 | Strong diuretic effect |

Negative factors mean the beverage causes net fluid loss. When a negative-factor beverage is logged, record the volume but subtract the net loss from effective intake and flag the compensatory water needed.

### 5. Pattern Detection (7-30 days)

| Pattern | Condition | Suggestion |
|---------|-----------|------------|
| Chronic under-hydration | <70% target for 3+ consecutive days | Increase intake; set reminders; consult doctor if persistent |
| Front-loading | >50% intake in first 3 waking hours | Spread intake more evenly throughout the day |
| Back-loading | >50% intake in last 3 waking hours | Shift intake earlier; may disrupt sleep with nighttime bathroom trips |
| Caffeine-heavy hydration | >40% effective intake from caffeinated beverages | Substitute some caffeine drinks with water or herbal tea |
| Weekend drop-off | Weekend avg < 80% of weekday avg | Maintain hydration habits on weekends; set weekend reminders |
| Improving trend | 7-day moving average increasing, slope > 50ml/day | Acknowledge progress |
| Declining trend | 7-day moving average decreasing, slope < -50ml/day | Alert user; investigate cause |
| Alcohol impact | Alcohol logged on 3+ days in a week | Note cumulative dehydration effect; suggest compensatory water |
| Meal-only drinking | >70% of intake within 30 min of meal times | Encourage between-meal hydration |

### 6. Dehydration Warning Signs

#### Mild Dehydration (1-3% body water loss)
- Thirst
- Dry mouth and lips
- Slightly dark yellow urine
- Minor headache
- Mild fatigue

#### Moderate Dehydration (3-5% body water loss)
- Very dry mouth
- Dark amber urine, reduced frequency
- Dizziness or lightheadedness
- Muscle cramps
- Rapid heartbeat
- Decreased skin elasticity

#### Severe Dehydration (>5% body water loss) -- Seek Medical Attention
- Extreme thirst
- Very dark or no urine output
- Sunken eyes
- Confusion or irritability
- Rapid breathing
- Fainting
- Low blood pressure

**Urine Color Guide** (quick self-check):

| Color | Hydration Status |
|-------|-----------------|
| Pale straw / transparent yellow | Well hydrated |
| Dark yellow | Mildly dehydrated -- drink water soon |
| Amber / honey | Moderately dehydrated -- drink water now |
| Brown / dark amber | Severely dehydrated -- seek medical attention |

## Output Format

### Single Entry Log (brief)

```markdown
## Hydration [hydration-tracker · HH:MM]

- Logged: 500ml water (room temp) at 14:30
- Effective hydration: 500ml
- Daily progress: 1,750ml / 2,400ml (72.9%)
- ████████░░░░░░░ 73%
- Remaining: 650ml (~2.5 glasses)
```

### Daily Summary

```markdown
## Hydration Summary [hydration-tracker · HH:MM]

### Overview
- Daily target: 2,400ml
- Total intake: 2,250ml (7 entries)
- Effective hydration: 2,120ml
- Target achieved: 88.3%

### Progress
████████████████░░ 88%

### Intake Breakdown
| Time | Beverage | Volume | Factor | Effective |
|------|----------|--------|--------|-----------|
| 07:30 | Water | 250ml | 1.0 | 250ml |
| 09:00 | Coffee | 300ml | 0.8 | 240ml |
| 11:00 | Water | 500ml | 1.0 | 500ml |
| 13:00 | Water | 250ml | 1.0 | 250ml |
| 15:00 | Green tea | 200ml | 0.85 | 170ml |
| 17:30 | Water | 500ml | 1.0 | 500ml |
| 20:00 | Herbal tea | 250ml | 0.95 | 237ml |

### Hydration Score: 76 / 100
| Dimension | Raw | Sub-score | Weight | Weighted |
|-----------|-----|-----------|--------|----------|
| Intake Ratio | 88.3% | 70 | 50% | 35.0 |
| Consistency | SD=180ml | 100 | 25% | 25.0 |
| Timing Distribution | even | 64 | 25% | 16.0 |
| **Total** | | | | **76.0** |

### Insights
- Short of target by 280ml effective hydration
- Good consistency across recent days
- Intake slightly front-loaded; try to drink more in the afternoon
- Caffeine beverages account for 19% of intake (within acceptable range)
```

### Weekly Summary

```markdown
## Weekly Hydration Summary (MM-DD ~ MM-DD)

### Key Metrics
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Score | 79 | 74 | +5 |
| Avg Intake | 2,180ml | 1,950ml | +230ml |
| Avg Target | 2,400ml | 2,400ml | -- |
| Achievement | 90.8% | 81.3% | +9.5% |
| Best Day | Tue (105%) | Wed (95%) | |
| Worst Day | Sat (68%) | Sun (62%) | |

### Daily Detail
| Date | Intake | Target | % | Score | Top Beverage |
|------|--------|--------|---|-------|-------------|
| Mon | 2,300ml | 2,400ml | 96% | 82 | Water (75%) |
| Tue | 2,520ml | 2,400ml | 105% | 88 | Water (80%) |
| Wed | 2,200ml | 2,400ml | 92% | 80 | Water (70%) |
| Thu | 2,100ml | 2,400ml | 88% | 76 | Water (65%) |
| Fri | 2,350ml | 2,400ml | 98% | 84 | Water (72%) |
| Sat | 1,630ml | 2,400ml | 68% | 58 | Coffee (40%) |
| Sun | 2,150ml | 2,400ml | 90% | 78 | Water (68%) |

### Patterns
- [Notice] Weekend drop-off detected: Saturday intake was 68% of target
- [Notice] Saturday hydration was caffeine-heavy (40% from coffee)
- [Good] Weekday average 95.6% -- excellent consistency
- [Improving] Overall trend is positive: +5 points vs last week
- [Suggestion] Set weekend hydration reminders to maintain weekday habits
```

## Data Persistence

### Daily File (`memory/health/daily/YYYY-MM-DD.md`)

```markdown
## Hydration [hydration-tracker · HH:MM]
- Score: 76/100
- Intake: 2,250ml (effective: 2,120ml)
- Target: 2,400ml (88.3%)
- Entries: 7
- Top beverage: Water (75%)
- Timing: slightly front-loaded
```

### Item File (`memory/health/items/hydration.md`)

```markdown
---
item: hydration
unit: score (0-100)
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Hydration Records

## User Profile
- Body weight: 70kg
- Base target: 2,100ml
- Default adjustments: none
- Custom target override: none

## Recent Status
- Latest: Score 76, 2,250ml intake, 88.3% of target (YYYY-MM-DD)
- 7-day average score: 79
- 7-day average intake: 2,180ml
- 7-day average achievement: 90.8%
- Trend: Improving

## History
| Date | Score | Intake | Effective | Target | % | Entries | Notes |
|------|-------|--------|-----------|--------|---|---------|-------|
| 2026-03-22 | 76 | 2,250ml | 2,120ml | 2,400ml | 88% | 7 | |
| 2026-03-21 | 82 | 2,350ml | 2,280ml | 2,400ml | 95% | 8 | Exercise day |
```

### Write Steps

1. Glob `memory/health/daily/` for the target date file; create if absent.
2. Read the daily file.
3. Grep `## .* \[hydration-tracker ·` for existing section.
4. Edit to replace existing section, or insert before `## Health Files` if new.
5. Update frontmatter `updated_at`.
6. Read `memory/health/items/hydration.md` (create if absent).
7. Update `## Recent Status` (including 7-day averages) and prepend new row to `## History`.
8. Remove rows older than 90 days.

## Formulas and Reference Data

### Daily Target Calculation

```
Base = body_weight_kg × 30ml
Target = Base + SUM(adjustments)
```

### Effective Hydration

```
Effective = SUM(volume_i × hydration_factor_i) for each intake entry i
```

### Hydration Score

```
Score = (Intake_Ratio_Points × 0.50) + (Consistency_Points × 0.25) + (Timing_Points × 0.25)
```

### Trend Determination

Linear regression on last 7 days of scores:
- Slope > 1: Improving
- Slope < -1: Declining
- Otherwise: Stable

### Standard Deviation (Consistency)

```
SD = sqrt( (1/N) * SUM[(x_i - mean)^2] )
```

### Timing Distribution Calculation

1. Determine waking hours (use sleep data if available, otherwise assume 07:00-23:00).
2. Divide into 4 equal blocks (e.g., 07:00-11:00, 11:00-15:00, 15:00-19:00, 19:00-23:00).
3. Sum effective intake per block.
4. Calculate each block's percentage of total.
5. Score based on deviation from ideal 25% per block.

## Alerts and Safety

### Overhydration Warning

Drinking excessive water can cause hyponatremia (dangerously low blood sodium). Flag a warning if:
- Daily intake exceeds 150% of target
- Any single hour has intake > 1000ml
- Daily intake exceeds 4000ml without corresponding exercise or heat adjustment

**Symptoms of overhydration**: nausea, headache, confusion, seizures in severe cases.

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice. It does not diagnose dehydration disorders or replace clinical assessment.

**Consult a doctor if**:
- Chronic thirst persists despite adequate intake (may indicate diabetes or other conditions)
- Urine remains consistently dark despite drinking sufficient water
- History of kidney disease, heart failure, or electrolyte disorders
- Experiencing symptoms of severe dehydration or overhydration
- Taking diuretic medications or other drugs affecting fluid balance
- Hydration needs during illness are unclear (especially with vomiting or diarrhea)
