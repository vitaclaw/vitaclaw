---
name: tcm-constitution-analyzer
description: "Analyzes Traditional Chinese Medicine (TCM) constitution data, identifies constitution types using the standardized nine-constitution framework, assesses constitution characteristics, and provides personalized wellness recommendations. Supports correlation analysis with nutrition, exercise, and sleep data. Use when the user wants a TCM constitution assessment or personalized TCM-based health advice."
version: 1.0.0
user-invocable: true
argument-hint: "[assess | query | trend | recommend | correlate]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏮","category":"health-analyzer"}}
---

# TCM Constitution Analysis Skill

Analyzes Traditional Chinese Medicine constitution data, identifies constitution types, assesses constitution characteristics, and provides personalized wellness improvement recommendations.

## Features

### 1. Constitution Identification Assessment

Constitution identification based on the "Classification and Determination of TCM Constitution Types" standard (per Chinese clinical guidelines).

**Assessment Dimensions:**
- Scoring for 9 constitution types (Balanced, Qi Deficiency, Yang Deficiency, Yin Deficiency, Phlegm-Dampness, Damp-Heat, Blood Stasis, Qi Stagnation, Inherited Special)
- Primary constitution determination
- Combined constitution identification
- Constitution characteristic analysis

**Assessment Method:**
- 60-question standardized questionnaire
- 5-point scale (Never / Rarely / Sometimes / Often / Always)
- Converted score calculation (0-100 points)

**Output:**
- Constitution type determination result
- Individual constitution scores
- Constitution characteristic descriptions
- Personalized wellness recommendations

### 2. Constitution Characteristic Analysis

Comprehensive assessment of user constitution characteristics.

**Analysis Content:**
- **Physical Characteristics:**
  - Body type features
  - Complexion appearance
  - Tongue and pulse signs

- **Psychological Characteristics:**
  - Personality traits
  - Emotional tendencies

- **Disease Susceptibility:**
  - Susceptible diseases
  - Health risks

- **Adaptability:**
  - Environmental adaptation
  - Seasonal adaptation

**Output:**
- Constitution type classification
- Characteristic descriptions
- Risk assessment
- Treatment priority

### 3. Constitution Change Trend Analysis

Track constitution changes and evaluate wellness intervention effectiveness.

**Analysis Content:**
- Multi-assessment comparison
- Score change trends
- Constitution stability analysis
- Treatment effectiveness evaluation

**Output:**
- Trend charts
- Improvement magnitude
- Stability assessment
- Continued treatment recommendations

### 4. Correlation Analysis

Analyze correlations between constitution and other health indicators.

**Supported Correlation Analyses:**
- **Constitution and Nutrition:**
  - Relationship between constitution type and dietary preferences
  - Impact of nutritional status on constitution
  - Personalized dietary recommendations

- **Constitution and Exercise:**
  - Exercise types suitable for different constitutions
  - Effects of exercise on constitution improvement

- **Constitution and Sleep:**
  - Relationship between constitution and sleep quality
  - Impact of sleep on constitution

- **Constitution and Chronic Disease:**
  - Diseases each constitution type is susceptible to
  - Relationship between constitution and disease

**Output:**
- Correlation coefficients
- Correlation strength
- Statistical significance
- Practical recommendations

### 5. Personalized Recommendation Generation

Generate personalized wellness recommendations based on constitution type.

**Recommendation Types:**
- **Dietary Therapy:**
  - Recommended food list
  - Foods to avoid list
  - Suggested recipes
  - Dietary principles

- **Daily Life Regimen:**
  - Schedule recommendations
  - Environmental requirements
  - Lifestyle habits

- **Exercise and Physical Activity:**
  - Recommended exercise types
  - Exercise frequency and intensity
  - Precautions

- **Emotional Regulation:**
  - Mood management
  - Psychological adjustment

- **Acupoint Self-Care:**
  - Recommended acupoints
  - Massage methods
  - Moxibustion recommendations

- **Herbal Medicine Guidance:**
  - Recommended formulas
  - Formula composition
  - Dosage and administration
  - Precautions

**Recommendation Basis:**
- TCM constitution theory
- User constitution type
- Seasonal factors
- User health status

---

## Usage Instructions

### Trigger Conditions

This skill is triggered when the user requests:
- TCM constitution identification assessment
- Constitution type query
- Constitution characteristic analysis
- TCM wellness recommendations
- Constitution trend analysis
- Correlation analysis between constitution and other health indicators

### Execution Steps

#### Step 1: Determine Analysis Scope

Identify the type of analysis the user requests:
- Constitution identification assessment
- Constitution characteristic query
- Wellness recommendation retrieval
- Trend analysis
- Correlation analysis

#### Step 2: Read Data

**Primary Data Sources:**
1. `data/constitutions.json` - Constitution knowledge base
2. `data/constitution-recommendations.json` - Wellness recommendation database
3. `data-example/tcm-constitution-tracker.json` - Constitution tracking main data
4. `data-example/tcm-constitution-logs/YYYY-MM/YYYY-MM-DD.json` - Daily assessment records

**Associated Data Sources:**
1. `data-example/profile.json` - Basic information
2. `data-example/nutrition-tracker.json` - Nutrition data
3. `data-example/fitness-tracker.json` - Exercise data
4. `data-example/sleep-tracker.json` - Sleep data

#### Step 3: Data Analysis

Execute the corresponding analysis algorithm based on the analysis type:

**Constitution Scoring Algorithm:**
```python
def calculate_constitution_scores(answers):
    """
    Based on the "Classification and Determination of TCM Constitution Types" standard
    (per Chinese clinical guidelines).

    Formula:
    Converted Score = [(Raw Score - Number of Questions) / (Number of Questions x 4)] x 100

    Where:
    - Raw Score = Sum of scores for all questions
    - Number of Questions = Number of questions for that constitution type
    """
    scores = {}
    for constitution, questions in CONSTITUTION_QUESTIONS.items():
        original_score = sum(answers[q] for q in questions)
        question_count = len(questions)
        converted_score = ((original_score - question_count) / (question_count * 4)) * 100
        scores[constitution] = round(converted_score, 1)
    return scores
```

**Constitution Determination Algorithm:**
```python
def determine_constitution_type(scores):
    """
    Determination Logic:
    1. Balanced Constitution determination:
       - Score >= 60
       - All other 8 constitution type scores < 40

    2. Imbalanced Constitution determination:
       - The constitution with the highest score is the result

    3. Combined Constitution determination:
       - If the second-highest constitution score >= 40
       - It is classified as a combined constitution
    """
    balanced_score = scores['Balanced']
    other_scores = {k: v for k, v in scores.items() if k != 'Balanced'}

    # Determine if Balanced Constitution
    if balanced_score >= 60 and all(s < 40 for s in other_scores.values()):
        return {
            'primary': 'Balanced',
            'secondary': [],
            'type': 'balanced'
        }

    # Imbalanced Constitution determination
    sorted_scores = sorted(other_scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_scores[0][0]

    # Determine Combined Constitution
    secondary = [k for k, v in sorted_scores[1:3] if v >= 40]

    return {
        'primary': primary,
        'secondary': secondary,
        'type': 'compound' if secondary else 'single'
    }
```

**Trend Analysis Algorithm:**
- Linear regression for trend calculation
- Moving average for fluctuation smoothing
- Statistical significance testing

#### Step 4: Generate Report

Output the analysis report in standard format (see "Output Format" section).

---

## Output Format

### Constitution Identification Assessment Report

```markdown
# TCM Constitution Identification Assessment Report

## Assessment Date
2025-06-20

## Assessment Results

### Constitution Type Determination
- **Primary Constitution**: Qi Deficiency
- **Combined Constitution**: Yang Deficiency
- **Constitution Category**: Combined Constitution

### Individual Constitution Scores

| Constitution Type | Score | Determination |
|-------------------|-------|---------------|
| Qi Deficiency | 78.5 | WARNING: Imbalanced |
| Yang Deficiency | 62.3 | WARNING: Imbalanced |
| Balanced | 42.1 | Normal |
| Phlegm-Dampness | 38.7 | Normal |
| Qi Stagnation | 35.2 | Normal |
| Yin Deficiency | 32.1 | Normal |
| Damp-Heat | 28.4 | Normal |
| Blood Stasis | 25.6 | Normal |
| Inherited Special | 18.3 | Normal |

---

## Constitution Characteristic Analysis

### Qi Deficiency Characteristics

**Physical Characteristics:**
- Soft muscles
- Easily fatigued
- Weak voice
- Prefers quiet, dislikes speaking
- Prone to sweating

**Psychological Characteristics:**
- Introverted personality
- Dislikes risk-taking
- Emotionally unstable

**Disease Susceptibility:**
- Prone to colds
- Prone to organ prolapse
- Prone to fatigue

**Adaptability:**
- Intolerant of wind, cold, summer heat, and dampness pathogens
- Susceptible to illness in autumn

### Yang Deficiency Characteristics

**Physical Characteristics:**
- Aversion to cold
- Cold hands and feet
- Preference for warm food and drinks

**Psychological Characteristics:**
- Tends to be quiet
- Introverted

**Disease Susceptibility:**
- Prone to phlegm-fluid retention, edema, and diarrhea
- Susceptible to cold pathogens

**Adaptability:**
- Intolerant of cold, tolerant of summer heat
- Susceptible to illness in winter

---

## Wellness Recommendations

### Dietary Therapy

**Principles:** Tonify Qi and strengthen the Spleen; warm and tonify Kidney Yang

**Recommended Foods:**
- Qi-tonifying: Chinese yam, jujube (red dates), astragalus, ginseng, white atractylodes
- Yang-warming: Lamb, Chinese chives, Sichuan pepper, ginger, longan
- Spleen-strengthening: Job's tears (coix seed), poria, hyacinth bean

**Foods to Avoid:**
- Raw and cold foods: Ice cream, iced drinks, sashimi
- Greasy and heavy foods: Fried foods, fatty meat
- Excessively pungent and drying: Chili pepper, Sichuan pepper

**Suggested Recipes:**
1. Astragalus-stewed chicken
2. Chinese yam porridge
3. Red dates and poria porridge
4. Chinese angelica, ginger, and lamb soup

**Dietary Advice:**
- Eat smaller, more frequent meals; chew thoroughly
- Prefer warm and hot foods; avoid raw and cold
- Rest briefly after meals

### Daily Life Regimen

**Schedule Recommendations:**
- Ensure adequate sleep (8+ hours)
- Go to bed early, rise late
- Avoid staying up late

**Environmental Requirements:**
- Maintain a warm, dry environment
- Avoid exposure to wind and cold
- Stay warm, especially around the waist, abdomen, and feet

**Lifestyle Habits:**
- Avoid excessive exertion
- Balance work and rest
- Get moderate sun exposure
- Soak feet in warm water

### Exercise and Physical Activity

**Principles:** Gentle exercise; avoid vigorous activity

**Recommended Exercises:**
- Tai Chi
- Baduanjin (Eight Brocades)
- Walking
- Qigong
- Yoga

**Exercise Recommendations:**
- Frequency: 1-2 times daily
- Duration: 20-30 minutes per session
- Intensity: Low to moderate
- Note: Should not cause excessive fatigue

**Precautions:**
- Avoid vigorous exercise
- Rest promptly after exercise
- Progress gradually
- Avoid exercising in cold environments

### Emotional Regulation

**Principles:** Maintain a cheerful mood; avoid excessive worry

**Regulation Methods:**
- Stay positive and optimistic
- Avoid overthinking
- Participate in social activities
- Learn relaxation techniques

**Mood Management:**
- Cultivate hobbies
- Maintain social connections
- Learn to regulate emotions

### Acupoint Self-Care

**Recommended Acupoints:**

#### 1. Zusanli (ST36)
- **Location**: Lateral lower leg, 3 cun below the knee eye
- **Effect**: Strengthens Spleen and tonifies Qi; strengthens the body
- **Method**: Massage 3-5 minutes daily; moxibustion may be applied

#### 2. Qihai (CV6)
- **Location**: 1.5 cun below the navel
- **Effect**: Cultivates and tonifies original Qi
- **Method**: Massage 3-5 minutes daily; moxibustion may be applied

#### 3. Guanyuan (CV4)
- **Location**: 3 cun below the navel
- **Effect**: Cultivates the origin and strengthens the foundation; warms and tonifies Kidney Yang
- **Method**: Massage 3-5 minutes daily; moxibustion 10-15 minutes

### Herbal Medicine Guidance

WARNING: The following content is for reference by TCM practitioners only; do not self-prescribe or self-medicate.

**Recommended Formula:** Si Junzi Tang (Four Gentlemen Decoction) with modifications

**Source:** "Taiping Huimin Heji Ju Fang" (Imperial Grace Formulary of the Taiping Era)

**Formula Composition:**
- Ginseng (Ren Shen): 9-15g, greatly tonifies original Qi
- White Atractylodes (Bai Zhu): 9-12g, strengthens Spleen and tonifies Qi
- Poria (Fu Ling): 9-15g, strengthens Spleen and promotes water metabolism
- Licorice (Gan Cao): 6-9g, harmonizes all herbs

**Modifications Based on Symptoms:**
- Severe Qi Deficiency: Add Astragalus (Huang Qi) 15-30g
- Spleen Deficiency with Excessive Dampness: Add Job's Tears (Yi Yi Ren) 15-30g, Hyacinth Bean (Bian Dou) 10-15g
- Poor Appetite with Abdominal Distention: Add Tangerine Peel (Chen Pi) 6-9g, Amomum (Sha Ren) 3-6g

**Administration:** Decoct in water; one dose daily, divided into two warm servings (morning and evening)

**Precautions:**
- WARNING: Must be used under the guidance of a qualified TCM practitioner
- WARNING: Pregnant women, children, and frail individuals require practitioner supervision
- WARNING: Avoid raw, cold, greasy, and pungent foods during treatment
- WARNING: Suspend use during colds and fever
- WARNING: Discontinue immediately and seek medical attention if adverse reactions occur

---

## Seasonal Wellness Recommendations

### Spring Wellness
- Focus on nourishing Yang to follow the rising energy of spring
- Eat more Chinese chives, spinach, and Chinese yam
- Maintain a cheerful mood; exercise appropriately
- Protect against wind and keep warm

### Summer Wellness
- Clear summer heat; nourish the Heart spirit
- Eat more mung beans, winter melon, and bitter gourd
- Prevent heatstroke and stay cool
- Maintain emotional calm

### Autumn Wellness
- Focus on gathering and moistening dryness; nourish the Lungs
- Eat more white fungus, lily bulb, and pear
- Keep warm; avoid catching cold
- Maintain emotional stability

### Winter Wellness
- Focus on storage; warm and tonify Kidney Yang
- Eat more lamb, walnuts, and chestnuts
- Keep warm, especially around the waist and abdomen
- Go to bed early, rise late; avoid overexertion

---

## Correlations with Other Health Indicators

### Constitution and Nutrition
- Qi Deficiency, Yang Deficiency: Warm and tonifying diet recommended
- Yin Deficiency, Damp-Heat: Light, mild diet recommended
- Phlegm-Dampness: Low-fat, low-sugar diet; weight management

### Constitution and Exercise
- Qi Deficiency, Yang Deficiency: Gentle exercise recommended
- Damp-Heat, Phlegm-Dampness: Moderate increase in exercise intensity
- Yin Deficiency: Avoid vigorous exercise

### Constitution and Sleep
- Qi Deficiency, Yang Deficiency: Ensure adequate sleep
- Yin Deficiency: Avoid staying up late
- Qi Stagnation: Soothe the Liver and relieve stagnation; improve sleep quality

### Constitution and Chronic Disease
- Phlegm-Dampness: Susceptible to hypertension, diabetes, hyperlipidemia
- Damp-Heat: Susceptible to metabolic syndrome
- Blood Stasis: Susceptible to cardiovascular disease
- Qi Stagnation: Susceptible to depression, anxiety disorders

---

## Medical Safety Boundaries

WARNING: Important Disclaimer

This analysis is for health reference only and does not constitute medical diagnosis or treatment advice.

### Analysis Capabilities

**CAN do:**
- TCM constitution identification assessment
- Constitution characteristic analysis
- General wellness recommendations
- TCM knowledge education
- Constitution trend tracking

**CANNOT do:**
- TCM disease diagnosis
- Herbal medicine prescription
- Replace TCM practitioner consultation
- Acupuncture or other therapeutic procedures
- Handle serious health issues

### Danger Signal Detection

The following danger signals are detected during analysis:

1. **Severe Constitution Imbalance:**
   - Single imbalanced constitution score > 80
   - Multiple imbalanced constitutions combined

2. **Health Risk Alerts:**
   - Phlegm-Dampness: Hypertension and diabetes risk
   - Damp-Heat: Metabolic syndrome risk
   - Blood Stasis: Cardiovascular disease risk
   - Qi Stagnation: Depression risk

3. **Medical Referral Guidance:**
   - Suspected disease symptoms: Recommend medical visit
   - Need for herbal treatment: Consult a TCM practitioner
   - Ineffective constitution management: Seek professional help

### Recommendation Tiers

**Level 1: General Recommendations**
- Based on TCM constitution theory
- Applicable to the general population
- No medical supervision required

**Level 2: Reference Recommendations**
- Based on user constitution and health status
- Should be combined with individual circumstances
- Recommend consulting a TCM practitioner

**Level 3: Medical Recommendations**
- Involves herbal medicine therapy
- Requires confirmation by a TCM practitioner
- Do not self-administer herbal medicine

---

## Data Structure

### Constitution Assessment Record

```json
{
  "date": "2025-06-20",
  "questionnaire": {
    "questions": [
      {
        "id": 1,
        "constitution": "Qi Deficiency",
        "question": "Do you tire easily?",
        "answer": 4,
        "weight": 1.0
      }
    ],
    "total_questions": 60
  },
  "results": {
    "primary_constitution": "Qi Deficiency",
    "secondary_constitutions": ["Yang Deficiency"],
    "constitution_scores": {
      "Balanced": 42.1,
      "Qi Deficiency": 78.5,
      "Yang Deficiency": 62.3,
      "Yin Deficiency": 32.1,
      "Phlegm-Dampness": 38.7,
      "Damp-Heat": 28.4,
      "Blood Stasis": 25.6,
      "Qi Stagnation": 35.2,
      "Inherited Special": 18.3
    },
    "constitution_type": "compound"
  },
  "characteristics": {
    "physical": ["Easily fatigued", "Shortness of breath", "Spontaneous sweating"],
    "psychological": ["Introverted", "Dislikes speaking"]
  },
  "recommendations": {
    "diet": {
      "principles": ["Tonify Qi and strengthen the Spleen", "Warm and tonify Kidney Yang"],
      "beneficial": ["Chinese yam", "Jujube", "Astragalus"],
      "avoid": ["Raw and cold foods", "Greasy and heavy foods"]
    },
    "exercise": "Gentle exercise such as Tai Chi and walking",
    "lifestyle": "Regular schedule; avoid overexertion",
    "acupoints": ["Zusanli (ST36)", "Qihai (CV6)", "Guanyuan (CV4)"]
  }
}
```

---

## References

### TCM Constitution Theory
- "Classification and Determination of TCM Constitution Types" standard (per Chinese clinical guidelines)
- Wang Qi's Nine Constitution Types theory
- "TCM Constitution Studies" textbook

### Wellness Principles
- TCM fundamental theory
- Four-season wellness principles
- Pattern differentiation and treatment principles

### Herbal Formulas
- "Formulary" (Fang Ji Xue) textbook
- "Taiping Huimin Heji Ju Fang" (Imperial Grace Formulary of the Taiping Era)
- "Jin Gui Yao Lue" (Essential Prescriptions from the Golden Cabinet)
