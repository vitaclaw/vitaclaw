---
name: emergency-card
description: "Generates a medical emergency information summary card for quick access during emergencies. Extracts critical data (allergies, medications, acute conditions, implants) from health records and outputs in multiple formats (HTML, JSON, text, QR code). Use when the user needs travel prep, emergency info, a medical card, or asks about first-aid information."
version: 1.0.0
user-invocable: true
argument-hint: "[generate | standard | child | elderly | severe] [a4 | wallet | large]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🆘","category":"health-scenario"}}
---

# Emergency Medical Information Card Generator

Generates a medical information summary for quick access during emergencies or hospital visits.

## Core Features

### 1. Emergency Information Extraction
Extracts the most critical information from the user's health data:
- **Severe Allergies**: Prioritizes grade 4 (anaphylaxis) and grade 3 allergies
- **Current Medications**: Active medication names, dosages, and frequencies
- **Acute Conditions**: Medical conditions requiring emergency treatment
- **Implants**: Pacemakers, stents, etc. (affects diagnostic imaging and treatment)
- **Emergency Contacts**: Family members for quick contact

### 2. Information Priority Ranking
Ranks information by medical urgency:
1. **P0 - Critical**: Anaphylaxis, severe drug allergies, life-threatening conditions
2. **P1 - Important**: Current medications, chronic diseases, implants
3. **P2 - General**: Blood type, age, weight, recent test results

### 3. Multiple Output Formats
Supports various output formats for different scenarios:
- **HTML Format**: Printable web page using Tailwind CSS and Lucide icons (recommended)
- **JSON Format**: Structured data for system integration
- **Text Format**: Concise and readable, suitable for printing and carrying
- **PDF Format**: Professional printing, suitable for long-term storage

#### HTML Format
Generates a standalone HTML file including:
- Tailwind CSS styling (via CDN)
- Lucide icons (via CDN)
- Responsive design
- Print optimization
- Multiple size variants (A4, wallet card, large print)
- Automatic card type detection (standard, child, elderly, severe allergy)

Usage:
```bash
# Generate standard card
python scripts/generate_emergency_card.py

# Specify card type
python scripts/generate_emergency_card.py standard
python scripts/generate_emergency_card.py child
python scripts/generate_emergency_card.py elderly
python scripts/generate_emergency_card.py severe

# Specify print size
python scripts/generate_emergency_card.py standard a4       # A4 standard
python scripts/generate_emergency_card.py standard wallet   # Wallet card
python scripts/generate_emergency_card.py standard large    # Large print (elderly)
```

Output file: `emergency-cards/emergency-card-{variant}-{YYYY-MM-DD}.html`

### 4. Offline Availability
- Supports saving to phone (photos, files)
- Supports printing for carrying (wallet, bag)
- Supports cloud backup (optional)

## Usage Instructions

### Trigger Conditions
Use this skill when the user mentions the following scenarios:
- "Generate an emergency medical information card"
- "I'm traveling, how can I quickly provide medical information"
- "Organize my allergy information into a card"
- "Emergency first-aid information"
- "Prepare materials for a doctor visit"
- "Medical information summary"

### Execution Steps

#### Step 1: Read User Base Data
Read information from the following data sources:

```javascript
// 1. User profile
const profile = readFile('data/profile.json');

// 2. Allergy history
const allergies = readFile('data/allergies.json');

// 3. Current medications
const medications = readFile('data/medications/medications.json');

// 4. Radiation records
const radiation = readFile('data/radiation-records.json');

// 5. Surgical records (search for implants)
const surgeries = glob('data/surgical-records/**/*.json');

// 6. Discharge summaries (search for acute conditions)
const dischargeSummaries = glob('data/discharge-summaries/**/*.json');
```

#### Step 2: Extract Key Information

##### 2.1 Basic Information
```javascript
const basicInfo = {
  name: profile.basic_info?.name || "Not set",
  age: calculateAge(profile.basic_info?.birth_date),
  gender: profile.basic_info?.gender || "Not set",
  blood_type: profile.basic_info?.blood_type || "Unknown",
  weight: `${profile.basic_info?.weight} ${profile.basic_info?.weight_unit}`,
  height: `${profile.basic_info?.height} ${profile.basic_info?.height_unit}`,
  bmi: profile.calculated?.bmi,
  emergency_contacts: profile.emergency_contacts || []
};
```

#### 2.2 Severe Allergies
```javascript
// Filter for grade 3-4 severe allergies
const criticalAllergies = allergies.allergies
  .filter(a => a.severity_level >= 3 && a.current_status.status === 'active')
  .map(a => ({
    allergen: a.allergen.name,
    severity: `Allergy ${getSeverityLabel(a.severity_level)} (Grade ${a.severity_level})`,
    reaction: a.reaction_description,
    diagnosed_date: a.diagnosis_date
  }));
```

#### 2.3 Chronic Disease Diagnoses
```javascript
// Extract diagnosis information from chronic disease management data
const chronicConditions = [];

// Hypertension
try {
  const hypertensionData = readFile('data/hypertension-tracker.json');
  if (hypertensionData.hypertension_management?.diagnosis_date) {
    chronicConditions.push({
      condition: 'Hypertension',
      diagnosis_date: hypertensionData.hypertension_management.diagnosis_date,
      classification: hypertensionData.hypertension_management.classification,
      current_bp: hypertensionData.hypertension_management.average_bp,
      risk_level: hypertensionData.hypertension_management.cardiovascular_risk?.risk_level
    });
  }
} catch (e) {
  // File does not exist or read failed, skip
}

// Diabetes
try {
  const diabetesData = readFile('data/diabetes-tracker.json');
  if (diabetesData.diabetes_management?.diagnosis_date) {
    chronicConditions.push({
      condition: diabetesData.diabetes_management.type === 'type_1' ? 'Type 1 Diabetes' : 'Type 2 Diabetes',
      diagnosis_date: diabetesData.diabetes_management.diagnosis_date,
      duration_years: diabetesData.diabetes_management.duration_years,
      hba1c: diabetesData.diabetes_management.hba1c?.history?.[0]?.value,
      control_status: diabetesData.diabetes_management.hba1c?.achievement ? 'Well controlled' : 'Needs improvement'
    });
  }
} catch (e) {
  // File does not exist or read failed, skip
}

// COPD
try {
  const copdData = readFile('data/copd-tracker.json');
  if (copdData.copd_management?.diagnosis_date) {
    chronicConditions.push({
      condition: 'COPD',
      diagnosis_date: copdData.copd_management.diagnosis_date,
      gold_grade: `GOLD Grade ${copdData.copd_management.gold_grade}`,
      cat_score: copdData.copd_management.symptom_assessment?.cat_score?.total_score,
      exacerbations_last_year: copdData.copd_management.exacerbations?.last_year
    });
  }
} catch (e) {
  // File does not exist or read failed, skip
}
```

#### 2.4 Current Medications
```javascript
// Include only active medications
const currentMedications = medications.medications
  .filter(m => m.active === true)
  .map(m => ({
    name: m.name,
    dosage: `${m.dosage.value}${m.dosage.unit}`,
    frequency: getFrequencyLabel(m.frequency),
    instructions: m.instructions,
    warnings: m.warnings || []
  }));
```

##### 2.4 Medical Conditions
Extract diagnosis information from discharge summaries:
```javascript
const medicalConditions = dischargeSummaries
  .flatMap(ds => {
    const data = readFile(ds.file_path);
    return data.diagnoses || [];
  })
  .map(d => ({
    condition: d.condition,
    diagnosis_date: d.date,
    status: d.status || "Under follow-up"
  }));
```

##### 2.5 Implants
Extract implant information from surgical records:
```javascript
const implants = surgeries
  .flatMap(s => {
    const data = readFile(s.file_path);
    return data.procedure?.implants || [];
  })
  .map(i => ({
    type: i.type,
    implant_date: i.date,
    hospital: i.hospital,
    notes: i.notes
  }));
```

##### 2.6 Recent Radiation Exposure
```javascript
const recentRadiation = {
  total_dose_last_year: calculateTotalDose(radiation.records, 'last_year'),
  last_exam: radiation.records[radiation.records.length - 1]
};
```

#### Step 3: Generate Information Card

Organize information by priority:
```javascript
const emergencyCard = {
  version: "1.0",
  generated_at: new Date().toISOString(),
  basic_info: basicInfo,
  critical_allergies: criticalAllergies.sort(bySeverityDesc),
  current_medications: currentMedications,
  medical_conditions: [...medicalConditions, ...chronicConditions], // Merge acute and chronic conditions
  implants: implants,
  recent_radiation_exposure: recentRadiation,
  disclaimer: "This information card is for reference only and does not replace professional medical diagnosis",
  data_source: "my-his Personal Health Information System",
  chronic_conditions: chronicConditions // Separate field for easy access
};
```

#### Step 4: Format Output

##### JSON Format
Output structured JSON data directly.

##### Text Format
Generate a readable text card:
```
+===========================================================+
|              EMERGENCY MEDICAL INFORMATION CARD            |
+===========================================================+
| Name: John Doe                    Age: 35                  |
| Blood Type: A+                    Weight: 70kg             |
+===========================================================+
| SEVERE ALLERGIES                                           |
| --------------------------------------------------------- |
| * Penicillin - Anaphylaxis (Grade 4) CRITICAL             |
|   Reaction: Dyspnea, laryngeal edema, loss of             |
|   consciousness                                           |
+===========================================================+
| CURRENT MEDICATIONS                                        |
| --------------------------------------------------------- |
| * Amlodipine 5mg - Once daily (Hypertension)              |
| * Metformin 1000mg - Twice daily (Diabetes)                |
+===========================================================+
| CHRONIC CONDITIONS                                         |
| --------------------------------------------------------- |
| * Hypertension (Diagnosed 2023-01-01, Grade 1, Controlled)|
|   Average BP: 132/82 mmHg                                 |
| * Type 2 Diabetes (Diagnosed 2022-05-10, HbA1c 6.8%)      |
|   Control Status: Good                                     |
| * COPD (Diagnosed 2020-03-15, GOLD Grade 2)               |
|   CAT Score: 18                                            |
+===========================================================+
| OTHER CONDITIONS                                           |
| --------------------------------------------------------- |
| (Other acute conditions or surgical diagnoses, if any)     |
+===========================================================+
| IMPLANTS                                                   |
| --------------------------------------------------------- |
| * Cardiac Pacemaker (Implanted 2022-06-10)                 |
|   Hospital: XX Hospital                                    |
|   Note: Regular follow-up required, avoid MRI              |
+===========================================================+
| EMERGENCY CONTACTS                                         |
| --------------------------------------------------------- |
| * Jane Doe (Spouse) - 138****1234                          |
+===========================================================+
| DISCLAIMER                                                 |
| This card is for reference only and does not replace       |
| professional medical diagnosis                             |
| Generated: 2025-12-31 12:34:56                             |
+===========================================================+
```

##### QR Code Format
Convert JSON data to a QR code image:
```javascript
const qrCode = generateQRCode(JSON.stringify(emergencyCard));
emergencyCard.qr_code = qrCode;
```

#### Step 5: Save File

Save the file in the user's chosen format:
```javascript
// JSON format
saveFile('emergency-card.json', JSON.stringify(emergencyCard, null, 2));

// Text format
saveFile('emergency-card.txt', generateTextCard(emergencyCard));

// QR code format
saveFile('emergency-card-qr.png', emergencyCard.qr_code);
```

#### Step 6: Output Confirmation

```
Emergency medical information card generated successfully.

File location: data/emergency-cards/emergency-card-2025-12-31.json
Generated at: 2025-12-31 12:34:56

Included information:
━━━━━━━━━━━━━━━━━━━━━━━━━━
- Basic information (name, age, blood type)
- Severe allergies (1 grade-4 allergy)
- Current medications (2 medications)
- Medical conditions (2 conditions)
- Implants (1 item)
- Emergency contacts (1 person)

Recommendations:
━━━━━━━━━━━━━━━━━━━━━━━━━━
- Save the JSON file to your phone's cloud storage
- Save the QR code to your phone's photo album
- Print the text version and carry it with you
- Update the information before traveling

Important Notes:
━━━━━━━━━━━━━━━━━━━━━━━━━━
- This information card is for reference only and does not replace professional medical diagnosis
- Update regularly (recommended every 3 months or when health information changes)
- If you have severe allergies, carry an allergy emergency card at all times
```

## Data Sources

### Primary Data Sources
- **data/profile.json**: User basic information, blood type, emergency contacts
- **data/allergies.json**: Allergy history and severity grading
- **data/medications/medications.json**: Current medication plan and dosages

### Chronic Disease Data Sources
- **data/hypertension-tracker.json**: Hypertension management data (diagnosis date, classification, BP control, target organ damage, cardiovascular risk)
- **data/diabetes-tracker.json**: Diabetes management data (type, HbA1c, blood glucose control, complication screening)
- **data/copd-tracker.json**: COPD management data (GOLD grade, CAT score, exacerbation history, pulmonary function)

### Supplementary Data Sources
- **data/radiation-records.json**: Recent radiation exposure records
- **data/surgical-records/**/*.json**: Surgical implant information
- **data/discharge-summaries/**/*.json**: Medical diagnosis information

### Optional Data Sources
- **data/index.json**: Global data index

## Safety Principles

### Must Follow
- Do NOT add medication recommendations (only list current medications)
- Do NOT provide diagnostic conclusions (only list known diagnoses)
- Do NOT give treatment advice (does not replace a physician)
- Include disclaimer (for reference only)

### Information Accuracy
- Only extract recorded information (do not speculate or infer)
- Label information source and last updated time
- Recommend regular information updates

### Privacy Protection
- Sensitive information can be optionally hidden
- Phone numbers partially masked (e.g., 138****1234)
- All data stored locally only

## Error Handling

### Missing Data
- **Missing allergy data**: Output "No allergy history recorded"
- **Missing medication data**: Output "No current medications recorded"
- **Missing implant data**: Output "No implants"

### File Read Failure
- **Cannot read profile.json**: Use default values (name: Not set)
- **Cannot read allergies.json**: Skip allergy information
- **Continue generating other information**: Do not abort due to a single file failure

### QR Code Generation Failure
- Fall back to text format output
- Prompt the user to record information manually

## Example Output

For a complete example, see [examples.md](examples.md).

## Test Data

Test data files are located at [test-data/emergency-example.json](test-data/emergency-example.json).

## Format Reference

For detailed output format specifications, see [formats.md](formats.md).
