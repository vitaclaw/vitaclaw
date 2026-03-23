---
name: circadian-rhythm-optimizer
description: "Analyzes circadian rhythm patterns, assesses chronotype (morningness-eveningness), provides light exposure protocols, optimizes meal/exercise/sleep timing windows, and supports jet lag recovery and shift work adaptation. Use when the user asks about their body clock, optimal daily timing, light exposure, jet lag, or shift schedules."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"☀️","category":"health"}}
---

# Circadian Rhythm Optimizer

Analyzes circadian rhythm patterns and provides personalized timing optimization. Assesses chronotype via MEQ scoring, designs light exposure protocols, calculates optimal windows for sleep/meals/exercise/cognitive work, manages jet lag recovery plans, supports shift work adaptation, computes a Circadian Health Score (0-100), and tracks core body temperature rhythm correlation.

## Capabilities

### 1. Chronotype Assessment

Use the reduced Morningness-Eveningness Questionnaire (rMEQ, 5 items) for quick assessment, or full MEQ-19 if user provides all answers.

#### rMEQ Scoring (5 items, range 4-25)

| Score | Chronotype | Label |
|-------|-----------|-------|
| 4-7 | Definitely Evening | 🦉 Night Owl |
| 8-11 | Moderately Evening | 🌙 Evening type |
| 12-17 | Intermediate | ⚖️ Neutral |
| 18-21 | Moderately Morning | 🌅 Morning type |
| 22-25 | Definitely Morning | 🐓 Early Bird |

#### rMEQ Questions

1. **Wake-up time preference** (if entirely free to plan): 05:00-06:30 (5), 06:30-07:45 (4), 07:45-09:45 (3), 09:45-11:00 (2), 11:00-12:00 (1)
2. **Tiredness in first 30 min after waking**: Very tired (1), Fairly tired (2), Fairly refreshed (3), Very refreshed (4)
3. **Time you feel your best**: 05:00-08:00 (5), 08:00-10:00 (4), 10:00-17:00 (3), 17:00-22:00 (2), 22:00-05:00 (1)
4. **Morning or evening person self-assessment**: Definitely morning (6), More morning than evening (4), More evening than morning (2), Definitely evening (0)
5. **Peak alertness if you went to bed at 23:00**: Before 08:00 (5), 08:00-10:00 (4), 10:00-14:00 (3), 14:00-17:00 (2), After 17:00 (1)

#### Simplified Estimation

If formal questionnaire is not completed, estimate from behavioral cues:
- Natural wake time (no alarm) → midpoint of sleep = dim-light melatonin onset (DLMO) estimate
- DLMO ≈ mid-sleep - 7 hours (population average)
- Chronotype = Early if DLMO < 20:00, Intermediate if 20:00-22:00, Late if > 22:00

### 2. Light Exposure Protocol

#### Morning Bright Light (Circadian Advance)

| Parameter | Recommendation |
|-----------|---------------|
| Timing | Within 30-60 min of waking |
| Duration | 20-30 min minimum |
| Intensity | ≥ 10,000 lux (light therapy box) or direct outdoor sunlight |
| Distance | 30-40 cm from light box, no direct staring |
| Best for | Evening types wanting to shift earlier, winter blues |

#### Evening Light Restriction (Circadian Maintenance)

| Parameter | Recommendation |
|-----------|---------------|
| Timing | 2-3 hours before target bedtime |
| Blue light | Use blue-light blocking glasses or night mode (< 50 lux) |
| Screen brightness | ≤ 30% with warm color temperature (≤ 2700K) |
| Room lighting | Dim, warm-toned (≤ 50 lux at eye level) |
| Best for | Everyone; critical for delayed sleep phase |

#### Light Exposure Schedule by Chronotype

| Chronotype | Morning Light | Evening Light Cutoff | Melatonin Window |
|------------|--------------|---------------------|------------------|
| Early Bird | 05:30-07:00 | 19:00 | 19:00-20:00 |
| Morning type | 06:00-07:30 | 20:00 | 20:00-21:00 |
| Neutral | 07:00-08:30 | 21:00 | 21:00-22:00 |
| Evening type | 08:00-09:30 | 22:00 | 22:00-23:00 |
| Night Owl | 09:00-10:30 | 23:00 | 23:00-00:00 |

### 3. Optimal Timing Windows

Based on chronotype and estimated DLMO, compute personalized windows.

#### Timing Offset Model

Define T0 = estimated habitual wake time. All windows are relative offsets:

| Activity | Window (T0 + offset) | Rationale |
|----------|----------------------|-----------|
| Peak alertness | T0 + 2-4h | Post-cortisol awakening response peak |
| Deep cognitive work | T0 + 2-4h | Prefrontal cortex optimal |
| Creative/divergent thinking | T0 + 10-12h | Reduced inhibitory control, wider associative thinking |
| Strength training | T0 + 8-11h | Core body temp peak → max muscle performance |
| Cardio/endurance | T0 + 6-9h | Lung function peaks, lower perceived exertion |
| Reaction time | T0 + 8-10h | Fastest neural processing |
| Learning/memorization | T0 + 1-3h (morning) or T0 + 10h (evening review) | Encoding + consolidation cycle |
| Nap window | T0 + 7-8h | Post-lunch circadian dip; limit 20 min |
| Melatonin onset | T0 + 14-16h | DLMO; avoid bright light after this |
| Optimal bedtime | T0 + 15-17h | 2 hours after DLMO |

#### Example Output (for wake time 07:00)

| Activity | Optimal Window |
|----------|---------------|
| Deep cognitive work | 09:00-11:00 |
| Creative thinking | 17:00-19:00 |
| Strength training | 15:00-18:00 |
| Cardio | 13:00-16:00 |
| Nap | 14:00-15:00 (≤20 min) |
| Light restriction begins | 20:00 |
| Bedtime | 22:00-23:00 |

### 4. Meal Timing & Circadian Nutrition

#### Time-Restricted Eating (TRE) Windows

| Pattern | Eating Window | Fasting Window | Notes |
|---------|-------------|----------------|-------|
| 16:8 | T0+1h to T0+9h | 15 hours | Most studied protocol |
| 14:10 | T0+1h to T0+11h | 13 hours | Moderate; easier adherence |
| 12:12 | T0+1h to T0+13h | 11 hours | Minimal circadian benefit |

#### Meal Timing Principles

- **Breakfast**: Within 1-2h of waking; largest meal of the day for circadian alignment
- **Lunch**: T0 + 5-7h; moderate portion
- **Dinner**: ≥ 3h before bedtime; smallest meal; avoid high-glycemic foods
- **Late eating penalty**: Eating within 2h of bedtime delays melatonin onset by ~30 min and impairs glucose tolerance by ~17%

#### Nutrient Timing

| Nutrient | Optimal Timing | Reason |
|----------|---------------|--------|
| Protein | Morning + post-exercise | Muscle protein synthesis peaks in morning |
| Complex carbs | Lunch/early afternoon | Serotonin → melatonin precursor pathway |
| Caffeine | T0+1h to T0+8h only | Half-life ~5h; later intake delays sleep onset |
| Magnesium | Evening (with dinner) | Supports GABA pathway, aids sleep onset |
| Tryptophan-rich foods | Dinner | Melatonin precursor |

### 5. Jet Lag Recovery Protocol

#### Jet Lag Severity Estimation

```
Recovery days ≈ (time zones crossed) × direction_factor
  Eastward: direction_factor = 1.0 day per zone
  Westward: direction_factor = 0.67 day per zone
```

#### Pre-Travel Preparation (3-5 days before departure)

| Direction | Daily Shift | Method |
|-----------|------------|--------|
| Eastward (1-3 zones) | Advance bedtime 30 min/day | Earlier light exposure + earlier meals |
| Eastward (4-8 zones) | Advance bedtime 30 min/day | + Low-dose melatonin (0.5 mg) at destination bedtime |
| Westward (1-3 zones) | Delay bedtime 30 min/day | Later light exposure + later meals |
| Westward (4-8 zones) | Delay bedtime 30 min/day | Morning bright light at current location |

#### Post-Arrival Protocol

| Day | Eastward Travel | Westward Travel |
|-----|----------------|----------------|
| Day 1 | Seek bright light in local morning; avoid PM light | Seek bright light in local afternoon/evening |
| Day 2-3 | Maintain local meal times strictly | Delay sleep to local bedtime; short nap OK (≤20 min) |
| Day 4+ | Light exposure normalized | Should be mostly adapted |

#### Anti-Jet-Lag Meal Strategy (Argonne Protocol)

- **Day -3**: High-protein breakfast, high-carb dinner (feast day)
- **Day -2**: Light meals, low calorie (fast day)
- **Day -1**: Feast day (repeat day -3 pattern)
- **Travel day**: Fast until breakfast at destination time → strong zeitgeber reset

### 6. Shift Work Adaptation

#### Shift Types and Strategies

| Shift | Hours (typical) | Light Strategy | Sleep Strategy |
|-------|----------------|----------------|----------------|
| Morning (06-14) | Bright light at start | Sleep 21:00-05:00; blackout curtains |
| Afternoon (14-22) | Natural light adequate | Sleep 23:00-07:00; relatively normal |
| Night (22-06) | Bright light 00:00-04:00 | Sleep 07:00-15:00; blackout + ear plugs |
| Rotating | See rotation protocol | Anchor sleep strategy |

#### Night Shift Protocol

1. **Before first night shift**: Nap 2-4h in the afternoon
2. **During shift**: Bright light exposure (≥ 2,500 lux) during first half; dim light last 2h
3. **Commute home**: Wear dark sunglasses to avoid morning light
4. **Sleep environment**: Blackout curtains, 18-20°C, white noise
5. **Anchor sleep**: Keep ≥ 4h of sleep at the same time every day (including days off)

#### Rotation Recovery

| Rotation Direction | Ease of Adaptation | Strategy |
|-------------------|-------------------|----------|
| Forward (M→A→N) | Easier (delay) | Shift sleep 2h later each rotation |
| Backward (N→A→M) | Harder (advance) | Shift sleep 1h earlier; use morning light |
| Rapid rotation (≤3 days) | Do not fully adapt | Maintain intermediate schedule; strategic napping |

#### Shift Work Health Monitoring

Flag increased risk for:
- Metabolic syndrome (meal timing disruption)
- Cardiovascular issues (chronic misalignment)
- Mood disturbances (serotonin/melatonin disruption)
- GI issues (eating during biological night)

### 7. Circadian Health Score (0-100)

```
Score = Sleep Timing(25%) + Light Exposure(25%) + Meal Timing(20%) + Consistency(20%) + Activity Timing(10%)
```

#### 7.1 Sleep Timing Sub-score (weight 25%)

| Alignment | Points |
|-----------|--------|
| Bedtime within 30 min of chronotype-optimal | 100 |
| Bedtime within 1h of optimal | 80 |
| Bedtime within 2h of optimal | 50 |
| Bedtime > 2h from optimal | 20 |
| Social jet lag (weekday-weekend midpoint diff) < 1h | +0 (no penalty) |
| Social jet lag 1-2h | -10 |
| Social jet lag > 2h | -25 |

#### 7.2 Light Exposure Sub-score (weight 25%)

| Behavior | Points |
|----------|--------|
| ≥ 30 min bright light within 1h of waking | 100 |
| 15-30 min bright light within 2h of waking | 70 |
| Some outdoor light but inconsistent | 40 |
| Minimal morning light exposure | 15 |
| Evening blue-light restriction practiced | +10 bonus (cap 100) |

#### 7.3 Meal Timing Sub-score (weight 20%)

| Behavior | Points |
|----------|--------|
| All meals within 10h window, dinner ≥ 3h before bed | 100 |
| Meals within 12h window, dinner ≥ 2h before bed | 80 |
| Meals within 14h window | 50 |
| Irregular meal timing or late-night eating | 20 |

#### 7.4 Consistency Sub-score (weight 20%)

Standard deviation of bedtime and wake time over last 7 days:

| SD (minutes) | Points |
|--------------|--------|
| ≤ 15 | 100 |
| 16-30 | 85 |
| 31-45 | 65 |
| 46-60 | 45 |
| > 60 | 20 |

#### 7.5 Activity Timing Sub-score (weight 10%)

| Behavior | Points |
|----------|--------|
| Exercise within optimal chronotype window | 100 |
| Exercise within 2h of optimal window | 75 |
| Exercise at any consistent time | 50 |
| Exercise within 2h of bedtime | 20 |
| No regular exercise | 10 |

#### Score Interpretation

| Score | Level | Interpretation |
|-------|-------|---------------|
| 90-100 | Excellent | Strong circadian alignment; maintain current habits |
| 75-89 | Good | Minor adjustments needed; review weakest sub-score |
| 60-74 | Fair | Moderate misalignment; focus on 1-2 key areas |
| 40-59 | Poor | Significant disruption; structured intervention recommended |
| < 40 | Critical | Severe misalignment; health risks elevated; prioritize sleep timing and light |

### 8. Temperature & Circadian Rhythm

#### Core Body Temperature (CBT) Rhythm

- **CBT minimum**: ~2h before habitual wake time (most reliable circadian marker)
- **CBT peak**: ~T0 + 10-12h (late afternoon)
- **Amplitude**: ~0.5-1.0°C variation across 24h

#### Temperature-Based Optimization

| Observation | Interpretation | Action |
|-------------|---------------|--------|
| Waking feels easy, alert | Waking after CBT minimum | Schedule is well-aligned |
| Waking feels very difficult | Waking near/before CBT minimum | Sleep phase may be delayed; advance with morning light |
| Afternoon energy crash severe | May coincide with post-lunch dip | Normal; schedule nap or light activity |
| Feeling cold in evening | Early circadian phase | May indicate early chronotype |

#### Using Wearable Temperature Data

If wrist/skin temperature data available:
- Identify nadir (lowest point) → estimate CBT minimum
- Track nadir drift over days → detect phase shifts
- Flag: nadir shifting > 30 min/week suggests circadian instability

## Output Format

### Chronotype Assessment Report

```markdown
## ☀️ Chronotype Assessment

### rMEQ Result
- **Score**: 14 / 25
- **Chronotype**: Intermediate (⚖️ Neutral)
- **Estimated DLMO**: ~21:30
- **Natural wake time**: ~07:30

### Your Optimal Daily Schedule
| Activity | Time Window |
|----------|------------|
| Wake | 07:00-07:30 |
| Morning bright light | 07:00-08:00 |
| Deep focus work | 09:00-11:30 |
| Cardio exercise | 13:00-15:00 |
| Strength training | 15:00-17:30 |
| Creative work | 17:00-19:00 |
| Last caffeine | Before 15:00 |
| Dinner | 18:30-19:30 |
| Light restriction | After 20:30 |
| Bedtime | 22:30-23:00 |

### Personalized Recommendations
- [Action] Get 30 min outdoor light before 08:30
- [Action] Set blue-light filter on devices after 20:30
- [Notice] Current bedtime (00:30) is 1.5h later than optimal — shift earlier gradually (15 min/3 days)
```

### Jet Lag Recovery Plan

```markdown
## ☀️ Jet Lag Recovery Plan

### Trip Details
- **Route**: Beijing (UTC+8) → London (UTC+0)
- **Direction**: Westward, 8 zones
- **Estimated recovery**: ~5.4 days

### Pre-Travel (3 days before)
| Day | Bedtime Shift | Light Strategy | Meal Shift |
|-----|-------------|---------------|-----------|
| Day -3 | Delay 30 min | Extra afternoon light | Delay dinner 30 min |
| Day -2 | Delay 60 min | Extra afternoon light | Delay all meals 30 min |
| Day -1 | Delay 90 min | Avoid early morning light | Shift to destination timing |

### Post-Arrival Protocol
| Day | Light Seeking | Light Avoiding | Sleep Target | Key Actions |
|-----|-------------|---------------|-------------|------------|
| Day 1 | 14:00-18:00 local | 06:00-12:00 local | 23:00-07:00 local | Short nap OK ≤ 20 min |
| Day 2 | 12:00-18:00 local | Before 10:00 | 23:00-07:00 | Eat meals at local times |
| Day 3+ | Morning OK | Normal | Normal | Should feel improved |
```

### Weekly Circadian Report

```markdown
## ☀️ Weekly Circadian Report (MM-DD ~ MM-DD)

### Circadian Health Score: 72 / 100
| Dimension | Raw | Sub-score | Weight | Weighted |
|-----------|-----|-----------|--------|----------|
| Sleep Timing | Within 45 min | 80 | 25% | 20.0 |
| Light Exposure | ~20 min morning | 70 | 25% | 17.5 |
| Meal Timing | 12h window | 80 | 20% | 16.0 |
| Consistency | SD=35 min | 65 | 20% | 13.0 |
| Activity Timing | Near optimal | 75 | 10% | 7.5 |
| Social Jet Lag | 1.5h | -2.0 | -- | -2.0 |
| **Total** | | | | **72.0** |

### 7-Day Rhythm Map
| Day | Wake | Bed | Light (min) | Eating Window | Exercise | Score |
|-----|------|-----|------------|--------------|----------|-------|
| Mon | 07:00 | 23:00 | 30 | 08:00-19:00 | 16:00 | 82 |
| Tue | 07:15 | 23:30 | 20 | 08:30-20:30 | -- | 68 |
| ... | | | | | | |

### Patterns & Insights
- [Good] Morning light exposure improving (avg 25 min, up from 15 min)
- [Notice] Weekend bedtime 1.5h later than weekday → social jet lag
- [Alert] Dinner after 21:00 on 3 days → meal timing score dropped
- [Suggestion] Shift weekend bedtime 30 min earlier; set dinner cutoff at 20:00
```

## Data Persistence

### Daily File (`memory/health/daily/YYYY-MM-DD.md`)

```markdown
## Circadian [circadian-rhythm-optimizer · HH:MM]
- Score: 72/100
- Bedtime alignment: Within 45 min of optimal
- Morning light: 25 min outdoor
- Eating window: 08:00-19:30 (11.5h)
- Last caffeine: 14:30
- Exercise: 16:00 (strength, within optimal window)
```

### Item File (`memory/health/items/circadian-rhythm.md`)

```markdown
---
item: circadian-rhythm
unit: score (0-100)
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Circadian Rhythm Records

## Profile
- Chronotype: Intermediate (rMEQ 14)
- Estimated DLMO: 21:30
- Natural wake time: 07:30
- CBT minimum (estimated): 05:30

## Recent Status
- Latest: Score 72, alignment fair (YYYY-MM-DD)
- 7-day average score: 74
- Social jet lag: 1.5h (weekday vs weekend midpoint)
- Trend: Stable

## History
| Date | Score | Wake | Bed | Light (min) | Eating Window | Exercise Time | Notes |
|------|-------|------|-----|------------|--------------|--------------|-------|
| 2026-03-10 | 72 | 07:15 | 23:30 | 25 | 08:00-19:30 | 16:00 | |
| 2026-03-09 | 78 | 07:00 | 23:00 | 30 | 08:00-19:00 | 16:00 | |
```

### Write Steps

1. Glob `memory/health/daily/` for the target date file; create if absent.
2. Read the daily file.
3. Grep `## .* \[circadian-rhythm-optimizer ·` for existing section.
4. Edit to replace existing section, or insert before `## Health Files` if new.
5. Update frontmatter `updated_at`.
6. Read `memory/health/items/circadian-rhythm.md` (create if absent).
7. Update `## Recent Status` (including 7-day averages) and prepend new row to `## History`.
8. Remove rows older than 90 days.

## Alerts and Safety

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice. It does not diagnose circadian rhythm sleep disorders (CRSD) or replace clinical chronotherapy.

**Consult a doctor if**:
- Unable to fall asleep before 02:00 consistently (possible Delayed Sleep Phase Disorder)
- Waking before 04:00 and unable to return to sleep (possible Advanced Sleep Phase Disorder)
- Sleep-wake schedule is completely irregular with no pattern (possible Non-24-Hour or Irregular Sleep-Wake Rhythm)
- Shift work causing persistent insomnia, excessive sleepiness, or mood disturbance
- Jet lag symptoms persisting > 2 weeks after travel
- Severe daytime sleepiness affecting safety (driving, operating machinery)

### Light Therapy Safety

- **Contraindicated**: Retinal conditions, bipolar disorder (may trigger mania without medical supervision), photosensitizing medications
- **Caution**: Bright light therapy should start at lower durations (10 min) and increase gradually
- **Never**: Look directly at light therapy devices; position at eye level but offset

### Supplement Disclaimer

- Melatonin dosing mentioned in this skill is for informational reference only
- Melatonin timing is more important than dose (0.3-0.5 mg often sufficient)
- Do not combine melatonin with sedatives, alcohol, or immunosuppressants without medical advice
- Melatonin is a prescription medication in some countries (China, UK, Australia) — check local regulations
