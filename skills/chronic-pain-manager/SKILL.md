---
name: chronic-pain-manager
description: "Manages chronic pain through pain diary logging, pattern analysis, weather and activity correlation, and non-pharmacological intervention suggestions. Use when the user reports pain, wants to track pain patterns, or seeks pain management strategies."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🩹","category":"health"}}
---

# Chronic Pain Manager

## Capabilities

### 1. Pain Diary Recording

Record structured pain entries with the following fields:

| Field | Description |
|-------|-------------|
| **date** | Date of the entry (YYYY-MM-DD) |
| **time** | Time of the entry (HH:MM) |
| **location** | Body area using body map categories (head, neck, upper back, lower back, left shoulder, right shoulder, left arm, right arm, left hand, right hand, chest, abdomen, left hip, right hip, left leg, right leg, left knee, right knee, left foot, right foot) |
| **intensity** | Pain intensity on the Numeric Rating Scale (NRS) 0-10 |
| **type** | Pain quality: sharp, dull, burning, throbbing, stabbing, aching, tingling |
| **duration** | How long the pain has lasted (minutes, hours, days) |
| **triggers** | What triggered or worsened the pain |
| **relief_measures** | What was done to relieve the pain and whether it helped |
| **medications_taken** | Any medications taken (name, dose, time taken) |
| **mood** | Current mood (1-10 or descriptive: anxious, calm, frustrated, hopeful, etc.) |
| **sleep_quality** | Previous night's sleep quality (1-10, hours slept, interruptions) |
| **activity_level** | Activity level for the day (sedentary, light, moderate, vigorous) |
| **notes** | Any additional observations or context |

### 2. Pain Intensity Scale (NRS 0-10)

| Score | Description |
|-------|-------------|
| 0 | No pain |
| 1-3 | Mild - noticeable but doesn't interfere with activities |
| 4-6 | Moderate - interferes with some activities |
| 7-9 | Severe - significantly limits activities |
| 10 | Worst imaginable pain |

When recording pain, always ask the user to rate on this scale. If they use descriptive words, map them to the appropriate range and confirm.

### 3. Pattern Analysis

Analyze pain diary entries to identify correlations and patterns across the following dimensions:

- **Time-of-day patterns**: Morning stiffness, afternoon fatigue, evening flares, nocturnal pain
- **Day-of-week patterns**: Work days vs weekends, specific day triggers
- **Activity correlation**: Which activities worsen pain (prolonged sitting, lifting, repetitive motions) and which improve it (walking, stretching, swimming)
- **Weather correlation**: Barometric pressure changes, humidity levels, temperature shifts, seasonal patterns
- **Sleep quality correlation**: Relationship between sleep duration/quality and next-day pain levels
- **Stress correlation**: Work stress, emotional events, anxiety levels and their impact on pain
- **Menstrual cycle correlation**: If applicable, track pain fluctuations across cycle phases (follicular, ovulatory, luteal, menstrual)
- **Medication effectiveness tracking**: Time to relief, duration of relief, side effects, tolerance patterns

When enough data is available (minimum 7 days), generate pattern insights automatically. For robust analysis, recommend at least 30 days of data.

### 4. Pain Score Trend (Weekly/Monthly)

Calculate and present the following summary statistics:

- **Average pain score** for the period
- **Peak pain score** and when it occurred
- **Lowest pain score** and when it occurred
- **Days with pain >5/10** (count and percentage)
- **Trend direction** (improving, stable, worsening) compared to previous period
- **Pain-free days** (count)

Present trends as a simple text-based visualization:

```
Week of 2026-03-16:
Mon: ████████░░ 8/10  (flare)
Tue: ██████░░░░ 6/10
Wed: █████░░░░░ 5/10
Thu: ████░░░░░░ 4/10
Fri: ████░░░░░░ 4/10
Sat: ███░░░░░░░ 3/10
Sun: ███░░░░░░░ 3/10
Avg: 4.7 | Peak: 8 | Low: 3 | Days >5: 2
```

### 5. Non-Pharmacological Interventions

Suggest evidence-based non-pharmacological interventions based on pain type, location, and patterns:

| Category | Techniques |
|----------|------------|
| **Heat/Cold** | Heat pads (for muscle tension, stiffness), ice packs (for acute inflammation, swelling), contrast therapy (alternating heat/cold for circulation) |
| **Movement** | Gentle stretching, yoga (particularly yin or restorative), swimming/aquatic therapy, walking, tai chi |
| **Mind-Body** | Meditation (body scan, mindfulness), deep breathing (4-7-8 technique, box breathing), progressive muscle relaxation, guided imagery |
| **Manual** | Self-massage, foam rolling, tennis ball release (trigger points), lacrosse ball for plantar fascia |
| **Lifestyle** | Sleep hygiene (consistent schedule, dark/cool room), anti-inflammatory diet (omega-3s, turmeric, reduce processed foods), stress reduction, ergonomic adjustments |
| **Other** | TENS (transcutaneous electrical nerve stimulation), acupuncture (professional referral), CBT for pain (cognitive behavioral therapy), biofeedback |

When suggesting interventions:
- Match to the specific pain type and location
- Start with the simplest, lowest-risk options
- Suggest trying one new intervention at a time to measure effectiveness
- Track which interventions were tried and their impact in the pain diary

### 6. Flare Management Protocol

When a user reports a pain flare (sudden increase of 3+ points or pain >7/10), guide them through a structured response:

**PEACE Protocol (Acute Phase - First 1-3 Days)**

| Step | Action |
|------|--------|
| **P**rotect | Reduce movement or loading of the painful area to a tolerable level. Avoid complete rest. |
| **E**levate | If applicable, elevate the affected limb above heart level. |
| **A**void anti-inflammatories initially | In the first 48 hours, inflammation is part of healing. Avoid NSAIDs unless advised by a physician. |
| **C**ompress | Use compression bandages if swelling is present. |
| **E**ducate | Understand that most flares are temporary. Reassure that flares do not necessarily mean damage. |

**LOVE Protocol (Recovery Phase - After Day 3)**

| Step | Action |
|------|--------|
| **L**oad management | Gradually reintroduce normal activities. Listen to the body but avoid fear-avoidance behavior. |
| **O**ptimism | Maintain a positive but realistic outlook. Pain flares are a normal part of chronic pain management. |
| **V**ascularisation | Gentle cardiovascular exercise (walking, cycling, swimming) to promote blood flow and healing. |
| **E**xercise | Resume regular exercise gradually. Movement is medicine. Modify intensity if needed, but keep moving. |

### 7. Functional Impact Assessment

Track how pain affects daily functioning across key life domains:

| Domain | Assessment |
|--------|------------|
| **Sleep** | Difficulty falling asleep, staying asleep, or waking refreshed (rate 1-10) |
| **Work** | Ability to perform job tasks, missed work days, reduced productivity (rate 1-10) |
| **Exercise** | Ability to maintain exercise routine, modifications needed (rate 1-10) |
| **Social activities** | Participation in social events, isolation tendencies (rate 1-10) |
| **Mood** | Emotional wellbeing, presence of frustration, anxiety, depression (rate 1-10) |
| **Daily tasks** | Ability to perform ADLs (cooking, cleaning, dressing, driving) (rate 1-10) |

Calculate a **Functional Impact Score** (average of all domains, 1-10 where 10 = no impact). Track this weekly to measure quality of life trends alongside pain scores.

## Output Format

### Pain Entry
When recording a new pain entry, output a structured summary:

```
## Pain Entry - [DATE] [TIME]
- Location: [body area]
- Intensity: [score]/10 ([description])
- Type: [pain type]
- Duration: [duration]
- Triggers: [triggers]
- Relief measures: [measures taken]
- Medications: [medications]
- Mood: [mood] | Sleep: [quality] | Activity: [level]
- Notes: [notes]
```

### Daily Summary
At end of day or on request, provide:
- Pain entries for the day
- Average/peak/low pain scores
- Interventions tried and effectiveness
- Functional impact summary

### Weekly/Monthly Pattern Report
- Pain score trends with text visualization
- Identified patterns and correlations
- Intervention effectiveness summary
- Functional impact trends
- Recommendations for the upcoming period

## Data Persistence

### Daily Pain Files
Store daily entries in: `daily/[YYYY-MM-DD].md` under a `## Pain Diary` section. Each entry is timestamped and appended throughout the day.

### Chronic Pain Master File
Maintain a cumulative record at: `items/chronic-pain.md` containing:
- Pain condition summary (diagnosed conditions, affected areas, baseline pain level)
- Medication list (current and past, with effectiveness notes)
- Intervention history (what has been tried, what works)
- Monthly summary statistics
- Provider information (pain specialist, PT, etc.)

Update the master file weekly or when significant changes occur.

## Alerts and Safety

### Medical Disclaimer
This tool is for **informational and self-tracking purposes only**. It is **not a substitute for professional medical advice, diagnosis, or treatment** from a qualified pain management specialist, physician, or healthcare provider.

### Important Limitations
- **Medication tracking is informational, not prescriptive.** Never adjust medication dosages based solely on this tool's output. Always consult your prescribing physician.
- Pain diary data can be shared with your healthcare provider to support clinical decision-making, but it does not replace clinical assessment.
- Pattern analysis identifies correlations, not causation.

### Seek Immediate Medical Care If You Experience:
- **Sudden severe headache** ("worst headache of my life") - may indicate stroke or aneurysm
- **Chest pain** especially with shortness of breath, sweating, or radiating to arm/jaw
- **Pain accompanied by numbness or weakness** in limbs - may indicate nerve compression or stroke
- **Pain after significant injury** especially with inability to bear weight or visible deformity
- **Fever with severe pain** - may indicate infection
- **Loss of bladder or bowel control** with back pain - may indicate cauda equina syndrome (emergency)

If any of these are reported, **immediately advise the user to call emergency services or go to the nearest emergency department**. Do not attempt to manage these situations through pain diary tracking.
