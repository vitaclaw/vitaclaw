---
name: rehabilitation-analyzer
description: "Analyzes rehabilitation training data, identifies recovery patterns, assesses rehabilitation progress, and provides personalized rehabilitation recommendations. Tracks ROM, muscle strength, balance, pain trends, and training adherence. Use when the user wants to review rehabilitation progress or analyze recovery trends."
version: 1.0.0
user-invocable: true
argument-hint: "[progress | analysis | trends | report]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🦿","category":"health-analyzer"}}
---

# Rehabilitation Training Analysis Skill

## Core Features

The Rehabilitation Training Analysis skill provides comprehensive rehabilitation data analysis, helping users track recovery progress, identify improvement patterns, and optimize training plans.

**Main Feature Modules:**

1. **Rehabilitation Progress Analysis** - Assess functional improvement trends and recovery effectiveness
2. **Functional Improvement Curves** - Visualize changes in ROM, muscle strength, balance, and other functional indicators
3. **Pain Pattern Recognition** - Analyze pain score change trends and trigger factors
4. **Goal Achievement Rate Assessment** - Track rehabilitation goal completion status
5. **Rehabilitation Phase Analysis** - Evaluate current phase progress and phase transition readiness
6. **Training Adherence Assessment** - Analyze training plan execution status

## Trigger Conditions

The skill is automatically triggered in the following situations:

1. User runs `/rehab progress` to view rehabilitation progress
2. User runs `/rehab analysis` to perform rehabilitation analysis
3. User runs `/rehab trends` to view trend analysis
4. User runs `/rehab report` to generate a rehabilitation report

## Execution Steps

### Step 1: Data Reading
Read rehabilitation data files:
- `data/rehabilitation-tracker.json` - Main rehabilitation profile
- `data/rehabilitation-logs/YYYY-MM/YYYY-MM-DD.json` - Daily training logs

**Data Validation:**
- Check if files exist
- Verify data structure integrity
- Confirm sufficient data points for analysis (recommend at least 3 assessments or 10 days of training records)

### Step 2: Functional Assessment Trend Analysis

**Range of Motion (ROM) Analysis:**
```
- Analyze ROM measurements at different time points
- Calculate ROM improvement rate (degrees/week)
- Identify ROM plateaus or regression
- Predict time to reach target ROM
- Compare against target range
```

**Muscle Strength Improvement Analysis:**
```
- Track muscle strength grade changes (MMT score)
- Identify strength improvement patterns
- Compare recovery rates across different muscle groups
- Assess muscle strength imbalances
```

**Balance Function Analysis:**
```
- Balance test score trends
- Single-leg stance time improvement
- Balance stability assessment
- Fall risk changes
```

### Step 3: Pain Pattern Analysis

**Pain Temporal Analysis:**
```
- Analyze morning pain trends
- Analyze post-activity pain trends
- Identify pain exacerbation/relief patterns
- Correlate pain with training intensity
```

**Pain Trigger Factor Identification:**
```
- Relationship between specific exercises and pain
- Correlation between training intensity and pain
- Relationship between activity type and pain
- Impact of timing factors on pain
```

### Step 4: Training Adherence Calculation

**Adherence Metrics:**
```
Adherence = (Actual Training Sessions / Planned Training Sessions) x 100%
```

**Analysis Dimensions:**
- Weekly adherence
- Monthly adherence
- Overall adherence
- Adherence by training type

### Step 5: Goal Achievement Assessment

**Goal Progress Tracking:**
- Calculate completion percentage for each goal
- Estimate goal achievement timeline
- Identify lagging goals
- Provide goal adjustment recommendations

### Step 6: Rehabilitation Phase Assessment

**Current Phase Analysis:**
- Phase goal completion status
- Readiness to progress to the next phase
- Phase transition recommendations

### Step 7: Report Generation

Output includes:
- Rehabilitation progress summary
- Functional improvement trends
- Pain control status
- Training adherence evaluation
- Goal achievement assessment
- Phase progression recommendations
- Personalized recommendations

## Output Format

### Rehabilitation Progress Report Structure

```markdown
# Rehabilitation Progress Report
**Report Date**: YYYY-MM-DD
**Rehabilitation Duration**: X days
**Current Phase**: Phase X - Phase Name

## 1. Rehabilitation Progress Summary

[Overall Progress Rating: Excellent/Good/Fair/Needs Improvement]
- Rehabilitation Duration: X days (Week X)
- Completed Training Sessions: X
- Training Adherence: X%
- Current Phase Progress: X%

## 2. Functional Improvement Trends

### Range of Motion (ROM)
- [Joint Name] [Movement Type]: Baseline X deg -> Current X deg -> Improvement X deg
- Improvement Rate: X deg/week
- Estimated Time to Goal: X weeks
- Trend Analysis: [Improvement trend description]

### Muscle Strength Assessment
- [Muscle Group]: Baseline X/5 -> Current X/5 -> Improvement X grade(s)
- Strength Improvement Pattern: [Description]
- Strength Balance: [Assessment]

### Balance Function
- [Test Type]: Baseline X -> Current X -> Improvement X
- Balance Stability: [Assessment]
- Fall Risk: [Assessment]

## 3. Pain Control Status

- Average Pain Level: X/10
- Pain Trend: [Improving/Stable/Worsening]
- Pain Pattern: [Description]
- Trigger Factors: [Identified triggers]
- Pain Control Recommendations: [Recommendations]

## 4. Training Adherence

- Overall Adherence: X%
- Planned Sessions: X
- Completed Sessions: X
- Adherence Rating: [Excellent/Good/Fair/Needs Improvement]
- Missed Session Analysis: [If applicable]

## 5. Goal Achievement Status

### Achieved Goals (X)
- Goal 1: [Description] - Achieved on: YYYY-MM-DD
- ...

### In-Progress Goals (X)
- Goal 1: [Description] - Current Progress: X% - Estimated Achievement: YYYY-MM-DD
- ...

### Lagging Goals (X)
- Goal 1: [Description] - Current Progress: X% - Needs Attention

## 6. Rehabilitation Phase Progress

**Current Phase**: Phase X - [Phase Name]
- Phase Goals Completed: X/X
- Phase Progress: X%
- Phase Duration: X weeks
- **Phase Rating**: [Rating]

**Ready to Progress to Next Phase**: [Yes/No]
- [Reasons for readiness] / [Items requiring further effort]

## 7. Personalized Recommendations

### Training Recommendations
- [Specific training recommendations]

### Goal Adjustment Recommendations
- [Goal adjustment recommendations]

### Phase Transition Recommendations
- [Phase transition recommendations]

### Precautions
- [Items to watch for]

## 8. Next Assessment

**Next Assessment Date**: YYYY-MM-DD
**Assessment Focus**: [Key assessment items]
```

### Brief Progress Report

```markdown
## Rehabilitation Progress Brief

**Overall Progress**: Good
**Rehabilitation Duration**: Week X (X days)
**Phase**: Phase X - [Phase Name]

**Functional Improvement**:
- ROM: +X deg (improvement rate X deg/week)
- Muscle Strength: Improved X grade(s)
- Balance: Improved X%

**Pain Control**: Average X/10 ([Trend])
**Training Adherence**: X% ([Rating])
**Goal Achievement**: X/X (X%)

**Current Phase**: X/X goals completed
**Next Phase Readiness**: [Yes/No]

**Recommendation**: [1-2 key recommendations]
```

## Data Sources

### Main Data File
- **File Path**: `data/rehabilitation-tracker.json`
- **Read Fields:**
  - `user_profile` - User profile and basic rehabilitation information
  - `rehabilitation_goals` - Rehabilitation goal list
  - `exercise_log` - Training log
  - `functional_assessments` - Functional assessment records
  - `phase_progression` - Phase progression records
  - `pain_diary` - Pain diary
  - `statistics` - Statistical data

### Log Data Files
- **File Path**: `data/rehabilitation-logs/YYYY-MM/YYYY-MM-DD.json`
- **Read Fields:**
  - `daily_summary` - Daily training summary
  - `exercise_sessions` - Training details
  - `pain_entries` - Pain records
  - `assessments` - Assessment records
  - `notes` - Daily notes

## Analysis Algorithms

### 1. Improvement Trend Analysis

**Linear Regression Analysis:**
```
Use least-squares method to fit functional improvement trends
Improvement Rate = (Current Value - Baseline Value) / Time Interval
```

**Improvement Pattern Recognition:**
- Linear improvement: Steady, continuous improvement
- Stepwise improvement: Rapid improvement following a plateau
- Plateau: Improvement stagnation
- Regression: Functional decline (requires attention)

### 2. Pain Temporal Analysis

**Moving Average Calculation:**
```
7-Day Moving Average Pain = sum(pain over last 7 days) / 7
```

**Pain Trend Determination:**
- Improving: Pain score decreased by >=20%
- Stable: Pain score change <20%
- Worsening: Pain score increased by >=20%

### 3. Adherence Calculation

```
Overall Adherence = (Actual Training Days / Planned Training Days) x 100%

Training Type Adherence = (Actual Completions of Type / Planned Completions of Type) x 100%
```

**Adherence Rating:**
- Excellent: >=90%
- Good: 75-89%
- Fair: 60-74%
- Needs Improvement: <60%

### 4. Goal Achievement Prediction

**Linear Extrapolation:**
```
Predicted Time = Current Date + ((Target Value - Current Value) / Improvement Rate)
```

**Factors Considered:**
- Recent improvement rate
- Plateau history
- Training adherence

### 5. Phase Transition Readiness Assessment

**Readiness Score:**
```
Readiness = (Phase Goals Achieved / Total Phase Goals) x 100%

Readiness >= 80%: Recommend progressing to next phase
Readiness 60-79%: May consider progressing to next phase with caution
Readiness < 60%: Recommend continuing current phase
```

## Security and Privacy

### Data Security Principles

1. **Local Storage**
   - All rehabilitation data is stored only on the user's local device
   - Not uploaded to any cloud servers
   - Not shared with third parties

2. **Privacy Protection**
   - Personal health information is strictly confidential
   - Data files do not contain personally identifiable information
   - Users have full control over data access permissions

3. **Data Integrity**
   - Original data is not modified
   - Analysis results are based on actual data
   - Supports data export and backup

### Medical Safety Boundaries

**What the system CANNOT do:**
- Does not provide specific rehabilitation exercise prescriptions
- Does not replace professional rehabilitation therapist guidance
- Does not diagnose injuries or complications
- Does not modify rehabilitation phase plans
- Does not predict rehabilitation prognosis timelines
- Does not handle acute pain or injuries

**What the system CAN do:**
- Provides data analysis and trend identification
- Provides progress tracking and goal management
- Provides general rehabilitation recommendations
- Provides professional rehabilitation referral reminders
- Records training and assessment data
- Generates rehabilitation progress reports

**Important Notice:**
- All rehabilitation training plans should follow therapist guidance
- Any worsening pain or functional regression should prompt immediate medical attention
- Regular professional assessments are key to successful rehabilitation
- System recommendations are for reference only and do not replace professional judgment

## Error Handling

### Data Reading Errors

**Error Type 1: File Not Found**
```
Error: Rehabilitation data file not found. Please use /rehab start to begin rehabilitation tracking first.
Action: Guide the user to start rehabilitation recording.
```

**Error Type 2: Insufficient Data**
```
Error: Insufficient data. At least 3 functional assessments or 10 days of training records are required to generate an analysis report.
Current Data: X assessments, X days of training records.
Action: Recommend the user continue recording more data.
```

**Error Type 3: Data Structure Error**
```
Error: Data file structure is abnormal. Please check data integrity.
Action: Recommend the user reinitialize the rehabilitation profile.
```

### Analysis Process Errors

**Error Type: Calculation Exception**
```
Error: An exception occurred during data analysis. Please try again later.
Action: Log the error; provide basic data display.
```

### Output Generation Errors

**Error Type: Report Generation Failed**
```
Error: Report generation failed. Please try simplifying query conditions or contact technical support.
Action: Provide a simplified report or raw data export.
```

## Usage Examples

### Example 1: View Rehabilitation Progress

**User Input:**
```
/rehab progress
```

**Skill Execution:**
1. Read rehabilitation-tracker.json
2. Read rehabilitation logs from the past 30 days
3. Analyze functional improvement trends
4. Calculate training adherence
5. Assess goal achievement status
6. Generate progress report

**Output:**
```
# Rehabilitation Progress Report

## Rehabilitation Progress Summary
Overall Progress: Good
Rehabilitation Duration: Week 6 (36 days)
Current Phase: Phase 3 - Strengthening

## Functional Improvement
- Knee Flexion: 30 deg -> 120 deg (+90 deg)
- Knee Extension: -10 deg -> 0 deg (+10 deg)
- Quadriceps Strength: 3/5 -> 4/5 (Improved 1 grade)
- Single-Leg Stance: 5 sec -> 30 sec (+25 sec)

## Pain Control
- Average Pain: 1.5/10 (Well controlled)
- Pain Trend: Stable

## Training Adherence: 92% (Excellent)

## Goal Achievement: 8/14 (57%)
- Achieved: 8
- In Progress: 5
- Lagging: 1

## Phase Progress
Phase 3 Progress: 2/5 goals completed (40%)
Next Phase Readiness: Needs further effort

Recommendation: Maintain current training intensity; focus on quadriceps strengthening exercises
```

### Example 2: Analyze Functional Improvement Trends

**User Input:**
```
/rehab trends rom
```

**Skill Execution:**
1. Extract all ROM assessment records
2. Describe ROM improvement curve
3. Calculate improvement rate
4. Predict time to reach target
5. Identify improvement pattern

**Output:**
```
# Range of Motion (ROM) Trend Analysis

## Knee Flexion
Improvement Trend: Good

Timeline:
- 5/15: 30 deg (Baseline)
- 5/30: 70 deg (+40 deg)
- 6/15: 100 deg (+30 deg)
- 6/20: 120 deg (+20 deg)

Improvement Rate: 8.6 deg/week
Target: 135 deg
Estimated Achievement: 2025-08-01 (2 more weeks)
Trend: Continuous improvement

## Knee Extension
Target achieved

Timeline:
- 5/15: -10 deg (Baseline)
- 6/10: 0 deg (Target achieved)
- 6/20: 0 deg (Maintained)

Improvement Rate: 2.5 deg/week
Target: 0 deg
Achievement Date: 2025-06-10
Trend: Maintaining target

## Recommendations
- Knee flexion progressing well; continue current approach
- Maintain extension exercises to prevent flexion contracture
- Target flexion goal expected within 2 weeks
```

### Example 3: Assess Pain Patterns

**User Input:**
```
/rehab analysis pain
```

**Skill Execution:**
1. Extract all pain records
2. Analyze pain temporal changes
3. Identify pain trigger factors
4. Assess pain control effectiveness

**Output:**
```
# Pain Pattern Analysis

## Pain Trend
Overall Trend: Improving

- Baseline Pain: 5/10
- Current Pain: 2/10
- Improvement: 3 points (60% improvement)

## Temporal Pattern
- Morning Pain: 1/10 (Mild)
- Post-Activity Pain: 2/10 (Mild)
- Resting Pain: 0/10 (None)

## Trigger Factor Identification
- Main Triggers: Prolonged sitting, stairs
- Pain-Aggravating Activities: Descending stairs, deep squats
- Relief Factors: Rest, ice, elevation

## Training-Related Pain
- Average Pain During Training: 1.2/10 (Safe range)
- Post-Training Pain: 2/10 (Resolves quickly)
- Training adherence unaffected by pain

## Recommendations
- Pain is well controlled; maintain current training intensity
- Rest and apply ice after training
- Avoid pain-aggravating activities (deep squats, descending stairs)
- If pain exceeds 4/10, seek medical evaluation promptly
```

## Correlation Analysis

### Correlation with Exercise Module

**Correlation Analysis:**
- Relationship between rehabilitation training and exercise capacity recovery
- Relationship between rehabilitation training intensity and heart rate changes
- Correlation between functional improvement and daily activity levels

**Example:**
```
User runs /rehab analysis correlation fitness
Skill reads:
- rehabilitation-tracker.json
- fitness-tracker.json
- Analyzes correlation between rehabilitation training and exercise metrics
```

### Correlation with Sleep Module

**Correlation Analysis:**
- Relationship between training intensity and sleep quality
- Relationship between pain levels and sleep duration
- Recovery-phase sleep needs analysis

### Correlation with Medication Module

**Correlation Analysis:**
- Pain medication usage trends
- Relationship between medication and training intensity
- Pain control and medication adherence
