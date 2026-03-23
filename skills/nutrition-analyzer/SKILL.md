---
name: nutrition-analyzer
description: "Analyzes nutrition data, identifies dietary patterns, evaluates nutritional status, and provides personalized nutrition recommendations. Supports correlation analysis with exercise, sleep, and chronic disease data. Use when the user wants to review nutrient intake trends, assess RDA achievement, or get dietary improvement advice."
version: 1.0.0
user-invocable: true
argument-hint: "[trend | assessment | correlation | recommendations]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🥗","category":"health-analyzer"}}
---

# Nutrition Analyzer Skill

Analyzes dietary and nutrition data, identifies nutritional patterns, evaluates nutritional status, and provides personalized nutrition improvement recommendations.

## Features

### 1. Nutrition Trend Analysis

Analyzes trends in nutrient intake and identifies areas of improvement or concern.

**Analysis Dimensions**:
- Macronutrient trends (protein, carbohydrates, fat, fiber, calories)
- Micronutrient trends (vitamins, minerals)
- Caloric source distribution changes
- Meal patterns (eating times, frequency)
- Food category preferences

**Output**:
- Trend direction (improving/stable/declining)
- Magnitude and percentage of change
- Trend significance
- Improvement recommendations

### 2. Nutrient Intake Assessment

Evaluates whether nutrient intake meets recommended standards (RDA/AI).

**Assessment Content**:
- **Macronutrient assessment**:
  - Protein intake quantity and quality
  - Carbohydrate type distribution (refined vs. complex carbs)
  - Fat type distribution (saturated/monounsaturated/polyunsaturated/trans fat)
  - Dietary fiber intake

- **Vitamin assessment**:
  - Vitamins A, C, D, E, K
  - B-vitamins (B1, B2, B3, B6, B12, folate, pantothenic acid, biotin)
  - Comparison against RDA
  - Deficiency risk assessment

- **Mineral assessment**:
  - Major minerals: calcium, phosphorus, magnesium, sodium, potassium, chloride, sulfur
  - Trace minerals: iron, zinc, copper, manganese, iodine, selenium, chromium, molybdenum
  - Comparison against RDA
  - Deficiency risk assessment

- **Special nutrient assessment**:
  - Omega-3 fatty acids (EPA, DHA, ALA)
  - Choline
  - Coenzyme Q10
  - Phytochemicals (flavonoids, carotenoids, etc.)

**Output**:
- Achievement rate for each nutrient
- Deficient/insufficient/adequate/excessive classification
- Deficiency risk identification
- Priority improvement recommendations

### 3. Nutritional Status Assessment

Comprehensive evaluation of the user's nutritional status.

**Assessment Content**:
- **Overall nutrition quality score**:
  - Nutrient density score
  - Food diversity score
  - Balanced diet score

- **Nutritional pattern identification**:
  - Dietary pattern type (Mediterranean, DASH, vegetarian, etc.)
  - Eating time patterns (meal frequency, eating window)
  - Snacking patterns

- **Nutritional risk identification**:
  - Deficiency risks (e.g., vitamin D deficiency, iron deficiency)
  - Excess risks (e.g., vitamin A excess, sodium excess)
  - Unhealthy eating habits (high sugar, high fat, high sodium)

**Output**:
- Nutritional status grade (excellent/good/fair/poor)
- Key nutritional issues identified
- Risk factor list
- Improvement priority

### 4. Correlation Analysis

Analyzes correlations between nutrition and other health metrics.

**Supported Correlation Analyses**:
- **Nutrition <-> Weight**:
  - Relationship between calorie intake and weight change
  - Macronutrient ratios and weight management
  - Eating timing and metabolic relationship

- **Nutrition <-> Exercise**:
  - Impact of nutritional intake on exercise performance
  - Nutritional needs on workout days vs. rest days
  - Protein intake and muscle recovery

- **Nutrition <-> Sleep**:
  - Caffeine intake and sleep quality
  - Dinner timing and sleep onset time
  - Specific nutrients (e.g., magnesium, tryptophan) and sleep

- **Nutrition <-> Blood Pressure**:
  - Sodium intake and blood pressure
  - Potassium/sodium ratio and blood pressure
  - DASH diet adherence and blood pressure control

- **Nutrition <-> Blood Glucose**:
  - Carbohydrate types and blood glucose fluctuations
  - Dietary fiber and blood glucose control
  - Meal timing and blood glucose curves

**Output**:
- Correlation coefficient (-1 to 1)
- Correlation strength (weak/moderate/strong)
- Statistical significance
- Causal inference
- Practical recommendations

### 5. Personalized Recommendation Generation

Generates personalized nutrition improvement recommendations based on user data.

**Recommendation Types**:
- **Nutrient adjustment recommendations**:
  - Increase deficient nutrients
  - Reduce excessive nutrients
  - Optimize nutrient ratios

- **Food selection recommendations**:
  - Recommend specific food categories
  - Food substitution suggestions (healthier alternatives)
  - Food pairing suggestions (to enhance absorption)

- **Dietary habit recommendations**:
  - Meal timing adjustments
  - Meal frequency adjustments
  - Cooking method suggestions

- **Supplement recommendations** (for reference only):
  - Supplement suggestions based on deficiency risk
  - Supplement dosage and timing
  - Interaction warnings

**Recommendation Basis**:
- DRIs/RDA standards
- User nutrition history data
- User health status and goals
- Evidence-based nutrition science

---

## Usage Instructions

### Trigger Conditions

This skill is triggered when the user requests:
- Nutrition trend analysis
- Nutrient intake assessment
- Nutritional status assessment
- Nutrition improvement recommendations
- Nutrition and other health metric correlation analysis

### Execution Steps

#### Step 1: Determine Analysis Scope

Clarify the analysis type and time range requested by the user:
- Analysis type: trend/assessment/correlation/recommendations
- Time range: week/month/quarter/custom
- Analysis depth: macronutrients/micronutrients/comprehensive analysis

#### Step 2: Read Data

**Primary data sources**:
1. `data-example/nutrition-tracker.json` - Main nutrition tracking data
2. `data-example/nutrition-logs/YYYY-MM/YYYY-MM-DD.json` - Daily diet records

**Related data sources**:
1. `data-example/profile.json` - Weight, BMI, and other baseline data
2. `data-example/fitness-tracker.json` - Exercise data
3. `data-example/sleep-tracker.json` - Sleep data
4. `data-example/hypertension-tracker.json` - Blood pressure data
5. `data-example/diabetes-tracker.json` - Blood glucose data

#### Step 3: Data Analysis

Execute the appropriate analysis algorithms based on the analysis type:

**Trend analysis algorithm**:
- Linear regression to calculate trend slope
- Moving average to smooth fluctuations
- Statistical significance tests

**RDA achievement rate calculation**:
```python
rda_achievement = (actual_intake / rda_value) * 100

status_classification:
- < 50%: Severe deficiency
- 50-75%: Insufficient
- 75-100%: Approaching target
- 100-150%: Adequate (ideal range)
- > 150%: Excess (check tolerable upper intake level, UL)
```

**Nutrient density score**:
```python
nutrient_density_score = (
    (vitamins_achieved / total_vitamins) * 40 +
    (minerals_achieved / total_minerals) * 30 +
    (fiber_achieved / fiber_rda) * 30
)
```

**Correlation analysis algorithm**:
- Pearson correlation coefficient calculation
- Lag correlation analysis (accounting for time-delay effects)
- Multivariate regression analysis

#### Step 4: Generate Report

Output the analysis report in the standard format (see "Output Format" section).

---

## Output Format

### Nutrition Trend Analysis Report

```markdown
# Nutrition Intake Trend Analysis Report

## Analysis Period
2025-03-20 to 2025-06-20 (3 months, 90 days recorded)

## Macronutrient Trends

### Calorie Intake
- **Trend**: Down
- **Start**: avg 2100 cal/day
- **Current**: avg 1950 cal/day
- **Change**: -150 cal/day (-7.1%)
- **Interpretation**: Moderate calorie reduction, consistent with weight loss goal

**Trend Line**:
```
2100 | ..
2050 | .  .
2000 +--    .
1950 |       .
1900 +----------
     Mar Apr May Jun
```

### Protein
- **Trend**: Stable
- **Average**: 82g/day (range: 70-95g)
- **Target**: 80g/day
- **Achievement rate**: 93% (84/90 days on target)
- **Interpretation**: Protein intake is stable and largely on target

### Dietary Fiber
- **Trend**: Improving
- **Start**: avg 18g/day
- **Current**: avg 22g/day
- **Change**: +4g/day (+22%)
- **Target**: 30g/day
- **Interpretation**: Significant fiber increase, but continued effort needed

### Fat
- **Trend**: Down
- **Start**: avg 75g/day
- **Current**: avg 68g/day
- **Change**: -7g/day (-9.3%)
- **Target**: <=65g/day
- **Interpretation**: Fat intake decreasing, approaching target

**Fat Type Distribution Changes**:
| Fat Type | Start | Current | Target | Trend |
|----------|-------|---------|--------|-------|
| Saturated fat | 25g | 20g | <20g | Improving |
| Monounsaturated | 30g | 32g | >35g | Slightly up |
| Polyunsaturated | 15g | 12g | 15-20g | Needs increase |
| Trans fat | 2g | 0.5g | 0g | Improving |

## Vitamin Status Trends

### Vitamin D
- **Intake trend**: Increasing (supplementation started)
- **Start**: avg 2 mcg/day (dietary sources)
- **Current**: avg 52 mcg/day (including 2000 IU supplement)
- **RDA**: 15 mcg/day
- **Serum level change**:
  - Baseline (2025-05): 18 ng/mL
  - Current (2025-06): 22 ng/mL
  - Target: 30-100 ng/mL
- **Interpretation**: Supplement is taking effect, but continued monitoring needed

### Vitamin C
- **Trend**: Improving
- **Start**: avg 65 mg/day
- **Current**: avg 85 mg/day
- **RDA**: 100 mg/day
- **Achievement rate**: from 65% to 85%
- **Recommendation**: Increase citrus fruits, kiwi, strawberries

### B-Vitamins
- **Vitamin B12**: Adequate (avg 2.5 mcg, RDA 2.4 mcg)
- **Folate**: Insufficient (avg 320 mcg, RDA 400 mcg)
- **B6**: Adequate (avg 1.5 mg, RDA 1.3 mg)

## Mineral Trends

### Calcium
- **Trend**: Stable
- **Average**: 850 mg/day
- **RDA**: 1000 mg/day
- **Achievement rate**: 85%
- **Main sources**: Dairy 40%, tofu 25%, leafy greens 20%

### Iron
- **Trend**: Adequate
- **Average**: 12 mg/day
- **RDA**: 8 mg/day (male)
- **Achievement rate**: 150%
- **Main sources**: Meat, eggs, legumes, leafy greens

### Sodium
- **Trend**: Improving
- **Start**: avg 2800 mg/day
- **Current**: avg 2100 mg/day
- **Target**: <2300 mg/day (ideal <1500 mg)
- **Interpretation**: General target met; ideal target still needs effort

### Potassium
- **Trend**: Improving
- **Start**: avg 2800 mg/day
- **Current**: avg 3200 mg/day
- **Target**: 3500-4700 mg/day
- **Potassium/sodium ratio**: from 1.0 to 1.5 (target >2)
- **Recommendation**: Continue increasing fruits and vegetables

## Special Nutrient Trends

### Omega-3
- **Trend**: Increasing (fish oil supplement)
- **Start**: avg 150 mg/day
- **Current**: avg 850 mg/day (including supplement)
- **Recommended**: 500-1000 mg/day
- **Status**: On target

### Choline
- **Trend**: Stable
- **Average**: 350 mg/day
- **AI (Adequate Intake)**: 425 mg/day
- **Achievement rate**: 82%
- **Main sources**: Eggs (60%), meat (25%), legumes (15%)

## Dietary Pattern Analysis

### Food Category Distribution
| Food Category | Proportion | Change | Rating |
|--------------|-----------|--------|--------|
| Fruits & vegetables | 35% | +8% | Increased |
| Whole grains | 20% | +5% | Improved |
| Refined grains | 15% | -7% | Reduced |
| Protein sources | 20% | Stable | Adequate |
| Added fats | 8% | -3% | Reduced |
| Added sugars | 2% | -2% | Reduced |

### Eating Time Patterns
- **Average eating window**: 12.5 hours (07:30 - 20:00)
- **Eating frequency**: avg 4.2 times/day
- **Most common meal times**:
  - Breakfast: 07:30 (90% of days)
  - Lunch: 12:15 (95% of days)
  - Dinner: 18:45 (98% of days)
  - Snack: 15:30 (60% of days)

### Diet Quality Score
- **Nutrient density score**: 7.2/10 (up from 6.5)
- **Food diversity score**: 6.8/10
- **Balanced diet score**: 7.5/10
- **Overall score**: 7.2/10 - **Good**

## Insights & Recommendations

### Key Insights

1. **Dietary fiber continues to improve but remains insufficient**
   - Increased from 18g to 22g, but still below target of 30g
   - Impact: satiety, gut health, blood glucose control
   - Recommendation: Include at least 5g of fiber per meal

2. **Fat quality improving**
   - Saturated fat decreased, trans fat nearly eliminated
   - Polyunsaturated fat slightly low, need to increase Omega-3 foods
   - Recommendation: Increase deep-sea fish, nuts, flaxseed

3. **Sodium improved but potassium/sodium ratio still low**
   - Sodium decreased 33%, potassium increased 14%
   - Potassium/sodium ratio from 1.0 to 1.5, still below target 2.0
   - Recommendation: Continue increasing high-potassium foods (bananas, oranges, potatoes, spinach)

4. **Vitamin D supplementation is effective**
   - Serum level from 18 to 22 ng/mL (+4 ng in 4 weeks)
   - Expected to reach target range in 3-4 months
   - Recommendation: Continue supplementation, monitor periodically

### Priority Action Plan

#### Priority 1: Increase dietary fiber to 30g/day (2 weeks)

**Specific Actions**:
1. Breakfast: Whole grains (oats/whole wheat bread) + fruit (9g)
2. Lunch: Brown rice/whole wheat noodles + 2 servings of vegetables (8g)
3. Dinner: Sweet potato/mixed grains + 2 servings of vegetables (8g)
4. Snack: Fruit + nuts (5g)
**Total**: 30g

#### Priority 2: Optimize potassium/sodium ratio to 2.0 (4 weeks)

**Specific Actions**:
1. Reduce processed foods (primary sodium source)
2. 2-3 servings of high-potassium fruits daily (bananas, oranges, kiwi)
3. Choose spinach, potatoes, mushrooms, tomatoes for vegetables
4. Use herbs and spices instead of salt for seasoning

#### Priority 3: Maintain vitamin D supplementation (long-term)

**Monitoring Plan**:
- Recheck serum levels in 3 months
- Target: 40-60 ng/mL
- Adjust dosage based on results

## Nutrition Goal Progress

| Goal | Start | Current | Target | Progress | Status |
|------|-------|---------|--------|----------|--------|
| Calories | 2100 | 1950 | 1800-2000 | 100% | On target |
| Protein | 75g | 82g | 80g | 100% | On target |
| Dietary fiber | 18g | 22g | 30g | 73% | In progress |
| Vitamin D | 18 ng/mL | 22 ng/mL | 30-100 | 20% | Improving |
| Sodium | 2800 mg | 2100 mg | <2300 | 100% | On target |
| Omega-3 | 150 mg | 850 mg | 500-1000 mg | 100% | On target |

---

**Report generated**: 2025-06-20
**Analysis period**: 2025-03-20 to 2025-06-20 (90 days)
**Days recorded**: 90
**Nutrition analyzer version**: v1.0
```

---

## Data Structures

### Diet Record Data

```json
{
  "date": "2025-06-20",
  "meals": [
    {
      "type": "breakfast",
      "time": "07:30",
      "foods": ["eggs", "milk", "whole wheat bread"],
      "calories": 450,
      "macronutrients": {
        "protein_g": 20,
        "carbs_g": 55,
        "fat_g": 15,
        "fiber_g": 5,
        "saturated_fat_g": 5,
        "monounsaturated_fat_g": 6,
        "polyunsaturated_fat_g": 3,
        "trans_fat_g": 0.1
      },
      "micronutrients": {
        "vitamin_a_mcg": 150,
        "vitamin_c_mg": 5,
        "vitamin_d_mcg": 1.5,
        "vitamin_e_mg": 1,
        "vitamin_k_mcg": 5,
        "thiamine_mg": 0.3,
        "riboflavin_mg": 0.4,
        "niacin_mg": 4,
        "vitamin_b6_mg": 0.1,
        "folate_mcg": 30,
        "vitamin_b12_mcg": 0.6,
        "calcium_mg": 250,
        "iron_mg": 2,
        "magnesium_mg": 40,
        "phosphorus_mg": 200,
        "zinc_mg": 2,
        "selenium_mcg": 10,
        "potassium_mg": 350,
        "sodium_mg": 300
      },
      "special_nutrients": {
        "omega_3_g": 0.1,
        "choline_mg": 150
      }
    }
  ],
  "daily_summary": {
    "total_calories": 2000,
    "total_macronutrients": {
      "protein_g": 80,
      "carbs_g": 250,
      "fat_g": 65,
      "fiber_g": 30
    },
    "rda_achievement": {
      "protein": 100,
      "vitamin_c": 85,
      "vitamin_d": 35,
      "calcium": 90,
      "iron": 75
    },
    "goal_achieved": true
  }
}
```

---

## Algorithm Descriptions

### RDA Achievement Rate Calculation

```python
def calculate_rda_achievement(actual_intake, rda_value, ul_value=None):
    """
    Calculate RDA achievement rate and status.

    Parameters:
    - actual_intake: Actual intake amount
    - rda_value: Recommended Dietary Allowance
    - ul_value: Tolerable Upper Intake Level (optional)

    Returns:
    - achievement_rate: Achievement rate percentage
    - status: Status label
    """
    achievement_rate = (actual_intake / rda_value) * 100

    if ul_value and actual_intake > ul_value:
        status = "exceeds_ul"
        category = "Excess (dangerous)"
    elif achievement_rate < 50:
        status = "severe_deficiency"
        category = "Severe deficiency"
    elif achievement_rate < 75:
        status = "insufficient"
        category = "Insufficient"
    elif achievement_rate < 100:
        status = "approaching_target"
        category = "Approaching target"
    elif achievement_rate <= 150:
        status = "adequate"
        category = "Adequate"
    else:
        status = "high_intake"
        category = "High"

    return {
        'achievement_rate': round(achievement_rate, 1),
        'status': status,
        'category': category
    }
```

### Nutrient Density Score

```python
def calculate_nutrient_density_score(meal_data):
    """
    Calculate food nutrient density score (0-10 scale).

    Factor weights:
    - Vitamin achievement rate: 40%
    - Mineral achievement rate: 30%
    - Dietary fiber: 20%
    - Restrictive nutrients (saturated fat, sodium, added sugars): 10%
    """
    score = 0

    # Vitamin score
    vitamin_achievements = [
        meal_data['micronutrients'][v] / RDA[v]
        for v in ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k']
    ]
    vitamin_score = min(sum(vitamin_achievements) / len(vitamin_achievements), 1.5) * 10
    score += min(vitamin_score, 10) * 0.40

    # Mineral score
    mineral_achievements = [
        meal_data['micronutrients'][m] / RDA[m]
        for m in ['calcium', 'iron', 'magnesium', 'zinc']
    ]
    mineral_score = min(sum(mineral_achievements) / len(mineral_achievements), 1.5) * 10
    score += min(mineral_score, 10) * 0.30

    # Dietary fiber score
    fiber_score = min(meal_data['macronutrients']['fiber_g'] / 5, 2) * 10
    score += min(fiber_score, 10) * 0.20

    # Restrictive nutrient penalty
    penalty = 0
    if meal_data['macronutrients']['saturated_fat_g'] > 10:
        penalty += 2
    if meal_data['micronutrients']['sodium_mg'] > 600:
        penalty += 2
    if meal_data.get('added_sugars_g', 0) > 10:
        penalty += 2

    score = max(0, score - penalty * 0.10)

    return round(score, 1)
```

### Healthy Eating Index Score

```python
def calculate_healthy_eating_index(daily_data):
    """
    Calculate Healthy Eating Index (adapted from HEI-2015).

    Score range: 0-100 points.
    """
    score = 0

    # Adequacy components (max 50 points)
    # 1. Fruits (5 points)
    fruit_servings = daily_data['fruit_servings']
    score += min(fruit_servings, 2.5) * 2

    # 2. Vegetables (5 points)
    veg_servings = daily_data['vegetable_servings']
    score += min(veg_servings, 3) * 1.67

    # 3. Whole grains (10 points)
    whole_grains_oz = daily_data['whole_grains_oz']
    score += min(whole_grains_oz, 3) * 3.33

    # 4. Dairy (10 points)
    dairy_servings = daily_data['dairy_servings']
    score += min(dairy_servings, 3) * 3.33

    # 5. Protein (5 points)
    protein_oz = daily_data['protein_oz']
    score += min(protein_oz, 5) * 1

    # 6. Seafood/plant protein (5 points)
    plant_protein_oz = daily_data['plant_protein_oz']
    score += min(plant_protein_oz, 2) * 2.5

    # 7. Fatty acid ratio (10 points)
    fat_ratio = daily_data['unsaturated_fat_g'] / max(daily_data['saturated_fat_g'], 1)
    score += min(fat_ratio, 2.5) * 4

    # Moderation components (max 40 points, reverse scored)
    # 8. Refined grains (10 points, less is better)
    refined_grains_oz = daily_data['refined_grains_oz']
    score += max(10 - refined_grains_oz * 2, 0)

    # 9. Sodium (10 points, less is better)
    sodium_g = daily_data['sodium_mg'] / 1000
    score += max(10 - sodium_g * 2, 0)

    # 10. Added sugars (10 points, less is better)
    added_sugars_pct = daily_data['added_sugars_g'] / (daily_data['total_calories'] / 100)
    score += max(10 - added_sugars_pct * 10, 0)

    # 11. Saturated fat (10 points, less is better)
    saturated_fat_pct = daily_data['saturated_fat_g'] / (daily_data['total_calories'] / 100)
    score += max(10 - saturated_fat_pct * 10, 0)

    return round(score, 1)
```

---

## Medical Safety Boundaries

**Important Disclaimer**

This analysis is for health reference only and does not constitute medical diagnosis or a nutrition prescription.

### Scope of Analysis

**Can do**:
- Nutrition data statistics and analysis
- Trend identification and visualization
- RDA achievement rate calculation
- Nutritional deficiency risk assessment
- General nutrition recommendations
- Supplement interaction checks

**Cannot do**:
- Diagnose nutritional deficiency diseases
- Prescribe supplements
- Replace a registered dietitian
- Handle severe malnutrition
- Assess food allergies

### Danger Signal Detection

The following danger signals are detected during analysis:

1. **Nutrient excess**:
   - Vitamin A > 3000 mcg (long-term)
   - Vitamin D > 100 mcg (long-term)
   - Iron > 45 mg (long-term)
   - Selenium > 400 mcg
   - Sodium > 2300 mg (persistent)

2. **Nutrient deficiency**:
   - Vitamin D < 10 mcg/day (serum < 12 ng/mL)
   - Vitamin B12 < 1.5 mcg/day (vegetarians)
   - Iron < 6 mg/day (women of childbearing age)
   - Calcium < 500 mg/day

3. **Abnormal energy intake**:
   - Persistent < 1200 cal/day (potential malnutrition)
   - Persistent > 3500 cal/day (potential overweight)

4. **Abnormal dietary patterns**:
   - Dietary fiber < 10g/day
   - Added sugars > 25% of calories
   - Saturated fat > 15% of calories

### Recommendation Levels

**Level 1: General recommendations**
- Based on DRIs/RDA standards
- Applicable to the general population
- No medical supervision required

**Level 2: Reference recommendations**
- Based on user data and health status
- Should be combined with personal circumstances
- Recommend consulting a dietitian

**Level 3: Medical recommendations**
- Involves disease management or supplements
- Requires physician confirmation
- Do not self-adjust medication dosages

---

## Reference Resources

- Chinese Dietary Reference Intakes (DRIs) (per Chinese clinical guidelines): http://www.cnsoc.org/
- US Dietary Guidelines: https://www.dietaryguidelines.gov/
- USDA FoodData Central: https://fooddatacentral.usda.gov/
- WHO Nutrition Recommendations: https://www.who.int/nutrition/
- Supplement Interaction Database: https://naturalmedicines.therapeuticresearch.com/
