---
name: travel-health-analyzer
description: "Analyzes travel health data, assesses destination health risks, provides vaccination recommendations, and generates multilingual emergency medical information cards. Supports professional-grade travel health risk assessment with WHO/CDC data integration. Use when the user is planning a trip and wants health risk evaluation or travel medical preparation guidance."
version: 1.0.0
user-invocable: true
argument-hint: "[plan-trip | risk-assess | vaccine-check | med-kit | emergency-card | pre-trip-check | post-trip-monitor]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"✈️","category":"health-analyzer"}}
---

# Travel Health Analysis Skill

## IMPORTANT Medical Disclaimer

**All health advice and information provided by this skill is for reference only and cannot replace professional medical advice.**

- WARNING: All recommendations must be reviewed by a qualified physician
- WARNING: Vaccination and medication plans must be prescribed by a physician
- WARNING: No specific medical prescriptions or diagnoses are provided
- WARNING: Health risk data is sourced from WHO/CDC and may have latency
- WARNING: Seek immediate medical attention for emergencies

---

## Skill Features

### 1. Travel Health Planning Analysis

Analyzes the user's travel plan and provides comprehensive health preparation recommendations.

**Input:** Travel destination, dates, trip purpose
**Output:**
- Destination health risk assessment
- Required and recommended vaccination list
- Travel medical kit recommendations
- Preventive measure suggestions
- Pre-trip preparation timeline

**Analysis Points:**
- Identify destination infectious disease risks
- Assess food and water safety
- Confirm environmental risks (extreme heat, high altitude, etc.)
- Check current outbreak information
- Provide WHO/CDC reference links

---

### 2. Destination Health Risk Assessment

Professional-grade health risk assessment of travel destinations based on WHO/CDC data.

**Data Sources:**
- World Health Organization (WHO) International Travel and Health
- Centers for Disease Control and Prevention (CDC) Travel Health
- Local health authority official data

**Assessment Dimensions:**
- Infectious disease risk (dengue, malaria, cholera, hepatitis A, etc.)
- Food and water safety
- Environmental risk (extreme heat, high altitude, air pollution)
- Seasonal risk
- Current outbreak alerts

**Risk Levels:**
- **Low Risk** - Standard preventive measures
- **Medium Risk** - Special attention required
- **High Risk** - Strict preventive measures required
- **Very High Risk** - Consider postponing travel or taking special precautions

**Output Format:**
```markdown
## Destination Health Risk Assessment: Thailand

### Infectious Disease Risk
#### HIGH RISK - Dengue Fever
- **Transmission**: Mosquito bites
- **Seasonality**: Year-round
- **Symptoms**: High fever, headache, muscle and joint pain, rash
- **Prevention**: Use insect repellent, wear long sleeves, choose air-conditioned accommodations
- **Sources**: [WHO](https://www.who.int/ith) | [CDC](https://www.cdc.gov/dengue)

### Food and Water Safety
#### MEDIUM RISK
- Drink bottled or boiled water
- Avoid ice cubes
- Avoid raw food
- Peel fruit yourself

### Current Outbreak Alerts
No major outbreak alerts at this time
```

---

### 3. Vaccination Needs Analysis

Analyzes vaccination requirements based on destination and travel plan.

**Analysis Content:**
- Required vaccinations (e.g., yellow fever)
- Recommended vaccinations (e.g., hepatitis A, typhoid)
- Vaccination schedule planning
- Vaccine interaction checks
- Contraindication assessment

**Vaccine Checklist Template:**
```json
{
  "vaccine": "Hepatitis A Vaccine",
  "status": "completed|planned|not_required|contraindicated",
  "date": "2025-06-15",
  "booster_required": false,
  "notes": "Vaccination completed; provides long-term protection"
}
```

**Schedule Planning Principles:**
- 4-6 weeks before departure: Complete required vaccinations
- 2-4 weeks before departure: Complete recommended vaccinations
- Some vaccines require multiple doses; plan ahead accordingly

---

### 4. Smart Travel Medical Kit Recommendations

Generates a personalized travel medical kit list based on destination health risks and personal health status.

**Kit Categories:**

#### Prescription Medications
- Personal chronic disease medications (sufficient supply + extra)
- Malaria prophylaxis (if needed)
- Other physician-prescribed travel medications

#### Over-the-Counter Medications
- Anti-diarrheal (loperamide)
- Oral rehydration salts
- Fever/pain reducer (acetaminophen/ibuprofen)
- Antihistamine (loratadine)
- Motion sickness medication
- Antacid

#### Protective Supplies
- Insect repellent (DEET 20-30%)
- Sunscreen (SPF 50+)
- Mask (N95)

#### First Aid Supplies
- Adhesive bandages
- Disinfectant
- Gauze and bandages
- Thermometer
- Small scissors and tweezers

**Personalized Recommendations:**
- Adjust medications based on personal disease history
- Add or remove items based on destination risks
- Consider trip duration and activity types

---

### 5. Drug Interaction Checking

Checks potential interactions between travel medications and personal chronic disease medications.

**Check Content:**
- Malaria prophylaxis vs. chronic disease medications
- Temporary travel medications vs. regular medications
- Vaccine vs. drug interactions
- Food vs. drug interactions

**Common Interactions:**
- Doxycycline vs. antacids, calcium/iron supplements
- Mefloquine vs. certain cardiac medications
- Certain antibiotics vs. oral contraceptives

**Output:**
```markdown
## Drug Interaction Check Results

### WARNING: Potential Interaction Detected

**Doxycycline vs. Antacid**
- **Impact**: Antacids reduce doxycycline absorption
- **Recommendation**: Take 2 hours apart
- **Severity**: Moderate

### OK: No Interaction
- Amlodipine vs. travel medications: No known interactions
```

---

### 6. Multilingual Emergency Information Card Generation

Generates multilingual emergency cards containing key medical information.

**Supported Languages:**
- English (en)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- French (fr)
- Spanish (es)
- Thai (th)
- Vietnamese (vi)

**Card Content:**
```markdown
---
EMERGENCY MEDICAL INFORMATION
---

Name: Zhang San
Blood Type: A+
Date of Birth: 1990-01-01

ALLERGIES
- Penicillin (Severe: Rash, Difficulty breathing)

CURRENT MEDICATIONS
- Amlodipine 5mg Once daily (Blood pressure)

MEDICAL CONDITIONS
- Hypertension (Controlled)

EMERGENCY CONTACT
- Spouse: Li Si +86-138-1234-5678
- Doctor: Dr. Wang +86-10-8765-4321

---
[QR Code: Scan for complete medical records]
---
```

**QR Code Features:**
- Encodes key medical information summary
- Cloud access link (simulated)
- Supports offline access
- Shareable with medical personnel

---

### 7. Pre- and Post-Trip Health Checks

#### Pre-Trip Health Check

**Check Content:**
- Personal health status assessment
- Chronic disease condition confirmation
- Medication supply check
- Vaccination confirmation
- Health recommendations

**Output:**
```markdown
## Pre-Trip Health Check Report

### Overall Assessment: SUITABLE FOR TRAVEL

### Health Status
- Blood Pressure: Well controlled
- Chronic Conditions: Stable
- Medications: Sufficient supply

### Preparation Completion
- Vaccinations: Completed
- Travel Medical Kit: Prepared
- Insurance: Purchased
- Emergency Card: Pending generation

### Recommendations
1. Generate multilingual emergency card
2. Carry sufficient chronic disease medications
3. Monitor blood pressure during travel
```

#### Post-Trip Health Monitoring

**Monitoring Content:**
- Fever monitoring (continue for 2-4 weeks)
- Gastrointestinal symptoms
- Skin abnormalities
- Other discomfort symptoms

**Incubation Period Disease Reminders:**
- Malaria: May develop months after return
- Dengue Fever: Typically 3-14 days
- Typhoid: 1-3 weeks
- Hepatitis A: 2-6 weeks

---

## Data File Operations

### Reading Data
```bash
# Read travel health data
Read: data/travel-health-tracker.json

# Read example data
Read: data-example/travel-health-tracker.json
```

### Writing Data
```bash
# Update travel plan
Write: data/travel-health-tracker.json

# Save health check log
Write: data/travel-health-logs/pre-trip-assessment-YYYY-MM-DD.json
```

### Data Structure Validation
- Verify required fields exist
- Validate date format correctness
- Validate enum values
- Verify data completeness

---

## WHO/CDC Data Integration

### Static Database (Current Implementation)

Built-in health risk data for common travel destinations:
- Southeast Asia: Dengue fever, hepatitis A, typhoid, malaria
- Africa: Malaria, yellow fever, cholera, meningitis
- South America: Dengue fever, yellow fever, Zika virus
- Middle East: Middle East Respiratory Syndrome (MERS)

**Data Updates:** Manually updated; recommended quarterly

### Dynamic Query (Future Extension)

Planned integrations:
- WHO outbreak news RSS feeds
- CDC Travel Health API
- Local health authority outbreak reports

---

## Output Format

### Report Format
- Markdown format for readability
- Structured for programmatic processing
- Includes data source citations
- Includes timestamps

### Log Format
```json
{
  "log_id": "log_20250728_pretrip",
  "log_type": "pre_trip_assessment",
  "trip_id": "trip_20250801_seasia",
  "generated_at": "2025-07-28T10:00:00.000Z",
  "assessment_results": {
    "health_status": "suitable_for_travel",
    "vaccination_status": "completed",
    "risk_assessment": {...},
    "recommendations": [...]
  }
}
```

---

## Security and Privacy

### Data Protection
- Passport numbers stored encrypted
- QR codes do not contain complete sensitive information
- Supports data export and deletion

### Medical Safety
- All recommendations include disclaimers
- Emphasizes the necessity of physician consultation
- Does not provide specific prescriptions
- Cites authoritative data sources

---

## Usage Examples

### Analyze a Travel Plan
```
Input: "Planning a 14-day trip to Southeast Asia in August 2025"

Output:
1. Destination health risk assessment
2. Vaccination recommendations
3. Travel medical kit checklist
4. Preventive measures
5. Timeline
```

### Generate Emergency Card
```
Input: "Generate an emergency card in English, Chinese, Japanese, and Thai"

Output:
1. Multilingual card text
2. QR code (description)
3. Storage recommendations
```

### Assess Health Risks
```
Input: "Assess health risks for Thailand"

Output:
1. Infectious disease risk list
2. Food and water safety recommendations
3. Environmental risks
4. Current outbreak alerts
5. WHO/CDC reference links
```
