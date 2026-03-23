---
name: occupational-health-analyzer
description: "Analyzes occupational health data, identifies work-related health risks, assesses occupational health status, and provides personalized workplace wellness recommendations. Supports correlation analysis with sleep, exercise, and mental health data. Use when the user wants to evaluate workplace ergonomics or track occupational health issues."
version: 1.0.0
user-invocable: true
argument-hint: "[trend | status | recommend | assess | issue | ergonomic]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏢","category":"health-analyzer"}}
---

# Occupational Health Analysis Skill

## Core Features

The Occupational Health Analysis skill provides comprehensive occupational health data analysis, helping users track work-related health issues, identify occupational health risks, assess workplace ergonomics, and optimize occupational wellness.

**Main Feature Modules:**

1. **Occupational Health Risk Assessment** - Multi-dimensional risk assessment covering prolonged sitting, VDT use, shift work, repetitive strain, and work stress
2. **Work-Related Issue Tracking** - Monitoring symptoms such as neck/shoulder/back/leg pain, eye fatigue, and carpal tunnel syndrome
3. **Ergonomic Assessment** - Comprehensive evaluation of workstation, chair, monitor, keyboard, and environment
4. **Occupational Disease Screening** - Risk assessment and screening recommendations based on job type
5. **Trend Analysis** - Symptom progression, improvement effects, and risk change trends
6. **Correlation Analysis** - Cross-analysis with sleep, exercise, mental health, and chronic disease modules
7. **Personalized Recommendations** - Work posture, break reminders, equipment suggestions, and environment optimization
8. **Alert System** - Warnings for high-risk patterns, symptom deterioration, and occupational disease risk

## Trigger Conditions

The skill is automatically triggered in the following situations:

1. User runs `/work trend` to view occupational health trends
2. User runs `/work status` to view comprehensive health status
3. User runs `/work recommend` to get improvement suggestions
4. User runs `/work assess` to perform a comprehensive assessment
5. User runs `/work issue` to analyze after logging an issue
6. User runs `/work ergonomic` to analyze after an ergonomic assessment

## Medical Safety Boundaries

**What this skill CANNOT do:**
- Does not diagnose occupational diseases
- Does not issue occupational disease certificates
- Does not replace workplace health surveillance
- Does not predict disease progression
- Does not handle acute health crises

**What this skill CAN do:**
- Occupational health risk assessment and screening
- Work-related symptom identification and tracking
- Ergonomic assessment and improvement recommendations
- Occupational disease risk alerts
- Workplace environment improvement suggestions
- Health record keeping (for reference during medical visits)
- Correlation analysis with other health data

## Execution Steps

### Step 1: Data Reading

Read occupational health data files:
- `data-example/occupational-health-tracker.json` - Main occupational health profile

**Data Validation:**
- Check if files exist
- Verify data structure integrity
- Confirm sufficient data points for analysis

### Step 2: Occupational Health Risk Assessment

#### Sedentary Risk Assessment (Sedentary Risk Score)

**Scoring Dimensions (0-10 points each):**

1. **Daily Sedentary Time** (sedentary_time_daily)
   - >8 hours: 10 points
   - 6-8 hours: 7 points
   - 4-6 hours: 4 points
   - <4 hours: 1 point

2. **Break Frequency** (break_frequency)
   - No breaks: 10 points
   - Every 3+ hours: 8 points
   - Every 2 hours: 5 points
   - Every hour: 2 points

3. **Weekly Exercise Time** (weekly_exercise_minutes)
   - 0 minutes: 10 points
   - <60 minutes: 7 points
   - 60-150 minutes: 4 points
   - >150 minutes: 1 point

4. **Existing Symptoms** (existing_symptoms_severity)
   - Severe symptoms: 10 points
   - Moderate symptoms: 7 points
   - Mild symptoms: 4 points
   - No symptoms: 1 point

**Total Score Calculation:**
```
Total = Sedentary Time + Break Frequency + Exercise Time + Existing Symptoms
Range: 4-40 points
```

**Risk Level Classification:**
- Low Risk: 4-13 points
- Medium Risk: 14-26 points
- High Risk: 27-40 points

#### VDT Risk Assessment (Visual Display Terminal Risk Score)

**Scoring Dimensions (0-10 points each):**

1. **Daily Screen Time** (screen_time_daily)
   - >8 hours: 10 points
   - 6-8 hours: 7 points
   - 4-6 hours: 4 points
   - <4 hours: 1 point

2. **20-20-20 Rule Compliance** (rule_20_20_20_compliance)
   - Never compliant: 10 points
   - Occasionally compliant: 6 points
   - Often compliant: 3 points
   - Always compliant: 1 point

3. **Lighting Conditions** (lighting_quality)
   - Very poor: 10 points
   - Poor: 7 points
   - Fair: 4 points
   - Good: 1 point

4. **Eye Symptoms** (eye_symptoms_severity)
   - Severe symptoms: 10 points
   - Moderate symptoms: 7 points
   - Mild symptoms: 4 points
   - No symptoms: 1 point

**Total score calculation and risk level classification are the same as Sedentary Risk.**

#### Comprehensive Risk Assessment

**Composite Risk Level Calculation:**
```
Composite Risk Score = max(Sedentary Risk, VDT Risk, Shift Work Risk, Strain Risk, Stress Risk)

If multiple high-risk factors exist (>=27 points), the composite risk level is elevated by one tier.
If 3 or more medium-risk factors exist (14-26 points), the composite risk level is elevated by one tier.
```

### Step 3: Ergonomic Assessment

#### Assessment Dimensions and Scoring

**Chair Assessment** (0-20 points):
```
- Adjustability (0-5 points)
- Lumbar Support (0-5 points)
- Seat Depth (0-5 points)
- Armrests (0-5 points)
```

**Monitor Assessment** (0-20 points):
```
- Height (0-7 points)
- Distance (0-7 points)
- Angle (0-6 points)
```

**Keyboard and Mouse Assessment** (0-20 points):
```
- Keyboard Position (0-5 points)
- Mouse Position (0-5 points)
- Wrist Support (0-10 points)
```

**Desk Assessment** (0-20 points):
```
- Height (0-10 points)
- Space (0-10 points)
```

**Environment Assessment** (0-20 points):
```
- Lighting (0-7 points)
- Noise (0-7 points)
- Temperature (0-6 points)
```

**Total Score Calculation:**
```
Total = Chair + Monitor + Keyboard/Mouse + Desk + Environment
Range: 0-100 points

Rating Scale:
- Excellent: 0-20 points
- Good: 21-40 points
- Fair: 41-60 points
- Poor: 61-80 points
- Very Poor: 81-100 points
```

### Step 4: Occupational Disease Screening

#### Job-Type-Based Screening Recommendations

**Office Work:**
```
Required Screenings:
- Vision test (annually)
- Musculoskeletal assessment (annually)
```

**Physical Labor:**
```
Required Screenings:
- Musculoskeletal assessment (annually)
- Pulmonary function test (annually for dust-exposed environments)
```

**Shift Work:**
```
Required Screenings:
- Sleep quality assessment (every 6 months)
- Mental health screening (annually)
```

**Noise-Exposed Work:**
```
Required Screenings:
- Hearing test (annually)
```

**Dust/Chemical-Exposed Work:**
```
Required Screenings:
- Pulmonary function test (annually)
- Dermatological screening (annually)
```

### Step 5: Correlation Analysis

#### Sleep-Occupational Health Correlation
- Correlation between shift work and sleep quality
- Relationship between sleep deprivation and work-related symptoms

#### Exercise-Occupational Health Correlation
- Relationship between sedentary work and physical activity levels
- Relationship between exercise and musculoskeletal symptoms

#### Mental Health-Occupational Health Correlation
- Relationship between work stress and mental state
- Association between occupational health issues and psychological symptoms

### Step 6: Report Generation

Output includes:
- Occupational health status summary
- Risk assessment results and trends
- Work-related issue analysis
- Ergonomic assessment results
- Occupational disease screening recommendations
- Correlation analysis with other health factors
- Alert information (if applicable)
- Personalized recommendations and action plan

## Output Format

### Occupational Health Analysis Report Structure

```markdown
# Occupational Health Analysis Report

**Report Date**: YYYY-MM-DD
**Analysis Period**: YYYY-MM-DD to YYYY-MM-DD
**Data Completeness**: Good

WARNING: This report is for reference only and does not constitute an occupational disease diagnosis.

---

## 1. Occupational Health Status Summary

[Overall Rating: Excellent/Good/Fair/Needs Improvement/High Risk]
- Composite Risk Level: [Low/Medium/High]
- Occupational Health Score: X/100
- Ergonomic Score: X/100
- Active Issues: X
- Overall Trend: Improving/Stable/Deteriorating

## 2. Risk Assessment Results

### Sedentary Risk Assessment
**Risk Level**: Low Risk | Medium Risk | High Risk
**Risk Score**: X/40

**Recommendations**: [Specific recommendations]

### VDT Risk Assessment
**Risk Level**: Low Risk | Medium Risk | High Risk
**Risk Score**: X/40

**Recommendations**: [Specific recommendations]

## 3. Work-Related Issue Analysis

### Currently Active Issues
- [Issue 1]: Severity, frequency, duration
- [Issue 2]: Severity, frequency, duration

### Symptom Trends
- Improving issues
- Stable issues
- Worsening issues (WARNING)

## 4. Ergonomic Assessment

**Ergonomic Score**: X/100
**Rating**: Excellent/Good/Fair/Poor/Very Poor

### Improvement Recommendations
- High priority recommendations
- Medium priority recommendations
- Low priority recommendations

## 5. Occupational Disease Screening

### Recommended Screenings
- [Screening Item 1] - Recommended timing
- [Screening Item 2] - Recommended timing

## 6. Comprehensive Recommendations

### Immediate Actions
- [Action item]

### Weekly Action Plan
- [Action item 1]
- [Action item 2]

### Preventive Measures
- [Preventive measures list]

---

**Report Generated**: YYYY-MM-DD HH:MM:SS
DISCLAIMER: This report is for reference only and does not constitute an occupational disease diagnosis or treatment recommendation.
```

## Error Handling

### Data File Not Found
```
Error: Occupational health data file not found.
Suggestion: Please use the /work assess command to create data first.
```

### Insufficient Data
```
Warning: Insufficient data for trend analysis.
Suggestion: At least 3 assessment records are required.
```

### High-Risk Alert
```
HIGH OCCUPATIONAL DISEASE RISK WARNING

The following high-risk factors have been detected:
- [List of high-risk factors]

Recommended Actions:
1. Seek immediate medical attention for occupational disease evaluation
2. Consult an occupational medicine specialist
3. Consider work adjustments
```

## Data Sources

**Primary Data Source:**
- `data-example/occupational-health-tracker.json` - Main occupational health data

**Associated Data Sources:**
- `data-example/sleep-tracker.json` - Sleep data
- `data-example/fitness-tracker.json` - Exercise data
- `data-example/mental-health-tracker.json` - Mental health data
