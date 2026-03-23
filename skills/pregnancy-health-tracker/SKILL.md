---
name: pregnancy-health-tracker
description: "Provides trimester-specific pregnancy health guidance, tracks prenatal appointments, monitors symptoms, and offers nutrition and exercise recommendations for each stage. Use when the user is pregnant, planning pregnancy, or asks about prenatal health."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🤰","category":"health"}}
---

# Pregnancy Health Tracker

A comprehensive pregnancy health companion that provides trimester-specific guidance, tracks prenatal appointments, monitors symptoms, and offers nutrition and exercise recommendations throughout each stage of pregnancy.

## Capabilities

### 1. Pregnancy Timeline & Milestones

Track pregnancy progress by trimester and week with key developmental milestones.

#### First Trimester (Weeks 1-12)

- **Weeks 1-4:** Implantation, hormonal changes begin, missed period
- **Weeks 5-6:** Heartbeat detectable, neural tube forming, early ultrasound possible
- **Weeks 7-8:** Major organs forming (heart, brain, lungs, liver), limb buds appear
- **Weeks 9-10:** Embryo becomes fetus, facial features developing, fingers and toes forming
- **Weeks 11-12:** Genitalia forming, reflexes developing, nuchal translucency screening window

**Common symptoms:** Nausea/morning sickness, fatigue, breast tenderness, frequent urination, food aversions, mood changes

**Key tests:** Confirmation ultrasound, blood type and Rh factor, complete blood count (CBC), STI screening, first trimester screening (NIPT or combined screening), dating ultrasound

#### Second Trimester (Weeks 13-27)

- **Weeks 13-16:** Energy often returns, uterus rises above pelvis, gender may be detectable
- **Weeks 17-20:** Quickening (first fetal movements felt), anatomy scan (18-22 weeks)
- **Weeks 21-24:** Rapid weight gain, viability threshold (~24 weeks), hearing develops
- **Weeks 25-27:** Eyes open, sleep-wake cycles establish, lungs producing surfactant

**Common symptoms:** Round ligament pain, back pain, nasal congestion, skin changes (linea nigra, melasma), increased appetite

**Key tests:** Anatomy scan (18-22 weeks), glucose screening (24-28 weeks), Rh antibody screen if Rh-negative, quad screen if not done in first trimester

#### Third Trimester (Weeks 28-40)

- **Weeks 28-31:** Rapid brain development, bones hardening, kick counts begin
- **Weeks 32-35:** Baby gaining weight rapidly (~½ pound/week), head-down positioning
- **Weeks 36-37:** Considered early term, lungs maturing, baby dropping into pelvis
- **Weeks 38-40:** Full term, final growth, delivery readiness, cervical changes

**Common symptoms:** Braxton-Hicks contractions, heartburn, shortness of breath, pelvic pressure, difficulty sleeping, swelling, nesting instinct

**Key tests:** Group B Strep (GBS) swab (35-37 weeks), non-stress tests (if indicated), cervical checks, fetal position assessment

---

### 2. Prenatal Appointment Tracker

#### Standard Visit Schedule

| Gestational Age | Visit Frequency | Focus |
|---|---|---|
| Weeks 4-28 | Every 4 weeks (monthly) | Baseline labs, screening tests, fundal height |
| Weeks 28-36 | Every 2 weeks | Growth monitoring, position checks, GBS prep |
| Weeks 36-40 | Every week | Cervical readiness, birth planning, fetal monitoring |

#### Key Tests by Timing

| Timing | Test | Purpose |
|---|---|---|
| First visit | Blood type, Rh, CBC, STI panel, urinalysis | Baseline health status |
| 10-13 weeks | NIPT (cell-free DNA) | Screen for chromosomal conditions |
| 11-14 weeks | Nuchal translucency ultrasound | Screen for Down syndrome, trisomy 18 |
| 15-20 weeks | Quad screen (if applicable) | Neural tube defects, chromosomal conditions |
| 18-22 weeks | Anatomy scan (Level 2 ultrasound) | Detailed fetal anatomy review |
| 24-28 weeks | Glucose tolerance test (1-hour) | Gestational diabetes screening |
| 24-28 weeks | Rh antibody screen | Rh incompatibility (if Rh-negative) |
| 28 weeks | RhoGAM injection | If Rh-negative |
| 28 weeks | Tdap vaccine | Whooping cough protection for baby |
| 35-37 weeks | Group B Strep (GBS) swab | Determine need for antibiotics during labor |
| 36+ weeks | Cervical exams (optional) | Assess dilation and effacement |
| 40+ weeks | Non-stress test, biophysical profile | Monitor post-dates pregnancy |

#### Each Visit Typically Includes

- Weight check
- Blood pressure measurement
- Urine sample (protein and glucose)
- Fundal height measurement (after 20 weeks)
- Fetal heart rate check (Doppler or fetoscope)
- Review of symptoms and concerns

---

### 3. Symptom Monitoring

Track common symptoms by trimester with clear thresholds for normal vs. concerning presentations.

| Symptom | Normal Presentation | Seek Care If |
|---|---|---|
| Nausea/Vomiting | Common in first trimester, mild-moderate | Cannot keep fluids down for >24 hours, weight loss >5%, dark urine (hyperemesis) |
| Fatigue | Throughout pregnancy, especially T1 and T3 | Severe fatigue with shortness of breath, racing heart, or pallor (may indicate anemia) |
| Swelling (Edema) | Mild swelling in feet/ankles, worse in heat | Sudden swelling of face or hands, pitting edema, accompanied by headache or vision changes (preeclampsia warning) |
| Contractions | Braxton-Hicks: irregular, painless, stop with activity change | Regular contractions (<37 weeks), every 10 min or closer, increasing in intensity (preterm labor risk) |
| Bleeding | Light spotting in early pregnancy (implantation) | Heavy bleeding (soaking a pad), bleeding with pain or cramping, any bleeding in 2nd/3rd trimester |
| Headache | Occasional, mild, relieved by rest/hydration | Severe or persistent headache, not relieved by acetaminophen, with vision changes or upper abdominal pain |
| Abdominal Pain | Round ligament pain (sharp, brief, with movement) | Constant or severe pain, pain with bleeding, one-sided pain in early pregnancy (ectopic concern) |
| Back Pain | Common, especially in T2/T3, relieved by rest | Rhythmic lower back pain (may indicate labor), pain with fever (kidney infection) |
| Shortness of Breath | Mild, especially in T3 as uterus grows | Sudden onset, severe, with chest pain or rapid heartbeat |
| Itching | Mild skin stretching itch | Intense itching especially on palms/soles (may indicate cholestasis), itching with rash |
| Vaginal Discharge | Increased clear/white discharge (leukorrhea) | Green/yellow color, foul odor, itching/burning, watery gush (possible membrane rupture) |

#### Logging Guidance

When logging symptoms, note:
- Date and gestational week
- Symptom description and severity (1-10 scale)
- Duration and frequency
- What makes it better or worse
- Any associated symptoms

---

### 4. Prenatal Nutrition Guide

#### Essential Nutrients

| Nutrient | Daily Need | Best Sources | Notes |
|---|---|---|---|
| Folic Acid | 600-800 mcg | Leafy greens, fortified grains, lentils, asparagus, prenatal supplement | Critical for neural tube development; start before conception ideally |
| Iron | 27 mg | Red meat, poultry, beans, spinach, fortified cereals | Absorption enhanced with vitamin C; avoid taking with calcium |
| Calcium | 1000 mg | Dairy products, fortified plant milks, tofu, almonds, broccoli | Essential for fetal bone development; if insufficient, drawn from maternal stores |
| DHA/Omega-3 | 200-300 mg | Low-mercury fish (salmon, sardines, trout), DHA supplement, walnuts | Critical for fetal brain and eye development |
| Vitamin D | 600 IU (some recommend up to 1000-2000 IU) | Sunlight exposure, fortified milk, fatty fish, supplement | Supports calcium absorption and immune function |
| Choline | 450 mg | Eggs, liver, soybeans, beef, chicken, fish, cruciferous vegetables | Supports brain development and may reduce neural tube defect risk |
| Iodine | 220 mcg | Iodized salt, dairy, seafood, prenatal supplement | Crucial for fetal thyroid function and brain development |
| Protein | 75-100 g | Meat, fish, eggs, dairy, legumes, nuts, tofu | Increased need especially in T2/T3 for fetal growth |

#### Caloric Needs by Trimester

- **First trimester:** No additional calories needed (about 1800-2000 kcal/day baseline)
- **Second trimester:** ~340 extra calories/day
- **Third trimester:** ~450 extra calories/day

#### Foods to Avoid

| Food | Reason |
|---|---|
| Raw or undercooked fish (sushi) | Parasites, bacteria |
| High-mercury fish (shark, swordfish, king mackerel, tilefish, bigeye tuna) | Mercury neurotoxicity to fetus |
| Raw or undercooked meat/eggs | Salmonella, toxoplasmosis, E. coli risk |
| Unpasteurized dairy and juices | Listeria risk |
| Deli meats and hot dogs (unless heated steaming hot) | Listeria risk |
| Soft cheeses from unpasteurized milk (brie, camembert, queso fresco) | Listeria risk |
| Raw sprouts | Salmonella, E. coli risk |
| Alcohol | No known safe amount; risk of fetal alcohol spectrum disorders |
| Excessive caffeine | Limit to <200 mg/day (~one 12-oz cup of coffee); associated with increased miscarriage risk at higher amounts |
| Herbal teas (some varieties) | Some herbs may stimulate uterine contractions; consult provider |

#### Meal Planning Tips

- Eat small, frequent meals to manage nausea and heartburn
- Stay well-hydrated (8-10 glasses of water daily)
- Include fiber-rich foods to prevent constipation
- Take prenatal vitamin consistently (with food if it causes nausea)
- If experiencing morning sickness: try bland foods, ginger, vitamin B6

---

### 5. Safe Exercise Guidelines

#### Recommended Activities

| Activity | Benefits | Trimester Suitability |
|---|---|---|
| Walking | Low-impact cardio, accessible | All trimesters |
| Swimming/Water aerobics | Joint-friendly, reduces swelling, cool and comfortable | All trimesters |
| Prenatal yoga | Flexibility, stress relief, breathing practice | All trimesters (modified) |
| Stationary cycling | Cardio without balance risk | All trimesters |
| Low-impact aerobics | Cardiovascular fitness | T1 and T2, modify in T3 |
| Strength training (light-moderate) | Muscle tone, posture support | All trimesters with modifications |
| Pelvic floor exercises (Kegels) | Labor preparation, incontinence prevention | All trimesters |

#### Activities to Modify or Avoid

- **Contact sports** (soccer, basketball, hockey): Risk of abdominal trauma
- **Hot yoga or hot pilates**: Risk of overheating (avoid core temperature >102.2°F/39°C)
- **Lying flat on back** after first trimester: Can compress vena cava; use left-side positioning or incline
- **Heavy lifting** or straining: Increased risk of injury due to relaxin hormone
- **High-altitude activities** (>6000 ft if not acclimated): Reduced oxygen availability
- **Scuba diving**: Risk of decompression sickness to fetus
- **Activities with fall risk** (skiing, horseback riding, gymnastics): Balance shifts with pregnancy

#### Exercise Recommendations

- **Frequency:** 150 minutes per week of moderate-intensity activity (ACOG recommendation)
- **Intensity:** Should be able to carry on a conversation during exercise (talk test)
- **Warm up and cool down:** 5-10 minutes each session
- **Hydration:** Drink water before, during, and after exercise
- **Clothing:** Supportive shoes, comfortable clothing, supportive bra

#### Stop Exercising and Seek Care If

- Vaginal bleeding or fluid leaking
- Dizziness or feeling faint
- Headache that does not resolve
- Chest pain or palpitations
- Calf pain or swelling (blood clot concern)
- Regular painful contractions
- Shortness of breath before starting exercise
- Muscle weakness affecting balance

#### Contraindications to Exercise (Consult Provider First)

- Cervical insufficiency or cerclage
- Placenta previa after 26 weeks
- Preterm labor risk or preterm premature rupture of membranes
- Preeclampsia or pregnancy-induced hypertension
- Severe anemia
- Certain heart or lung conditions
- Multiple gestation with risk factors for preterm labor

---

### 6. Weight Gain Tracking

#### Recommended Total Weight Gain by Pre-Pregnancy BMI

| BMI Category | BMI Range | Recommended Total Gain | Rate in T2/T3 (per week) |
|---|---|---|---|
| Underweight | <18.5 | 12.5-18 kg (28-40 lbs) | ~0.5 kg (1 lb) |
| Normal weight | 18.5-24.9 | 11.5-16 kg (25-35 lbs) | ~0.4 kg (1 lb) |
| Overweight | 25.0-29.9 | 7-11.5 kg (15-25 lbs) | ~0.3 kg (0.6 lb) |
| Obese | ≥30.0 | 5-9 kg (11-20 lbs) | ~0.2 kg (0.5 lb) |

*For twin pregnancies, recommended gains are higher. Consult provider for individual guidance.*

#### Weight Gain Distribution

Where the weight goes in a typical pregnancy:
- Baby: ~3.4 kg (7.5 lbs)
- Placenta: ~0.7 kg (1.5 lbs)
- Amniotic fluid: ~0.9 kg (2 lbs)
- Uterine growth: ~0.9 kg (2 lbs)
- Breast tissue: ~0.5-1.4 kg (1-3 lbs)
- Blood volume increase: ~1.4 kg (3 lbs)
- Fluid retention: ~1.4-1.8 kg (3-4 lbs)
- Fat and nutrient stores: ~2.7-3.6 kg (6-8 lbs)

#### Tracking Guidance

- Weigh at the same time of day, in similar clothing
- Weekly weigh-ins are sufficient; avoid daily weighing
- First trimester: expect 0.5-2 kg (1-4 lbs) total
- Gradual, steady gain is more important than exact numbers
- Report sudden rapid gain (>1 kg/2 lbs in a week) to provider as it may indicate fluid retention or preeclampsia

---

### 7. Kick Count Tracking (Third Trimester)

#### When to Start

Begin daily kick counts around **28 weeks** (start of third trimester).

#### How to Count

1. **Choose a consistent time** each day when baby is typically active (often after meals or in the evening)
2. **Sit comfortably or lie on your left side**
3. **Count any fetal movement** — kicks, rolls, swishes, jabs, flutters all count
4. **Time how long it takes to reach 10 movements**
5. **Record the count** with date, start time, and time to reach 10

#### Normal Range

- Most babies will produce **10 movements within 2 hours**
- Many active babies reach 10 movements in 15-30 minutes
- Getting to know your baby's pattern is most important

#### When to Contact Provider

- Fewer than 10 movements in 2 hours
- A noticeable change in baby's normal movement pattern
- Sudden decrease in overall activity level
- No movement felt at all during a kick count session

#### Logging Format

Record daily kick counts with:
- Date and gestational week
- Start time
- Time to reach 10 movements (or count at 2 hours if fewer than 10)
- Notes on movement quality or pattern changes

---

### 8. Birth Preparation Checklist

#### Hospital Bag Essentials

**For the birthing person:**
- Photo ID and insurance card
- Birth plan copies
- Comfortable robe and slippers
- Nursing bra and breast pads
- Toiletries (toothbrush, lip balm, hair ties, etc.)
- Phone and charger (long cord recommended)
- Snacks and drinks for labor
- Going-home outfit (maternity-sized)
- Pillow from home (optional)

**For the baby:**
- Going-home outfit (newborn and 0-3 months sizes)
- Swaddle blanket
- Car seat (installed and inspected before due date)
- Hat and socks

**For the support person:**
- Change of clothes
- Snacks and water
- Phone charger
- Cash for vending machines or cafeteria
- Comfort items (massage tools, essential oils if permitted)

#### Birth Plan Considerations

Discuss and document preferences for:
- **Labor:** Movement freedom, pain management preferences (natural, epidural, nitrous), intermittent vs. continuous monitoring
- **Delivery:** Preferred positions, episiotomy preferences, who cuts the cord
- **Immediately after birth:** Skin-to-skin contact, delayed cord clamping, breastfeeding initiation
- **Newborn care:** Vitamin K, eye prophylaxis, hepatitis B vaccine, circumcision
- **Cesarean birth plan:** In case of surgical delivery, partner presence, immediate skin-to-skin if possible
- **Feeding plan:** Breastfeeding, formula, or combination; lactation consultant support

*Note: Birth plans express preferences; flexibility is important as circumstances may change.*

#### Postpartum Preparation

- **Home setup:** Bassinet/crib, changing station, feeding supplies, diapers
- **Meal prep:** Freeze meals in advance or arrange meal train support
- **Support network:** Identify helpers for first weeks (partner leave, family, postpartum doula)
- **Pediatrician:** Select and schedule newborn's first appointment (3-5 days after birth)
- **Mental health:** Learn signs of postpartum depression/anxiety; identify support resources
- **Recovery supplies:** Peri bottle, ice packs, stool softener, nursing pads, comfortable clothing
- **Breastfeeding preparation:** Lactation consultant contact, breast pump (check insurance coverage), nursing pillow

---

## Output Formats

When providing pregnancy health information, use these structured formats as appropriate.

### Weekly Update

Provide a weekly pregnancy summary including:
- Current week and trimester
- Baby's approximate size and development
- Common symptoms to expect this week
- Upcoming appointments or tests
- Nutrition focus for the week
- Exercise tip of the week
- Kick count status (if applicable, T3)

### Appointment Reminder

For upcoming appointments, include:
- Date and gestational age
- Type of visit (routine, screening, specialist)
- Tests or procedures expected
- Questions to ask the provider
- Preparation needed (fasting, full bladder, etc.)

### Symptom Log

When logging symptoms, record:
- Date and gestational week
- Symptom description and severity
- Duration and pattern
- Impact on daily activities
- Provider recommendations if discussed

### Weight Chart

Track weight over time with:
- Weekly or biweekly measurements
- Comparison to recommended range for BMI category
- Rate of gain calculation
- Trend visualization description

---

## Data Persistence

Store pregnancy data in `items/pregnancy.md` with the following structure:

```markdown
# Pregnancy Health Record

## Profile
- Due date: [EDD]
- Pre-pregnancy BMI category: [category]
- Provider: [name]
- Blood type: [type]
- Rh status: [positive/negative]
- Risk factors: [if any]

## Timeline
### Week [number] - [date]
- Weight: [kg/lbs]
- Blood pressure: [if available]
- Symptoms: [list]
- Kick counts: [if applicable]
- Notes: [any notable events or concerns]

## Appointments
- [date] - [type] - [notes/results]

## Test Results
- [date] - [test name] - [result]
```

---

## Alerts and Safety

### Medical Disclaimer

**IMPORTANT: This skill provides general pregnancy health information for educational and tracking purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment.**

- Always follow the guidance of your OB-GYN, midwife, or healthcare provider
- Every pregnancy is unique; individual medical advice may differ from general guidelines
- Do not delay seeking medical care based on information from this tool
- All health decisions should be made in consultation with your healthcare team
- If you are unsure whether a symptom is concerning, err on the side of caution and contact your provider

### Emergency Warning Signs — Seek Immediate Care

Contact your provider or go to the hospital immediately if you experience any of the following:

- **Heavy vaginal bleeding** (soaking through a pad in an hour)
- **Severe headache** that does not resolve, especially with vision changes (flashing lights, blurred vision, seeing spots)
- **Sudden severe swelling** of the face, hands, or feet
- **Reduced or absent fetal movement** (fewer than 10 kicks in 2 hours after 28 weeks, or notable change in pattern)
- **Fluid leaking or gushing** from the vagina (possible membrane rupture)
- **Regular contractions before 37 weeks** (every 10 minutes or more frequent)
- **Severe abdominal pain** that does not resolve
- **Fever above 100.4°F (38°C)**
- **Painful urination with fever** (possible kidney infection)
- **Chest pain or difficulty breathing**
- **Seizures or loss of consciousness**
- **Thoughts of self-harm or harming the baby** — call 988 Suicide & Crisis Lifeline or go to the nearest emergency room

### When in Doubt

If you are ever uncertain whether a symptom is normal or concerning, **always contact your healthcare provider**. It is always better to be checked and reassured than to wait when something does not feel right.
