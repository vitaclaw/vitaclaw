---
name: sexual-health-analyzer
description: "Analyzes sexual health data including IIEF-5 scoring, STD screening management, contraception effectiveness, activity statistics, and cross-module correlation with medications, chronic conditions, mental health, nutrition, and exercise. Use when the user tracks sexual health metrics or needs reproductive health assessment."
version: 1.0.0
user-invocable: true
argument-hint: "[iief5-assessment | std-screening | contraception-review | activity-log | risk-assessment]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🔒","category":"health-analyzer"}}
---

# Sexual Health Analyzer Skill

## Skill Overview

This skill provides comprehensive sexual health data analysis, including IIEF-5 scoring analysis, STD screening management, contraception effectiveness evaluation, sexual activity statistics, and in-depth cross-module correlation analysis with medications, chronic conditions, mental health, nutrition, and exercise.

## Medical Disclaimer

**Important**: The data analysis and recommendations provided by this skill are for informational purposes only and do not constitute medical diagnosis or treatment advice.

- All sexual health concerns should be diagnosed and treated by a qualified physician
- Analysis results cannot replace professional medical examinations
- Seek immediate medical attention for emergencies
- Always follow your physician's professional recommendations

## Core Features

### 1. IIEF-5 Score Analysis

#### 1.1 Interactive Questionnaire

**Questionnaire Structure**:
- 5 questions, each scored 0-5
- Total score range: 0-25
- Assessment period: past 6 months

**Question Details**:

**Question 1**: Erectile Confidence
- Assesses the user's confidence in achieving and maintaining an erection
- Reflects the impact of psychological factors on sexual function
- Low scores may indicate performance anxiety

**Question 2**: Erection Achievement
- Assesses the ability to achieve an erection upon sexual stimulation
- Reflects vascular and neurological function
- Low scores may indicate organic ED

**Question 3**: Penetration Ability
- Assesses whether erection firmness is sufficient for penetration
- A clinically relevant erection quality indicator
- Low scores typically require medical intervention

**Question 4**: Erection Maintenance
- Assesses the ability to maintain an erection during intercourse
- Reflects veno-occlusive function
- Combined analysis with Question 3 can determine ED type

**Question 5**: Intercourse Satisfaction
- Assesses subjective satisfaction during intercourse
- Influenced by multiple factors including firmness, duration, and partner satisfaction
- A comprehensive indicator of overall sexual function

#### 1.2 ED Severity Assessment

| Total Score | ED Severity | Clinical Significance | Recommended Actions |
|-------------|------------|----------------------|---------------------|
| 22-25 | Normal | Good erectile function | Maintain healthy lifestyle |
| 17-21 | Mild ED | Mild dysfunction | Lifestyle modifications, periodic reassessment |
| 12-16 | Mild-Moderate ED | Moderate dysfunction | Medical evaluation recommended |
| 8-11 | Moderate ED | Significant dysfunction | Medical intervention needed |
| 5-7 | Severe ED | Severe dysfunction | Comprehensive medical evaluation and treatment |

#### 1.3 Trend Analysis

**Analysis Dimensions**:
- Total score change trend (improving/stable/worsening)
- Score change patterns for each question
- ED severity change trajectory
- Treatment intervention effectiveness assessment

**Output Content**:
- IIEF-5 score time-series chart
- Improvement/worsening trend indicators
- Rate of change calculations
- Correlation analysis with other health metrics

#### 1.4 Risk Factor Analysis

**Physiological Factors**:
- Age: ED risk increases approximately 20% per decade
- Diabetes: ED risk increases 3-fold
- Cardiovascular disease: ED risk increases 2-3-fold
- Hypertension: ED risk increases 1.5-2-fold
- Obesity: BMI >30 increases ED risk
- Hormonal abnormalities: low testosterone levels

**Psychological Factors**:
- Performance anxiety
- Depressive symptoms
- Stress levels
- Partner relationship issues

**Lifestyle Factors**:
- Smoking: increases ED risk 1.5-fold
- Excessive alcohol: long-term impact on sexual function
- Sedentary lifestyle: declining cardiovascular health
- Sleep quality: affects hormone secretion

**Medication Factors**:
- Antidepressants (SSRIs, etc.)
- Antihypertensives (beta-blockers, thiazides)
- Antipsychotics
- Hormonal medications

#### 1.5 Improvement Recommendations

**Lifestyle Interventions**:
- **Smoking cessation**: significantly improves vascular health
- **Alcohol limitation**: <2 drinks/day for men
- **Weight loss**: target BMI 18.5-24.9
- **Regular exercise**:
  - 150 minutes of moderate-intensity aerobic exercise per week
  - Strength training 2-3 times per week
  - Daily pelvic floor exercises (Kegel exercises)
- **Healthy diet**:
  - Mediterranean dietary pattern
  - Increased fruit and vegetable intake
  - Reduced saturated fat and processed foods
  - Moderate amounts of nuts and whole grains

**Psychological Interventions**:
- Sex therapist consultation
- Cognitive behavioral therapy
- Couples therapy
- Stress management techniques (meditation, yoga)

**Medical Interventions**:
- PDE5 inhibitors (prescription required)
- Testosterone replacement therapy (if testosterone is low)
- Vacuum erection devices
- Penile injection therapy
- Surgical treatment (vascular surgery, prosthesis)

### 2. STD Screening Management

#### 2.1 Screening Tests in Detail

**HIV (Human Immunodeficiency Virus)**:
- **Testing method**: Blood test (antibody + antigen combination)
- **Window period**: 1-3 months
- **High-risk populations**: MSM, sex workers, individuals with multiple partners
- **Screening frequency**: Every 3-6 months for high risk, annually for average risk

**Syphilis**:
- **Testing method**: Blood test (RPR/VDRL + TPPA confirmation)
- **Window period**: 10-90 days
- **Stages**: Primary, secondary, latent, tertiary
- **Treatment**: Penicillin is effective; high cure rate in early stages

**Chlamydia**:
- **Testing method**: Urine test or swab
- **Window period**: 1-3 weeks
- **Characteristics**: Often asymptomatic but can cause infertility
- **Treatment**: Azithromycin or doxycycline

**Gonorrhea**:
- **Testing method**: Urine test or swab
- **Window period**: 1-14 days
- **Characteristics**: Symptoms prominent in males, often asymptomatic in females
- **Treatment**: Ceftriaxone + azithromycin (considering resistance patterns)

**HPV (Human Papillomavirus)**:
- **Testing method**: Swab DNA test
- **Window period**: 1 month to several years
- **Characteristics**: Very common; most infections resolve spontaneously
- **High-risk types**: HPV 16/18 associated with cervical cancer
- **Prevention**: HPV vaccine is effective

**Hepatitis B**:
- **Testing method**: Blood test (HBsAg + anti-HBs)
- **Window period**: 1-6 months
- **Prevention**: Hepatitis B vaccine is effective
- **Treatment**: Antiviral medications

**Genital Herpes**:
- **Testing method**: Swab PCR or blood antibody test
- **Window period**: 2-12 days
- **Characteristics**: No cure; symptoms can be managed
- **Treatment**: Antiviral medications (acyclovir, etc.)

#### 2.2 Risk Assessment

**Behavioral Risk Factors**:
- Number of sexual partners (>3/year = high risk)
- Frequency of protective measure use
- STD status of sexual partners
- History of sex work or contact with sex workers
- MSM population
- History of injection drug use

**Dynamic Risk Score**:
- **Low risk** (<10 points): Single stable partner, consistent protection
- **Moderate risk** (10-30 points): 2-3 sexual partners, occasional protection
- **High risk** (30-50 points): Multiple partners, inconsistent protection
- **Very high risk** (>50 points): Sex workers, MSM, unprotected sex

#### 2.3 Screening Frequency Recommendations

Personalized screening schedules based on risk level:

| Risk Level | HIV/Syphilis | Chlamydia/Gonorrhea | HPV | Hepatitis B |
|------------|-------------|---------------------|-----|-------------|
| Low risk | Every 1-2 years | Every 1-2 years | Every 3 years | No testing needed if vaccinated |
| Moderate risk | Annually | Annually | Every 3 years | Every 1-2 years |
| High risk | Every 3-6 months | Every 3-6 months | Annually | Annually |
| Very high risk | Every 3 months | Every 3 months | Every 6 months | Every 6 months |

#### 2.4 Positive Result Management

**Immediate Actions**:
- Begin treatment (per physician's orders)
- Notify sexual partners and arrange testing
- Abstain from sexual activity or use strict protection
- Minimize transmission risk

**Treatment Tracking**:
- Post-treatment testing to confirm cure
- Monitor medication side effects
- Assess treatment adherence
- Document treatment process and outcomes

**Reinfection Prevention**:
- Concurrent partner treatment
- Resume protective measures after cure
- Regular follow-up testing
- Risk reduction education

#### 2.5 Statistical Analysis

- Screening frequency trends
- Positivity rate changes
- Infection type distribution
- Cure rate statistics
- Reinfection rate analysis

### 3. Contraception Management

#### 3.1 Detailed Contraceptive Method Analysis

**Condoms (Male/Female)**:
- **Typical use effectiveness**: 85%
- **Perfect use effectiveness**: 98%
- **Advantages**:
  - Only method that prevents both pregnancy and STDs
  - No hormonal side effects
  - Easily accessible
  - Immediately effective
- **Disadvantages**:
  - Must be used every time
  - May affect sexual pleasure
  - May break or slip
- **Satisfaction Factors**:
  - Proper fit
  - Lubricant use
  - Application technique
  - Brand preference

**Oral Contraceptive Pills**:
- **Typical use effectiveness**: 91%
- **Perfect use effectiveness**: 99.7%
- **Types**:
  - Combined pills (estrogen + progestin)
  - Progestin-only pills (suitable for breastfeeding)
  - 24/4 regimen vs 21/7 regimen
- **Advantages**:
  - Highly effective contraception
  - Can regulate menstrual cycle
  - Improves acne and premenstrual syndrome
  - Reduces risk of ovarian and endometrial cancer
- **Disadvantages**:
  - Requires daily administration
  - Hormonal side effects
  - Not suitable for female smokers >35 years old
  - Does not prevent STDs
- **Side Effect Tracking**:
  - Nausea, breast tenderness
  - Mood changes
  - Libido changes
  - Weight changes
  - Breakthrough bleeding

**Intrauterine Device (IUD)**:
- **Effectiveness**: 99%+
- **Types**:
  - Copper IUD (10-12 years)
  - Levonorgestrel IUD (3-8 years)
- **Advantages**:
  - Long-acting reversible
  - Immediately effective
  - Can be removed at any time
  - Hormonal IUD can reduce menstrual flow
- **Disadvantages**:
  - Requires clinician placement
  - Discomfort during insertion
  - May increase menstrual flow and cramping (copper IUD)
  - Does not prevent STDs
- **Side Effect Tracking**:
  - Post-insertion pain
  - Menstrual changes
  - Spotting
  - Perforation risk (rare)

**Subdermal Implant**:
- **Effectiveness**: 99%+
- **Duration**: 3-5 years
- **Advantages**:
  - Long-acting reversible
  - Simple insertion
  - Can be removed at any time
  - Discreet
- **Disadvantages**:
  - Hormonal side effects
  - May cause irregular menstruation
  - Possible scarring at insertion site
  - Does not prevent STDs

**Injectable Contraceptive**:
- **Typical use effectiveness**: 94%
- **Perfect use effectiveness**: 99%+
- **Frequency**: Every 3 months
- **Advantages**:
  - No daily administration required
  - Discreet
- **Disadvantages**:
  - Requires regular injections
  - Weight gain is common
  - Fertility recovery may be delayed
  - Does not prevent STDs

**Withdrawal Method**:
- **Typical use effectiveness**: 78%
- **Perfect use effectiveness**: 96%
- **Risks**:
  - Requires high self-control
  - Pre-ejaculatory fluid may contain sperm
  - Increases sexual anxiety
  - Does not prevent STDs
- **Not recommended**: High failure rate

**Fertility Awareness Methods**:
- **Typical use effectiveness**: 76-88%
- **Perfect use effectiveness**: 95-99%
- **Methods**:
  - Calendar method
  - Basal body temperature method
  - Cervical mucus method
  - Symptothermal method
- **Risks**:
  - Unreliable with irregular menstrual cycles
  - Requires meticulous record-keeping
  - Ovulation timing may be irregular
  - Does not prevent STDs
- **Not recommended**: High failure rate

**Sterilization**:
- **Effectiveness**: 99%+
- **Types**:
  - Vasectomy (male)
  - Tubal ligation (female)
- **Advantages**:
  - Permanent contraception
  - Highly effective
  - No hormonal effects
- **Disadvantages**:
  - Generally irreversible
  - Requires surgery
  - Post-operative recovery period
  - Does not prevent STDs

#### 3.2 Effectiveness Evaluation

**Contraceptive Failure Rate Analysis**:
- Pearl Index (failures per 100 woman-years)
- Typical use vs perfect use discrepancy
- Usage error analysis
- Failure cause tracking

**Satisfaction Scoring**:
- Ease of use (1-10)
- Comfort (1-10)
- Impact on sexual experience (1-10)
- Side effect tolerability (1-10)
- Overall satisfaction (1-10)

#### 3.3 Side Effect Tracking

**Hormonal Side Effects**:
- Menstrual pattern changes
- Mood swings
- Libido changes
- Weight changes
- Breast tenderness

**Non-Hormonal Side Effects**:
- Pain or discomfort (IUD)
- Allergic reactions (condoms)
- Scar formation (implant, sterilization)

**Serious Side Effects**:
- Thromboembolic risk (hormonal methods)
- Ectopic pregnancy risk (upon IUD failure)
- Infection risk (IUD insertion)

#### 3.4 Switching History

**Switching Reason Analysis**:
- Intolerable side effects
- Unsatisfactory effectiveness
- Lifestyle changes
- Health status changes
- Financial reasons
- Partner preferences

**Switching Recommendations**:
- Selection based on side effect history
- Consider age and reproductive plans
- Assess health risk factors
- Partner discussion

### 4. Sexual Activity Log

#### 4.1 Recorded Content

**Basic Information**:
- Date and time
- Activity type (intercourse, oral sex, manual stimulation, etc.)
- Duration
- Partner type (steady, new partner, etc.)

**Protective Measures**:
- Contraceptive method (condom, oral contraceptive pill, etc.)
- Whether correctly used
- Whether it broke or failed

**Subjective Experience**:
- Satisfaction rating (1-10)
- Libido level (1-10)
- Pain or discomfort (yes/no, severity)
- Whether orgasm was achieved

**Special Circumstances**:
- Unusual symptoms
- Contraceptive failure
- Unexpected situations
- Notes

#### 4.2 Privacy Protection

**Data Labeling**:
- Sensitive data tagging
- Encryption recommendations
- Access permission settings
- Data anonymization options

**User Control**:
- Optional feature, entirely user-directed
- Records can be deleted at any time
- Selective data export available
- Selective disclosure during medical consultations

#### 4.3 Statistical Analysis

**Frequency Statistics**:
- Weekly/monthly/annual sexual activity count
- Frequency change trends
- Comparison with age/relationship stage norms

**Satisfaction Analysis**:
- Average satisfaction score
- Satisfaction trend changes
- Factor analysis influencing satisfaction
- Correlation with IIEF-5/FSFI scores

**Protective Measure Statistics**:
- Protection usage rate
- Usage frequency by contraceptive method
- Contraceptive failure count and causes
- Relationship between protective measures and satisfaction

**Pattern Recognition**:
- Sexual activity timing patterns
- Relationship with menstrual cycle (females)
- Correlation with mood/stress
- Correlation with medication use

### 5. Cross-Module Correlation Analysis

#### 5.1 Correlation with Medication Module

**PDE5 Inhibitor Effectiveness Tracking**:
- Drug name and dosage
- Frequency and timing of use
- Effectiveness score (1-10)
- Side effect records
- Effectiveness changes over time
- Correlation with IIEF-5 scores
- Cost-benefit analysis

**Antidepressant Impact on Sexual Function**:
- Drug class (SSRIs, SNRIs, TCAs, etc.)
- Types of sexual function side effects
- Severity assessment
- Time of onset (early treatment/long-term)
- Relationship with libido, erection, and orgasm
- Medication switching or augmentation recommendations

**Antihypertensive Impact on Sexual Function**:
- Drug class (beta-blockers, thiazides, etc.)
- ED incidence
- Libido impact
- Alternative medication recommendations

**Hormonal Medications**:
- Testosterone replacement therapy
- Estrogen/progestin
- Sexual function impact
- Dosage adjustment recommendations

**Other Medications**:
- Antipsychotics
- Antihistamines
- Chemotherapy agents
- Impact on sexual function

#### 5.2 Correlation with Chronic Disease Module

**Diabetes and ED**:
- **Pathological Mechanisms**:
  - Vascular endothelial damage
  - Neuropathy
  - Hormonal abnormalities
- **Blood Glucose Control and ED Relationship**:
  - HbA1c <7%: Lower ED risk
  - HbA1c 7-9%: Moderate risk
  - HbA1c >9%: High risk
- **Diabetes Duration and ED**:
  - <5 years: 2-fold increased ED risk
  - 5-10 years: 3-fold increased ED risk
  - >10 years: 4-5-fold increased ED risk
- **Management Recommendations**:
  - Strict blood glucose control
  - Regular ED screening
  - Early intervention
  - Comprehensive management (blood pressure, lipids)

**Hypertension and Sexual Function**:
- **Pathological Mechanisms**:
  - Vascular damage
  - Endothelial dysfunction
- **Antihypertensive Effects**:
  - Beta-blockers: increase ED risk
  - Thiazide diuretics: may cause ED
  - ACE inhibitors/ARBs: neutral or beneficial
  - Calcium channel blockers: neutral
- **Management Recommendations**:
  - Control blood pressure to target levels
  - Choose medications with minimal sexual function impact
  - Regular sexual function assessment

**Cardiovascular Disease and Sexual Function**:
- **ED as an Early Warning Sign**:
  - ED may precede angina symptoms by 2-3 years
  - ED is an independent predictor of cardiovascular disease
  - Cardiovascular evaluation recommended for ED patients
- **Sexual Activity Safety Assessment**:
  - Cardiac functional classification assessment
  - Exercise tolerance evaluation
  - Medication considerations (nitrates are contraindicated with PDE5 inhibitors)
- **Post-Myocardial Infarction Sexual Activity Guidance**:
  - Can typically resume after 2-4 weeks
  - Gradually increase intensity
  - Monitor symptoms

**Obesity and Sexual Function**:
- **Impact Mechanisms**:
  - Hormonal changes (decreased testosterone, increased estrogen)
  - Vascular endothelial dysfunction
  - Psychological factors (body image)
- **Weight Loss Benefits**:
  - 5-10% weight loss can produce significant improvement
  - Average IIEF-5 score improvement of 3-5 points after weight loss
  - Combined exercise and diet yields best results

#### 5.3 Correlation with Mental Health Module

**Anxiety and Sexual Function**:
- **Performance Anxiety**:
  - Worrying about sexual performance
  - Fear of not satisfying partner
  - Leading to erectile difficulty or premature ejaculation
- **Generalized Anxiety**:
  - Decreased libido
  - Difficulty relaxing and enjoying
  - Distraction and inability to focus
- **Interventions**:
  - Cognitive behavioral therapy
  - Relaxation training
  - Sensate focus exercises

**Depression and Sexual Function**:
- **Depressive Symptoms and Libido**:
  - Loss of libido is a common symptom
  - Significant decline in sexual interest
  - May be one of the earliest presenting symptoms
- **Dual Impact of Antidepressants**:
  - Improving depression may restore libido
  - But the medication itself may cause sexual dysfunction
- **Management Strategies**:
  - Choose antidepressants with less sexual function impact (bupropion)
  - Augmentation agents (e.g., buspirone)
  - Dosage adjustment
  - Psychotherapy

**Post-Traumatic Stress Disorder (PTSD)**:
- Sexual avoidance
- Arousal difficulty
- Flashback interference
- Requires specialized trauma therapy

**Body Image**:
- Dissatisfaction with one's body
- Affects sexual confidence
- Leads to avoidance of intimate relationships
- Body positivity training

**Partner Relationship**:
- Relationship quality is highly correlated with sexual satisfaction
- Communication issues affect sexual fulfillment
- Unresolved conflicts impact libido
- Couples therapy may be beneficial

#### 5.4 Correlation with Nutrition Module

**Key Nutrients**:

**Zinc**:
- **Function**: Essential element for testosterone synthesis
- **Deficiency manifestations**: Decreased libido, ED
- **Recommended intake**: 11 mg/day for men
- **Food sources**: Oysters, beef, pumpkin seeds, cashews
- **Supplementation**: 15-30 mg/day if deficient

**L-Arginine**:
- **Function**: Promotes nitric oxide production, improves blood flow
- **Potential ED benefits**: May mildly improve erectile function
- **Recommended dosage**: 3-5 g/day
- **Food sources**: Nuts, seeds, meat, fish
- **Precautions**: May interact with certain medications

**Vitamin D**:
- **Function**: Supports testosterone synthesis
- **Deficiency manifestations**: Low vitamin D levels associated with ED
- **Target level**: Serum 25(OH)D >30 ng/mL
- **Supplementation**: 1000-2000 IU/day if deficient

**Magnesium**:
- **Function**: Supports testosterone synthesis, improves blood flow
- **Recommended intake**: 400-420 mg/day for men
- **Food sources**: Leafy green vegetables, nuts, whole grains
- **Supplementation**: 200-400 mg/day if deficient

**Omega-3 Fatty Acids**:
- **Function**: Improves cardiovascular health, indirectly improves sexual function
- **Recommended intake**: 1-2 g EPA+DHA/day
- **Food sources**: Deep-sea fish, flaxseeds, walnuts

**Antioxidants**:
- **Function**: Protects vascular endothelium
- **Important antioxidants**: Vitamin C, Vitamin E, selenium, lycopene
- **Food sources**: Fruits, vegetables, nuts

**Dietary Patterns**:

**Mediterranean Diet**:
- **Characteristics**: High in fruits, vegetables, whole grains, olive oil, fish
- **Research evidence**: Improves ED, reduces cardiovascular risk
- **Mechanism**: Improves vascular health, reduces inflammation

**Dietary Restrictions**:
- **Saturated fat**: Reduce red meat and full-fat dairy
- **Trans fat**: Avoid processed foods
- **Added sugars**: Control sugar intake, especially for diabetic patients
- **Alcohol**: <2 drinks/day for men

**Nutritional Status Assessment**:
- Evaluate nutrient deficiencies
- Provide personalized nutritional recommendations
- Recommend supplements (if needed)
- Monitor nutritional improvement outcomes

#### 5.5 Correlation with Exercise Module

**Aerobic Exercise**:
- **Types**: Brisk walking, running, swimming, cycling
- **Recommended amount**: 150 minutes of moderate intensity per week
- **ED Benefits**:
  - Improves cardiovascular health
  - Enhances blood flow
  - Reduces ED risk by approximately 40%
  - Average IIEF-5 score improvement of 2-4 points
- **Mechanisms**:
  - Improves endothelial function
  - Increases nitric oxide bioavailability
  - Lowers blood pressure and blood glucose

**Strength Training**:
- **Types**: Weight training, resistance training
- **Recommended amount**: 2-3 times per week
- **Sexual Function Benefits**:
  - Increases testosterone levels
  - Enhances muscular strength and endurance
  - Improves body image and confidence
- **Precautions**:
  - Avoid overtraining
  - Allow adequate recovery

**Pelvic Floor Exercises (Kegel Exercises)**:
- **Functions**:
  - Strengthens erection firmness and maintenance
  - Improves ejaculatory control
  - Beneficial for both ED and premature ejaculation
- **Method**:
  - Contract pelvic floor muscles (as if stopping urination)
  - Hold for 5 seconds, relax for 5 seconds
  - 3 sets daily, 10-15 repetitions per set
- **Results**:
  - Significant improvement after 6-12 weeks
  - Average IIEF-5 score improvement of 3-5 points

**Yoga**:
- **Benefits**:
  - Improves body image and sexual confidence
  - Enhances flexibility and body awareness
  - Reduces stress and anxiety
  - Certain poses strengthen pelvic floor muscles
- **Recommendations**:
  - 2-3 times per week
  - Combine with meditation and breathing exercises

**Exercise and Libido**:
- Moderate exercise increases libido
- Excessive exercise may decrease libido (Female Athlete Triad)
- Finding the right balance is key

**Exercise Prescription**:
- Based on age, health status, and interests
- Progressive increase in intensity
- Combine aerobic, strength, and flexibility training
- Pelvic floor training as a supplement

### 6. Risk Assessment

#### 6.1 ED Risk Score

**Weighted Risk Factors**:

| Risk Factor | Weight | Score |
|-------------|--------|-------|
| Age | 15% | <40: 0, 40-49: 1, 50-59: 2, 60+: 3 |
| Diabetes | 20% | None: 0, Controlled: 1, Uncontrolled: 3 |
| Cardiovascular disease | 15% | None: 0, Stable: 1, Unstable: 3 |
| Hypertension | 10% | None: 0, Controlled: 1, Uncontrolled: 2 |
| Smoking | 10% | Never: 0, Former: 1, Current: 2 |
| Excessive alcohol | 5% | None: 0, Occasional: 1, Frequent: 2 |
| Obesity | 10% | BMI <25: 0, 25-30: 1, >30: 2 |
| Sedentary lifestyle | 5% | Regular exercise: 0, Occasional: 1, Sedentary: 2 |
| Stress/Anxiety | 5% | None: 0, Mild: 1, Moderate-Severe: 2 |
| Medication side effects | 5% | None: 0, Mild: 1, Significant: 2 |

**Risk Levels**:
- **Low risk** (0-20 points): Low ED probability
- **Moderate risk** (21-40 points): Increased ED risk
- **High risk** (41-60 points): ED highly likely
- **Very high risk** (>60 points): ED almost certain

#### 6.2 STD Risk Score

**Behavioral Factors**:

| Risk Factor | Score |
|-------------|-------|
| Number of sexual partners | Single: 0, 2-3: 5, 4-10: 15, >10: 30 |
| Protective measure use | Always: 0, Usually: 5, Sometimes: 15, Never: 30 |
| Partner type | Steady: 0, New/casual: 10, Sex worker: 30 |
| MSM | No: 0, Yes: 20 |
| Known infected partner | No: 0, Yes: 50 |
| Injection drug use | No: 0, Yes: 30 |
| Prior STD history | None: 0, 1 occurrence: 10, >1 occurrence: 20 |

**Risk Levels**:
- **Low risk** (0-10 points): Low STD probability
- **Moderate risk** (11-30 points): Increased STD risk
- **High risk** (31-50 points): STD highly likely
- **Very high risk** (>50 points): Immediate screening needed

### 7. Personalized Recommendations

#### 7.1 Recommendations Based on IIEF-5 Score

**Normal (22-25 points)**:
- Maintain healthy lifestyle
- Periodic reassessment (annually)
- Preventive measures

**Mild ED (17-21 points)**:
- Prioritize lifestyle interventions
- Stress management
- Limit alcohol and quit smoking
- Reassess in 3-6 months

**Mild-Moderate ED (12-16 points)**:
- Lifestyle interventions
- Consider PDE5 inhibitors
- Psychological factor assessment
- Medical consultation recommended

**Moderate ED (8-11 points)**:
- Active medical intervention
- PDE5 inhibitors
- Consider alternative treatment options
- Psychological counseling

**Severe ED (5-7 points)**:
- Comprehensive medical evaluation
- Multidisciplinary treatment
- Specialist referral may be needed
- Partner involvement

#### 7.2 Recommendations Based on Risk Assessment

**High ED Risk**:
- Regular screening (every 3-6 months)
- Active control of risk factors
- Preventive intervention
- Early treatment

**High STD Risk**:
- Frequent screening (every 3 months)
- Consider PrEP (Pre-Exposure Prophylaxis)
- Vaccination (HPV, Hepatitis B)
- Risk reduction counseling

#### 7.3 Lifestyle Prescriptions

**Exercise Prescription**:
- Aerobic exercise: 150 minutes per week
- Strength training: 2-3 times per week
- Pelvic floor exercises: daily
- Flexibility training: 2-3 times per week

**Dietary Prescription**:
- Mediterranean dietary pattern
- Increase fruits and vegetables to 5-9 servings/day
- Replace refined grains with whole grains
- Deep-sea fish twice per week
- Limit processed foods and added sugars

**Behavioral Prescription**:
- Smoking cessation plan
- Alcohol limitation: <2 drinks/day for men
- Sleep improvement: 7-9 hours/day
- Stress management: daily relaxation practice
- Weight management: BMI 18.5-24.9

### 8. Alert System

#### 8.1 Routine Check-Up Reminders

**IIEF-5 Assessment**:
- Normal: annually
- Mild ED: every 6 months
- Moderate or above: every 3-6 months

**STD Screening**:
- Personalized schedule based on risk level
- High risk: every 3 months
- Average risk: annually
- Low risk: every 1-2 years

**Sexual Health Check-Up**:
- Under 40: every 1-2 years
- Over 40: annually
- Patients with chronic conditions: annually

#### 8.2 Problem Alerts

**IIEF-5 Score Decline**:
- Score drops >3 points across 2 consecutive assessments
- Score drops >5 points within one month
- ED severity level escalation

**High-Risk STD Behavior**:
- Increase in unprotected sexual activity
- Increase in number of sexual partners
- Known exposure without subsequent screening

**Contraceptive Failure**:
- Condom breakage >2 times/month
- Missed contraceptive pills >2 times/month
- IUD malposition

#### 8.3 Trend Alerts

**Significant Libido Decline**:
- Persisting >3 months
- Affecting quality of life
- Impacting partner relationship

**Persistent Satisfaction Decline**:
- Average satisfaction <5 points
- Sustained downward trend
- Professional evaluation needed

## Use Cases

### Use Case 1: Routine Sexual Health Assessment

**User Request**: Analyze my sexual health status over the past 6 months

**Analysis Workflow**:
1. Read all sexual health records from the past 6 months
2. Analyze IIEF-5 score trends
3. Review STD screening history
4. Assess contraceptive method effectiveness
5. Analyze medication effects
6. Evaluate lifestyle factors

**Output**:
- IIEF-5 score change curve
- ED severity changes
- Key risk factors
- Improvement recommendations
- Next check-up date

### Use Case 2: ED Diagnostic Assistance

**User Request**: I've been having erection difficulties recently; IIEF-5 score is 15. What could be causing this?

**Analysis Workflow**:
1. Retrieve recent IIEF-5 score history
2. Analyze medication records
3. Assess chronic disease control status
4. Review mental health records
5. Analyze lifestyle factors
6. Identify primary causes

**Output**:
- ED severity: mild-moderate
- Key risk factors (e.g., poorly controlled diabetes)
- Modifiable factors (e.g., smoking, sedentary lifestyle)
- Medication impact analysis
- Personalized improvement plan

### Use Case 3: Contraceptive Method Selection

**User Request**: I want to switch contraceptive methods; my current oral contraceptive pill has side effects

**Analysis Workflow**:
1. Assess current contraceptive method satisfaction and side effects
2. Analyze health history and risk factors
3. Consider age and reproductive plans
4. Compare advantages and disadvantages of various methods
5. Identify suitable alternatives

**Output**:
- Current method problem analysis
- Suitable alternatives
- Comparative advantages and disadvantages of each option
- Recommended option with rationale
- Switching timeline recommendations

### Use Case 4: STD Risk Assessment

**User Request**: I have a new partner recently. Do I need STD screening?

**Analysis Workflow**:
1. Assess sexual behavior patterns
2. Identify risk factors
3. Calculate risk score
4. Determine required screening tests
5. Establish screening schedule

**Output**:
- Current risk level
- Recommended screening tests
- Screening timeline recommendations
- Risk reduction measures
- Follow-up plan

### Use Case 5: Multidisciplinary Joint Analysis

**User Request**: I have diabetes. How does this affect my sexual function?

**Analysis Workflow**:
1. Read diabetes management data
2. Analyze blood glucose control status
3. Assess sexual function status
4. Analyze correlation between the two
5. Evaluate complication risks
6. Generate joint management recommendations

**Output**:
- Mechanism of diabetes impact on sexual function
- Current blood glucose control and ED risk
- Comprehensive management strategy
- Recommended monitoring indicators
- Lifestyle intervention priorities

## Data Analysis Methods

### Quantitative Analysis
- Descriptive statistics (mean, median, standard deviation)
- Trend analysis (linear regression, moving average)
- Correlation analysis (Pearson/Spearman correlation)
- Risk score calculation (multifactor weighting)

### Qualitative Analysis
- Textual description analysis
- Symptom pattern recognition
- Chief complaint classification
- Satisfaction assessment

### Visualization Output
- IIEF-5 score time-series chart
- ED severity change chart
- STD screening history timeline
- Contraceptive method effectiveness comparison
- Sexual activity frequency statistics chart
- Risk factor radar chart

## Quality Assurance

### Data Validation
- Check data completeness
- Verify data consistency
- Identify outliers
- Handle missing data

### Result Validation
- Medical logic checks
- Comparison with clinical guidelines
- Expert review (if available)
- User feedback collection

### Continuous Improvement
- Regular updates to analysis algorithms
- Incorporation of new scientific evidence
- User experience optimization
- Feature scope expansion

## References

### Clinical Guidelines
- WHO Sexual Health Guidelines
- EAU (European Association of Urology) ED Guidelines
- AUA (American Urological Association) Sexual Dysfunction Guidelines
- CDC STD Screening and Treatment Guidelines
- Chinese Medical Association Andrology Guidelines

### Assessment Tools
- IIEF-5 (International Index of Erectile Function-5)
- FSFI (Female Sexual Function Index)
- SHEF (Sexual Health Evaluation Framework)

### Data Sources
- User-recorded data
- Medication module data
- Chronic disease module data
- Mental health module data
- Nutrition module data
- Exercise module data

## Limitations

### System Limitations
- Cannot replace professional medical examinations
- Cannot perform laboratory tests
- Cannot perform physical examinations
- Analysis results are affected by data quality

### Data Limitations
- Relies on user recording accuracy
- Records may be incomplete
- Subjective assessments may contain bias
- Time span may be insufficient

### Recommendation Limitations
- Cannot account for all individual factors
- Cannot predict all complications
- Must be combined with clinical judgment
- Cannot guarantee 100% accuracy

## Future Enhancements

### Planned Features
- AI-assisted diagnosis
- Personalized treatment plan generation
- Partner health correlation analysis
- Reproductive health tracking (fertility planning)
- Sexual education module

### Research Directions
- Machine learning predictive models
- Genetic risk analysis
- Personalized prevention strategies
- Telemedicine integration
