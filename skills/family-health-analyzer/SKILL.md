---
name: family-health-analyzer
description: "Analyzes family medical history, assesses hereditary risk, identifies family health patterns, and provides personalized prevention recommendations. Generates visual reports including family tree diagrams, genetic risk heat maps, and disease distribution charts. Use when the user wants a family health report, hereditary risk assessment, or family disease pattern analysis."
version: 1.0.0
user-invocable: true
argument-hint: "[report | risk | history | trends]"
allowed-tools: Read, Write, Grep, Glob, Edit
metadata: {"openclaw":{"emoji":"👨‍👩‍👧‍👦","category":"health-analyzer"}}
---

# Family Health Analyzer Skill

## Skill Overview

This skill provides in-depth analysis of family health data, including:
- Hereditary risk assessment
- Family disease pattern recognition
- Shared family health issue analysis
- Personalized prevention recommendations
- Visual report generation

## Trigger Conditions

Use this skill when the user requests:
- "Family health report"
- "Family medical history analysis"
- "Hereditary risk assessment"
- "Family health trends"
- Running the `/family report` command
- Running the `/family risk` command

## Analysis Steps

### Step 1: Determine Analysis Objective

Identify the user's request type:
- Family medical history analysis
- Hereditary risk assessment
- Family health trends
- Family health report

### Step 2: Read Family Data

**Data Sources:**
1. Main data file: `data/family-health-tracker.json`
2. Integrated module data:
   - `data/hypertension-tracker.json`
   - `data/diabetes-tracker.json`
   - `data/profile.json`

### Step 3: Data Validation & Cleaning

**Validation Items:**
- Relationship completeness
- Age plausibility
- Data consistency

### Step 4: Genetic Pattern Recognition

**Recognition Algorithm:**
1. Family clustering analysis
2. Genetic pattern identification
3. Early-onset case identification (typically < 50 years of age)

### Step 5: Risk Calculation Algorithm

**Weighted Calculation:**
```python
genetic_risk_score = (first_degree_relative_cases * 0.4) +
                     (early_onset_cases * 0.3) +
                     (family_clustering_degree * 0.3)

Risk levels:
- High risk: >= 70%
- Moderate risk: 40%-69%
- Low risk: < 40%
```

### Step 6: Generate Prevention Recommendations

**Recommendation Categories:**
- Screening recommendations: Regular checkup items
- Lifestyle recommendations: Diet, exercise, daily routine
- Medical recommendations: When to seek care, specialist consultations

**Example:**
```json
{
  "category": "screening",
  "action": "Regular blood pressure monitoring",
  "frequency": "3 times per week",
  "start_age": 35,
  "priority": "high"
}
```

### Step 7: Generate Visual Report

**HTML Report Components:**
1. Family tree (ECharts tree diagram)
2. Genetic risk heat map
3. Disease distribution pie chart
4. Prevention recommendation timeline

### Step 8: Output Results

**Output Formats:**
1. Text report (concise version): Command line output
2. HTML report (full version): Visual charts

## Safety Principles

### Medical Safety Boundaries
- Performs only statistical analysis based on family medical history
- Provides prevention recommendations and screening reminders
- Clearly labels uncertainties
- Does not diagnose genetic diseases
- Does not predict individual disease probability
- Does not recommend specific treatment plans

### Disclaimer
Every analysis output must include:
```
Disclaimer:
1. This analysis is based on family medical history statistics and is for reference only
2. Hereditary risk assessment does not predict individual disease occurrence
3. All medical decisions should be made in consultation with a qualified physician
4. For genetic counseling, consult a certified genetic counselor
```

## Integration with Existing Modules

- Reads hypertension management data
- Reads diabetes management data
- Correlates medication records
