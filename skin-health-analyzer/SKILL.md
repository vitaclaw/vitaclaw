---
name: skin-health-analyzer
description: "Analyzes skin health data, identifies dermatological problem patterns, assesses skin health status, and provides personalized skincare recommendations. Supports correlation analysis with nutrition, chronic disease, and medication data. Use when the user wants to evaluate their skin health, track moles, or optimize their skincare routine."
version: 1.0.0
user-invocable: true
argument-hint: "[checkup-review | mole-monitor | acne-plan | sunscreen-plan | cross-module-analysis]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🧴","category":"health-analyzer"}}
---

# Skin Health Analysis Skill

## Skill Overview

This skill provides comprehensive skin health data analysis, including trend identification, risk assessment, problem diagnosis, and personalized recommendation generation. Special emphasis is placed on mole monitoring and skin cancer prevention.

## Medical Disclaimer

WARNING: The data analysis and recommendations provided by this skill are for reference only and do not constitute medical diagnosis or treatment advice.

- All skin issues should be diagnosed and treated by a professional dermatologist
- Abnormal changes in moles must be examined by a physician immediately
- Skin cancer requires professional diagnosis and cannot rely solely on self-assessment
- Analysis results cannot replace professional dermatological examinations
- Seek immediate medical attention for emergencies
- Follow the professional advice of your dermatologist

## Core Features

### 1. Trend Analysis

#### Skin Problem Development Trends
- Identify occurrence patterns for acne, eczema, and other conditions
- Analyze seasonal and cyclical patterns
- Assess changes in problem severity
- Predict future flare-up risk

**Output:**
- Problem occurrence frequency curve
- Severity change trends
- Trigger factor analysis
- Prevention recommendations

#### Mole Change Monitoring
- Track new mole locations and counts
- Monitor size changes in existing moles
- Record ABCDE feature changes
- Identify high-risk moles

**Output:**
- Mole distribution map
- Change alert report
- List of moles requiring attention
- Medical visit recommendations

#### Skincare Effectiveness Evaluation
- Skincare routine frequency analysis
- Product effectiveness evaluation
- Skin condition improvement tracking
- Adverse reaction monitoring

**Output:**
- Skincare effectiveness score
- Product recommendations
- Routine optimization suggestions
- Cost-benefit analysis

#### Sun Protection Effectiveness Analysis
- Sunscreen usage statistics
- Sunburn occurrence frequency
- Photoaging sign assessment
- Sun protection habit improvement suggestions

**Output:**
- Protection score trends
- Risk assessment
- Improvement recommendations
- Product recommendations

### 2. Risk Assessment

#### Skin Cancer Risk Assessment
Comprehensive assessment based on the following factors:
- Skin type (Fitzpatrick classification)
- Sun exposure history
- Mole count and characteristics
- Sunburn history
- Family history
- Tanning bed use history

**Risk Levels:**
- **Low Risk**: Dark skin, minimal sun exposure, no abnormal moles
- **Medium Risk**: Light skin, moderate sun exposure, abnormal moles present
- **High Risk**: Light skin, extensive sun exposure, multiple abnormal moles, family history

**Output:**
- Risk level (Low/Medium/High)
- Main risk factors
- Quantitative risk score
- Risk reduction strategies
- Screening recommendations

#### Acne Severity Assessment
Comprehensive assessment based on the following factors:
- Acne types (blackheads, whiteheads, inflammatory papules, nodules, cysts)
- Lesion count and distribution
- Degree of inflammation
- Scarring risk

**Severity Classification:**
- **Mild**: Primarily blackheads and whiteheads, few inflammatory lesions
- **Moderate**: More inflammatory lesions, possible mild scarring
- **Severe**: Nodules and cysts, high scarring risk

**Output:**
- Severity classification
- Main trigger analysis
- Treatment reference recommendations
- Skincare recommendations
- Medical visit recommendations

#### Allergy Risk Identification
Comprehensive assessment based on the following factors:
- Known allergens
- Skin sensitivity history
- Product use history
- Seasonal allergy patterns
- Family allergy history

**Output:**
- Allergen list
- Risk assessment
- Avoidance recommendations
- Alternative product suggestions

#### Photoaging Risk Prediction
Comprehensive assessment based on the following factors:
- Total sun exposure
- Protection habits
- Skin type
- Age
- Lifestyle

**Output:**
- Photoaging risk level
- Current photoaging signs
- Prevention recommendations
- Treatment options reference

### 3. Correlation Analysis

#### Correlation with Nutrition Module
**Nutrient Impact on Skin Health:**
- Vitamin A: Skin cell renewal, vision
- Vitamin C: Collagen synthesis, antioxidant
- Vitamin E: Antioxidant, cell membrane protection
- Omega-3 fatty acids: Anti-inflammatory effect
- Zinc: Wound healing, oil control
- Water: Skin hydration

**Food Impact on Skin Problems:**
- High-sugar foods: Acne aggravation
- Dairy products: Acne trigger factor in some populations
- Spicy foods: Rosacea aggravation
- Alcohol: Skin dehydration, flushing

**Skin Manifestations of Nutritional Deficiencies:**
- Vitamin A deficiency: Dry skin, keratinization
- Vitamin C deficiency: Slow wound healing, easy bruising
- Vitamin B deficiency: Dermatitis, angular cheilitis
- Iron deficiency: Pallor, fragility
- Protein deficiency: Skin laxity, edema

**Output:**
- Nutritional status assessment
- Deficiency risk identification
- Dietary adjustment recommendations
- Supplement recommendations (if needed)

#### Correlation with Chronic Disease Module
**Diabetes and Skin:**
- Diabetic skin conditions (diabetic dermopathy)
- Delayed wound healing
- Increased fungal infection risk
- Acanthosis nigricans
- Necrobiosis lipoidica

**Autoimmune Diseases and Skin:**
- Lupus: Butterfly rash, photosensitivity
- Rheumatoid arthritis: Rheumatoid nodules, vasculitis
- Psoriatic arthritis: Psoriatic skin lesions
- Dermatomyositis: Gottron papules, heliotrope rash

**Thyroid Disease and Skin:**
- Hyperthyroidism: Moist skin, hair thinning, nail loosening
- Hypothyroidism: Dry skin, coarse hair, edema

**Liver Disease and Skin:**
- Jaundice: Skin and scleral yellowing
- Spider angiomas: Vascular spider-like lesions
- Palmar erythema: Palm redness
- Pruritus: Cholestasis

**Output:**
- Skin symptom and disease correlation analysis
- Complication risk assessment
- Comprehensive management recommendations
- Specialist referral recommendations

#### Correlation with Medication Module
**Drug Rash (Drug Allergy):**
- Common sensitizing drugs: Antibiotics, antiepileptics, NSAIDs
- Rash types: Morbilliform, urticarial, fixed drug eruption
- Severe reactions: Stevens-Johnson Syndrome

**Photosensitizing Drugs:**
- Tetracycline antibiotics
- Thiazide diuretics
- NSAIDs
- Certain antipsychotics

**Drug-Induced Pigmentation:**
- Minocycline: Blue-gray pigmentation
- Amiodarone: Blue-gray pigmentation
- Certain chemotherapy drugs

**Drug-Induced Skin Dryness:**
- Retinoids
- Benzodiazepines
- Antihistamines (long-term use)

**Output:**
- Drug risk identification
- Interaction analysis
- Alternative drug recommendations (discuss with physician)
- Monitoring recommendations

#### Correlation with Endocrine Module
**Hormonal Changes and Skin Impact:**
- Puberty: Androgen increase, acne
- Pregnancy: Pigmentation, stretch marks, skin vascular changes
- Menopause: Estrogen decline, dry skin, wrinkles
- Menstrual cycle: Cyclic acne aggravation

**Polycystic Ovary Syndrome (PCOS):**
- Acne
- Hirsutism
- Androgenetic alopecia
- Acanthosis nigricans

**Cushing's Syndrome:**
- Moon face, buffalo hump
- Skin thinning, purple striae
- Acne, hirsutism

**Output:**
- Hormonal impact on skin analysis
- Cyclic symptom identification
- Management recommendations
- Treatment timing recommendations

### 4. Personalized Recommendations

#### Skincare Routine Optimization
**Customized by Skin Type:**
- Dry skin: Enhance moisturizing, avoid over-cleansing
- Oily skin: Oil control, maintain cleanliness, oil-water balance
- Combination skin: Zone-specific care, T-zone oil control, U-zone moisturizing
- Normal skin: Maintain status, basic care
- Sensitive skin: Gentle products, avoid irritants

**Customized by Main Concern:**
- Acne: Cleansing, oil control, anti-inflammatory, avoid comedogenic ingredients
- Hyperpigmentation: Sun protection, brightening ingredients, antioxidants
- Anti-aging: Antioxidants, repair, sun protection
- Sensitivity: Soothing, repair, barrier protection

**Output:**
- Morning skincare routine recommendations
- Evening skincare routine recommendations
- Weekly treatment recommendations
- Product selection guidance
- Budget range suggestions

#### Lifestyle Adjustments
**Dietary Adjustments:**
- Low glycemic index diet (acne)
- Anti-inflammatory diet (eczema, psoriasis)
- Antioxidant-rich foods (anti-aging)
- Adequate water intake

**Sleep Management:**
- Ensure 7-9 hours of sleep
- Regular sleep schedule
- Pre-bedtime skincare routine
- Pillow cleanliness (acne)

**Stress Management:**
- Identify stress-triggered skin problems
- Learn relaxation techniques
- Regular exercise
- Engage in hobbies

**Environmental Adjustments:**
- Indoor humidity control (dry skin)
- Allergen avoidance (allergic skin)
- Workplace protection (occupational skin problems)

**Output:**
- Personalized lifestyle recommendations
- Goal setting
- Progress tracking methods
- Motivation mechanisms

#### Prevention Recommendations
**Skin Cancer Prevention:**
- Daily sunscreen (SPF 30+)
- Avoid tanning beds
- Regular skin examinations
- Protect children from sun exposure
- Early detection of abnormal moles

**Acne Prevention:**
- Proper skin cleansing
- Avoid touching the face
- Clean phone and glasses
- Pillowcase change frequency
- Non-comedogenic cosmetics

**Eczema Prevention:**
- Keep skin moisturized
- Avoid known triggers
- Use gentle detergents
- Wear cotton clothing
- Control indoor temperature and humidity

**Photoaging Prevention:**
- Year-round sun protection
- Antioxidant skincare products
- No smoking
- Adequate sleep
- Healthy diet

**Output:**
- Targeted prevention strategies
- Priority ranking
- Implementation steps
- Effectiveness evaluation methods

#### Product Selection Guidance
**Ingredient Knowledge:**
- Acne treatment: Salicylic acid, benzoyl peroxide, retinoids
- Brightening: Vitamin C, niacinamide, arbutin
- Anti-aging: Retinol, peptides, hyaluronic acid
- Moisturizing: Hyaluronic acid, glycerin, ceramides
- Soothing: Aloe vera, centella asiatica, oat

**Product Selection Principles:**
- Choose based on skin type
- Avoid known allergens
- Simple formulations over complex ones
- Fragrance-free formulas are safer
- Try small sizes first

**Reading Product Labels:**
- Identify comedogenic ingredients
- Identify allergens
- Understand active ingredient concentrations
- Understand product efficacy claims

**Output:**
- Ingredient education
- Product recommendation framework (not specific brands)
- Ingredients-to-avoid list
- Product trial recommendations

### 5. Goal Management

#### Goal Setting
- Collaborate with users to set realistic goals
- Break down into achievable steps
- Set milestones
- Establish evaluation criteria

**Common Goal Types:**
- Improve acne condition
- Establish regular skincare habits
- Increase sunscreen usage frequency
- Reduce hyperpigmentation
- Improve skin dryness
- Establish regular self-examination habits

#### Progress Tracking
- Regularly evaluate goal achievement
- Provide motivation and feedback
- Adjust goals (if needed)
- Celebrate milestone achievements
- Document improvement process

#### Barrier Identification
- Identify factors hindering goal achievement
- Provide strategies to overcome barriers
- Adjust plans to fit real-world situations
- Provide ongoing support
- Connect to resources and support networks

### 6. Statistical Analysis

#### Comprehensive Health Score
Calculated based on the following factors:
- Skin problem control status (30%)
- Skincare habits (25%)
- Sun protection (20%)
- Regular checkups (15%)
- Goal achievement (10%)

**Score Range:** 0-100 points
- **Excellent**: 90-100 points
- **Good**: 75-89 points
- **Fair**: 60-74 points
- **Poor**: <60 points

#### Skin Health Age
- Calculated based on skin condition, problem status, and protection habits
- Compared with actual age
- Improvement recommendations provided

#### Problem Statistics
- Problem type distribution
- Problem occurrence frequency
- Problem duration
- Resolution rate statistics
- Recurrence rate analysis

#### Skincare Statistics
- Skincare routine adherence rate
- Product usage frequency
- Skincare expenditure statistics
- Product turnover frequency
- Adverse reaction statistics

### 7. Alert System

#### Mole Change Alerts
- Abnormal increase in new mole count
- Rapid growth of existing moles
- ABCDE feature abnormalities
- Color or morphology changes
- Symptom onset (itching, bleeding)

**Alert Levels:**
- **Yellow Alert**: Needs observation; consult physician at next checkup
- **Orange Alert**: Needs prompt medical attention (within 1 week)
- **Red Alert**: Needs immediate medical attention

#### Skin Problem Alerts
- Sudden acne worsening
- New onset severe rash
- Signs of drug reaction
- Signs of infection (redness, swelling, heat, pain)
- Skin manifestations of chronic disease

#### Skincare Alerts
- Product adverse reactions
- Improper skincare routine
- Signs of over-treatment
- Use of expired products
- Product interactions

#### Examination Reminders
- Regular skin self-examination reminders (monthly)
- Dermatology checkup reminders (annually)
- Mole monitoring reminders (monthly)
- Sunscreen reapplication reminders

## Usage Scenarios

### Scenario 1: Routine Health Assessment
**User Request:** Analyze my skin health over the past 6 months

**Analysis Workflow:**
1. Read all skin health records from the past 6 months
2. Analyze problem records, mole monitoring, and skincare records
3. Assess changes in protection habits
4. Calculate health score changes
5. Identify improvement or deterioration trends
6. Generate comprehensive assessment report

**Output:**
- Health score change trends
- Key improvements
- Issues requiring attention
- Next steps and recommendations

### Scenario 2: Mole Monitoring Assessment
**User Request:** I noticed a mole on my back has changed; please evaluate it

**Analysis Workflow:**
1. Retrieve historical records for the mole
2. Compare ABCDE feature changes
3. Assess risk level
4. Check for other abnormal moles
5. Analyze personal risk factors
6. Generate assessment report

**Output:**
- ABCDE assessment results
- Degree of change analysis
- Risk level
- Medical visit recommendation (Strongly Recommended/Recommended/Monitor)
- Monitoring frequency recommendations

### Scenario 3: Acne Management Plan
**User Request:** I want to improve my acne; create a management plan

**Analysis Workflow:**
1. Assess current acne severity
2. Analyze main trigger factors
3. Evaluate current skincare and dietary habits
4. Identify areas for improvement
5. Set phased goals
6. Develop personalized plan

**Output:**
- Current severity assessment
- Main trigger analysis
- Skincare routine recommendations
- Dietary and lifestyle recommendations
- Goals and timeline
- When to seek medical advice

### Scenario 4: Sun Protection Improvement Plan
**User Request:** My sunscreen habits are poor; help me create an improvement plan

**Analysis Workflow:**
1. Assess current sun protection habits
2. Analyze sun exposure patterns
3. Evaluate skin type and risk
4. Identify main barriers
5. Set achievable goals
6. Develop a gradual improvement plan

**Output:**
- Current sun protection score
- Risk assessment
- Improvement goals
- Product selection recommendations
- Habit-building strategies
- Progress tracking methods

### Scenario 5: Multidisciplinary Joint Analysis
**User Request:** I have diabetes; how does it affect my skin?

**Analysis Workflow:**
1. Read diabetes management data
2. Analyze blood sugar control status
3. Assess skin complication risk
4. Identify potential diabetic skin problems
5. Analyze correlation between the two
6. Generate joint management recommendations

**Output:**
- Impact of diabetes on skin
- Common diabetic skin problems
- Complication risk assessment
- Joint management strategies
- Monitoring indicator recommendations
- When to seek medical attention

### Scenario 6: Anti-Aging Planning
**User Request:** I want to prevent skin aging; what should I start doing now?

**Analysis Workflow:**
1. Assess current skin condition
2. Analyze lifestyle and habits
3. Evaluate photoaging risk
4. Identify modifiable risk factors
5. Develop prevention strategies
6. Establish monitoring metrics

**Output:**
- Current skin age assessment
- Main aging risk factors
- Prevention strategies (sun protection, skincare, lifestyle)
- Skincare routine recommendations
- Periodic evaluation recommendations
- Cost-benefit analysis

## Data Analysis Methods

### Quantitative Analysis
- Descriptive statistics (mean, median, standard deviation)
- Trend analysis (linear regression, moving average)
- Correlation analysis (Pearson/Spearman correlation)
- Risk score calculation (multi-factor weighting)
- Time series analysis

### Qualitative Analysis
- Text description analysis
- Symptom pattern recognition
- Chief complaint classification
- Satisfaction evaluation
- Photo analysis (if available)

### ABCDE Assessment Algorithm
- Asymmetry score (0-2 points)
- Border regularity score (0-2 points)
- Color uniformity score (0-2 points)
- Diameter score (0-2 points)
- Evolution score (0-2 points)
- Total score >=4: Recommend medical visit

### Visualization Output
- Time series charts
- Body region distribution maps
- Mole location maps
- Risk assessment radar charts
- Progress tracking dashboards
- Comparative analysis bar charts

## Quality Assurance

### Data Validation
- Check data completeness
- Verify data consistency
- Identify outliers
- Handle missing data
- Cross-validate data from different sources

### Result Validation
- Medical logic checks
- Cross-reference with clinical guidelines
- Expert review (if available)
- User feedback collection
- Regular algorithm updates

### Continuous Improvement
- Regularly update analysis algorithms
- Incorporate new scientific evidence
- Optimize user experience
- Expand feature scope
- Improve accuracy

## References

### Clinical Guidelines
- American Academy of Dermatology (AAD) Guidelines
- European Academy of Dermatology and Venereology (EADV) Guidelines
- Chinese Dermatology Society Clinical Guidelines
- Skin Cancer Foundation (SCF) Guidelines

### Assessment Tools
- ABCDE Rule (Melanoma Screening)
- Glasgow 7-Point Checklist (Melanoma Assessment)
- Acne Severity Scoring System
- Eczema Area and Severity Index (EASI)
- Dermatology Life Quality Index (DLQI)

### Data Sources
- User-recorded data
- Nutrition module data
- Chronic disease module data
- Medication module data
- Endocrine module data
- Environmental data (UV index)

## Limitations

### System Limitations
- Cannot replace professional dermatological examinations
- Cannot perform dermoscopy
- Cannot perform pathological examinations
- Analysis results are affected by data quality
- Cannot perform biopsies

### Data Limitations
- Depends on user recording accuracy
- Records may be incomplete
- Subjective assessments may be biased
- Time span may be insufficient
- Photo quality affects assessment

### Recommendation Limitations
- Cannot account for all individual factors
- Cannot predict all complications
- Must be combined with clinical judgment
- Cannot guarantee 100% accuracy
- Product recommendations may vary by individual

## Future Extensions

### Planned Features
- AI image recognition (mole and skin lesion analysis)
- Voice record entry
- Smart reminder system
- Integration with dermatology practice systems
- Teledermatology support

### Research Directions
- Machine learning prediction models
- Personalized prevention strategies
- Genetic risk analysis
- Skin microbiome analysis
- Environmental factor impact analysis
