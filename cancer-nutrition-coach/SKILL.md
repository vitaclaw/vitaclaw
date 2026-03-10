---
name: cancer-nutrition-coach
description: "Performs nutritional assessment and diet plan generation for cancer patients using NRS-2002 scoring and LLM-based dietary recommendations. Tracks weight, albumin, caloric intake, and generates personalized meal plans based on cancer type and treatment phase. Use when the user wants nutrition guidance during cancer treatment."
version: 1.0.0
user-invocable: true
argument-hint: "[record | screen | weight-alert | bmi | diet-plan | report]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🥗","category":"health-scenario"}}
---

# Cancer Nutrition Coach

A nutrition management tool designed specifically for cancer patients, providing the following capabilities:

## Features

- **Nutrition Data Logging**: Record nutritional indicators including weight, height, albumin, prealbumin, and daily caloric intake
- **NRS-2002 Nutritional Risk Screening**: Performs nutritional risk scoring per the NRS-2002 standard, including nutritional status score (0-3), disease severity score (0-3), and age correction; a total score of 3 or above indicates nutritional risk
- **Weight Alert**: Monitors weight trend over the last 30 days and issues a warning if the decline exceeds 5%
- **BMI Calculation and Classification**: Calculates and classifies BMI per Chinese clinical guidelines (underweight <18.5 / normal 18.5-23.9 / overweight 24-27.9 / obese >=28)
- **Personalized Diet Plan Generation**: Uses LLM to generate personalized nutrition plans based on cancer type, treatment phase, allergy history, and dietary preferences, covering calorie/protein targets, recommended/avoided foods, meal scheduling, and supplement suggestions
- **Comprehensive Nutrition Report**: Summarizes multi-dimensional nutrition data including weight trend, BMI, albumin/prealbumin trend, and caloric intake trend

## Usage Examples

```bash
# Record nutrition data
python cancer_nutrition_coach.py record --weight 65.5 --albumin 35 --intake 1800 --phase chemotherapy

# NRS-2002 nutritional risk screening
python cancer_nutrition_coach.py screen --ns 2 --ds 2 --age 68

# Weight alert
python cancer_nutrition_coach.py weight-alert --days 30

# BMI calculation
python cancer_nutrition_coach.py bmi --weight 65 --height 170

# Generate personalized diet plan
python cancer_nutrition_coach.py diet-plan --diagnosis "colorectal cancer" --phase "on FOLFOX chemotherapy" --allergies "seafood"

# Generate comprehensive nutrition report
python cancer_nutrition_coach.py report --days 30
```
