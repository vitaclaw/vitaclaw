---
name: oral-health-analyzer
description: "Analyzes oral health data, identifies dental problem patterns, assesses oral health status, and provides personalized dental care recommendations. Supports correlation analysis with nutrition, chronic disease, and medication data. Use when the user wants to evaluate their dental health or track oral conditions."
version: 1.0.0
user-invocable: true
argument-hint: "[checkup-review | risk-assessment | treatment-plan | cross-module-analysis]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🦷","category":"health-analyzer"}}
---

# Oral Health Analysis Skill

## Skill Overview

This skill provides comprehensive oral health data analysis, including trend identification, risk assessment, problem diagnosis, and personalized recommendation generation.

## Medical Disclaimer

WARNING: The data analysis and recommendations provided by this skill are for reference only and do not constitute medical diagnosis or treatment advice.

- All oral health issues should be diagnosed and treated by a professional dentist
- Analysis results cannot replace professional dental examinations
- Seek immediate medical attention for emergencies
- Follow the professional advice of your dentist

## Core Features

### 1. Trend Analysis

#### Caries Development Trends
- Identify patterns and frequency of caries occurrence
- Analyze distribution of caries across different tooth positions
- Assess caries progression rate
- Predict future caries risk

**Output:**
- Caries count change curve
- High-risk tooth position identification
- Development trend prediction
- Prevention recommendations

#### Periodontal Health Changes
- Periodontal bleeding frequency statistics
- Periodontal pocket depth changes
- Attachment loss monitoring
- Gingival recession progression

**Output:**
- Periodontal health score trends
- Disease progression warnings
- Treatment effectiveness evaluation
- Maintenance recommendations

#### Hygiene Habit Improvement
- Brushing frequency changes
- Flossing frequency changes
- Professional cleaning record tracking
- Hygiene habit scoring

**Output:**
- Habit improvement curve
- Score change trends
- Goal achievement status
- Motivational recommendations

### 2. Risk Assessment

#### Caries Risk Assessment
Comprehensive assessment based on the following factors:
- Dietary habits (sugar intake)
- Oral hygiene habits
- Fluoride use
- Salivary flow status
- Previous caries history
- Family history

**Risk Levels:**
- **Low Risk**: Good hygiene habits + low-sugar diet + regular checkups
- **Medium Risk**: Moderate sugar intake + average hygiene habits
- **High Risk**: High-sugar diet + poor hygiene habits + irregular checkups + caries history

**Output:**
- Risk level (Low/Medium/High)
- Main risk factors
- Quantitative risk score
- Risk reduction recommendations

#### Periodontal Disease Risk Assessment
Comprehensive assessment based on the following factors:
- Gingival bleeding frequency
- Periodontal pocket depth
- Degree of attachment loss
- Smoking status
- Diabetes control status
- Stress level
- Family history

**Risk Levels:**
- **Healthy**: No bleeding, probing depth 1-3mm
- **Gingivitis**: Bleeding on probing, probing depth 3-4mm
- **Mild Periodontitis**: Probing depth 4-5mm, mild attachment loss
- **Moderate Periodontitis**: Probing depth 5-6mm, moderate attachment loss
- **Severe Periodontitis**: Probing depth >6mm, severe attachment loss

**Output:**
- Disease staging
- Risk factor list
- Progression risk prediction
- Management recommendations

#### Oral Cancer Risk Assessment
Comprehensive assessment based on the following factors:
- Smoking history
- Alcohol consumption habits
- Betel nut chewing
- HPV infection
- Sun exposure (lip cancer)
- Nutritional status
- Oral hygiene

**Risk Levels:**
- **Low Risk**: No risk factors
- **Medium Risk**: 1-2 risk factors
- **High Risk**: 3+ risk factors or previous lesions

**Output:**
- Risk level
- Main risk factors
- Screening recommendations
- Prevention strategies

### 3. Correlation Analysis

#### Correlation with Nutrition Module
**Sugar Intake and Caries Risk:**
- Analyze daily sugar intake
- Assess impact of eating frequency on caries
- Identify high-sugar food types
- Recommend low-sugar alternatives

**Calcium and Vitamin D and Dental Health:**
- Assess whether calcium intake is adequate
- Analyze vitamin D levels
- Evaluate impact on tooth strength
- Recommend supplements (if needed)

**Oral Manifestations of Nutritional Deficiencies:**
- Vitamin C deficiency: Gingival bleeding
- Vitamin B deficiency: Oral ulcers
- Iron deficiency: Tongue inflammation
- Protein deficiency: Mucosal atrophy

#### Correlation with Chronic Disease Module
**Diabetes and Periodontal Disease:**
- Analyze relationship between blood sugar control and periodontal health
- Assess diabetes complication risk
- Explain the impact of periodontal disease on blood sugar
- Joint management recommendations

**Cardiovascular Disease and Periodontal Disease:**
- Analyze impact of periodontitis on cardiovascular disease
- Assess inflammatory marker correlations
- Provide preventive treatment recommendations
- Joint monitoring recommendations

**Oral Health During Pregnancy:**
- Pregnancy gingivitis risk assessment
- Dental treatment timing recommendations
- Medication safety assessment
- Prenatal oral care guidance

**Osteoporosis and Dental Health:**
- Assess impact of bone density on teeth
- Analyze side effects of anti-resorptive medications
- Provide dental protection recommendations

#### Correlation with Medication Module
**Drug-Induced Dry Mouth:**
- Identify medications that cause dry mouth
- Assess dry mouth severity
- Provide relief recommendations
- Communicate with physician regarding medication adjustments

**Drug-Induced Gingival Hyperplasia:**
- Identify medications that cause gingival hyperplasia
- Assess degree of hyperplasia
- Provide management recommendations
- Communicate with physician regarding alternative medications

**Drug Effects on Tooth Color:**
- Identify medications that cause tooth discoloration
- Provide cosmetic solutions
- Prevention recommendations

#### Correlation with Eye Health Module
**Sjogren's Syndrome:**
- Joint analysis of dry mouth and dry eyes
- Assessment of systemic autoimmune disease
- Multi-system symptom tracking
- Specialist referral recommendations

**Oral Manifestations of Autoimmune Diseases:**
- Lupus oral lesions
- Rheumatoid arthritis TMJ effects
- Oral manifestations of other immune diseases

### 4. Personalized Recommendations

#### Prevention Recommendations
**Caries Prevention:**
- Brushing technique guidance (Bass brushing method)
- Flossing instructions
- Fluoride product recommendations
- Dietary adjustment recommendations
- Regular checkup reminders

**Periodontal Disease Prevention:**
- Improve oral hygiene habits
- Smoking cessation support
- Stress management
- Blood sugar control (for diabetic patients)
- Regular professional cleaning recommendations

**Oral Cancer Prevention:**
- Smoking cessation and alcohol limitation
- Avoid betel nut
- Sun protection (lips)
- Balanced nutrition
- Regular self-examination methods

#### Treatment Recommendations
**Based on Problem Type:**
- Routine checkup recommendations (every 6 months)
- Emergency situation handling guidance
- Specialist referral recommendations (if needed)
- Treatment timing recommendations
- Cost estimate reference

#### Lifestyle Recommendations
**Dietary Adjustments:**
- Reduce free sugar intake
- Increase calcium and vitamin D intake
- Drink more water (prevent dry mouth)
- Avoid excessively hard foods (protect dental crowns)

**Habit Improvement:**
- Develop a personalized brushing plan
- Gradually increase flossing frequency
- Establish an oral hygiene routine
- Set up a reminder system

**Risk Factor Management:**
- Smoking cessation strategies
- Alcohol limitation recommendations
- Stress management techniques
- Bruxism management

### 5. Goal Management

#### Goal Setting
- Collaborate with users to set realistic goals
- Break down into achievable steps
- Set milestones
- Establish evaluation criteria

**Common Goal Types:**
- Increase flossing frequency
- Improve brushing technique
- Reduce sugar intake
- Regular dental checkups
- Smoking cessation

#### Progress Tracking
- Regularly evaluate goal achievement
- Provide motivation and feedback
- Adjust goals (if needed)
- Celebrate milestone achievements

#### Barrier Identification
- Identify factors hindering goal achievement
- Provide strategies to overcome barriers
- Adjust plans to fit real-world situations
- Provide ongoing support

### 6. Statistical Analysis

#### Comprehensive Health Score
Calculated based on the following factors:
- Oral hygiene habits (40%)
- Checkup frequency (20%)
- Treatment completion status (20%)
- Problem control status (10%)
- Goal achievement status (10%)

**Score Range:** 0-100 points
- **Excellent**: 90-100 points
- **Good**: 75-89 points
- **Fair**: 60-74 points
- **Poor**: <60 points

#### Oral Health Age
- Calculated based on dental status, periodontal health, and hygiene habits
- Compared with actual age
- Improvement recommendations provided

#### Treatment Statistics
- Treatment type distribution
- Treatment cost statistics
- Treatment frequency analysis
- Dental visit records

#### Problem Statistics
- Problem type distribution
- Problem occurrence frequency
- Problem duration
- Resolution rate statistics

### 7. Alert System

#### Regular Checkup Reminders
- 30 days before next checkup: Friendly reminder
- 7 days before next checkup: Urgent reminder
- Past checkup date: Overdue reminder

#### Problem Alerts
- Toothache lasting >3 days: Recommend medical visit
- Gingival bleeding persisting for 1 week: Recommend examination
- Oral ulcer lasting >2 weeks: Recommend biopsy
- New lumps/white patches: Seek immediate medical attention

#### Trend Alerts
- Rapid increase in caries count: Risk upgrade
- Worsening periodontal indicators: Refer to periodontal specialist
- Declining hygiene habits: Intervention recommendation
- Increasing treatment frequency: In-depth assessment

## Usage Scenarios

### Scenario 1: Routine Health Assessment
**User Request:** Analyze my oral health over the past 6 months

**Analysis Workflow:**
1. Read all oral health records from the past 6 months
2. Analyze checkup records, treatment records, and problem records
3. Assess hygiene habit changes
4. Calculate health score changes
5. Identify improvement or deterioration trends
6. Generate comprehensive assessment report

**Output:**
- Health score change trends
- Key improvements
- Issues requiring attention
- Next steps and recommendations

### Scenario 2: Problem Diagnosis Assistance
**User Request:** My gums have been bleeding when I brush for the past week

**Analysis Workflow:**
1. Retrieve recent oral examination records
2. Analyze periodontal status history
3. Assess current hygiene habits
4. Check for related medication records
5. Analyze nutritional data (e.g., vitamin C intake)
6. Generate diagnostic assistance report

**Output:**
- Possible cause analysis
- Severity assessment
- Medical visit recommendations
- Home care methods
- Preventive measures

### Scenario 3: Treatment Planning
**User Request:** I want to improve my oral hygiene and reduce caries risk

**Analysis Workflow:**
1. Assess current caries risk
2. Analyze main risk factors
3. Evaluate current hygiene habits
4. Identify areas for improvement
5. Set phased goals
6. Develop personalized plan

**Output:**
- Current risk assessment
- Improvement goals
- Action plan
- Timeline
- Progress tracking methods

### Scenario 4: Multidisciplinary Joint Analysis
**User Request:** I have diabetes; how does it affect my oral health?

**Analysis Workflow:**
1. Read diabetes management data
2. Analyze blood sugar control status
3. Assess periodontal health status
4. Analyze correlation between the two
5. Evaluate complication risk
6. Generate joint management recommendations

**Output:**
- Impact of diabetes on oral health
- Impact of oral health on blood sugar
- Complication risk assessment
- Joint management strategies
- Monitoring indicator recommendations

### Scenario 5: Preventive Guidance
**User Request:** I am planning to get pregnant; what oral issues should I watch for?

**Analysis Workflow:**
1. Assess current oral health status
2. Identify potential risks
3. Analyze current medication safety
4. Assess treatment urgency
5. Generate prenatal oral management plan

**Output:**
- Pre-pregnancy dental checkup recommendations
- Common oral problems during pregnancy
- Medication safety
- Treatment timing recommendations
- Prenatal care guidance

## Data Analysis Methods

### Quantitative Analysis
- Descriptive statistics (mean, median, standard deviation)
- Trend analysis (linear regression, moving average)
- Correlation analysis (Pearson/Spearman correlation)
- Risk score calculation (multi-factor weighting)

### Qualitative Analysis
- Text description analysis
- Symptom pattern recognition
- Chief complaint classification
- Satisfaction evaluation

### Visualization Output
- Time series charts
- Tooth position distribution maps
- Risk assessment radar charts
- Progress tracking dashboards
- Comparative analysis bar charts

## Quality Assurance

### Data Validation
- Check data completeness
- Verify data consistency
- Identify outliers
- Handle missing data

### Result Validation
- Medical logic checks
- Cross-reference with clinical guidelines
- Expert review (if available)
- User feedback collection

### Continuous Improvement
- Regularly update analysis algorithms
- Incorporate new scientific evidence
- Optimize user experience
- Expand feature scope

## References

### Clinical Guidelines
- American Dental Association (ADA) Guidelines
- World Health Organization (WHO) Oral Health Guidelines
- Chinese Stomatological Association Clinical Guidelines
- Cochrane Oral Health Group Systematic Reviews

### Assessment Tools
- DMFT Index (Decayed, Missing, Filled Teeth Index)
- CPI Index (Community Periodontal Index)
- Oral Health Impact Profile (OHIP-14)
- Caries Risk Assessment Tool (CAT)

### Data Sources
- User-recorded data
- Nutrition module data
- Chronic disease module data
- Medication module data
- Eye health module data

## Limitations

### System Limitations
- Cannot replace professional dental examinations
- Cannot perform radiographic examinations
- Cannot perform laboratory tests
- Analysis results are affected by data quality

### Data Limitations
- Depends on user recording accuracy
- Records may be incomplete
- Subjective assessments may be biased
- Time span may be insufficient

### Recommendation Limitations
- Cannot account for all individual factors
- Cannot predict all complications
- Must be combined with clinical judgment
- Cannot guarantee 100% accuracy

## Future Extensions

### Planned Features
- AI image recognition (dental X-ray analysis)
- Voice record entry
- Smart reminder system
- Community support features
- Integration with dental practice systems

### Research Directions
- Machine learning prediction models
- Personalized prevention strategies
- Genetic risk analysis
- Microbiome analysis
