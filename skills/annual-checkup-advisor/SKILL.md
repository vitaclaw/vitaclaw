---
name: annual-checkup-advisor
description: "Orchestrates comprehensive annual checkup interpretation by coordinating report parsing, lab interpretation, family history analysis, genetic risk scoring, TCM constitution assessment, and guideline lookup. Use when the user uploads a checkup report or asks for help interpreting physical examination results."
version: 1.0.0
user-invocable: true
argument-hint: "[checkup report text or PDF path]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🩺","category":"health-scenario"}}
---

# Annual Checkup Advisor

Comprehensive annual checkup interpretation skill for individuals who have received a physical examination report and want a deep, multi-dimensional health analysis. Coordinates report parsing, lab interpretation, year-over-year comparison, family history risk stratification, polygenic risk scoring, nutrigenomic advice, TCM constitution assessment, and clinical guideline lookup to produce a structured 7-chapter health report.

## Skill Chain

| Step | Skill | Purpose | Trigger |
|------|-------|---------|---------|
| 1 | checkup-report-interpreter | Parse checkup report into structured indicators with severity grading | Always |
| 2 | lab-results | Deep clinical interpretation of abnormal indicators + year-over-year comparison | Always |
| 3 | patiently-ai | Translate professional interpretations into patient-friendly language | Always |
| 4 | family-health-analyzer | Hereditary risk stratification based on family history + abnormal indicators | Always |
| 5 | gwas-prs | Polygenic risk score (PRS) for common diseases | When genetic data is provided |
| 6 | nutrigx_advisor | Gene-nutrition personalized advice (MTHFR, VDR, CYP1A2, etc.) | When genetic data is provided |
| 7 | tcm-constitution-analyzer | TCM constitution identification and lifestyle recommendations | Always |
| 8 | tooluniverse-clinical-guidelines | Guideline-level recommendations for abnormal indicators | Always |
| 9 | deep-research | PubMed literature deep-dive for concerning abnormalities | When urgent/important abnormalities exist and user requests |

## Workflow

### Full Interpretation (default mode)

- [ ] Step 1: Parse checkup report (PDF or text) via `checkup-report-interpreter`. Extract 40+ indicators, structure as JSON, grade each indicator: urgent (red) / important (orange) / minor (yellow) / normal (green). If prior-year reports are provided, parse those as well.
- [ ] Step 2: Deep-interpret abnormal indicators via `lab-results`. If prior-year data exists, calculate year-over-year change magnitude and direction. Flag indicators worsening for 2+ consecutive years. Identify new abnormalities and improvements.
- [ ] Step 3: Translate all professional interpretations into patient-friendly plain language via `patiently-ai`. Use everyday analogies for medical terminology.
- [ ] Step 4: Stratify hereditary risk via `family-health-analyzer`. Input family history + abnormal indicators from Step 1. Identify familial clustering diseases (cardiovascular, diabetes, cancer, etc.). Assign risk levels (high/medium/low). Generate targeted screening recommendations.
- [ ] Step 5 (optional): If genetic data is provided, calculate polygenic risk scores via `gwas-prs` covering T2D, CAD, breast cancer, prostate cancer, Alzheimer's, and diseases related to abnormal indicators. Integrate with family history risk from Step 4.
- [ ] Step 6 (optional): If genetic data is provided, analyze nutrigenomic profile via `nutrigx_advisor` covering folate metabolism (MTHFR), vitamin D metabolism (VDR/CYP2R1), lactose tolerance (MCM6/LCT), alcohol metabolism (ADH1B/ALDH2), and caffeine metabolism (CYP1A2). Generate gene-guided supplement recommendations.
- [ ] Step 7: Perform TCM constitution identification via `tcm-constitution-analyzer` based on checkup indicators + self-reported symptoms. Classify into one of nine constitution types (balanced, qi-deficient, yang-deficient, yin-deficient, phlegm-dampness, damp-heat, blood-stasis, qi-stagnation, special). Generate lifestyle recommendations (diet, exercise, sleep, emotional wellness).
- [ ] Step 8: Query clinical guidelines via `tooluniverse-clinical-guidelines` for abnormal indicators from Step 2. Match guideline-level management recommendations (observe / recheck / refer / intervene). Cite guideline sources (AHA, ADA, NCCN, etc.).
- [ ] Step 9 (optional): If urgent/important abnormalities exist and user requests deeper analysis, conduct PubMed literature deep-dive via `deep-research`. Retrieve latest research, prognosis data, and intervention evidence. Generate literature summary with evidence-level assessment.

## Input Format

| Input | Required | Description |
|-------|----------|-------------|
| Checkup report | Yes | Annual physical examination report (text or PDF) |
| Prior-year reports | No | One or more previous year reports for year-over-year comparison |
| Family medical history | Yes | First-degree relative disease information (parents, siblings, children) |
| Genetic test data | No | Genotyping chip or whole-genome sequencing results |

## Output Format

### Annual Health Deep Report (7 chapters)

```
# Annual Health Deep Report

## 1. Results Overview
Red/yellow/green traffic-light table for all indicators.

### Red (Urgent Attention Required)
| Indicator | Value | Reference Range | Severity | Summary |

### Yellow (Monitor Closely)
| Indicator | Value | Reference Range | Severity | Summary |

### Green (Normal)
Count of normal indicators (no item-by-item listing needed).

## 2. Indicator-by-Indicator Interpretation
### 2.1 [Indicator Name]
- Value: xxx (reference range: xxx)
- Status: elevated / low / normal
- Plain-language explanation
- Clinical significance
- Recommendation: recheck / visit specialist / lifestyle adjustment

(Repeat for each abnormal indicator)

## 3. Year-over-Year Trend Comparison
### Trend Overview
| Indicator | Last Year | This Year | Change | Trend |
(If no prior data: "No historical data available. Keep this report for future comparison.")

### Concerning Trends
- Persistently worsening indicators (2+ consecutive years)
- Newly abnormal indicators
- Improved indicators

## 4. Genetic Risk Profile
### 4.1 Family History Risk Stratification
| Disease | Family History | Risk Level | Recommended Screening |

### 4.2 Polygenic Risk Scores (if genetic data available)
| Disease | PRS Percentile | Risk Level | Notes |

### 4.3 Nutrigenomic Recommendations (if genetic data available)
- Genotype-related metabolic characteristics
- Personalized supplement recommendations
(If no genetic data: "No genetic data available. Consider consumer-grade genetic testing for more precise risk assessment.")

## 5. TCM Constitution and Lifestyle Recommendations
### Constitution Assessment
- Primary constitution: xxx type
- Secondary constitution: xxx type (if applicable)

### Lifestyle Recommendations
- Diet (foods to favor / avoid)
- Exercise recommendations
- Sleep schedule adjustments
- Emotional wellness practices

## 6. Action Plan
### Items Requiring Recheck
| Item | Reason | Recommended Timeline | Department |

### Items Requiring Specialist Visit
| Item | Reason | Urgency | Department |

### Lifestyle Adjustments
- Prioritized actionable recommendations with specific methods

## 7. Next Checkup Focus Areas
- Additional tests recommended for next checkup based on current abnormalities and risk profile
- Recommended recheck intervals
- Indicators requiring ongoing monitoring
```

## Alert Rules

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Urgent indicator detected | Any red-graded indicator | Recommend prompt specialist visit |
| Persistent worsening | Same indicator worsening 2+ consecutive years | Flag as concerning trend, recommend intervention |
| High genetic risk | PRS >= 90th percentile for any disease | Highlight in report, recommend targeted screening |
| Multiple abnormalities | 5+ abnormal indicators across different systems | Recommend comprehensive follow-up |

## Data Persistence

This skill does not directly invoke `health-memory`. If the user wishes to save checkup results for long-term tracking, recommend entering key indicators into `health-memory` item files (e.g., `memory/health/items/blood-lipids.md`).

## Medical Disclaimer

This report is for health reference only and does not constitute medical diagnosis or treatment advice. All urgent (red) indicators should be evaluated by a physician promptly. Genetic risk assessments are based on statistical models and do not represent definitive diagnoses. PRS scores are influenced by population baselines and are for reference only. TCM constitution assessment is a supplementary reference and does not replace clinical examination. If experiencing any symptoms, seek medical attention immediately rather than waiting for the next checkup.
