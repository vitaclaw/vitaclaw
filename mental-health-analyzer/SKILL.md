---
name: mental-health-analyzer
description: "Analyzes mental health data, identifies psychological patterns, evaluates mental health status, and provides personalized mental wellness recommendations. Includes PHQ-9/GAD-7 trend analysis, mood pattern recognition, therapy progress tracking, multi-level crisis risk assessment, and correlation analysis with sleep, exercise, nutrition, and chronic disease data. Use when the user wants to review mental health trends, assess crisis risk, or track therapy progress."
version: 1.0.0
user-invocable: true
argument-hint: "[trend | pattern | therapy-progress | crisis-assessment | report | correlations]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🧠","category":"health-analyzer"}}
---

# Mental Health Analyzer Skill

## Core Features

The mental health analyzer skill provides comprehensive mental health data analysis, helping users track psychological states, identify mood patterns, monitor crisis risk, and optimize coping strategies.

**Main Modules:**

1. **Mental Health Assessment Analysis** - PHQ-9/GAD-7 scale score trend analysis
2. **Mood Pattern Recognition** - Identify common moods, triggers, and coping strategy effectiveness
3. **Therapy Progress Tracking** - Treatment goal achievement and symptom improvement assessment
4. **Crisis Risk Assessment** - Multi-level crisis risk detection (high/moderate/low) and early warning
5. **Sleep-Mental Health Correlation Analysis** - Correlation between sleep quality and mental state
6. **Exercise-Mood Correlation Analysis** - Relationship between exercise and mood improvement
7. **Nutrition-Mental Health Correlation Analysis** - Impact of diet on mood and anxiety
8. **Chronic Disease-Mental Health Correlation Analysis** - Relationship between chronic illness and mental health

## Trigger Conditions

The skill is automatically triggered in the following situations:

1. User runs `/mental trend` to view mental health trends
2. User runs `/mental pattern` to analyze mood patterns
3. User runs `/mental therapy progress` to view therapy progress
4. User runs `/crisis assessment` for crisis risk assessment
5. User runs `/mental report` to generate a mental health report

## Medical Safety Boundaries

**What this skill CANNOT do:**
- Cannot make mental illness diagnoses
- Cannot prescribe psychiatric medications
- Cannot predict suicide risk or self-harm behavior
- Cannot replace professional psychotherapy
- Cannot handle acute psychiatric crises

**What this skill CAN do:**
- Identify mental health trends and patterns
- Assess crisis risk levels and issue alerts
- Provide coping strategy suggestions (non-therapeutic)
- Track therapy progress and goal achievement
- Provide referral recommendations and professional resource information
- Analyze correlations between mental health and other health factors

## Execution Steps

### Step 1: Data Reading

Read mental health data files:
- `data-example/mental-health-tracker.json` - Main mental health file
- `data-example/mental-health-logs/.index.json` - Log index
- `data-example/mental-health-logs/YYYY-MM/YYYY-MM-DD.json` - Daily mood journal

**Data Validation:**
- Check if files exist
- Verify data structure integrity
- Confirm sufficient data points for analysis (minimum 3 PHQ-9/GAD-7 assessments, or 7 days of mood journal)

### Step 2: Mental Health Assessment Trend Analysis

**PHQ-9 Depression Score Trend Analysis:**
```
- Analyze PHQ-9 scores at different time points
- Calculate score change rate (points/month)
- Identify severity changes (none/mild/moderate/severe)
- Monitor PHQ-9 item 9 (self-harm ideation) changes
- Predict future trends (improving/stable/worsening)
- Correlate with therapy progress
```

**GAD-7 Anxiety Score Trend Analysis:**
```
- Analyze GAD-7 score temporal changes
- Identify anxiety symptom change patterns
- Correlate triggers with anxiety levels
- Evaluate coping strategy effectiveness
- Predict anxiety trends
```

**PSQI Sleep Quality and Mental State Correlation:**
```
- PSQI score correlation with PHQ-9/GAD-7 scores
- Impact of sleep disturbance on mood
- Relationship between sleep improvement and mental state improvement
```

**Severity Change Detection:**
```
- Identify severity escalation (needs attention)
- Identify severity reduction (positive signal)
- Detect rapid deterioration (>=5 points/month, crisis alert)
- Detect rapid improvement (reinforce effective strategies)
```

### Step 3: Mood Pattern Recognition

**Common Mood Statistics:**
```
- Count most frequent primary moods (top 5)
- Calculate average mood intensity
- Identify mood distribution patterns
- Analyze emotional diversity
```

**Temporal Pattern Analysis:**
```
- Daily mood change patterns (morning/afternoon/evening)
- Weekly mood change patterns (Monday through Sunday)
- Mood fluctuation magnitude (variance/standard deviation)
- Emotional stability assessment
```

**Trigger Factor Analysis:**
```
- Count high-frequency triggers (top 10)
- Calculate average impact of each trigger
- Identify high-risk triggers (high impact + high frequency)
- Correlate triggers with mood types
```

**Coping Strategy Effectiveness Assessment:**
```
- Calculate effectiveness of each coping strategy (helpful/unhelpful ratio)
- Identify highly effective coping strategies (>80% effective)
- Identify ineffective coping strategies (<50% effective)
- Analyze coping strategy-mood type matching
```

### Step 4: Therapy Progress Tracking

**Treatment Goal Achievement Assessment:**
```
- Calculate completion percentage for each goal
- Evaluate symptom improvement (baseline -> current -> target)
- Estimate goal achievement timeline
- Identify lagging goals (need adjustment)
```

**Treatment Process Analysis:**
```
- Treatment frequency and adherence
- Homework completion rate and quality
- Therapeutic alliance strength
- Pre- and post-session mood changes
```

**Symptom Improvement Assessment:**
```
- PHQ-9/GAD-7 score changes (pre-treatment -> post-treatment)
- Symptom relief percentage
- Functional level improvement
- Quality of life changes
```

### Step 5: Crisis Risk Assessment (Priority: Highest)

**Multi-Level Risk Detection Mechanism:**

```
Risk level calculation (total score 0-20+):

1. PHQ-9 Item 9 detection (highest priority)
   - Score = 2 (often): +10 points, automatically classified as high risk
   - Score = 1 (sometimes): +5 points
   - Score = 0 (not at all): +0 points

2. Rapid symptom deterioration detection
   - Rapid deterioration (>=5 points/month): +5 points
   - Deterioration (2-4 points/month): +3 points
   - Stable (-1 to 1 points/month): +0 points
   - Improvement (<=-2 points/month): -2 points

3. High-intensity negative mood proportion detection
   - Proportion > 70%: +3 points
   - Proportion 50-70%: +2 points
   - Proportion < 50%: +0 points

4. Mood fluctuation detection
   - Variance > 6 (large fluctuation): +2 points
   - Variance 4-6 (moderate fluctuation): +1 point
   - Variance < 4 (small fluctuation): +0 points

5. Crisis plan warning signal detection
   - Each warning signal detected: +2 points

6. Social withdrawal detection
   - Severe withdrawal (alone time > 80%): +3 points
   - Moderate withdrawal (alone time 50-80%): +2 points
   - Mild/no withdrawal: +0 points

7. Functional impairment detection
   - Severe impairment (>=5 days/week): +4 points
   - Moderate impairment (3-4 days/week): +2 points
   - Mild/no impairment: +0 points

Risk level determination:
- High risk (>=10 points): Seek immediate medical attention, initiate crisis intervention
- Moderate risk (5-9 points): Close monitoring, consider medical visit (within 48 hours)
- Low risk (0-4 points): Continue monitoring, regular assessment
```

**Crisis Warning Signal Detection:**
```
- Hopelessness
- Social withdrawal
- Extreme mood swings
- Talk of death
- Giving away possessions
- Self-harm ideation
- Suicidal thoughts
- Substance abuse
```

**Emergency Action Trigger Conditions:**
```
Seek immediate medical attention (within 24 hours):
- PHQ-9 item 9 score >= 2
- Total risk score >= 10
- Hallucinations or delusions
- Self-harm or suicide plan

Seek prompt medical attention (within 48 hours):
- PHQ-9 >= 15 or GAD-7 >= 15
- Total risk score 5-9
- Rapid symptom deterioration (>=5 points/month)
- Severe functional impact

Seek scheduled medical attention (within 1 month):
- PHQ-9 10-14 or GAD-7 10-14
- Total risk score < 5 but symptoms persist
- Need professional support
```

### Step 6: Sleep-Mental Health Correlation Analysis

**Data Sources:**
- Read `data-example/sleep-tracker.json`
- Extract sleep duration, sleep quality (PSQI), sleep onset time, etc.

**Correlation Analysis:**
```
- Correlation between sleep duration and PHQ-9 scores
- Correlation between sleep quality and GAD-7 scores
- Relationship between insomnia symptoms and mood stability
- Temporal relationship between sleep improvement and mental state improvement
- Association between sleep disturbance types and specific psychological symptoms
```

**Analysis Output:**
```
- Correlation coefficients and statistical significance
- Impact of sleep on mental state (high/moderate/low)
- Sleep improvement recommendations
- Bidirectional relationship between sleep and mood
```

### Step 7: Exercise-Mood Correlation Analysis

**Data Sources:**
- Read `data-example/fitness-tracker.json`
- Extract exercise frequency, exercise type, exercise intensity, exercise duration, etc.

**Correlation Analysis:**
```
- Relationship between exercise frequency and average mood intensity
- Relationship between exercise type and mood improvement effects
- Relationship between exercise intensity and anxiety levels
- Relationship between exercise duration and mood persistence
- Post-exercise mood change patterns
- Relationship between exercise habits and depression symptoms
```

**Analysis Output:**
```
- Degree of positive impact of exercise on mood
- Most effective exercise type recommendations
- Optimal exercise frequency recommendations
- Relationship between exercise and coping strategies
```

### Step 8: Nutrition-Mental Health Correlation Analysis

**Data Sources:**
- Read `data-example/nutrition-tracker.json`
- Extract caffeine intake, sugar intake, dietary habits, etc.

**Correlation Analysis:**
```
- Relationship between caffeine intake and GAD-7 anxiety scores
- Association between sugar intake and mood fluctuations
- Relationship between dietary regularity and mood stability
- Specific nutrient deficiencies (vitamin D, Omega-3) and depression symptoms
- Dietary patterns and overall mental health
```

**Analysis Output:**
```
- Degree of dietary impact on mental state
- Nutrition recommendations (e.g., reduce caffeine, balanced diet)
- Possible nutritional deficiency alerts
- Dietary adjustment recommendations
```

### Step 9: Chronic Disease-Mental Health Correlation Analysis

**Data Sources:**
- Read related chronic disease data files (e.g., `diabetes-tracker.json`, `hypertension-tracker.json`)
- Extract disease control status, symptom burden, functional limitations, etc.

**Correlation Analysis:**
```
- Relationship between chronic pain and depression symptoms
- Relationship between disease control status and mental state
- Relationship between functional limitations and mental health
- Relationship between disease burden and anxiety levels
- Comorbidity pattern recognition
- Impact of medication side effects on mood
- Relationship between medication adherence and symptom improvement
```

**Analysis Output:**
```
- Degree of chronic disease impact on mental health
- Mental health issues requiring special attention
- Holistic health management recommendations
- Benefits of mental health support for disease management
```

### Step 10: Report Generation

Output includes:
- Mental health status summary
- Assessment scale trend analysis
- Mood patterns and triggers
- Therapy progress assessment
- Crisis risk level and recommendations
- Correlation analysis with other health factors
- Personalized recommendations and action plans

## Output Format

### Mental Health Analysis Report Structure

```markdown
# Mental Health Analysis Report

**Report Date**: YYYY-MM-DD
**Analysis Period**: YYYY-MM-DD to YYYY-MM-DD
**Data Completeness**: Good

**Important Notice**: This report is for reference only and does not constitute a medical diagnosis. If you have serious psychological distress, please seek help from a professional psychologist or psychiatrist.

---

## Crisis Risk Alert

**Current Risk Level**: Low Risk | Moderate Risk | High Risk

**Risk Score**: X/20

**Risk Factors**:
- [List detected risk factors]

**Recommended Actions**:
- [Provide specific recommendations based on risk level]

---

## 1. Mental Health Status Summary

[Overall assessment: Excellent/Good/Fair/Needs Improvement/Crisis]
- PHQ-9 score: X points (severity)
- GAD-7 score: X points (severity)
- Sleep quality: X points (PSQI)
- Overall trend: Improving/Stable/Worsening

## 2. Mental Assessment Trend Analysis

### PHQ-9 Depression Score Trend
- Current score: X points
- Baseline score: X points
- Change: +/-X points
- Rate of change: X points/month
- Trend: Improving/Stable/Worsening
- Severity change: [Severity 1] -> [Severity 2]

**Chart Description**:
- [Line chart showing PHQ-9 score changes]
- [Mark severity thresholds: 5, 10, 15]

**Special Attention**:
- Item 9 (self-harm ideation) score: X
- Highest scoring item: [item name]
- Persistent issues: [list items]

### GAD-7 Anxiety Score Trend
- Current score: X points
- Baseline score: X points
- Change: +/-X points
- Rate of change: X points/month
- Trend: Improving/Stable/Worsening

**Chart Description**:
- [Line chart showing GAD-7 score changes]
- [Mark severity thresholds: 5, 10, 15]

**Primary Anxiety Symptoms**:
- Highest scoring item: [item name]
- Primary triggers: [list]

### PSQI Sleep Quality
- Total score: X points
- Sleep quality: [assessment]
- Primary issues: [list problem components]

## 3. Mood Pattern Analysis

### Common Moods
1. [Mood 1] - X% proportion, avg intensity X/10
2. [Mood 2] - X% proportion, avg intensity X/10
3. [Mood 3] - X% proportion, avg intensity X/10

**Chart Description**:
- [Pie chart showing mood distribution]
- [Radar chart showing multi-dimensional mood]

### Temporal Patterns
- Morning: Primary mood [mood], avg intensity X/10
- Afternoon: Primary mood [mood], avg intensity X/10
- Evening: Primary mood [mood], avg intensity X/10

### Weekly Patterns
- Monday-Friday: Primary mood [mood], avg intensity X/10
- Weekends: Primary mood [mood], avg intensity X/10

### Emotional Stability
- Fluctuation level: High/Moderate/Low
- Mood variance: X

**Chart Description**:
- [Line chart showing mood intensity over time]
- [Fluctuation range visualization]

## 4. Trigger Factor Analysis

### High-Frequency Triggers (Top 10)
| Rank | Trigger | Frequency | Avg Impact |
|------|---------|-----------|------------|
| 1 | [Trigger 1] | X times | High/Moderate/Low |
| 2 | [Trigger 2] | X times | High/Moderate/Low |
| ... |

### High-Risk Triggers (High Impact + High Frequency)
- [Trigger 1] - Frequency X, impact high, suggestion: [coping advice]
- [Trigger 2] - Frequency X, impact high, suggestion: [coping advice]

**Chart Description**:
- [Bar chart showing trigger frequency]
- [Heat map showing trigger-mood type correlations]

## 5. Coping Strategy Effectiveness Assessment

### Coping Strategy Ranking (by effectiveness)
| Coping Strategy | Effective Count | Ineffective Count | Effectiveness Rate | Rank |
|----------------|----------------|-------------------|-------------------|------|
| [Strategy 1] | X times | X times | XX% | 1 |
| [Strategy 2] | X times | X times | XX% | 2 |
| ... |

### Highly Effective Strategies (>80% effective)
- [Strategy 1] - XX% effectiveness, recommended for use
- [Strategy 2] - XX% effectiveness, recommended for use

### Ineffective Strategies (<50% effective)
- [Strategy 1] - XX% effectiveness, consider adjusting or discontinuing
- [Strategy 2] - XX% effectiveness, consider adjusting or discontinuing

**Chart Description**:
- [Bar chart showing coping strategy effectiveness ranking]
- [Pie chart showing effective/ineffective ratio]

## 6. Therapy Progress

### Treatment Overview
- Treatment type: [CBT/Psychodynamic/Humanistic, etc.]
- Treatment frequency: [Weekly/Biweekly, etc.]
- Sessions completed: X
- Treatment duration: X months

### Treatment Goal Progress
| Goal | Baseline | Current | Target | Progress | Estimated Achievement |
|------|----------|---------|--------|----------|----------------------|
| [Goal 1] | X pts | X pts | X pts | XX% | YYYY-MM-DD |
| [Goal 2] | X pts | X pts | X pts | XX% | YYYY-MM-DD |

**Overall Progress Assessment**: [Excellent/Good/Fair/Needs Improvement]

### Symptom Improvement
- PHQ-9 score change: X pts -> X pts, XX% improvement
- GAD-7 score change: X pts -> X pts, XX% improvement
- Overall functional level: [Improved/Stable/Worsened]

### Homework Completion
- Average completion rate: XX%
- High-quality completion: XX%
- Areas needing improvement: [list]

## 7. Crisis Risk Assessment

### Risk Level
**Current Risk Level**: Low Risk | Moderate Risk | High Risk

**Risk Score**: X/20

### Risk Factor Analysis
| Risk Factor | Score | Details |
|------------|-------|---------|
| PHQ-9 Item 9 | X pts | Score X, [details] |
| Symptom Change | X pts | [Rapid deterioration/Deterioration/Stable/Improvement] |
| Mood Intensity | X pts | High-intensity negative mood proportion XX% |
| Mood Fluctuation | X pts | Fluctuation [large/moderate/small] |
| Warning Signals | X pts | X warning signals detected: [list] |
| Social Withdrawal | X pts | [Severe/Moderate/Mild/No] withdrawal |
| Functional Impairment | X pts | [Severe/Moderate/Mild/No] impairment |

### Detected Warning Signals
- [List if any]

### Recommended Actions
- [Provide specific action recommendations based on risk level]

### Emergency Resources
- Mental health crisis hotline: 988 (Suicide & Crisis Lifeline, US) / contact local emergency services
- Psychiatric emergency: Nearest hospital emergency department
- Emergency number: 911 (US) / local emergency number

## 8. Correlation Analysis with Other Health Factors

### Sleep-Mental Health Correlation
**Correlation Strength**: High/Moderate/Low

**Key Findings**:
- Correlation between sleep duration and PHQ-9 scores: r=X.XX
- Relationship between sleep quality and mood stability: [description]
- Primary sleep issues: [list]
- Potential benefits of improving sleep on mental state: [description]

**Recommendations**:
- [Specific sleep improvement recommendations]

### Exercise-Mood Correlation
**Correlation Strength**: High/Moderate/Low

**Key Findings**:
- Relationship between exercise frequency and mood improvement: [description]
- Most effective exercise types: [list]
- Post-exercise mood changes: [description]

**Recommendations**:
- [Specific exercise recommendations]

### Nutrition-Mental Health Correlation
**Correlation Strength**: High/Moderate/Low

**Key Findings**:
- Relationship between caffeine intake and anxiety: [description]
- Relationship between sugar intake and mood fluctuations: [description]
- Possible nutritional deficiencies: [list]

**Recommendations**:
- [Specific nutrition recommendations]

### Chronic Disease-Mental Health Correlation
**Correlation Strength**: High/Moderate/Low

**Key Findings**:
- Relationship between [chronic disease] and mental state: [description]
- Impact of disease burden on mental health: [description]
- Relationship between functional limitations and mood: [description]

**Recommendations**:
- [Specific holistic health management recommendations]

## 9. Comprehensive Recommendations

### Immediate Actions (if applicable)
- [List actions to take immediately if there are urgent issues]

### This Week's Action Plan
1. [Action item 1] - Priority: High/Moderate/Low
2. [Action item 2] - Priority: High/Moderate/Low
3. ...

### Monthly Goals
1. [Goal 1]
2. [Goal 2]
3. ...

### Areas to Continue
- [List areas that are going well, encourage continued effort]

### Areas to Improve
- [List areas needing improvement, provide specific suggestions]

### Recommended Resources
- [Books/apps/support groups/online resources, etc.]

## 10. Data Quality Notes

- Data completeness: [Excellent/Good/Fair/Needs Improvement]
- PHQ-9 assessments: X times
- GAD-7 assessments: X times
- Mood journal entries: X entries
- Time span: X days

---

**Report generated**: YYYY-MM-DD HH:MM:SS
**Next assessment recommended**: YYYY-MM-DD

**Disclaimer**: This report is automatically generated by the mental health analyzer skill. It is for reference only and does not constitute a medical diagnosis or treatment recommendation. If you have any mental health concerns, please seek help from a professional psychologist or psychiatrist.
```

## Usage Examples

### Example 1: Trend Analysis

**User Input**:
```
/mental trend 3months
```

**Skill Execution**:
1. Read the most recent 3 months of PHQ-9 and GAD-7 assessment data
2. Calculate score change rates and trends
3. Analyze severity changes
4. Check PHQ-9 item 9 changes
5. Generate trend report

**Output**:
```markdown
# Mental Health Trend Analysis (Past 3 Months)

## Overall Trend
- PHQ-9: 14 pts -> 8 pts, improved by 6 pts, Trend: Improving
- GAD-7: 12 pts -> 6 pts, improved by 6 pts, Trend: Improving
- Rate of change: ~2 pts/month

## Severity Changes
- PHQ-9: Moderate depression -> Mild depression
- GAD-7: Moderate anxiety -> Mild anxiety

## Positive Signals
- Sustained symptom improvement
- PHQ-9 item 9 score: 1 -> 0
- Treatment is effective

## Recommendations
- Continue current treatment
- Maintain exercise and sleep habits
- Next assessment: 1 month from now
```

### Example 2: Mood Pattern Analysis

**User Input**:
```
/mental pattern
```

**Skill Execution**:
1. Read mood journal data
2. Count common moods and temporal patterns
3. Analyze triggers and coping strategies
4. Generate pattern recognition report

**Output**:
```markdown
# Mood Pattern Analysis

## Common Moods (Top 3)
1. Anxiety - 35% proportion, avg intensity 7/10
2. Fatigue - 25% proportion, avg intensity 6/10
3. Calm - 20% proportion, avg intensity 7/10

## Temporal Patterns
- Morning: Calm (intensity 7/10)
- Afternoon: Anxiety (intensity 7/10)
- Evening: Fatigue (intensity 6/10)

## Primary Triggers (Top 5)
1. Work stress - 12 times, impact high
2. Sleep deprivation - 8 times, impact moderate
3. Exercise - 6 times, impact positive
4. Social activities - 5 times, impact positive
5. Traffic congestion - 4 times, impact moderate

## Highly Effective Coping Strategies
1. Exercise - 90% effectiveness
2. Meditation - 85% effectiveness
3. Deep breathing - 75% effectiveness

## Recommendations
- When afternoon work stress is high, try deep breathing or a short walk
- Maintain regular exercise, which has significant mood improvement effects
- Improving sleep can help reduce anxiety and fatigue
```

### Example 3: Crisis Risk Assessment

**User Input**:
```
/crisis assessment
```

**Skill Execution**:
1. Read the most recent PHQ-9/GAD-7 assessments
2. Read the most recent mood journal entries
3. Execute crisis risk detection algorithm
4. Calculate risk score and level
5. Generate crisis risk report

**Output**:
```markdown
# Crisis Risk Assessment

## Current Risk Level: Low Risk

**Risk Score**: 3/20

## Risk Factor Analysis
| Risk Factor | Score | Details |
|------------|-------|---------|
| PHQ-9 Item 9 | 0 pts | Score 0, no self-harm ideation |
| Symptom Change | -2 pts | Improving trend |
| Mood Intensity | 2 pts | High-intensity negative mood proportion 45% |
| Mood Fluctuation | 1 pt | Moderate fluctuation |
| Warning Signals | 0 pts | None detected |
| Social Withdrawal | 0 pts | Social activities are good |
| Functional Impairment | 0 pts | Function normal |
| **Total** | **3 pts** | **Low risk** |

## Recommended Actions
- Continue monitoring mental state
- Maintain healthy lifestyle habits
- Regular mental health assessments (monthly)
- Continue psychotherapy (if applicable)

## Emergency Resources (for reference)
- Mental health crisis hotline: 988 (Suicide & Crisis Lifeline, US) / contact local emergency services
- Psychiatric emergency: Nearest hospital emergency department
- Emergency number: 911 (US) / local emergency number

If any of the following occur, seek professional help immediately:
- Self-harm or suicidal thoughts or plans
- Hallucinations, delusions
- Complete loss of function
- Uncontrollable emotional outbursts
```

### Example 4: Therapy Progress Analysis

**User Input**:
```
/mental therapy progress
```

**Skill Execution**:
1. Read therapy records and goals
2. Calculate goal completion percentages
3. Analyze symptom improvement
4. Evaluate homework completion
5. Generate therapy progress report

**Output**:
```markdown
# Therapy Progress Analysis

## Treatment Overview
- Treatment type: CBT (Cognitive Behavioral Therapy)
- Treatment frequency: Weekly
- Sessions completed: 24
- Treatment duration: 5 months

## Treatment Goal Progress
| Goal | Baseline | Current | Target | Progress | Est. Achievement |
|------|----------|---------|--------|----------|-----------------|
| Reduce anxiety level | 14 pts | 8 pts | 5 pts | 57% | 2025-08-01 |
| Improve sleep quality | 10 pts | 6 pts | 4 pts | 60% | 2025-07-15 |
| Increase pleasant activities | 2x/week | 5x/week | 7x/week | 50% | 2025-07-01 |

**Overall Progress Assessment**: Good

## Symptom Improvement
- PHQ-9 score: 14 pts -> 8 pts, 43% improvement
- GAD-7 score: 14 pts -> 6 pts, 57% improvement
- Overall functional level: Significantly improved

## Homework Completion
- Average completion rate: 85%
- High-quality completion: 60%
- Area needing improvement: Cognitive restructuring exercises

## Treatment Highlights
- Significant anxiety symptom improvement
- Notable sleep quality improvement
- Behavioral activation working well
- Improved cognitive distortion identification

## Continue
- Weekly therapy sessions
- Daily relaxation exercises
- Behavioral activation (exercise, social activities)
- Thought records

## Areas to Strengthen
- Cognitive restructuring exercises
- Coping skill application
- Sleep hygiene maintenance
```

### Example 5: Correlation Analysis

**User Input**:
```
/mental analysis correlations
```

**Skill Execution**:
1. Read mental health, sleep, exercise, nutrition, chronic disease data
2. Calculate correlation coefficients
3. Analyze impact levels
4. Generate correlation analysis report

**Output**:
```markdown
# Mental Health Correlation Analysis

## Sleep-Mental Health Correlation (Strength: High)

### Key Findings
- Sleep duration negatively correlated with PHQ-9 score (r=-0.72, p<0.01)
- Sleep quality positively correlated with mood stability (r=0.68, p<0.01)
- Each 1-point improvement in PSQI is associated with 1.2-point decrease in PHQ-9

### Sleep Problem Impact
- Difficulty falling asleep -> 40% increase in next-day anxiety
- Night waking -> 35% increase in next-day low mood
- Insufficient sleep -> Difficulty concentrating, increased mood fluctuations

### Recommendations
- Maintain regular schedule, aim to be in bed by 23:00
- Improve sleep hygiene: avoid afternoon caffeine
- Continue relaxation exercises to promote sleep

## Exercise-Mood Correlation (Strength: High)

### Key Findings
- Exercise frequency positively correlated with positive mood proportion (r=0.75, p<0.01)
- Average mood intensity 1.5 points higher on exercise days vs. non-exercise days
- Anxiety decreases by 50% on average after exercise

### Most Effective Exercise Types
1. Aerobic exercise (running, swimming) - 85% improvement rate
2. Yoga - 80% improvement rate
3. Outdoor walking - 75% improvement rate

### Recommendations
- Maintain 3-5 exercise sessions per week, 30+ minutes each
- Prioritize aerobic exercise
- Try outdoor walking when anxious

## Nutrition-Mental Health Correlation (Strength: Moderate)

### Key Findings
- Caffeine intake positively correlated with GAD-7 score (r=0.52, p<0.05)
- High-sugar diet positively correlated with mood fluctuations (r=0.48, p<0.05)
- Insufficient Omega-3 intake may be associated with depression symptoms

### Recommendations
- Reduce caffeine intake (max 2 cups/day)
- Reduce added sugar intake
- Consider Omega-3 supplementation (consult physician)

## Comprehensive Recommendations
Based on correlation analysis, the following lifestyle factors are most effective for improving mental health:
1. **Regular exercise** (3-5 times/week, 30 min+)
2. **Adequate sleep** (7-8 hours, in bed by 23:00)
3. **Balanced diet** (reduce caffeine and sugar)
4. **Continued treatment** (CBT psychotherapy)

These 4 areas combined contribute approximately **75%** of mental health improvement.
```

### Example 6: Full Report Generation

**User Input**:
```
/mental report
```

**Skill Execution**:
1. Read all relevant data
2. Execute complete analysis workflow
3. Generate interactive HTML report
4. Include crisis warnings and recommendations

**Output**:
Generates a complete mental health analysis HTML report file, including:
- All charts (ECharts interactive charts)
- Crisis risk warnings (if applicable)
- Detailed analysis and recommendations
- Downloadable or printable

---

## Error Handling

### Data File Not Found
```
Error: Mental health data file not found.
Suggestion: Please use /mental assess or /mental mood commands to create data first.
```

### Insufficient Data
```
Warning: Insufficient data for trend analysis.
Suggestion: At least 3 PHQ-9/GAD-7 assessments or 7 days of mood journal needed.
Current data: X PHQ-9 assessments, X mood journal entries.
```

### High Crisis Risk
```
CRISIS WARNING: High risk factors detected.

Immediate actions:
1. Contact mental health crisis hotline: 988 (US) / local emergency services
2. Go to nearest psychiatric emergency department
3. Call emergency number: 911 (US) / local emergency number
4. Contact family or friends to stay with you

Detected risk factors:
- [List high-risk factors]

Do not hesitate - seek professional help immediately!
```

## Data Source Description

**Primary Data Sources**:
- `data-example/mental-health-tracker.json` - Main mental health data
- `data-example/mental-health-logs/` - Mood journal logs

**Related Data Sources**:
- `data-example/sleep-tracker.json` - Sleep data
- `data-example/fitness-tracker.json` - Exercise data
- `data-example/nutrition-tracker.json` - Nutrition data
- `data-example/diabetes-tracker.json` - Diabetes data (if applicable)
- `data-example/hypertension-tracker.json` - Hypertension data (if applicable)
- `data-example/medication-tracker.json` - Medication data

## Performance Optimization

For large data volumes (e.g., >6 months of mood journal), the following optimization strategies are used:
- Data aggregation: Aggregate mood data by week/month
- Sampling analysis: Random sampling of representative data points
- Incremental analysis: Analyze only newly added data
- Cache intermediate results
