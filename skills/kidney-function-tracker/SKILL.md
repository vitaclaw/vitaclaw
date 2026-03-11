---
name: kidney-function-tracker
description: "Tracks kidney function using CKD-EPI 2021 (race-free) eGFR formula, stages CKD G1-G5, monitors albuminuria categories A1-A3, and calculates eGFR decline rate. Use when the user provides creatinine or eGFR results or asks about kidney health."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🫘","category":"health"}}
---

# Kidney Function Tracker

Record creatinine, eGFR, and albuminuria indicators. Auto-calculate CKD-EPI eGFR, determine CKD stage, monitor decline rate, and provide follow-up reminders.

## Capabilities

### 1. eGFR Calculation (CKD-EPI 2021, Race-Free)

Calculate eGFR from serum creatinine (Scr), sex, and age.

**Female**:
- Scr <= 0.7 mg/dL: eGFR = 142 * (Scr/0.7)^(-0.241) * 0.9938^age
- Scr > 0.7 mg/dL: eGFR = 142 * (Scr/0.7)^(-1.200) * 0.9938^age

**Male**:
- Scr <= 0.9 mg/dL: eGFR = 142 * (Scr/0.9)^(-0.302) * 0.9938^age
- Scr > 0.9 mg/dL: eGFR = 142 * (Scr/0.9)^(-1.200) * 0.9938^age

**Unit conversion**: Chinese labs report creatinine in umol/L. Convert: Scr (mg/dL) = Scr (umol/L) / 88.4

**Steps**:
1. Get creatinine value from user (umol/L or mg/dL)
2. If umol/L, divide by 88.4 to convert to mg/dL
3. Read sex and date of birth from `memory/health/_health-profile.md` to compute age
4. Apply the sex-appropriate formula
5. Round result to 1 decimal place

**Example**: Male, 52 years, creatinine 95 umol/L
- Scr = 95 / 88.4 = 1.075 mg/dL
- Scr > 0.9, use: eGFR = 142 * (1.075/0.9)^(-1.200) * 0.9938^52
- eGFR = 142 * 0.779 * 0.724 = 80.1 mL/min/1.73m^2

### 2. CKD Staging

| Stage | eGFR (mL/min/1.73m^2) | Description |
|-------|------------------------|-------------|
| G1 | >= 90 | Normal or high |
| G2 | 60-89 | Mildly decreased |
| G3a | 45-59 | Mildly to moderately decreased |
| G3b | 30-44 | Moderately to severely decreased |
| G4 | 15-29 | Severely decreased |
| G5 | < 15 | Kidney failure |

**Stage change detection**: Compare current vs. previous stage. If stage worsens (number increases), trigger "stage progression" alert. Pay special attention to G2->G3a and G3b->G4 transitions.

### 3. Albuminuria Classification

| Category | ACR (mg/g) | Description |
|----------|-----------|-------------|
| A1 | < 30 | Normal to mildly increased |
| A2 | 30-300 | Moderately increased (microalbuminuria) |
| A3 | > 300 | Severely increased (macroalbuminuria) |

Trigger alert on A2->A3 transition indicating worsening kidney damage.

### 4. eGFR Decline Rate

**Formula**: Annual decline rate = (previous eGFR - current eGFR) / time interval in years
- Time interval (years) = days between tests / 365.25

**Decline rate classification**:

| Rate (mL/min/1.73m^2/year) | Grade | Significance |
|-----------------------------|-------|-------------|
| < 1 | Stable | Normal physiological decline |
| 1-3 | Slow decline | Continue monitoring |
| 3-5 | Moderate decline | Intensify management, consider treatment adjustment |
| > 5 | Rapid decline | **Seek immediate medical attention**, active intervention |

**Steps**:
1. Read `memory/health/items/kidney-function.md` `## History` table
2. Extract two most recent eGFR entries
3. Calculate time interval (days / 365.25)
4. Calculate decline rate
5. If >= 3 data points, also compute 6-month and 1-year average decline rates

Require at least 2 eGFR readings >= 3 months apart for meaningful calculation. Single-interval rates may be affected by acute factors (dehydration, medications).

### 5. Monitoring Schedule (by CKD Stage)

| CKD Stage | Frequency | Tests |
|-----------|-----------|-------|
| G1-G2 | Annually | Creatinine, eGFR, urinalysis, ACR |
| G3a | Every 6 months | Creatinine, eGFR, ACR, electrolytes, CBC, PTH |
| G3b-G4 | Quarterly | Creatinine, eGFR, ACR, electrolytes, CBC, PTH, calcium/phosphorus, lipids |
| G5 | Monthly | Full renal panel + dialysis-related markers |

**Follow-up reminder logic**:
1. Read latest CKD stage
2. Find most recent test date in `## History`
3. Calculate next due date based on stage-appropriate frequency
4. If current date > due date: "Overdue" reminder
5. If <= 14 days to due date: "Upcoming" reminder

## Output Format

### Kidney Function Assessment Report

```markdown
# Kidney Function Assessment Report

## Date
YYYY-MM-DD

## Current Indicators

| Indicator | Value | Reference | Status |
|-----------|-------|-----------|--------|
| Serum Creatinine | 95 umol/L (1.07 mg/dL) | 57-111 umol/L (male) | Normal |
| eGFR (CKD-EPI 2021) | 80.1 mL/min/1.73m^2 | >= 90 | Mildly decreased |
| ACR | 45 mg/g | < 30 | Moderately increased (A2) |

## CKD Stage
- **Current: G2 (Mildly decreased)**
- Previous: G2 (YYYY-MM-DD)
- Change: None

## Albuminuria Classification
- **Current: A2 (Moderately increased)**
- Previous: A1 (YYYY-MM-DD)
- **Change: A1 -> A2 (new microalbuminuria)**

## eGFR Decline Analysis

| Period | Start eGFR | End eGFR | Rate |
|--------|-----------|----------|------|
| Last interval | X | Y | Z mL/min/year |
| Last 6 months | X | Y | Z mL/min/year |
| Last 1 year | X | Y | Z mL/min/year |

## eGFR Trend

| Date | Scr (umol/L) | eGFR | Stage | ACR (mg/g) | Alb Category |
|------|-------------|------|-------|-----------|-------------|

## Alerts
1. [Priority] [Description]

## Monitoring Plan
- Current stage recommendation
- Adjusted recommendation if decline is rapid
- Next suggested test date
- Suggested test items
```

## Data Persistence

Follow health-memory write protocol:

1. **Update daily file**: Insert/replace section `## Kidney Function [kidney-function-tracker · HH:MM]`
2. **Update items file** (`memory/health/items/kidney-function.md`):
   - Update `## Recent Status`: latest creatinine, eGFR, CKD stage, ACR, decline rate
   - Prepend row to `## History` table
   - Trim rows older than 90 days

History table columns:
```
| Date | Scr (umol/L) | Scr (mg/dL) | eGFR | CKD Stage | ACR (mg/g) | Alb Category | Decline Rate | Notes |
```

Daily section format:
```markdown
## Kidney Function [kidney-function-tracker · 10:00]
- Creatinine: 95 umol/L (1.07 mg/dL)
- eGFR (CKD-EPI 2021): 80.1 mL/min/1.73m^2
- CKD Stage: G2, Albuminuria: A2 (ACR 45 mg/g)
- Decline Rate: -8.4 mL/min/year (rapid)
- Alert: Rapid eGFR decline, new microalbuminuria
```

## Alerts and Safety

### Alert Thresholds (by priority)

**Emergency (seek immediate care)**:
- eGFR < 15 (kidney failure)
- eGFR single drop > 25% (possible acute kidney injury)
- ACR > 300 and rapidly rising

**Important**:
- CKD stage progression (e.g., G2 -> G3a)
- Annual decline rate > 5 mL/min/1.73m^2
- ACR category A2 -> A3
- eGFR < 30 (recommend nephrology referral)

**Attention**:
- Annual decline rate 3-5 mL/min/1.73m^2
- ACR category A1 -> A2
- Creatinine rising for 3 consecutive readings
- Follow-up overdue

### Medical Disclaimer

This skill is for health monitoring reference only. It does not constitute medical diagnosis or treatment advice. It does not confirm CKD diagnosis (requires comprehensive clinical judgment), formulate treatment plans, evaluate dialysis regimens, or replace nephrologist consultations.
