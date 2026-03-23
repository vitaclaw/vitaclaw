---
name: medication-reminder
description: "Manages medication schedules, tracks adherence (doses taken vs. due), identifies missed dose patterns, and monitors refill timelines. Use when the user logs medications, asks about adherence, or needs a medication schedule."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"💊","category":"health"}}
---

# Medication Reminder

Manage multi-drug records, generate daily medication schedules, calculate adherence rates, identify missed-dose patterns, and track refill timelines.

## Capabilities

### 1. Medication Record Management

**Record fields**:

| Field | Description | Example |
|-------|------------|---------|
| Drug name | Generic or brand name | Amlodipine / Norvasc |
| Dose | Single dose | 5mg |
| Frequency | Frequency code | QD / BID / TID / QID / QW / PRN |
| Timing | Timing code | AC / PC / HS / AM / PM |
| Start date | Start date | 2026-01-15 |
| End date | Stop date (optional) | 2026-06-15 or empty |
| Prescriber | Prescribing physician (optional) | Dr. Zhang |
| Notes | Special instructions | Do not take with grapefruit |

**Frequency codes**:

| Code | Meaning | Daily doses |
|------|---------|-------------|
| QD | Once daily | 1 |
| BID | Twice daily | 2 |
| TID | Three times daily | 3 |
| QID | Four times daily | 4 |
| QW | Once weekly | 1/7 |
| Q2W | Every two weeks | 1/14 |
| QM | Once monthly | 1/30 |
| PRN | As needed | Not included in adherence |

**Timing codes**:

| Code | Meaning | Suggested time |
|------|---------|---------------|
| AC | Before meals | 30 min before meal |
| PC | After meals | 30 min after meal |
| HS | At bedtime | 30 min before sleep |
| AM | Morning | After waking |
| PM | Afternoon | 14:00-16:00 |
| EMPTY | Fasting | 1 hour before breakfast |
| WITH_FOOD | With food | During meal |

**Operations**: Add, discontinue (set end date to today, preserve history), modify (record change history), list current medications.

### 2. Adherence Calculation

**Formula**: Adherence rate = (actual doses taken / doses due) * 100%

**Dimensions**:

| Dimension | Calculation |
|-----------|------------|
| Daily | Today's taken / today's due * 100% |
| Weekly (7-day rolling) | Past 7 days total taken / total due * 100% |
| Monthly (30-day rolling) | Past 30 days total taken / total due * 100% |
| Per-drug | Drug's taken / drug's due * 100% |
| Overall | Weighted average across all drugs |

**Doses due**: Derived from frequency code and active date range. PRN drugs excluded from adherence calculation. Only count doses within the drug's active period.

**Adherence grades**:

| Rate | Grade | Interpretation |
|------|-------|---------------|
| >= 80% | Good | Regular adherence, maintain current pattern |
| 50-79% | Fair | Frequent misses affecting efficacy; analyze causes, set reminders |
| < 50% | Poor | Severe non-adherence; discuss regimen simplification with physician |

**Steps**:
1. Read `memory/health/items/medications.md` for drug list
2. Glob `memory/health/daily/*.md` for the target date range
3. Extract `## Medications` sections from daily files
4. Per drug: count doses due vs. doses taken
5. Output adherence by all dimensions

### 3. Missed Dose Pattern Identification

**Time-of-day pattern**: Compare completion rates across time slots (morning / midday / evening / bedtime). Flag any slot with rate significantly lower than others.

**Day-of-week pattern**: Compare daily completion rates Monday through Sunday. Flag if weekends are notably lower than weekdays.

**Drug-specific pattern**: Compare per-drug adherence. Flag any drug with adherence notably below overall average (by 20%+). Possible causes: side effects, inconvenience, forgetting.

**Steps**:
1. Extract medication time and status from daily records
2. Aggregate by time-of-day / day-of-week / drug
3. Compute completion rates per dimension
4. Flag dimensions significantly below average (20%+ lower)
5. Output pattern descriptions and improvement suggestions

### 4. Daily Schedule Generation

Generate today's medication schedule from the active drug list.

**Time-slot ordering**:
1. EMPTY / AM -- morning fasting (~07:00)
2. AC (breakfast) -- ~07:30
3. PC (breakfast) / WITH_FOOD -- ~08:00
4. AM other -- ~08:30
5. AC (lunch) -- ~11:30
6. PC (lunch) -- ~12:30
7. PM -- ~15:00
8. AC (dinner) -- ~17:30
9. PC (dinner) -- ~18:30
10. HS -- ~21:30

**Multi-dose distribution**: BID = morning + evening; TID = morning + midday + evening; QID = morning + midday + evening + bedtime.

### 5. Common Drug Interaction Alerts

Flag the following known high-risk combinations when a new drug is added:

| Combination | Risk |
|------------|------|
| Warfarin + NSAIDs | Increased bleeding risk |
| ACEIs + Potassium-sparing diuretics | Hyperkalemia risk |
| Statins + Macrolides | Rhabdomyolysis risk |
| Metformin + Iodinated contrast | Lactic acidosis risk |
| Digoxin + Amiodarone | Digoxin toxicity risk |

For comprehensive interaction checking, recommend the user run a dedicated drug-interaction-checker skill or consult a pharmacist.

### 6. Refill Tracking

**Remaining supply**: Remaining days = remaining tablets / daily doses

**Reminders**:
- Remaining <= 7 days: "Running low" reminder
- Remaining <= 3 days: "Urgent refill" reminder
- Remaining = 0: "Out of stock" alert

## Output Format

### Daily Medication Schedule

```markdown
# Daily Medication Schedule

## Date
YYYY-MM-DD (Day of week)

## Today's Plan

### Morning (07:00-08:30)
| Time | Drug | Dose | Requirement | Status |
|------|------|------|-------------|--------|
| 07:00 | Levothyroxine | 50ug | Fasting, 1h before meal | [ ] |
| 07:30 | Metformin | 500mg | With food | [ ] |
| 08:00 | Amlodipine | 5mg | After meal | [ ] |

### Midday (11:30-12:30)
| Time | Drug | Dose | Requirement | Status |
|------|------|------|-------------|--------|

### Evening (17:30-18:30)
| Time | Drug | Dose | Requirement | Status |
|------|------|------|-------------|--------|

### Bedtime (21:30)
| Time | Drug | Dose | Requirement | Status |
|------|------|------|-------------|--------|

## Summary
- Total: N drugs, M doses
- Special notes: [e.g., Levothyroxine must be taken fasting, 1h apart from others]

## Refill Alerts
- [Drug]: N tablets remaining (~N days), refill soon
```

### Adherence Report

```markdown
# Adherence Report

## Period
YYYY-MM-DD to YYYY-MM-DD (N days)

## Overall Adherence
- **Rate: N% (Good/Fair/Poor)**
- Doses due: N
- Doses taken: N
- Doses missed: N

## Per-Drug Adherence

| Drug | Dose | Freq | Due | Taken | Rate | Grade |
|------|------|------|-----|-------|------|-------|

## Missed Dose Patterns

### Time-of-Day Analysis
| Slot | Rate | Assessment |
|------|------|-----------|

### Day-of-Week Analysis
| Sun | Mon | Tue | Wed | Thu | Fri | Sat |
|-----|-----|-----|-----|-----|-----|-----|

### Drug-Specific Analysis
- [Drug with low adherence]: [analysis]

## Improvement Suggestions
1. [specific, actionable suggestion]
```

## Data Persistence

Follow health-memory write protocol:

1. **Update daily file**: Insert/replace section `## Medications [medication-reminder · HH:MM]`
2. **Update items file** (`memory/health/items/medications.md`):
   - Update `## Current Medications` table
   - Update `## Recent Status`: today's adherence, 7-day, 30-day, next refill
   - Prepend row to `## Adherence History` table
   - Trim rows older than 90 days

Items file structure:
```markdown
---
item: medications
unit: n/a
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Medication Records

## Current Medications
| Drug | Dose | Frequency | Timing | Start | End | Notes |
|------|------|-----------|--------|-------|-----|-------|

## Recent Status
- Today's adherence: N% (N/N doses taken)
- 7-day adherence: N%
- 30-day adherence: N%
- Next refill needed: [drug] (N days)

## Adherence History
| Date | Due | Taken | Missed | Rate | Missed Details |
|------|-----|-------|--------|------|----------------|
```

Daily section format:
```markdown
## Medications [medication-reminder · 21:00]
- Taken: Amlodipine 5mg (AM), Metformin 500mg x2 (AM, PM), Valsartan 80mg (HS)
- Missed: Atorvastatin 20mg (PM)
- Today's adherence: 83% (5/6)
- Refill alert: Metformin 6 days remaining
```

## Alerts and Safety

### Safety Rules
- Any medication change (add/stop/adjust dose) must follow physician orders
- Do not double up on missed doses without consulting a physician or pharmacist
- Interaction alerts in this skill are for reference only; consult a pharmacist for comprehensive checks
- Stop medication and seek medical attention immediately if adverse reactions occur

### Consult a Physician/Pharmacist When
- Adherence is persistently below 50%
- Frequently missing the same drug (may indicate side effects)
- Taking 5+ concurrent medications
- Concerned about interactions when adding a new drug
- Experiencing any suspected adverse reactions

### Medical Disclaimer

This skill is for medication recording and reminder reference only. It does not constitute medical advice. It does not prescribe, recommend adding or removing medications, adjust dosages, or replace a pharmacist or physician.
