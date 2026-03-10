---
name: goal-analyzer
description: "Analyzes health goal data, identifies goal patterns, evaluates goal progress, and provides personalized goal management recommendations. Supports SMART goal validation, habit tracking, motivation assessment, achievement systems, obstacle identification, and correlation analysis with nutrition, exercise, and sleep data. Use when the user wants to review goal progress, validate a new goal, or get habit-building advice."
version: 1.0.0
user-invocable: true
argument-hint: "[progress | smart-check | habits | motivation | achievements | report]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🎯","category":"health-analyzer"}}
---

# Health Goal Analyzer Skill

Analyzes health goal data, identifies goal patterns and progress, evaluates goal achievement, and provides personalized goal management recommendations.

## Features

### 1. SMART Goal Validation

Validates whether a newly set goal conforms to the SMART principles.

**Validation Dimensions**:
- **S**pecific
  - Is the goal clear and specific?
  - Does it have a well-defined scope?
  - Does it avoid vague wording?

- **M**easurable
  - Does it have quantifiable metrics?
  - Are there clear measurement criteria?
  - Can progress be tracked?

- **A**chievable
  - Is the goal realistic and feasible?
  - Does it account for current circumstances?
  - Is the timeframe reasonable?
  - Weight loss goals: recommended 0.5-1 kg per week
  - Exercise goals: recommended 3-5 times per week, 30-60 minutes each

- **R**elevant
  - Is the goal health-related?
  - Does it align with the user's overall health plan?
  - Is it consistent with existing goals?

- **T**ime-bound
  - Does it have a clear deadline?
  - Is the timeframe reasonable?
  - Are there interim milestones?

**Output**:
- SMART score (1-5 per dimension)
- Overall score and grade (S/A/B/C)
- Improvement suggestions
- Goal optimization plan

**Example Assessment**:
```json
{
  "goal": "Lose 5 kg in 6 months",
  "smart_scores": {
    "specific": 5,
    "measurable": 5,
    "achievable": 4,
    "relevant": 5,
    "time_bound": 5
  },
  "overall_score": 4.8,
  "grade": "A",
  "assessment": "Excellent SMART goal",
  "suggestions": [
    "Set interim milestones (lose 1.5-2 kg every 2 months)",
    "Pair with an exercise plan and dietary adjustments"
  ]
}
```

---

### 2. Goal Progress Tracking

Tracks and analyzes goal completion progress.

**Tracking Content**:
- **Current Progress**
  - Completion percentage
  - Current value vs. target value
  - Remaining gap

- **Time Progress**
  - Elapsed time percentage
  - Remaining time
  - Ahead/behind schedule determination

- **Speed Analysis**
  - Average progress rate (per week/month)
  - Estimated completion time
  - Whether plan adjustment is needed

- **Trend Identification**
  - Progress trend (accelerating/stable/decelerating)
  - Cyclical patterns
  - Anomaly fluctuation detection

**Output**:
- Progress visualization (progress bar, percentage)
- Completion probability prediction
- Time estimates (optimistic/neutral/pessimistic)
- Adjustment recommendations

**Progress Ratings**:
- **Excellent** - Ahead of schedule, expected to finish early
- **Normal** - Progress meets expectations
- **Behind** - Slightly slow, needs to accelerate
- **Seriously Behind** - Significantly lagging, consider adjusting the goal

---

### 3. Habit Building Analysis

Analyzes habit formation status and consistency.

**Analysis Content**:
- **Streak Tracking**
  - Current streak days
  - Longest historical streak
  - Average streak length

- **Completion Rate Statistics**
  - Overall completion rate
  - Weekly completion rate
  - Monthly completion rate
  - Day-of-week completion rate

- **Habit Strength Assessment**
  - Habit consolidation level (1-10)
  - Habit stability score
  - Automaticity assessment

- **Habit Pattern Identification**
  - Best trigger times
  - Common interruption causes
  - Success factor identification

**Habit Formation Stages**:
- **Days 1-7** - Launch phase (highest dropout risk)
- **Days 8-21** - Formation phase (gradually stabilizing)
- **Days 22-30** - Consolidation phase (approaching automaticity)
- **Days 31-66** - Habit phase (essentially formed)
- **Day 67+** - Automaticity phase (fully automatic)

**Output**:
- Habit heat map (calendar view)
- Streak statistics
- Completion rate trend chart
- Habit strength score
- Habit stacking suggestions

**Example Analysis**:
```json
{
  "habit": "morning-stretch",
  "current_streak": 21,
  "longest_streak": 21,
  "completion_rate": 95.2,
  "strength_score": 7.5,
  "stage": "Consolidation phase",
  "assessment": "Habit is about to form, keep going!",
  "next_milestone": 30,
  "suggestions": [
    "Keep it up, approaching the 30-day milestone",
    "Consider adding a new related habit"
  ]
}
```

---

### 4. Motivation Assessment & Management

Evaluates and manages user motivation levels.

**Assessment Content**:
- **Motivation Score Tracking**
  - Current motivation level (1-10)
  - Motivation change trend
  - Motivation fluctuation cycles

- **Motivation Factor Analysis**
  - Intrinsic motivation (health, self-actualization)
  - Extrinsic motivation (rewards, recognition)
  - Social support (encouragement from family and friends)

- **Motivation Low-Point Identification**
  - Motivation decline signals
  - Common low-point timing
  - Risk period warnings

**Motivation Boosting Strategies**:
- **Weeks 2-3** - Motivation dip; emphasize completed progress
- **Months 1-2** - Fatigue period; adjust goals and rewards
- **3+ months** - Burnout period; introduce novelty and challenges

**Output**:
- Motivation trend chart
- Motivation low-point warnings
- Personalized motivational recommendations
- Reward mechanism suggestions

**Motivational Advice Examples**:
- When motivation < 5: Revisit initial reasons, lower short-term goals
- When motivation 5-7: Emphasize progress, set small rewards
- When motivation > 7: Set challenges, pursue excellence

---

### 5. Achievement System Management

Manages the basic achievement system for unlocking and progress.

**Achievement Types**:
- **Goal-Related Achievements**
  - First Goal - Complete the first health goal
  - Halfway There - Any goal reaches 50%
  - Goal Complete - Complete a health goal
  - Early Finish - Complete a goal ahead of schedule
  - Overachiever - Exceed a goal target

- **Habit-Related Achievements**
  - 7-Day Streak - Any habit checked in for 7 consecutive days
  - 21-Day Streak - Any habit checked in for 21 consecutive days
  - 30-Day Streak - Any habit checked in for 30 consecutive days
  - 66-Day Streak - Any habit checked in for 66 consecutive days (fully formed)

- **Comprehensive Achievements**
  - Multi-Tasker - Complete 3 goals simultaneously
  - Perfect Streak - 100% habit completion for 30 days
  - Fastest Progress - Greatest progress in a single week
  - Long-Term Commitment - Continuous tracking for 180 days

**Achievement Tracking**:
- Unlocked achievements list
- Locked achievement progress
- Achievement unlock times
- Achievement-related recommendations

**Output**:
- Achievement badge display
- Achievement completion progress
- Next unlockable achievement
- Achievement tips

---

### 6. Obstacle Identification & Recommendations

Identifies factors blocking goal achievement and provides solutions.

**Obstacle Types**:
- **Time obstacles**
  - Busy, insufficient time
  - Suggestion: Shorten session duration, increase frequency; use fragmented time

- **Motivation obstacles**
  - Lack of drive, procrastination
  - Suggestion: Set reminders; find a partner; adjust goals

- **Environmental obstacles**
  - Lack of support, too many temptations
  - Suggestion: Change environment; find alternatives; build support system

- **Ability obstacles**
  - Goal too difficult, lacking knowledge
  - Suggestion: Lower difficulty; learn skills; seek professional help

- **Physical obstacles**
  - Fatigue, discomfort, injury
  - Suggestion: Rest and recover; adjust plan; consult a doctor

**Output**:
- Primary obstacles identified
- Obstacle frequency statistics
- Personalized solutions
- Preventive recommendations

---

### 7. Data Correlation Analysis

Correlates health goals with other health data for analysis.

**Correlation Dimensions**:
- **Weight loss goal correlations**
  - Nutritional intake (calories, macronutrients)
  - Exercise expenditure (frequency, intensity, duration)
  - Sleep quality (duration, depth)
  - Weight change trends

- **Exercise goal correlations**
  - Sleep quality (recovery)
  - Nutritional intake (protein, carbohydrates)
  - Body metrics (weight, body fat percentage)

- **Diet goal correlations**
  - Nutrient intake (vitamins, minerals)
  - Body metrics (blood pressure, blood glucose)
  - Exercise performance

- **Sleep goal correlations**
  - Exercise timing (evening exercise impact)
  - Meal timing (dinner time, caffeine)
  - Screen time (blue light impact)

**Analysis Methods**:
- Correlation analysis (Pearson correlation coefficient)
- Regression analysis (predictive modeling)
- Trend matching (trend synchronization)
- Causal inference (potential causal relationships)

**Output**:
- Correlation strength (strong/moderate/weak)
- Positive/negative relationships
- Causal inference
- Optimization recommendations

**Example Correlation**:
```json
{
  "goal": "weight-loss",
  "correlations": [
    {
      "factor": "daily_calories",
      "correlation": -0.75,
      "strength": "Strong negative correlation",
      "insight": "Daily calorie intake strongly negatively correlated with weight loss progress; reducing intake accelerates progress"
    },
    {
      "factor": "exercise_frequency",
      "correlation": 0.68,
      "strength": "Strong positive correlation",
      "insight": "Exercise frequency strongly positively correlated with weight loss progress; recommend maintaining 4+ sessions per week"
    },
    {
      "factor": "sleep_duration",
      "correlation": 0.45,
      "strength": "Moderate positive correlation",
      "insight": "Sleep duration affects weight loss; recommend ensuring 7-8 hours of sleep"
    }
  ],
  "recommendations": [
    "Focus on controlling calorie intake while maintaining current exercise frequency",
    "Optimize sleep duration to enhance weight loss effectiveness"
  ]
}
```

---

### 8. Visualization Report Generation

Generates HTML interactive reports with ECharts charts.

**Report Types**:

#### A. Progress Trend Report
- Line chart showing goal progress over time
- Milestone annotations
- Predicted completion time range
- Progress speed analysis

#### B. Habit Heat Map Report
- Calendar heat map showing habit completion
- Color depth indicates completion frequency
- Streak annotations
- Completion rate statistics

#### C. Multi-Goal Comparison Report
- Ring chart showing multiple goal completion rates
- Priority ranking
- Resource allocation recommendations
- Progress synchronization analysis

#### D. Motivation Trend Report
- Line chart showing motivation changes
- Motivation-progress correlation
- Motivation low-point warnings
- Motivational recommendations

#### E. Comprehensive Report
- Includes all charts above
- Overall health assessment
- Comprehensive improvement recommendations
- Next-phase goal suggestions

**Report Features**:
- Responsive design, mobile-friendly
- Dark/light theme toggle
- Interactive charts (zoom, filter)
- Data tables
- PDF export capability
- Fully local, no internet required

**ECharts Chart Configuration**:
```javascript
// Progress trend line chart
{
  type: 'line',
  xAxis: { type: 'category', data: ['Jan', 'Feb', 'Mar', ...] },
  yAxis: { type: 'value', name: 'Completion %' },
  series: [{
    name: 'Goal Progress',
    type: 'line',
    data: [0, 15, 35, 50, 70, 85, 100],
    smooth: true,
    markLine: {
      data: [{ yAxis: 50, name: '50% Milestone' }]
    }
  }]
}

// Habit heat map
{
  type: 'heatmap',
  xAxis: { type: 'category', data: ['Mon', 'Tue', ...] },
  yAxis: { type: 'category', data: ['Week 1', 'Week 2', ...] },
  visualMap: {
    min: 0, max: 1,
    inRange: { color: ['#ebedf0', '#216e39'] }
  },
  series: [{
    type: 'heatmap',
    data: [[0, 0, 1], [1, 0, 1], [2, 0, 0], ...]
  }]
}

// Goal achievement ring chart
{
  type: 'pie',
  radius: ['50%', '70%'],
  series: [{
    type: 'pie',
    radius: ['50%', '70%'],
    data: [
      { value: 70, name: 'Completed' },
      { value: 30, name: 'Remaining' }
    ],
    label: { formatter: '{b}: {c}%' }
  }]
}
```

**Output**:
- HTML file (with embedded CSS, JS, ECharts)
- Interactive chart features
- Data tables
- Analysis text
- Recommendation list

---

## Medical Safety Boundaries

### Scope Statement
- Can assist in setting health goals
- Can track and analyze goal progress
- Can identify health behavior patterns
- Can provide general health improvement recommendations
- Can generate visualization reports

- Cannot provide medical diagnoses
- Cannot prescribe treatment
- Cannot replace professional medical advice
- Cannot handle eating disorders or compulsive behaviors

### Danger Signal Recognition
**Extreme Goal Warnings**:
- Weight loss goal > 1 kg per week
- Weight gain goal > 0.5 kg per week
- Extreme calorie restriction (< 1200 cal/day)
- Excessive exercise (> 2 hours/day, 7 days/week)

**Unhealthy Behavior Indicators**:
- Completion rate < 30% for 3 consecutive weeks
- Motivation score < 3 for 2 consecutive weeks
- Physical discomfort reports
- Compulsive behavior patterns

**Referral Recommendations**:
- When danger signals appear, recommend consulting a doctor
- For chronic diseases, recommend consulting the relevant specialist
- When setting diet goals, recommend consulting a dietitian
- When setting exercise goals, recommend consulting a fitness trainer

---

## Output Format

### Goal Analysis Report
```markdown
# Health Goal Analysis Report

## Goal Overview
- Goal: Lose 5 kg in 6 months
- Start date: 2025-01-01
- Target date: 2025-06-30
- Current date: 2025-03-20

## SMART Assessment
- Specific: 5/5
- Measurable: 5/5
- Achievable: 4/5
- Relevant: 5/5
- Time-bound: 5/5

**Overall Score: A (4.8/5)**

## Progress Analysis
- Current progress: 70%
- Completed: 3.5 kg / 5.0 kg
- Time progress: 27% (79 days / 180 days)
- Progress rating: Excellent (ahead of schedule)

### Trend Analysis
- Average rate: 0.77 kg/month
- Estimated completion: 2025-05-20 (40 days early)
- Progress trend: Steady increase

## Habit Tracking
### Morning Stretch Habit
- Current streak: 21 days
- Longest streak: 21 days
- Completion rate: 95.2%
- Habit stage: Consolidation phase
- Next milestone: 30 days

## Motivation Assessment
- Current motivation: 8/10
- Motivation trend: Stable
- Motivation status: Good

## Data Correlation Analysis
### Strongly Correlated Factors (Impact > 60%)
1. Daily calorie intake (negative correlation -0.75)
2. Weekly exercise frequency (positive correlation +0.68)
3. Sleep duration (positive correlation +0.45)

### Recommendations
- Maintain current calorie intake level
- Continue 4x/week exercise frequency
- Optimize sleep duration to 7-8 hours

## Obstacle Identification
Primary obstacle: Diet control during social activities

Solutions:
- Plan meals before social events
- Choose healthy restaurants
- Control portion sizes appropriately

## Achievement Unlocked
- 21-Day Streak - Morning stretch habit achieved!
- Halfway There - Weight loss goal 50% complete!

## Next Steps
1. Maintain current progress
2. Focus on social event diet control
3. Continue building the morning stretch habit
4. Prepare for the 30-day milestone
```

---

## Technical Implementation Notes

### Data Reading
- Read main data file: `data-example/health-goals-tracker.json`
- Read log files: `data-example/health-goals-logs/YYYY-MM/YYYY-MM-DD.json`
- Related data: `data-example/nutrition-tracker.json`, `fitness-tracker.json`, etc.

### Data Processing
- Calculate completion percentage: `(current_value / target_value) * 100`
- Calculate time progress: `(days_elapsed / total_days) * 100`
- Calculate streak days: Iterate logs, count consecutive completed days
- Calculate completion rate: `(completed_days / total_days) * 100`
- Calculate habit strength: Composite score based on completion rate and streak days

### SMART Validation Algorithm
```python
def validate_smart_goal(goal):
    scores = {
        'specific': check_specificity(goal),
        'measurable': check_measurability(goal),
        'achievable': check_achievability(goal),
        'relevant': check_relevance(goal),
        'time_bound': check_time_bound(goal)
    }
    overall = sum(scores.values()) / len(scores)
    grade = get_grade(overall)
    return scores, overall, grade
```

### HTML Report Generation
- Uses ECharts 5.x CDN
- Responsive CSS layout
- JavaScript handles chart interaction
- Supports dark/light theme toggle
- Data dynamically loaded from JSON files

---

**When using this skill, always prioritize the user's health and safety!**
