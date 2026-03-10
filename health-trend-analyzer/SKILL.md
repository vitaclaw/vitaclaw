---
name: health-trend-analyzer
description: "Analyzes health data trends and patterns over time. Correlates medications, symptoms, vital signs, lab results, and other health metrics. Identifies concerning trends, improvements, and provides data-driven insights with interactive HTML visualization reports (ECharts). Use when the user asks about health trends, patterns, changes over time, or 'how has my health changed?'"
version: 1.0.0
user-invocable: true
argument-hint: "[general | symptoms | weight | medication | labs | mood-sleep]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📈","category":"health-analyzer"}}
---

# Health Trend Analyzer

Analyzes health data trends and patterns over time, identifies changes, correlations, and provides data-driven health insights.

## Core Features

### 1. Multi-Dimensional Trend Analysis
- **Weight/BMI Trends**: Tracks weight and BMI changes over time, evaluates health trends
- **Symptom Patterns**: Identifies recurring symptoms, frequency changes, potential triggers
- **Medication Adherence**: Analyzes medication compliance patterns, identifies missed-dose patterns and areas for improvement
- **Lab Result Trends**: Tracks biochemical marker changes (cholesterol, blood glucose, blood pressure, etc.)
- **Mood & Sleep**: Correlates mood states with sleep quality, identifies mental health trends

### 2. Correlation Analysis Engine
- **Medication-Symptom Correlation**: Identifies whether new medications are associated with symptom changes
- **Lifestyle Impact**: Correlates diet/sleep with symptoms and mood
- **Treatment Effectiveness Assessment**: Measures whether treatments lead to improvement
- **Cycle-Symptom Correlation**: Cycle-related correlations in women's health tracking

### 3. Change Detection
- **Significant Changes**: Alerts on rapid weight changes, new symptoms, medication changes
- **Deterioration Patterns**: Early identification of declining health conditions
- **Improvement Recognition**: Highlights positive health changes
- **Threshold Alerts**: Warnings when approaching dangerous levels (radiation, extreme BMI)

### 4. Predictive Insights
- **Risk Assessment**: Identifies risk factors based on trends
- **Prevention Recommendations**: Suggests preventive measures based on patterns
- **Early Warning**: Predicts problems before they become serious

## Usage Instructions

### Trigger Conditions

Use this skill when the user mentions the following scenarios:

**General Inquiries**:
- "How has my health changed over the past period?"
- "Analyze my health trends"
- "What changes have there been in my physical condition?"
- "Health status summary"

**Specific Dimensions**:
- "What are my weight/BMI trends?"
- "Analyze my symptom patterns"
- "How is my medication adherence?"
- "What changes are there in my lab results?"
- "My mood and sleep trends"

**Correlation Analysis**:
- "What are my symptoms correlated with?"
- "Is my medication effective?"
- "What is the relationship between sleep and my mood?"

**Time Range**:
- Default analysis covers the **past 3 months** of data
- Supports: "past 1 month", "past 6 months", "past 1 year"
- Supports: "January 2025 to present", "last 90 days"

### Execution Steps

#### Step 1: Determine Analysis Time Range

Extract the time range from user input, or use the default (3 months).

#### Step 2: Read Health Data

Read the following data sources:

```javascript
// 1. Personal profile (BMI, weight)
const profile = readFile('data/profile.json');

// 2. Symptom records
const symptomFiles = glob('data/symptoms/**/*.json');
const symptoms = readAllJson(symptomFiles);

// 3. Mood records
const moodFiles = glob('data/mood/**/*.json');
const moods = readAllJson(moodFiles);

// 4. Diet records
const dietFiles = glob('data/diet/**/*.json');
const diets = readAllJson(dietFiles);

// 5. Medication logs
const medicationLogs = glob('data/medication-logs/**/*.json');

// 6. Women's health data (if applicable)
const cycleData = readFile('data/cycle-tracker.json');
const pregnancyData = readFile('data/pregnancy-tracker.json');
const menopauseData = readFile('data/menopause-tracker.json');

// 7. Allergy history
const allergies = readFile('data/allergies.json');

// 8. Radiation records
const radiation = readFile('data/radiation-records.json');
```

#### Step 3: Data Filtering

Filter data by time range:

```javascript
function filterByDate(data, startDate, endDate) {
  return data.filter(item => {
    const itemDate = new Date(item.date || item.created_at);
    return itemDate >= startDate && itemDate <= endDate;
  });
}
```

#### Step 4: Trend Analysis

Perform trend analysis for each data dimension:

**4.1 Weight/BMI Trend**
- Extract historical weight data
- Calculate BMI changes
- Identify trend direction (rising/falling/stable)
- Evaluate magnitude of change

**4.2 Symptom Patterns**
- Count symptom frequency
- Identify high-frequency symptoms
- Analyze symptom temporal patterns
- Detect symptom triggers

**4.3 Medication Adherence**
- Calculate overall adherence rate
- Analyze adherence for each medication
- Identify missed-dose patterns
- Evaluate improvement recommendations

**4.4 Lab Results**
- Track biochemical markers across multiple reports
- Compare against reference ranges
- Identify improvement/deterioration
- Flag abnormal markers

**4.5 Mood & Sleep**
- Correlate mood scores with sleep duration
- Identify mood fluctuation patterns
- Detect stress levels
- Evaluate mental health trends

#### Step 5: Correlation Analysis

Use statistical methods to identify correlations:

```javascript
// Pearson correlation coefficient
function pearsonCorrelation(x, y) {
  // Calculate correlation coefficient
  // Return value range: -1 (negative correlation) to 1 (positive correlation)
}

// Application scenarios
- Medication start date vs. symptom frequency
- Sleep duration vs. mood score
- Weight change vs. diet records
- Exercise volume vs. mood state
```

#### Step 6: Change Detection

Identify significant changes:

```javascript
// Change point detection
function detectChangePoints(timeSeries) {
  // Use statistical methods to detect significant change points
  // E.g.: sudden weight loss, sudden symptom increase
}

// Threshold alerts
function checkThresholds(value, thresholds) {
  // Check whether values approach or exceed danger thresholds
  // E.g.: BMI > 30, radiation dose > safety limit
}
```

#### Step 7: Generate Insights

Generate predictive insights based on analysis results:

```javascript
// Risk assessment
function assessRisks(trends) {
  // Identify high-risk trends
  // E.g.: rapid weight loss, frequent symptoms
}

// Prevention recommendations
function generateRecommendations(trends, correlations) {
  // Suggest preventive measures based on patterns
  // E.g.: improve sleep, increase medication adherence
}

// Early warnings
function earlyWarnings(trends) {
  // Predict problems before they become serious
  // E.g.: rising symptom frequency, persistent low mood
}
```

#### Step 8: Generate Visualization Report

Generate an interactive HTML report:

1. **Data summary**: Generate analysis results in JSON format
2. **HTML template rendering**: Inject data into HTML template
3. **ECharts chart configuration**: Configure 6 types of interactive charts
4. **Save file**: Save as a standalone HTML file

See [Data Source Documentation](data-sources.md) for detailed output format.

## Output Format

### Text Report (Concise Version)

```
Health Trend Analysis Report
==============================
Generated: 2025-12-31
Analysis Period: Past 3 months (2025-10-01 to 2025-12-31)

Overall Assessment
==============================
Improving: Weight management, cholesterol levels
Stable: Blood glucose control, mood state
Needs Attention: Medication adherence, sleep quality

Weight/BMI Trend
|- Current weight: 68.5 kg
|- Current BMI: 23.1 (normal range)
|- 3-month change: -2.3 kg (-3.2%)
|- Trend: Gradual weight loss
|- Assessment: Positive trend, within healthy range

Medication Adherence
|- Current medications: 3
|- Overall adherence rate: 78%
|- Missed doses: 8
|- Best: Aspirin (95%)
|- Needs improvement: Amlodipine (65%)

Symptom Patterns
|- Most frequent: Headache (12 times in past 3 months)
|- Trend: Frequency decreasing (4 fewer than previous period)
|- Potential trigger: Moderate correlation with sleep quality identified (r=0.62)
|- Recommendation: Continue improving sleep patterns

Lab Result Trends
|- Cholesterol: 240 -> 210 mg/dL (improved)
|- Blood glucose: 5.6 -> 5.4 mmol/L (stable)
|- Last test: 30 days ago
|- Recommendation: Recheck in 3 months

Mood & Sleep
|- Average mood score: 6.8/10
|- Average sleep duration: 6.5 hours
|- Trend: Mood stable, sleep slightly improved
|- Correlation: Sleep duration strongly correlated with mood score (r=0.78)

Correlation Analysis
==============================
- Sleep duration <-> Mood score: Strong positive correlation (r=0.78)
- Weight change <-> Diet records: Moderate correlation (r=0.55)
- Medication adherence <-> Symptom frequency: Moderate negative correlation (r=-0.62)

Risk Assessment & Recommendations
==============================

Keep It Up
- Current weight management approach is effective
- Cholesterol levels show notable improvement

Needs Attention
- Improve amlodipine adherence (set reminders)
- Increase sleep duration to 7-8 hours

Follow-up Schedule
- Recheck lipid panel in 3 months
- Assess medication adherence improvement in 1 month

==============================
Disclaimer:
This analysis is for reference only and does not replace
professional medical diagnosis. Please consult a doctor
for professional advice.
```

### HTML Visualization Report (Full Version)

Generates a standalone HTML file with ECharts interactive charts, including:

1. **Overall assessment cards**: Key metrics at a glance
2. **Weight/BMI trend chart**: Dual Y-axis line chart (weight + BMI)
3. **Symptom frequency chart**: Color-coded bar chart (high-frequency red / moderate yellow / low green)
4. **Medication adherence dashboard**: Overall adherence rate + per-medication details
5. **Lab result trend chart**: Multi-series line chart + reference lines
6. **Correlation heat map**: Heat map showing inter-variable correlations
7. **Mood & sleep area chart**: Dual Y-axis area chart

**HTML File Features**:
- Fully standalone (all dependencies via CDN)
- Interactive charts (zoom, export, legend toggle)
- Responsive design (mobile-friendly)
- Print-ready (print-optimized styles)
- Shareable (can be sent to a physician)

## Data Sources

### Primary Data Sources

| Data Source | File Path | Data Content |
|------------|-----------|-------------|
| Personal profile | `data/profile.json` | Weight, height, BMI history |
| Symptom records | `data/symptoms/**/*.json` | Symptom name, severity, duration |
| Mood records | `data/mood/**/*.json` | Mood score, sleep quality, stress level |
| Diet records | `data/diet/**/*.json` | Meals, foods, calories, nutrients |
| Medication logs | `data/medication-logs/**/*.json` | Medication time, adherence records |
| Lab results | `data/medical_records/**/*.json` | Biochemical markers, reference ranges |

### Supplementary Data Sources

| Data Source | File Path | Data Content |
|------------|-----------|-------------|
| Menstrual cycle | `data/cycle-tracker.json` | Cycle length, symptom records |
| Pregnancy tracking | `data/pregnancy-tracker.json` | Gestational week, weight, exam records |
| Menopause | `data/menopause-tracker.json` | Symptoms, HRT use |
| Allergy history | `data/allergies.json` | Allergens, severity |
| Radiation records | `data/radiation-records.json` | Cumulative radiation dose |

For detailed data structure descriptions, see: [data-sources.md](data-sources.md)

## Analysis Algorithms

### Time Series Analysis
- Trend detection (linear regression)
- Seasonality analysis
- Outlier detection

### Correlation Analysis
- Pearson correlation coefficient (continuous variables)
- Spearman correlation coefficient (ordinal variables)
- Cross-correlation analysis (time series)

### Change Point Detection
- CUSUM algorithm
- Sliding window t-test
- Bayesian change point detection

### Statistical Metrics
- Mean, median, standard deviation
- Percentiles (25%, 50%, 75%)
- Rate of change (period-over-period, year-over-year)

For detailed algorithm descriptions, see: [algorithms.md](algorithms.md)

## Safety & Privacy

### Must Follow

- Do not provide medical diagnoses
- Do not provide specific medication advice
- Do not make survival/prognosis judgments
- Include disclaimer (for reference only)

### Information Accuracy

- Analyze only based on recorded data
- Do not speculate or infer missing information
- Clearly label data sources and time ranges
- Recommendations should be reviewed by a healthcare professional

### Privacy Protection

- All data remains local
- No external API calls
- Analysis results saved locally only
- HTML reports run independently (no data transmission)

## Error Handling

### Missing Data
- **No data**: Output "No data available yet. Please start recording [data type] first."
- **Insufficient data**: Output "Insufficient data (at least 1 month of data is needed for trend analysis)."
- **Narrow data range**: Use available data and note "Consider extending the recording period for more accurate trends."

### Analysis Failure
- **Cannot calculate trend**: Output "Cannot calculate trend; insufficient data points."
- **Correlation analysis failed**: Output "Correlation analysis requires more data."
- **Chart rendering failed**: Fall back to text report.

## Usage Examples

### Example 1: General Health Trends
**User**: "How has my health changed over the past 3 months?"
**Output**: Generates a complete HTML report with trend analysis across all dimensions.

### Example 2: Symptom Analysis
**User**: "Analyze my symptom patterns"
**Output**: Focused analysis of symptom frequency, triggers, and trends.

### Example 3: Weight Trends
**User**: "What are my weight trends?"
**Output**: Focused analysis of weight/BMI changes, correlation with diet/exercise.

### Example 4: Medication Effectiveness
**User**: "Is my blood pressure medication working?"
**Output**: Correlates medication start date with blood pressure readings and symptom improvement.

For more complete examples, see: [examples.md](examples.md)

## Related Commands

- `/symptom`: Record symptoms
- `/mood`: Record mood
- `/diet`: Record diet
- `/medication`: Manage medications and dosing records
- `/query`: Query specific data points

## Technical Implementation

### Tool Limitations

This skill uses only the following tools (no additional permissions required):
- **Read**: Read JSON data files
- **Grep**: Search for specific patterns
- **Glob**: Find data files by pattern
- **Write**: Generate HTML reports (saved to `data/health-reports/`)

### Performance Optimization

- Incremental reading: Only read data files within the specified time range
- Data caching: Avoid re-reading the same file
- Lazy computation: Generate chart data on demand

### Extensibility

- Supports adding new data dimensions
- Supports custom chart types
- Supports custom analysis algorithms
