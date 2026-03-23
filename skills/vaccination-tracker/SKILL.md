---
name: vaccination-tracker
description: "Records vaccination history, tracks due dates for boosters, provides travel vaccination requirements, and maintains an immunization schedule. Use when the user logs vaccines, asks about upcoming vaccinations, or plans travel requiring immunizations."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"💉","category":"health"}}
---

# Vaccination Tracker

## Capabilities

### 1. Vaccination Record

Maintain a comprehensive record for each vaccination administered. Each entry includes the following fields:

| Field | Required | Description |
|---|---|---|
| vaccine_name | Yes | Name of the vaccine (e.g., Pfizer COVID-19, Shingrix) |
| date_administered | Yes | Date the vaccine was given (YYYY-MM-DD) |
| dose_number | Yes | Dose number in the series (e.g., 1 of 2, 2 of 3) |
| lot_number | No | Manufacturer lot number for the specific vial |
| provider | No | Name of clinic, pharmacy, or healthcare provider |
| site | Yes | Injection site (Left Arm, Right Arm, Left Thigh, Right Thigh, etc.) |
| next_due_date | Yes | Calculated date for the next dose or booster |
| notes | No | Any additional information (reactions, exemptions, etc.) |

When the user logs a vaccination, collect at minimum the required fields, calculate the next due date based on the standard schedule, and persist the record.

### 2. Standard Adult Immunization Schedule (CDC/WHO-based)

Reference schedule for recommending and tracking adult vaccinations:

| Vaccine | Primary Series | Booster Frequency |
|---|---|---|
| Influenza | Annual | Every year (fall) |
| COVID-19 | Primary + boosters | Per current guidelines |
| Tdap/Td | 1 Tdap then Td | Every 10 years |
| Shingles (Shingrix) | 2 doses (2-6 months apart) | Age 50+ |
| Pneumococcal | PCV20 or PCV15+PPSV23 | Age 65+ or risk factors |
| HPV | 2-3 doses | Through age 26 (catch-up to 45) |
| Hepatitis B | 3 doses (0, 1, 6 months) | If not previously vaccinated |
| Hepatitis A | 2 doses (0, 6 months) | If at risk |
| MMR | 1-2 doses | If born after 1957 without evidence of immunity |
| Varicella | 2 doses (4-8 weeks apart) | If no evidence of immunity |

Use the user's age, risk factors, and vaccination history to determine which vaccines are recommended, due, or overdue.

### 3. Pediatric Schedule Support

Track key childhood vaccines from birth through 18 years, following the CDC/WHO recommended timeline:

- **Birth**: Hepatitis B (dose 1)
- **2 months**: DTaP, IPV, Hib, PCV13, RV, HepB (dose 2)
- **4 months**: DTaP, IPV, Hib, PCV13, RV
- **6 months**: DTaP, IPV (if needed), Hib, PCV13, RV, HepB (dose 3), Influenza (annual from 6 months)
- **12-15 months**: MMR (dose 1), Varicella (dose 1), HepA (dose 1), PCV13 (dose 4), Hib (booster)
- **18 months**: HepA (dose 2)
- **4-6 years**: DTaP (dose 5), IPV (dose 4), MMR (dose 2), Varicella (dose 2)
- **11-12 years**: Tdap, HPV (2-3 doses), Meningococcal ACWY (dose 1)
- **16 years**: Meningococcal ACWY (booster), Meningococcal B (if indicated)

Support tracking for children by associating records with a named dependent.

### 4. Travel Vaccination Advisor

Provide region-specific vaccination recommendations for international travel:

| Vaccine | Regions | Notes |
|---|---|---|
| Yellow Fever | Sub-Saharan Africa, tropical South America | International Certificate of Vaccination required for entry to many countries; administer at least 10 days before travel |
| Typhoid | South Asia, Africa, Central/South America | Oral (4 doses) or injectable (1 dose); recommended 2+ weeks before travel |
| Japanese Encephalitis | Rural areas of East/Southeast Asia, Pacific Islands | 2-dose series; complete 1+ week before travel |
| Rabies (pre-exposure) | South/Southeast Asia, Africa, Central/South America | 3-dose series over 21-28 days; recommended for prolonged stays or animal exposure risk |
| Meningococcal | Sub-Saharan Africa (meningitis belt), required for Hajj/Umrah | Administer at least 10 days before travel |
| Cholera | Areas with active outbreaks (parts of Africa, Asia) | Oral vaccine; 2 doses 1-6 weeks apart |
| Malaria prophylaxis | Sub-Saharan Africa, South/Southeast Asia, Central/South America | Not a vaccine but critical reminder; prescribe antimalarials based on region-specific resistance patterns; start before travel per drug schedule |

When the user specifies a travel destination:
1. Identify required vaccinations (legally mandated for entry)
2. Identify recommended vaccinations (based on risk)
3. Generate a pre-travel timeline accounting for multi-dose schedules and lead times
4. Flag any vaccines the user has already completed

### 5. Reminder System

Actively manage vaccination timing:

- **Next due date calculation**: Automatically compute the next dose or booster date based on the vaccine schedule and the date of the last administered dose
- **Overdue flagging**: Identify any vaccinations that are past their recommended due date and flag them prominently
- **Pre-travel timeline**: For travel-related vaccines, calculate the optimal start date working backward from the departure date, accounting for:
  - Multi-dose series completion requirements
  - Minimum intervals between doses
  - Lead time (some vaccines need 4-6 weeks before departure)
- **Upcoming reminders**: List all vaccinations due within the next 30, 60, and 90 days
- **Annual reminders**: Flag recurring annual vaccines (Influenza, COVID-19 boosters) at the appropriate season

### 6. Immunization Completeness Score

Calculate a percentage score reflecting how up-to-date the user is on recommended vaccinations:

- **Inputs**: User age, known risk factors, vaccination history
- **Calculation**: (Number of recommended vaccines up-to-date) / (Total recommended vaccines for age and risk profile) x 100
- **Breakdown**: Show which vaccines contribute to or detract from the score
- **Categories**:
  - 90-100%: Fully up-to-date
  - 70-89%: Mostly current, minor gaps
  - 50-69%: Significant gaps, action recommended
  - Below 50%: Critical gaps, schedule appointments promptly

## Output Format

Provide output in the following formats depending on context:

### Vaccination Card
A formatted summary of all recorded vaccinations, displayed as a table:

```
| Vaccine | Date | Dose | Lot # | Provider | Site | Next Due |
|---|---|---|---|---|---|---|
| COVID-19 (Pfizer) | 2025-10-15 | Booster 3 | FN1234 | CVS Pharmacy | L Arm | 2026-10-15 |
| Tdap | 2023-03-01 | 1 | TD5678 | Dr. Smith | R Arm | 2033-03-01 |
```

### Reminder List
A prioritized list of upcoming and overdue vaccinations:

```
OVERDUE:
- Influenza (2025-2026 season) — was due by Nov 2025

DUE SOON (next 90 days):
- Shingrix dose 2 — due by 2026-04-15
- Hepatitis A dose 2 — due by 2026-06-01

UPCOMING:
- Td booster — due 2033-03-01
```

### Travel Prep Checklist
A timeline for travel-related vaccinations:

```
Trip to Kenya — Departure: 2026-06-01

REQUIRED:
- [ ] Yellow Fever — administer by 2026-05-22 (10 days before departure)

RECOMMENDED:
- [ ] Typhoid (injectable) — administer by 2026-05-18 (2 weeks before)
- [ ] Hepatitis A dose 1 — administer ASAP (ideally 4+ weeks before)
- [ ] Malaria prophylaxis — obtain prescription, start per drug schedule

ALREADY COMPLETE:
- [x] Tdap — current (2023-03-01)
- [x] COVID-19 — current booster (2025-10-15)
```

## Data Persistence

All vaccination records are stored in `items/vaccinations.md` with the following structure:

```markdown
# Vaccination Records

## Personal Information
- Name: [User Name]
- Date of Birth: [DOB]
- Known Allergies: [Any vaccine allergies]
- Risk Factors: [Immunocompromised, pregnancy, healthcare worker, etc.]

## Vaccination History

| Vaccine | Date | Dose | Lot # | Provider | Site | Next Due | Notes |
|---|---|---|---|---|---|---|---|
| [entries] |

## Dependents

### [Dependent Name] (DOB: [date])

| Vaccine | Date | Dose | Lot # | Provider | Site | Next Due | Notes |
|---|---|---|---|---|---|---|---|
| [entries] |
```

When updating records:
1. Read the existing `items/vaccinations.md` file (create if it does not exist)
2. Add the new entry to the appropriate table
3. Recalculate next due dates and completeness score
4. Write the updated file

## Alerts and Safety

**IMPORTANT MEDICAL DISCLAIMER**: This vaccination tracker is an organizational tool only. It does **not** constitute medical advice, diagnosis, or treatment.

- **Consult your healthcare provider** before making any vaccination decisions, especially regarding scheduling, contraindications, or special circumstances (pregnancy, immunocompromised status, allergies)
- **Vaccine contraindications and precautions** vary by individual; always discuss your full medical history with your doctor before receiving any vaccine
- **Report adverse reactions** to the appropriate authority:
  - **United States**: VAERS (Vaccine Adverse Event Reporting System) at https://vaers.hhs.gov
  - **United Kingdom**: Yellow Card Scheme at https://yellowcard.mhra.gov.uk
  - **European Union**: EudraVigilance via national competent authorities
  - **Canada**: CAEFISS (Canadian Adverse Events Following Immunization Surveillance System)
  - **Other countries**: Contact your national health authority
- **Seek immediate medical attention** if you experience severe symptoms after vaccination (difficulty breathing, swelling of face/throat, rapid heartbeat, dizziness, or widespread rash)
- Vaccination schedules and recommendations change over time; this tool uses general guidelines and may not reflect the most current recommendations
- This tool does **not** replace your official immunization records maintained by your healthcare provider or state/national immunization registry
