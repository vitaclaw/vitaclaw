---
name: fitness-analyzer
description: "Analyzes fitness data, identifies exercise patterns, evaluates workout progress, and provides personalized training recommendations. Supports correlation analysis with chronic disease data such as blood pressure and blood glucose. Use when the user wants to review their exercise trends, track running progress, or understand how workouts affect other health metrics."
version: 1.0.0
user-invocable: true
argument-hint: "[trend | progress | correlation | habits]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏃","category":"health-analyzer"}}
---

# Fitness Analyzer Skill

Analyzes fitness data, identifies exercise patterns, evaluates workout progress, and provides personalized training recommendations.

## Features

### 1. Exercise Trend Analysis
Analyzes trends in exercise volume, frequency, and intensity, identifying areas of improvement or those needing adjustment.

**Analysis Dimensions**:
- Exercise volume trends (duration, distance, calories)
- Exercise frequency trends (workout days per week)
- Intensity distribution changes (low/moderate/high intensity ratio)
- Exercise type preference changes

**Output**:
- Trend direction (improving/stable/declining)
- Magnitude and percentage of change
- Trend significance
- Improvement recommendations

### 2. Workout Progress Tracking
Tracks progress in specific exercise types and quantifies fitness outcomes.

**Supported Progress Tracking**:
- **Running progress**: pace improvement, distance increase, heart rate improvement
- **Strength training progress**: weight increase, volume increase, RPE changes
- **Endurance progress**: increased workout duration, extended distance
- **Flexibility progress**: improved joint range of motion

**Output**:
- Starting value vs. current value
- Improvement percentage
- Progress visualization
- Milestones achieved

### 3. Exercise Habit Analysis
Identifies the user's exercise habits and patterns.

**Analysis Content**:
- Preferred workout time (morning/afternoon/evening)
- Exercise frequency patterns (days per week)
- Exercise type preferences
- Rest day distribution
- Exercise consistency score

**Output**:
- Habit summary
- Consistency score (0-100)
- Optimization recommendations
- Habit-building suggestions

### 4. Correlation Analysis
Analyzes correlations between exercise and other health metrics.

**Supported Correlation Analyses**:
- **Exercise <-> Weight**: relationship between exercise expenditure and weight change
- **Exercise <-> Blood Pressure**: long-term impact of exercise on blood pressure
- **Exercise <-> Blood Glucose**: effect of exercise on blood glucose control
- **Exercise <-> Mood/Sleep**: impact of exercise on mood and sleep

**Output**:
- Correlation coefficient (-1 to 1)
- Correlation strength (weak/moderate/strong)
- Statistical significance
- Causal inference
- Practical recommendations

### 5. Personalized Recommendation Generation
Generates personalized exercise recommendations based on user data.

**Recommendation Types**:
- **Exercise frequency recommendations**: whether to increase/decrease workout frequency
- **Exercise intensity recommendations**: intensity adjustment suggestions
- **Exercise type recommendations**: recommended exercise types to try
- **Exercise timing recommendations**: optimal workout times
- **Recovery recommendations**: rest and recovery suggestions

**Recommendation Basis**:
- WHO/ACSM/AHA exercise guidelines
- User exercise history data
- User health status
- User fitness goals

## Output Format

### Trend Analysis Report

```markdown
# Exercise Trend Analysis Report

## Analysis Period
2025-03-20 to 2025-06-20 (3 months)

## Exercise Volume Trends

### Workout Duration
- Trend: Up
- Start: avg 120 min/week
- Current: avg 180 min/week
- Change: +50% (+60 min/week)
- Interpretation: Significant increase in exercise volume, excellent performance

### Calorie Burn
- Trend: Up
- Start: avg 960 cal/week
- Current: avg 1440 cal/week
- Change: +50%
- Interpretation: Increased exercise expenditure, beneficial for weight management

### Exercise Distance
- Trend: Up
- Start: avg 10 km/week
- Current: avg 20 km/week
- Change: +100%
- Interpretation: Significant endurance improvement

## Exercise Frequency

- Current frequency: 4 days/week
- Target frequency: 4-5 days/week
- Status: On target
- Recommendation: Maintain current frequency

## Intensity Distribution

| Intensity | Proportion | Change |
|-----------|-----------|--------|
| Low intensity | 25% | +5% |
| Moderate intensity | 55% | -10% |
| High intensity | 20% | +5% |

**Analysis**: Intensity distribution is reasonable with moderate intensity dominant, consistent with aerobic exercise recommendations.

## Exercise Type Distribution

| Exercise Type | Proportion |
|--------------|-----------|
| Running | 50% |
| Yoga | 25% |
| Strength training | 25% |

**Recommendation**: Consider increasing strength training proportion to 30-40%.

## Insights & Recommendations

### Strengths
1. Steady growth in exercise volume (+50%)
2. Stable exercise frequency at 4 days/week
3. Adequate rest days, good recovery

### Improvement Recommendations
1. Add 2 strength training sessions per week
2. Try different exercise types to avoid monotony
3. Incorporate high-intensity interval training (HIIT)

### Warnings
1. Avoid excessively high exercise intensity; maintain moderate intensity as the primary level
```

### Correlation Analysis Report

```markdown
# Exercise and Blood Pressure Correlation Analysis

## Data Sources
- Exercise data: fitness-logs (2025-03-20 to 2025-06-20)
- Blood pressure data: hypertension-tracker (same period)

## Analysis Results

### Correlation Coefficient
- Variables: weekly exercise duration <-> systolic blood pressure
- Correlation coefficient: r = -0.68
- Correlation strength: **Strong negative correlation**
- Statistical significance: p < 0.01 **Highly significant**

### Interpretation
Weekly exercise duration is strongly negatively correlated with systolic blood pressure, meaning:
- More exercise leads to lower blood pressure
- Each additional 30 minutes of exercise is associated with a 3-5 mmHg decrease in systolic blood pressure

### Practical Recommendations
1. Continue regular exercise, 5-7 days per week
2. 30-60 minutes per session, moderate intensity
3. Prioritize aerobic exercise (brisk walking, jogging, cycling)
4. Avoid breath-holding exercises and sudden explosive movements

### Medical References
- AHA statement: Regular aerobic exercise can lower systolic blood pressure by 5-7 mmHg
- Your exercise effect: approximately 10 mmHg reduction, significant results!
```

### Progress Tracking Report

```markdown
# Running Progress Tracking

## Analysis Period
2025-01-01 to 2025-06-20 (6 months)

## Pace Progress

| Metric | Start | Current | Improvement |
|--------|-------|---------|-------------|
| Average pace | 7:30 min/km | 6:00 min/km | +20% |
| Best pace | 7:00 min/km | 5:30 min/km | +22% |
| 5K time | 37:30 | 30:00 | +20% |

**Trend**: Pace is improving steadily and significantly!

## Distance Progress

| Metric | Start | Current | Improvement |
|--------|-------|---------|-------------|
| Longest single run | 3 km | 12 km | +300% |
| Monthly total distance | 40 km | 86 km | +115% |
| Average distance | 5 km | 6 km | +20% |

**Trend**: Endurance has improved substantially, capable of longer distances.

## Heart Rate Improvement

| Metric | Start | Current | Improvement |
|--------|-------|---------|-------------|
| Resting heart rate | 78 bpm | 72 bpm | -6 bpm |
| Heart rate at same pace | 155 bpm | 145 bpm | -10 bpm |

**Analysis**: Significant cardiovascular improvement; heart rate is lower at the same pace.

## Milestones

- 2025-03-15: First 5K run completed
- 2025-05-20: First 10K run completed
- 2025-06-10: Pace broke through 6:00 min/km

## Next Goals

- Complete a half marathon (21 km)
- Improve pace to 5:30 min/km
- Try interval training to increase speed
```

## Data Sources

### Primary Data Sources

1. **Exercise logs**
   - Path: `data/fitness-logs/YYYY-MM/YYYY-MM-DD.json`
   - Content: Exercise records (type, duration, intensity, heart rate, distance, etc.)
   - Frequency: Updated after each workout

2. **User profile**
   - Path: `data/fitness-tracker.json`
   - Content: User profile, fitness goals, statistics
   - Update: Periodically updated

3. **Health data correlations**
   - `data/hypertension-tracker.json` (blood pressure data)
   - `data/diabetes-tracker.json` (blood glucose data)
   - `data/profile.json` (weight, BMI, etc.)

### Data Quality Checks

- Data completeness: Check whether required fields exist
- Data plausibility: Check whether values are within reasonable ranges
- Temporal consistency: Check whether timestamps are reasonable
- Duplicate data: Detect and handle duplicate records

## Algorithm Descriptions

### 1. Linear Regression Trend Analysis

Uses linear regression to analyze time trends in exercise data.

**Formula**:
y = a + bx

Where:
- y: exercise metric (duration, calories, distance, etc.)
- x: time
- a: intercept
- b: slope (trend direction and rate)

**Interpretation**:
- b > 0: upward trend
- b < 0: downward trend
- b ~ 0: stable

### 2. Pearson Correlation Coefficient

Used to analyze the linear correlation between two variables.

**Formula**:
r = Sum[(xi - x_mean)(yi - y_mean)] / sqrt[Sum(xi - x_mean)^2 * Sum(yi - y_mean)^2]

**Range**: -1 <= r <= 1

**Interpretation**:
- r = 1: perfect positive correlation
- r = -1: perfect negative correlation
- r = 0: no linear correlation

**Strength Classification**:
- |r| < 0.3: weak correlation
- 0.3 <= |r| < 0.7: moderate correlation
- |r| >= 0.7: strong correlation

### 3. Pace Calculation

**Pace** = workout duration / distance

Unit: min/km or min/mile

**Example**:
- 30 minutes to run 5 km
- Pace = 30 / 5 = 6 min/km

### 4. MET Energy Expenditure Calculation

**Calorie burn** = MET x body weight (kg) x time (hours)

**Common exercise MET values**:
- Walking (3-5 km/h): 3.5-5 MET
- Jogging (8 km/h): 8 MET
- Fast running (10 km/h): 10 MET
- Swimming: 6-10 MET
- Cycling (leisure): 4 MET
- Strength training: 5 MET
- Yoga: 3 MET

## Medical Safety Boundaries

**Important Disclaimer**
This analysis is for health reference only and does not constitute medical advice.

### Scope of Analysis

**Can do**:
- Exercise data statistics and analysis
- Trend identification and visualization
- Correlation calculation and interpretation
- General exercise recommendations

**Cannot do**:
- Disease diagnosis
- Exercise risk assessment
- Specific exercise prescription design
- Exercise injury diagnosis and treatment

### Danger Signal Detection

The following danger signals are detected during analysis:

1. **Abnormal heart rate**
   - Exercise heart rate > 95% of maximum heart rate
   - Resting heart rate > 100 bpm

2. **Abnormal blood pressure**
   - Systolic blood pressure >= 180 mmHg
   - Diastolic blood pressure >= 110 mmHg

3. **Overtraining signs**
   - 7 consecutive days of high-intensity exercise
   - Persistent decline in perceived exertion (RPE > 17)

4. **Rapid weight loss**
   - Weight loss > 1 kg per week (may be unhealthy)

### Recommendation Levels

**Level 1: General recommendations**
- Based on WHO/ACSM guidelines
- Applicable to the general population

**Level 2: Reference recommendations**
- Based on user data
- Should be combined with personal circumstances

**Level 3: Medical recommendations**
- Involves disease management
- Requires physician confirmation

## Usage Examples

### Example 1: Generate exercise trend report

```bash
/fitness trend 3months
```

Output:
- 3-month exercise trend analysis
- Volume, frequency, intensity changes
- Insights and recommendations

### Example 2: Track running progress

```bash
/fitness analysis progress running
```

Output:
- Pace progress
- Distance progress
- Heart rate improvement
- Milestones achieved

### Example 3: Analyze exercise and blood pressure correlation

```bash
/fitness analysis correlation blood_pressure
```

Output:
- Correlation coefficient
- Correlation strength
- Significance test
- Practical recommendations
