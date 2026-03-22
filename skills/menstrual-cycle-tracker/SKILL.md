---
name: menstrual-cycle-tracker
description: "Tracks menstrual cycles, predicts ovulation and next period, logs symptoms and flow, and provides PMS management suggestions. Use when the user logs period data, asks about cycle predictions, or wants menstrual health insights."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🌙","category":"health"}}
---

# Menstrual Cycle Tracker

## Capabilities

### 1. Cycle Data Recording

Record and store the following fields for each cycle entry:

| Field | Description | Values/Format |
|-------|-------------|---------------|
| `period_start_date` | First day of menstrual bleeding | YYYY-MM-DD |
| `period_end_date` | Last day of menstrual bleeding | YYYY-MM-DD |
| `flow_level` | Intensity of menstrual flow | spotting / light / medium / heavy / very_heavy |
| `symptoms` | Physical and emotional symptoms | Free text or predefined list |
| `mood` | Emotional state | Free text or scale (1-5) |
| `temperature` | Basal body temperature (BBT) | Decimal in °C or °F, taken at rest before rising |
| `cervical_mucus` | Cervical mucus consistency | dry / sticky / creamy / egg-white / watery |
| `notes` | Additional observations | Free text |

Each daily entry should capture as many fields as the user provides. Missing fields are acceptable and should not block logging.

### 2. Cycle Length Analysis

- **Cycle length calculation**: Count from the first day of one period (period_start_date) to the first day of the next period (exclusive). This is the standard clinical definition.
- **Average cycle length**: Compute the mean cycle length over the last 6-12 recorded cycles. If fewer than 6 cycles exist, use all available data and note the limited sample size.
- **Cycle regularity assessment**:
  - **Regular**: Standard deviation (SD) of cycle lengths < 4 days
  - **Somewhat irregular**: SD between 4 and 6 days
  - **Irregular**: SD >= 7 days
- **Normal range**: 21-35 days is considered clinically normal (average is 28 days). Flag cycles outside this range.

### 3. Ovulation Prediction

- **Calendar method**: Estimated ovulation day = cycle_length - 14 days (based on a typical 14-day luteal phase). For a 28-day cycle, ovulation is estimated around Day 14.
- **Fertile window**: Spans from 5 days before estimated ovulation through 1 day after (total of ~6 fertile days). This accounts for sperm viability (up to 5 days) and egg viability (~12-24 hours).
- **BBT confirmation**: A sustained rise of 0.2-0.5°C (0.4-1.0°F) in basal body temperature indicates ovulation has occurred. The temperature shift should persist for at least 3 consecutive days to confirm ovulation.
- **Cervical mucus patterns**: Track progression through the cycle:
  - Post-menstrual: **Dry** (low fertility)
  - Early follicular: **Sticky** (low fertility)
  - Pre-ovulatory: **Creamy** (moderate fertility)
  - Peak fertility: **Egg-white** — clear, stretchy, slippery (high fertility)
  - Post-ovulatory: **Dry/Sticky** (low fertility)

### 4. Phase Identification

Identify the current cycle phase based on cycle day and average cycle length:

| Phase | Typical Days (28-day cycle) | Key Characteristics |
|-------|----------------------------|---------------------|
| Menstrual | Days 1-5 | Active bleeding; shedding of uterine lining |
| Follicular | Days 1-13 | Estrogen rising; follicle development; energy increasing |
| Ovulation | Day ~14 | LH surge triggers egg release; peak fertility; possible mittelschmerz |
| Luteal | Days 15-28 | Progesterone dominant; uterine lining thickens; PMS symptoms may appear |

Adjust phase day ranges proportionally for cycles shorter or longer than 28 days. The luteal phase is relatively constant (~14 days), so variations primarily affect the follicular phase length.

### 5. PMS Management

Provide evidence-based suggestions for common premenstrual symptoms:

| Symptom | Suggestions |
|---------|-------------|
| **Cramps (dysmenorrhea)** | Heat therapy (heating pad on lower abdomen), NSAIDs (ibuprofen, naproxen — take with food), magnesium supplementation (200-400mg/day), gentle exercise, ginger tea |
| **Bloating** | Reduce sodium intake, increase water consumption (counterintuitive but effective), limit carbonated beverages, eat potassium-rich foods (bananas, avocados), light physical activity |
| **Mood changes** | Regular aerobic exercise (30 min/day), omega-3 fatty acids (fish oil), vitamin B6 (50-100mg/day), mindfulness/meditation, maintain consistent sleep schedule |
| **Fatigue** | Iron-rich foods (spinach, red meat, lentils), adequate sleep (7-9 hours), moderate exercise, vitamin D check, stay hydrated |
| **Breast tenderness** | Reduce caffeine intake, wear supportive bra, evening primrose oil, vitamin E (400 IU/day), cold compresses |
| **Headaches** | Stay hydrated, magnesium supplementation, consistent meal timing, reduce alcohol, cold compress on forehead/neck |
| **Acne** | Gentle cleansing routine, avoid touching face, zinc supplementation, reduce dairy and high-glycemic foods |
| **Food cravings** | Eat complex carbohydrates, chromium supplementation, frequent small meals, ensure adequate protein intake |

Always note that persistent or severe symptoms warrant medical consultation.

### 6. Cycle Health Score (0-100)

Calculate a composite health score with the following weighted components:

| Component | Weight | Scoring Criteria |
|-----------|--------|-----------------|
| **Regularity** | 40% | 100 = SD < 2 days; 75 = SD 2-4 days; 50 = SD 4-6 days; 25 = SD 6-8 days; 0 = SD > 8 days |
| **Flow Normal** | 20% | 100 = medium flow, 3-7 day duration; deduct points for very heavy, very light, too short (<2 days), or too long (>7 days) |
| **Symptom Severity** | 20% | 100 = no/mild symptoms; 75 = moderate; 50 = significant; 25 = severe; 0 = debilitating |
| **Luteal Length** | 20% | 100 = 12-14 days; 75 = 10-11 days; 50 = 8-9 days; 25 = <8 days or >16 days |

Present the overall score along with individual component breakdowns. Provide context: 80-100 = Excellent, 60-79 = Good, 40-59 = Fair (consider consulting a provider), <40 = Needs attention (recommend medical evaluation).

### 7. Pattern Detection

Actively monitor for and flag the following patterns across recorded cycles:

- **Irregular cycles**: Cycle length varying by more than 7 days between cycles
- **Missed periods**: No recorded period start within expected window + 7 days
- **Shortened cycles**: Progressive decrease in cycle length over 3+ cycles
- **Lengthened cycles**: Progressive increase in cycle length over 3+ cycles
- **Worsening PMS trends**: Increasing symptom severity or duration over 3+ cycles
- **Heavy bleeding alerts**: Flow rated "very_heavy" for 3+ consecutive days, or "heavy" for 5+ days
- **Cycle length trends**: Compute and display trend direction (stable, shortening, lengthening) over the last 6-12 cycles using simple linear regression or moving average comparison
- **Spotting between periods**: Mid-cycle spotting logged outside the menstrual phase

When a pattern is detected, explain what it may indicate and whether medical consultation is advisable.

### 8. Fertility Awareness (Informational Only)

- **Fertile vs. non-fertile days**: Identify days based on the calendar method combined with BBT and cervical mucus data when available. Mark days as: high fertility, moderate fertility, or low fertility.
- **BBT charting support**: Plot or tabulate daily BBT readings to help identify the thermal shift indicating ovulation. Flag the coverline (the line drawn 0.1°C above the highest of the last 6 pre-ovulation temps).
- **Sympto-thermal method overview**: When both BBT and cervical mucus data are available, cross-reference them to provide a more accurate fertility assessment.

**Critical disclaimer**: Fertility awareness data provided by this tool is for **informational and educational purposes only**. It is **NOT a reliable method of contraception** and should **NOT** be used as the sole method for pregnancy prevention. Consult a healthcare provider for contraceptive guidance.

## Output Format

### Cycle Log Entry
When recording a daily entry, confirm with a structured summary:

```
## Cycle Log — [DATE]
- **Cycle Day**: [N] (Phase: [phase name])
- **Flow**: [level]
- **Symptoms**: [list]
- **Mood**: [description/rating]
- **BBT**: [temp]°C/°F
- **Cervical Mucus**: [type]
- **Fertility Estimate**: [high/moderate/low]
- **Notes**: [user notes]
```

### Monthly Summary
At the end of a cycle or on request, provide:

```
## Cycle Summary — [Start Date] to [End Date]
- **Cycle Length**: [N] days
- **Period Duration**: [N] days
- **Average Flow**: [level]
- **Estimated Ovulation**: Day [N] ([date])
- **Luteal Phase Length**: [N] days
- **Health Score**: [score]/100
- **Key Symptoms**: [most reported symptoms]
- **Patterns Noted**: [any detected patterns or "None"]
- **Next Period Prediction**: ~[date] (±[N] days)
```

### Prediction Output
When predicting upcoming events:

```
## Cycle Predictions
- **Next Period**: ~[date] (based on [N]-day average cycle)
- **Next Fertile Window**: [start date] to [end date]
- **Next Estimated Ovulation**: ~[date]
- **Current Phase**: [phase] (Day [N])
- **Confidence**: [high/moderate/low] (based on [N] cycles of data)
```

## Data Persistence

### Daily Log Files
Store daily entries as individual files:
- **Path**: `daily/[YYYY-MM-DD].md`
- Each file contains that day's complete log entry in the format above.

### Consolidated Cycle File
Maintain a master tracking file:
- **Path**: `items/menstrual-cycle.md`
- Contains:
  - **Cycle history table**: Start date, end date, cycle length, period duration, ovulation day, health score
  - **Running averages**: Average cycle length, average period duration, average luteal phase
  - **Active alerts**: Any currently flagged patterns
  - **Last updated timestamp**

Update the consolidated file whenever a new entry is logged or a cycle is completed.

## Alerts and Safety

### Medical Disclaimer
This tool is for **personal health tracking and informational purposes only**. It does **not** provide medical diagnoses, treatment recommendations, or clinical advice. All suggestions are general wellness information based on published medical literature and are not a substitute for professional medical care.

### Not a Contraceptive Method
Cycle tracking and fertility awareness data provided by this tool are **NOT reliable for contraception**. The calendar method, BBT, and cervical mucus observations have significant failure rates when used alone or in combination. Always consult a healthcare provider for family planning decisions.

### Not for Diagnosing Conditions
This tool **cannot diagnose** gynecological or endocrine conditions, including but not limited to:
- Polycystic ovary syndrome (PCOS)
- Endometriosis
- Thyroid disorders
- Premature ovarian insufficiency
- Uterine fibroids

Detected patterns are observational only and are meant to prompt further evaluation by a qualified medical professional.

### Seek Medical Attention If
Flag and strongly recommend medical consultation if any of the following are detected or reported:

- **Cycle length consistently < 21 days or > 35 days**
- **Menstrual bleeding lasting more than 7 days**
- **Soaking through a pad or tampon every hour** for 2+ consecutive hours
- **Severe pelvic pain** that interferes with daily activities or is not relieved by OTC pain medication
- **Missed periods** (3+ consecutive months) when not pregnant
- **Sudden change in cycle pattern** after previously regular cycles
- **Intermenstrual bleeding** (bleeding between periods) that is new or persistent
- **Postmenopausal bleeding** (any bleeding after 12 months without a period)
- **Symptoms of anemia**: dizziness, shortness of breath, unusual fatigue alongside heavy periods

When any of these conditions are detected, display a prominent alert and recommend scheduling an appointment with a gynecologist or primary care provider.
