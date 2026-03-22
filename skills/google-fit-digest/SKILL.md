---
name: google-fit-digest
description: "Analyzes Google Fit exported data including steps, heart rate, sleep, and activity metrics. Generates health digests and trend reports from Google Fit JSON/CSV exports. Use when the user provides Google Fit data or asks about their Google Fit health metrics."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📱","category":"health"}}
---

# Google Fit Digest

Analyze Google Fit exported health and fitness data. Generate daily digests, weekly summaries, monthly trend reports, and composite health scores from step counts, heart rate, sleep, activity, weight, and vitals data.

## Capabilities

### 1. Data Import Support

Supported Google Fit export formats:

- **Google Takeout JSON** (primary) — the standard export from Google Takeout containing all Fit data organized by data source and type.
- **CSV exports from third-party apps** — tabular exports from apps that sync with Google Fit (e.g., MyFitnessPal, Strava, Samsung Health).
- **Manual entry fallback** — when no structured file is available, accept user-provided values directly and construct records.

#### Data Types Supported

| Data Type | Google Fit Source | Fields |
|---|---|---|
| Steps | `com.google.step_count.delta` | count, start_time, end_time |
| Heart Rate | `com.google.heart_rate.bpm` | bpm, timestamp |
| Sleep | `com.google.sleep.segment` | stage, start_time, end_time |
| Activity | `com.google.activity.segment` | activity_type, duration, calories |
| Weight | `com.google.weight` | kg, timestamp |
| Blood Pressure | `com.google.blood_pressure` | systolic, diastolic, timestamp |
| Body Temperature | `com.google.body.temperature` | celsius, timestamp |
| Oxygen Saturation | `com.google.oxygen_saturation` | spo2, timestamp |

#### Import Procedure

1. **Locate data files.** Use `Glob` to find JSON or CSV files matching Google Fit export patterns (e.g., `**/Fit/**/*.json`, `**/Google Fit/**/*.csv`).
2. **Identify data sources.** Read file headers or JSON structure to determine which data types are present.
3. **Parse and normalize.** Convert all timestamps to ISO 8601 with timezone. Convert units to metric (steps as integers, weight in kg, temperature in Celsius, heart rate in bpm).
4. **Validate ranges.** Flag physiologically implausible values:
   - Steps per minute > 250
   - Heart rate < 30 or > 220
   - SpO2 < 70% or > 100%
   - Systolic BP < 60 or > 250
   - Body temperature < 34°C or > 42°C
5. **Handle duplicates.** Deduplicate by timestamp and data source, preferring higher-precision sources.

### 2. Daily Health Digest

Compile the following from imported data for a given date:

**Steps:**
- Total step count for the day
- Hourly distribution (24-hour breakdown)
- Goal progress against configurable target (default: 10,000 steps)
- Peak activity hour
- Comparison to user's rolling 7-day average

**Active Minutes:**
- Total active minutes
- Breakdown by intensity level:
  - Light (< 3 METs): slow walking, household chores
  - Moderate (3-6 METs): brisk walking, cycling < 16 km/h
  - Vigorous (> 6 METs): running, swimming laps, HIIT
- Heart rate zone time if HR data available

**Heart Rate:**
- Resting heart rate (lowest sustained 5-minute average during sleep or rest)
- Daily average heart rate
- Maximum heart rate recorded
- Zone distribution:
  - Zone 1 (50-60% max HR): very light
  - Zone 2 (60-70% max HR): light / fat burn
  - Zone 3 (70-80% max HR): moderate / aerobic
  - Zone 4 (80-90% max HR): hard / threshold
  - Zone 5 (90-100% max HR): maximum / anaerobic
- Max HR estimated as `220 - age` unless user provides measured value

**Calories:**
- Estimated total burn = BMR + activity calories
- BMR estimated using Mifflin-St Jeor equation if height, weight, age, and sex are available
- Activity calories from Google Fit activity segments
- Net calorie position if dietary intake data available

**Sleep Summary** (if sleep data available):
- Total sleep duration (time asleep, excluding awake periods)
- Time in bed vs. time asleep (sleep efficiency percentage)
- Sleep stages breakdown:
  - Awake
  - Light sleep
  - Deep sleep
  - REM sleep
- Sleep onset time and wake time
- Number of awakenings
- Sleep score (weighted composite: duration 40%, efficiency 30%, deep+REM percentage 30%)

**Vitals** (if available):
- Latest weight reading and trend arrow (up/down/stable vs. 7-day average)
- Blood pressure reading with classification (normal/elevated/stage 1/stage 2 per AHA)
- Body temperature
- SpO2 reading with flag if < 95%

### 3. Weekly/Monthly Trend Analysis

**Steps Trend:**
- Daily totals for the period with 7-day moving average
- Days meeting step goal vs. total days
- Best and worst days
- Weekend vs. weekday comparison

**Activity Consistency Score:**
- Percentage of days meeting activity guidelines
- Streak tracking (consecutive days meeting goals)
- Activity variety index (number of distinct activity types)

**Heart Rate Trends:**
- Resting heart rate over time (plotted or tabulated)
- Average HR trend
- HR recovery patterns if workout data available
- Flag significant changes (> 10% shift in resting HR over 2 weeks)

**Weight Trend:**
- Current weight vs. period start
- Rate of change (kg/week)
- Trend direction with linear regression
- BMI calculation and category if height available

**Sleep Duration and Quality Trends:**
- Average sleep duration over period
- Sleep consistency score (regularity of bed/wake times)
- Deep sleep and REM percentages over time
- Correlation between sleep and next-day activity levels

**Guideline Comparison:**
- WHO/AHA recommendation: 150 minutes moderate OR 75 minutes vigorous activity per week
- Calculate current week's progress toward guidelines
- Equivalent minutes conversion (1 min vigorous = 2 min moderate)
- Monthly adherence rate (weeks meeting guidelines / total weeks)

### 4. Health Metrics Dashboard

Composite health score (0-100) calculated from weighted components:

| Metric | Target | Weight | Scoring |
|---|---|---|---|
| Daily Steps | 10,000 | 25% | Linear 0-100, capped at 150% of target |
| Active Minutes | 30 min/day | 25% | Linear 0-100, bonus for vigorous intensity |
| Sleep Duration | 7-9 hours | 20% | 100 in range, decreasing outside |
| Resting HR | Age-appropriate range | 15% | Lower is better within healthy range |
| Weight Stability | Within ±2% of target/baseline | 15% | 100 at target, linear decrease |

**Score interpretation:**
- 90-100: Excellent — consistently meeting all health targets
- 75-89: Good — meeting most targets with minor gaps
- 60-74: Fair — some targets met but room for improvement
- 40-59: Needs attention — multiple targets not met
- < 40: Concern — significant gaps in health metrics

**Age-appropriate resting HR ranges:**
- 18-25: 55-70 bpm (excellent), 71-80 (good), 81-90 (fair)
- 26-35: 55-72 bpm (excellent), 73-82 (good), 83-92 (fair)
- 36-45: 56-73 bpm (excellent), 74-83 (good), 84-93 (fair)
- 46-55: 57-75 bpm (excellent), 76-84 (good), 85-95 (fair)
- 56-65: 56-74 bpm (excellent), 75-83 (good), 84-94 (fair)
- 65+: 55-73 bpm (excellent), 74-82 (good), 83-93 (fair)

When data is missing for a component, redistribute its weight proportionally among available metrics and note the gap.

### 5. Activity Classification

Map Google Fit activity type integers to human-readable categories:

**Cardio:**
- Running (8) — outdoor and treadmill
- Cycling (1) — outdoor and stationary
- Swimming (82) — pool and open water
- Rowing (103)
- Elliptical (25)
- Jump rope (106)
- Aerobics (119)

**Strength:**
- Weight training (80)
- Bodyweight exercises (general fitness: 120)
- CrossFit (113)
- Circuit training (9)

**Flexibility:**
- Yoga (100)
- Stretching (44)
- Pilates (101)
- Tai chi (102)

**Daily Activity:**
- Walking (7) — includes commute and leisure
- Household activities (general: 108)
- Gardening (35)
- Stair climbing (111)

**Sports:**
- Tennis (87)
- Basketball (14)
- Soccer (73)
- Badminton (10)
- Table tennis (97)

For each activity session, extract:
- Activity type and category
- Duration (minutes)
- Estimated calories burned
- Average heart rate during activity (if HR data overlaps)
- Intensity classification (light/moderate/vigorous) based on HR zones or MET values

### 6. Comparison with Apple Health

When both Google Fit and Apple Health data are available (cross-reference with `apple-health-digest` skill):

- **Side-by-side metrics:** Compare step counts, active minutes, heart rate, and sleep from both platforms for the same dates.
- **Discrepancy detection:** Flag differences > 10% between platforms for the same metric on the same day.
- **Source preference:** Allow user to set preferred source per metric, or use the higher-precision source by default.
- **Merged view:** Create a unified health timeline combining unique data from both sources, deduplicating overlapping metrics.
- **Device mapping:** Note which devices feed each platform (e.g., Pixel Watch to Google Fit, Apple Watch to Apple Health) to explain discrepancies.

### 7. Data Quality Assessment

Evaluate data completeness and reliability:

**Completeness Checks:**
- Count days with data vs. total days in requested period
- Identify gaps > 24 hours in step or HR data
- Flag days with suspiciously low data points (e.g., < 100 steps may indicate device not worn)

**Sensor Accuracy Flags:**
- Heart rate readings with high variance in short periods (possible poor sensor contact)
- Step counts that spike unnaturally (e.g., 5,000 steps in 5 minutes — likely driving on rough road)
- Sleep data with no awake periods detected (possible tracking failure)

**Sync Issues:**
- Duplicate data from multiple synced apps
- Timezone inconsistencies across data sources
- Data arriving out of chronological order

**Quality Score:**
- A (> 90% complete, no flags): High confidence in analysis
- B (75-90% complete, minor flags): Good confidence, note gaps
- C (50-75% complete, some flags): Moderate confidence, interpret with caution
- D (< 50% complete, major flags): Low confidence, recommend improving data collection

Report quality assessment at the top of every digest or report.

## Output Format

### Daily Digest

```
## Google Fit Daily Digest — [DATE]

**Data Quality:** [A/B/C/D] — [brief note]

### Steps
- Total: [count] / 10,000 ([percentage]%)
- Peak hour: [hour] ([count] steps)
- vs. 7-day avg: [+/-count] ([+/-percentage]%)

### Active Minutes
- Total: [minutes] min
- Light: [minutes] min | Moderate: [minutes] min | Vigorous: [minutes] min

### Heart Rate
- Resting: [bpm] bpm | Average: [bpm] bpm | Max: [bpm] bpm
- Zone distribution: Z1 [min] | Z2 [min] | Z3 [min] | Z4 [min] | Z5 [min]

### Sleep
- Duration: [hours]h [minutes]m (efficiency: [percentage]%)
- Stages: Light [percentage]% | Deep [percentage]% | REM [percentage]% | Awake [percentage]%

### Vitals
- Weight: [kg] kg ([trend arrow] [change] from 7-day avg)
- BP: [systolic]/[diastolic] mmHg ([classification])
- SpO2: [percentage]%

### Health Score: [score]/100 ([interpretation])
```

### Weekly Summary

```
## Google Fit Weekly Summary — [START_DATE] to [END_DATE]

**Data Quality:** [grade] — [days with data]/7 days

### Steps Overview
| Day | Steps | Goal Met |
|---|---|---|
| Mon | [count] | [yes/no] |
| ... | ... | ... |
| **Average** | **[count]** | **[X]/7 days** |

### Activity Minutes: [total] min ([percentage]% of 150 min guideline)
### Avg Resting HR: [bpm] bpm (trend: [direction])
### Avg Sleep: [hours]h [minutes]m ([consistency score])
### Weight: [start] → [end] kg ([change])

### Weekly Health Score: [score]/100
```

### Monthly Report

```
## Google Fit Monthly Report — [MONTH YEAR]

**Data Quality:** [grade] — [days with data]/[total days] days

### Monthly Highlights
- Best step day: [date] ([count] steps)
- Most active week: Week of [date]
- Longest activity streak: [count] days

### Trend Summary
- Steps: [trend direction] ([avg] daily avg)
- Resting HR: [trend direction] ([start] → [end] bpm)
- Weight: [trend direction] ([start] → [end] kg, [rate] kg/week)
- Sleep: [trend direction] ([avg] avg duration)

### Guideline Adherence
- Weeks meeting WHO activity guidelines: [count]/[total]
- Average weekly active minutes: [minutes] min

### Monthly Health Score: [score]/100 ([vs. previous month])
### Recommendations
- [Actionable recommendation based on data trends]
- [...]
```

## Data Persistence

### Daily Digest Files
Save each daily digest to: `items/google-fit-daily-[YYYY-MM-DD].md`

### Consolidated Reference File
Maintain a running reference at: `items/google-fit.md`

Structure of `items/google-fit.md`:
```markdown
# Google Fit Health Data

## User Profile
- Age: [if known]
- Height: [if known]
- Weight target: [if set]
- Step goal: [default 10,000]
- Preferred units: [metric/imperial]

## Latest Metrics
- Last updated: [date]
- Current weight: [kg]
- Resting HR (7-day avg): [bpm]
- Daily steps (7-day avg): [count]
- Weekly active minutes: [minutes]
- Avg sleep duration: [hours]

## Data Sources
- Primary device: [e.g., Pixel Watch 3]
- Connected apps: [list]
- Export format: [JSON/CSV]
- Date range available: [start] to [end]

## Monthly Scores
| Month | Health Score | Steps Avg | Active Min/Week | Sleep Avg | Resting HR |
|---|---|---|---|---|---|
| [month] | [score] | [steps] | [minutes] | [hours] | [bpm] |
```

Update `items/google-fit.md` after each digest generation with the latest metrics and monthly score entry.

## Alerts and Safety

### Automated Alerts

Flag the following conditions when detected in the data:

- **Resting HR spike:** Resting HR > 20% above 30-day average
- **SpO2 drop:** Oxygen saturation < 92%
- **BP elevation:** Systolic > 180 or diastolic > 120 (hypertensive crisis range)
- **Significant weight change:** > 2 kg change in 48 hours (possible fluid retention or measurement error)
- **Sleep deprivation:** < 5 hours sleep for 3+ consecutive nights
- **Inactivity:** < 1,000 steps for 2+ consecutive days (possible illness or device not worn)

### Medical Disclaimer

**IMPORTANT: This skill provides informational health data summaries only.**

- All data accuracy depends on the sensors in the user's wearable device. Consumer-grade wrist-based sensors have known limitations for heart rate (especially during high-intensity exercise), SpO2, and blood pressure estimation.
- Heart rate data from wrist-worn devices is **not medical-grade** and should not be used for clinical decision-making.
- Blood pressure readings from consumer devices are estimates and do not replace clinical sphygmomanometer measurements.
- SpO2 readings from consumer devices are screening-level only.
- This tool is **not a diagnostic tool**. It does not diagnose, treat, or prevent any medical condition.
- Anomalous readings should be verified with medical-grade equipment and discussed with a healthcare provider.
- If any alert is triggered, recommend the user consult a healthcare professional. Do not provide medical advice, diagnosis suggestions, or treatment recommendations.
- Always include: *"This summary is generated from consumer wearable data and is not a substitute for professional medical advice, diagnosis, or treatment."*
