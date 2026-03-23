---
name: hormone-health-tracker
description: "Tracks hormone lab results over time, analyzes trends for thyroid, sex hormones, cortisol, and metabolic markers, and provides lifestyle optimization suggestions. Use when the user logs hormone test results, asks about hormonal health, or wants to understand hormone trends."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"⚖️","category":"health"}}
---

# Hormone Health Tracker

A comprehensive tool for recording hormone lab results, tracking trends over time, correlating symptoms, and providing evidence-based lifestyle optimization suggestions.

**Important:** This tool is for informational and tracking purposes only. It does not replace professional medical advice. Always consult an endocrinologist or qualified healthcare provider before making changes to medications or treatment plans.

---

## Capabilities

### 1. Hormone Lab Result Recording

When a user provides hormone lab results, record them with the following fields:

| Field | Required | Description |
|-------|----------|-------------|
| `date` | Yes | Date the blood was drawn (YYYY-MM-DD) |
| `test_name` | Yes | Name of the hormone marker tested |
| `value` | Yes | Numeric result value |
| `unit` | Yes | Unit of measurement |
| `reference_range` | Yes | Lab-provided reference range |
| `lab_name` | No | Name of the laboratory that processed the test |
| `fasting` | No | Whether the patient was fasting (yes/no) |
| `cycle_day` | No | Day of menstrual cycle at time of draw (if applicable) |
| `notes` | No | Any additional context (time of draw, medications, symptoms) |

Store results in `items/hormones.md` using structured tables organized by hormone panel category.

---

### 2. Common Hormone Panels & Reference Ranges

Use the following reference ranges as general guidelines. Always prefer the lab-specific reference range provided with results, as ranges vary by laboratory method and assay.

#### Thyroid Panel

| Marker | Typical Range | Unit | Notes |
|--------|--------------|------|-------|
| TSH | 0.4 - 4.0 | mIU/L | Some functional ranges use 0.5 - 2.5 |
| Free T4 | 0.8 - 1.8 | ng/dL | Primary thyroid output |
| Free T3 | 2.3 - 4.2 | pg/mL | Active thyroid hormone |
| TPO Antibodies | < 35 | IU/mL | Elevated suggests autoimmune thyroiditis |
| Thyroglobulin Ab | < 20 | IU/mL | Elevated suggests autoimmune thyroid disease |
| Reverse T3 | 9.2 - 24.1 | ng/dL | May indicate conversion issues if elevated |

#### Sex Hormones (Female)

Reference ranges vary significantly by menstrual cycle phase:

| Marker | Follicular | Ovulatory | Luteal | Postmenopausal | Unit |
|--------|-----------|-----------|--------|----------------|------|
| Estradiol (E2) | 19 - 144 | 64 - 357 | 56 - 214 | < 31 | pg/mL |
| Progesterone | 0.1 - 0.9 | 0.1 - 12 | 1.8 - 24 | < 0.2 | ng/mL |
| LH | 1.9 - 12.5 | 8.7 - 76.3 | 0.5 - 16.9 | 10 - 54 | mIU/mL |
| FSH | 2.5 - 10.2 | 3.4 - 33.4 | 1.5 - 9.1 | 23 - 116 | mIU/mL |
| DHEA-S | 35 - 430 | 35 - 430 | 35 - 430 | 12 - 154 | mcg/dL |
| Total Testosterone | 8 - 60 | 8 - 60 | 8 - 60 | 3 - 41 | ng/dL |
| Free Testosterone | 0.2 - 5.0 | 0.2 - 5.0 | 0.2 - 5.0 | 0.1 - 3.2 | pg/mL |

#### Sex Hormones (Male)

| Marker | Typical Range | Unit | Notes |
|--------|--------------|------|-------|
| Total Testosterone | 264 - 916 | ng/dL | AM draw preferred; declines ~1% per year after 30 |
| Free Testosterone | 5.0 - 21.0 | ng/dL | Bioavailable fraction |
| SHBG | 10 - 57 | nmol/L | Binds testosterone; elevated SHBG lowers free T |
| Estradiol (E2) | 10 - 40 | pg/mL | Elevated may indicate aromatase activity |
| LH | 1.5 - 9.3 | mIU/mL | Low with low T suggests secondary hypogonadism |
| FSH | 1.6 - 8.0 | mIU/mL | Elevated with low T suggests primary hypogonadism |
| DHEA-S | 80 - 560 | mcg/dL | Age-dependent; declines with age |

#### Adrenal / Stress Hormones

| Marker | Typical Range | Unit | Notes |
|--------|--------------|------|-------|
| Cortisol (AM, 7-9am) | 6 - 23 | mcg/dL | Must be drawn in the morning for accuracy |
| Cortisol (PM) | 3 - 16 | mcg/dL | Should be lower than AM value |
| DHEA-S | Age-dependent | mcg/dL | Peaks in 20s, declines with age |
| Salivary Cortisol (AM) | 0.1 - 0.75 | mcg/dL | Four-point salivary testing preferred for rhythm |
| Salivary Cortisol (PM) | 0.004 - 0.11 | mcg/dL | Should show clear diurnal decline |

#### Metabolic Markers

| Marker | Typical Range | Unit | Notes |
|--------|--------------|------|-------|
| Insulin (fasting) | 2.0 - 19.6 | mIU/mL | Optimal functional range: 2 - 8 |
| HbA1c | 4.0 - 5.6 | % | 5.7 - 6.4 = prediabetic; >= 6.5 = diabetic |
| Vitamin D (25-OH) | 30 - 100 | ng/mL | Optimal: 40 - 60 ng/mL; acts as hormone precursor |
| IGF-1 | Age-dependent | ng/mL | Growth hormone surrogate marker |

---

### 3. Trend Analysis

When the user has multiple data points for the same marker, perform trend analysis:

- **Plot values over time** against the reference range, noting where values fall within the range (low-normal, mid-range, high-normal, out-of-range).
- **Flag the following conditions:**
  - Out-of-range values (above or below reference range)
  - Significant changes: greater than 20% shift between consecutive tests
  - Trending toward boundary: value moving consistently toward upper or lower limit across 3+ data points
  - Rapid changes that may warrant earlier retesting
- **Unit conversion support:**
  - Testosterone: ng/dL to nmol/L (multiply by 0.0347)
  - Estradiol: pg/mL to pmol/L (multiply by 3.671)
  - Cortisol: mcg/dL to nmol/L (multiply by 27.59)
  - Vitamin D: ng/mL to nmol/L (multiply by 2.496)
  - TSH: mIU/L = mcIU/mL (equivalent)

Present trends in table format with directional arrows and percentage change between consecutive readings.

---

### 4. Symptom-Hormone Correlation

Track symptoms alongside lab values to identify potential correlations. When recording symptoms, note date, severity (1-10), and frequency.

#### Thyroid-Related Symptoms
- Fatigue / low energy
- Unexplained weight gain or loss
- Hair loss or thinning
- Cold intolerance (hypothyroid) or heat intolerance (hyperthyroid)
- Resting heart rate changes (bradycardia or tachycardia)
- Dry skin, brittle nails
- Constipation or diarrhea
- Brain fog, difficulty concentrating
- Depression or anxiety

#### Sex Hormone-Related Symptoms
- Libido changes (increase or decrease)
- Mood swings, irritability, depression
- Energy level fluctuations
- Menstrual cycle changes (irregular, heavy, absent)
- Hot flashes, night sweats
- Erectile dysfunction
- Muscle mass changes
- Acne, oily skin
- Breast tenderness

#### Cortisol / Adrenal-Related Symptoms
- Sleep disturbances (difficulty falling or staying asleep)
- Weight gain (especially central/abdominal)
- Anxiety, feeling "wired but tired"
- Energy patterns (afternoon crash, second wind at night)
- Salt or sugar cravings
- Dizziness upon standing
- Slow recovery from illness or exercise
- Sensitivity to stress

#### Metabolic Symptoms
- Blood sugar crashes (shakiness, irritability between meals)
- Excessive thirst or urination
- Difficulty losing weight despite caloric deficit
- Fatigue after meals

---

### 5. Lifestyle Optimization Suggestions

Provide evidence-based lifestyle factor recommendations. Always include the evidence level:
- **Strong evidence:** Supported by multiple RCTs or meta-analyses
- **Moderate evidence:** Supported by limited RCTs or large observational studies
- **Emerging evidence:** Supported by preliminary studies or mechanistic data

#### Sleep (affects cortisol, growth hormone, testosterone, insulin)
- **7-9 hours per night** -- Strong evidence for cortisol regulation and testosterone production (testosterone production peaks during sleep)
- **Consistent sleep/wake schedule** -- Strong evidence for cortisol rhythm normalization
- **Dark, cool sleep environment** -- Moderate evidence for melatonin production and downstream hormone effects
- **Limit blue light 1-2 hours before bed** -- Moderate evidence for melatonin and cortisol timing

#### Exercise (affects testosterone, insulin sensitivity, cortisol, growth hormone)
- **Resistance training 3-4x/week** -- Strong evidence for testosterone and growth hormone release; improves insulin sensitivity
- **Moderate cardio 150 min/week** -- Strong evidence for insulin sensitivity and cortisol management
- **Avoid chronic overtraining** -- Moderate evidence that excessive endurance exercise can suppress testosterone and elevate cortisol
- **HIIT in moderation** -- Moderate evidence for growth hormone release and insulin sensitivity

#### Nutrition (affects thyroid, estrogen metabolism, insulin, testosterone)
- **Iodine (seaweed, dairy, eggs)** -- Strong evidence for thyroid hormone synthesis (150-300 mcg/day)
- **Selenium (Brazil nuts, fish)** -- Strong evidence for T4-to-T3 conversion and thyroid antibody reduction (55-200 mcg/day)
- **Cruciferous vegetables (broccoli, cauliflower)** -- Moderate evidence for healthy estrogen metabolism via DIM and I3C
- **Dietary fiber (25-35g/day)** -- Strong evidence for estrogen clearance and blood sugar regulation
- **Healthy fats (olive oil, avocado, nuts)** -- Moderate evidence for testosterone and hormone precursor production
- **Zinc-rich foods (oysters, red meat, pumpkin seeds)** -- Moderate evidence for testosterone and thyroid function
- **Limit processed sugar and refined carbs** -- Strong evidence for insulin sensitivity and SHBG levels
- **Adequate protein (0.7-1g per lb bodyweight)** -- Moderate evidence for IGF-1 and muscle-mediated hormone signaling

#### Stress Management (affects cortisol, DHEA, thyroid, sex hormones)
- **Meditation / breathwork (10-20 min/day)** -- Moderate evidence for cortisol reduction
- **Nature exposure** -- Emerging evidence for cortisol and DHEA improvement
- **Social connection** -- Moderate evidence for oxytocin and cortisol modulation
- **Limit caffeine after 12pm** -- Moderate evidence for cortisol rhythm preservation

#### Supplements (discuss with provider before starting)
| Supplement | Target Hormones | Typical Dose | Evidence Level |
|-----------|-----------------|-------------|----------------|
| Vitamin D3 | Testosterone, insulin, thyroid | 2,000 - 5,000 IU/day | Strong |
| Magnesium glycinate | Cortisol, insulin, testosterone | 200 - 400 mg/day | Moderate |
| Zinc | Testosterone, thyroid | 15 - 30 mg/day | Moderate |
| Selenium | Thyroid (T4 to T3) | 100 - 200 mcg/day | Strong |
| Ashwagandha (KSM-66) | Cortisol, testosterone, thyroid | 300 - 600 mg/day | Moderate |
| Omega-3 (EPA/DHA) | Inflammation, insulin sensitivity | 1 - 3 g/day | Strong |
| Myo-inositol | Insulin, FSH/LH ratio (PCOS) | 2 - 4 g/day | Moderate |
| DIM (diindolylmethane) | Estrogen metabolism | 100 - 200 mg/day | Emerging |

---

### 6. Hormone Health Score (0-100)

Calculate a composite hormone health score using three weighted components:

#### Component Breakdown

**Lab Values In Range -- 40% of total score**
- For each tracked marker: score 100 if within optimal range, 75 if within standard reference range, 50 if borderline (within 10% of range boundary), 25 if mildly out of range (within 20% beyond boundary), 0 if significantly out of range
- Average across all tracked markers, weighted by clinical significance

**Symptom Burden -- 30% of total score**
- Based on symptom severity ratings (1-10 scale) across all tracked symptoms
- Score = 100 - (average symptom severity x 10)
- Weighted by number of hormone-related symptoms reported

**Lifestyle Factors -- 30% of total score**
- Sleep quality and duration: 0-25 points
- Exercise frequency and type: 0-25 points
- Nutrition quality: 0-25 points
- Stress management practices: 0-25 points

#### Score Interpretation
| Score Range | Interpretation |
|-------------|---------------|
| 85 - 100 | Excellent -- hormones well-optimized |
| 70 - 84 | Good -- minor areas for improvement |
| 55 - 69 | Fair -- several areas need attention |
| 40 - 54 | Below average -- significant optimization opportunities |
| 0 - 39 | Poor -- recommend comprehensive evaluation with endocrinologist |

---

### 7. Testing Schedule Recommendations

#### Thyroid
- **On thyroid medication (levothyroxine, etc.):** Retest TSH and Free T4 every 6-8 weeks after dose changes, then every 6-12 months once stable
- **Stable, no medication:** Annual thyroid panel
- **Hashimoto's or Graves' disease:** TSH, Free T4, Free T3, and antibodies every 6 months
- **Timing:** Fasting, morning draw preferred; hold thyroid medication until after blood draw

#### Sex Hormones (Female)
- **Fertility evaluation:** Day 3 (FSH, LH, Estradiol) and Day 21 (Progesterone) of cycle
- **PCOS workup:** Total and free testosterone, DHEA-S, fasting insulin, LH/FSH ratio -- any cycle day
- **Perimenopause/menopause symptoms:** FSH, Estradiol, tested during early follicular phase if still cycling
- **On HRT:** Retest 6-8 weeks after starting or dose change, then every 6-12 months

#### Sex Hormones (Male)
- **Initial low-T evaluation:** Total testosterone, free testosterone, SHBG, LH, FSH, estradiol, prolactin -- fasting AM draw (before 10am)
- **On TRT:** Total and free testosterone, estradiol, hematocrit, PSA every 3-6 months initially, then every 6-12 months
- **Monitoring:** Always draw between 7-10am for consistency

#### Cortisol
- **Serum cortisol:** Must be drawn between 7-9am for AM cortisol
- **Four-point salivary cortisol:** Waking, noon, afternoon, bedtime -- provides diurnal rhythm assessment
- **DUTCH test (dried urine):** Comprehensive cortisol metabolites and hormone panel -- follow provider instructions for timing
- **Retest frequency:** Every 3-6 months if managing adrenal issues; annually for general monitoring

#### Metabolic Markers
- **Fasting insulin and glucose:** Annually for general health; every 3-6 months if managing insulin resistance
- **HbA1c:** Every 3 months if diabetic/prediabetic; annually for general screening
- **Vitamin D:** Test in late winter (trough) and late summer (peak) initially, then annually

---

## Output Formats

### Lab Result Entry Confirmation

When a user logs hormone results, respond with:

```
## Lab Results Recorded - [DATE]

| Marker | Value | Unit | Reference Range | Status |
|--------|-------|------|----------------|--------|
| [name] | [value] | [unit] | [range] | [In Range / High / Low / Borderline] |

**Fasting:** [Yes/No]
**Lab:** [Lab name if provided]
**Cycle Day:** [If applicable]
**Notes:** [Any notes]

### Observations
- [Note any out-of-range values]
- [Note any significant changes from previous results]
- [Suggest follow-up testing if appropriate]
```

### Trend Report

When a user requests a trend analysis:

```
## Hormone Trend Report - [MARKER NAME]

| Date | Value | Unit | Status | Change |
|------|-------|------|--------|--------|
| [date] | [value] | [unit] | [status] | [% change from previous] |

### Trend Summary
- Direction: [Increasing / Decreasing / Stable]
- Average value: [avg]
- Range: [min] - [max]
- Time in optimal range: [X]%

### Flags
- [Any alerts or concerns]

### Recommendations
- [Next test date suggestion]
- [Lifestyle factors to consider]
```

### Comprehensive Panel Review

When reviewing a full panel:

```
## Comprehensive Hormone Panel Review - [DATE]

### Hormone Health Score: [X]/100
- Lab Values: [X]/40
- Symptom Burden: [X]/30
- Lifestyle: [X]/30

### Panel Results
[Table of all results with status]

### Key Findings
1. [Most significant finding]
2. [Second finding]
3. [Third finding]

### Correlations
- [Symptom-hormone correlations identified]

### Action Items
1. [Priority recommendation]
2. [Secondary recommendation]
3. [Lifestyle adjustment]

### Next Steps
- [Follow-up testing schedule]
- [Topics to discuss with provider]
```

---

## Data Persistence

All hormone data is stored in `items/hormones.md` with the following structure:

```markdown
# Hormone Health Records

## Patient Profile
- Age:
- Sex:
- Known conditions:
- Current medications:
- Current supplements:

## Lab History

### Thyroid Panel
| Date | TSH | Free T4 | Free T3 | TPO Ab | Tg Ab | Lab | Notes |
|------|-----|---------|---------|--------|-------|-----|-------|

### Sex Hormones
| Date | Marker | Value | Unit | Cycle Day | Lab | Notes |
|------|--------|-------|------|-----------|-----|-------|

### Adrenal / Cortisol
| Date | Cortisol AM | Cortisol PM | DHEA-S | Lab | Notes |
|------|------------|------------|--------|-----|-------|

### Metabolic Markers
| Date | Insulin | HbA1c | Vitamin D | IGF-1 | Lab | Notes |
|------|---------|-------|-----------|-------|-----|-------|

## Symptom Log
| Date | Symptom | Severity (1-10) | Category | Notes |
|------|---------|-----------------|----------|-------|

## Lifestyle Log
| Date | Sleep (hrs) | Exercise | Nutrition Notes | Stress Level (1-10) |
|------|------------|----------|-----------------|---------------------|

## Hormone Health Score History
| Date | Overall | Lab Score | Symptom Score | Lifestyle Score |
|------|---------|-----------|--------------|-----------------|
```

When updating records:
1. Read the existing `items/hormones.md` file using the Read tool
2. Append new entries to the appropriate table
3. Write the updated file using the Edit tool
4. If the file does not exist, create it with the template structure above

---

## Alerts and Safety

### Medical Disclaimer
This tool is designed for personal health tracking and educational purposes only. It is NOT a diagnostic tool and should NEVER be used to:
- Diagnose any medical condition
- Adjust medication dosages
- Replace consultation with a qualified healthcare provider
- Make treatment decisions

### Clinical Context Matters
- **Reference ranges vary** by laboratory, assay method, age, sex, time of day, and individual factors. The ranges listed in this skill are general guidelines only.
- **A single lab value rarely tells the full story.** Patterns over time and symptom correlation are more informative than isolated readings.
- **Subclinical findings** (values technically in range but at the extremes) may be clinically significant in the context of symptoms.

### When to Recommend Urgent Medical Consultation
Flag and strongly recommend the user seek prompt medical attention for:
- TSH > 10 or < 0.1 (may indicate significant thyroid dysfunction)
- Cortisol AM < 3 mcg/dL (possible adrenal insufficiency)
- Fasting insulin > 25 mIU/mL (significant insulin resistance)
- HbA1c > 6.5% (diabetic range -- needs management)
- Total testosterone (male) < 150 ng/dL (severely low)
- Any sudden, dramatic shift in lab values without explanation
- New or worsening symptoms alongside abnormal labs

### Data Privacy
- All hormone data is stored locally in the user's items directory
- No data is transmitted externally
- Recommend users keep their health data backed up and secure
