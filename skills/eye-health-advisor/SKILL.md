---
name: eye-health-advisor
description: "Provides eye health guidance including 20-20-20 rule reminders, screen time management, vision change tracking, and dry eye prevention tips. Use when the user asks about eye strain, screen time impact, vision health, or wants eye care reminders."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"👁️","category":"health"}}
---

# Eye Health Advisor

A comprehensive skill for managing eye health, reducing digital eye strain, tracking vision changes, and providing evidence-based guidance for long-term ocular wellness.

**Medical Disclaimer:** This skill provides general eye health information and is not a substitute for professional eye care. Always consult an ophthalmologist or optometrist for diagnosis and treatment. See the Alerts and Safety section for urgent warning signs.

---

## Capabilities

### 1. Screen Time & Eye Strain Management

#### The 20-20-20 Rule
Every **20 minutes** of screen use, look at something **20 feet (~6 meters) away** for at least **20 seconds**. This relaxes the ciliary muscle and reduces accommodative strain.

#### Recommended Screen Break Schedule
| Screen Time | Break Duration | Activity |
|-------------|---------------|----------|
| Every 20 min | 20 seconds | 20-20-20 rule (distance gaze) |
| Every 60 min | 5-10 minutes | Stand, stretch, walk around |
| Every 2 hours | 15-20 minutes | Extended break away from all screens |
| After 8+ hours | 30+ minutes | Prolonged rest, outdoor time if possible |

#### Optimal Screen Setup
- **Distance:** Arm's length (~50-70 cm / 20-28 inches) from the screen.
- **Position:** Top of the monitor at or slightly below eye level. The center of the screen should be 15-20 degrees below your horizontal line of sight.
- **Tilt:** Screen tilted back 10-20 degrees to reduce glare and neck strain.
- **Font size:** Increase text size so you can read comfortably without leaning forward.

#### Monitor Brightness & Blue Light
- Match screen brightness to the ambient lighting in your environment. The screen should not feel like a light source or appear dull/gray.
- Use warm color temperature settings in the evening (3000-4000K).
- Enable built-in blue light filters (Night Shift, Night Light, f.lux) starting 2-3 hours before bedtime.
- Reduce contrast to a comfortable level; overly high contrast increases strain.
- Position the screen to avoid glare from windows or overhead lights. Use an anti-glare screen protector if needed.

#### Blink Rate Awareness
- **Normal blink rate:** 15-20 blinks per minute.
- **During screen use:** Drops to 5-7 blinks per minute, leading to tear film instability and dryness.
- **Countermeasures:**
  - Practice conscious blinking: perform a full, deliberate blink every few seconds when you notice dryness.
  - Post a "BLINK" reminder note near your screen.
  - Use artificial tears before extended screen sessions.

---

### 2. Daily Screen Time Logging

Track screen time and symptoms daily. When the user requests logging, record the following fields.

#### Log Entry Fields
| Field | Type | Description |
|-------|------|-------------|
| `date` | date | Date of the log entry (YYYY-MM-DD) |
| `total_screen_hours` | number | Total hours of screen exposure for the day |
| `breaks_taken` | number | Number of intentional screen breaks taken |
| `symptoms` | list | Any symptoms experienced: `strain`, `dryness`, `headache`, `blurred_vision`, `tearing`, `light_sensitivity`, `neck_pain` |
| `screen_types` | list | Types of screens used: `computer`, `phone`, `tablet`, `TV`, `e-reader` |
| `notes` | text | Optional free-text notes (lighting conditions, new glasses, etc.) |

#### Storage Format
Daily logs are stored in `items/eye-health-daily/YYYY-MM-DD.md` with YAML frontmatter:

```yaml
---
type: eye-health-daily-log
date: 2026-03-22
total_screen_hours: 9.5
breaks_taken: 12
symptoms:
  - dryness
  - strain
screen_types:
  - computer
  - phone
notes: "Worked late, forgot evening breaks"
---
```

#### Weekly Aggregation
At the end of each week (or on request), compute:
- Average daily screen hours
- Total breaks taken vs. recommended
- Symptom frequency distribution
- Trend comparison with previous weeks

---

### 3. Dry Eye Prevention & Management

#### Environmental Factors
- **Humidity:** Maintain indoor humidity at 40-60%. Use a humidifier in dry climates or heated/air-conditioned rooms.
- **Air conditioning & heating:** Avoid direct airflow on the face and eyes. Redirect vents away from your workspace.
- **Wind:** Wear wraparound glasses or sunglasses outdoors on windy days.
- **Altitude & air travel:** Cabin air is extremely dry; use artificial tears proactively during flights.

#### Artificial Tears Guidance
- **Preservative-free** formulations are recommended for use more than 4 times per day.
- **Preserved drops** are acceptable for occasional use (up to 4 times daily).
- Apply drops before symptoms worsen, not just when eyes feel dry.
- Gel-based drops or ointments can be used at bedtime for overnight relief.
- Avoid drops that "reduce redness" (vasoconstrictors) as a substitute for lubricating tears.

#### Warm Compress Technique
1. Soak a clean washcloth in warm water (40-45 degrees C / 104-113 degrees F). Alternatively, use a microwaveable eye mask designed for this purpose.
2. Close your eyes and place the compress over both eyes.
3. Hold for **10 minutes**. Re-warm as needed to maintain temperature.
4. After removing, gently massage the eyelids in a downward motion (upper lids) and upward motion (lower lids) to express meibomian glands.
5. Perform once or twice daily, especially before bed.

#### Lid Hygiene
- Use a gentle, tear-free cleanser or commercially available lid scrub pads.
- Clean along the lash line with a cotton swab or pad using light, horizontal strokes.
- Rinse with warm water.
- Perform daily, particularly if prone to blepharitis or meibomian gland dysfunction.

#### Omega-3 Fatty Acids
- Omega-3s (EPA and DHA) support healthy tear film lipid layer production.
- Dietary sources: fatty fish (salmon, mackerel, sardines), flaxseed, chia seeds, walnuts.
- Supplementation: 1000-2000 mg combined EPA/DHA daily (consult a healthcare provider before starting).
- Benefits may take 6-12 weeks of consistent intake to become noticeable.

#### Screen Positioning for Dry Eyes
- Position the screen so your gaze is directed **slightly downward**. This reduces the exposed ocular surface area, slowing tear evaporation.
- Avoid placing screens near air vents, fans, or open windows with drafts.

---

### 4. Vision Change Tracking

Track and monitor vision changes over time. Prompt the user to record any new or changing symptoms.

#### Vision Log Entry Fields
| Field | Type | Description |
|-------|------|-------------|
| `date` | date | Date of observation (YYYY-MM-DD) |
| `test_type` | text | Type of assessment: `self_check`, `optometrist_exam`, `ophthalmologist_exam`, `online_screening` |
| `result` | text | Result summary if available (e.g., "OD -2.50, OS -2.75") |
| `symptoms` | list | Symptoms: `blurring_distance`, `blurring_near`, `floaters`, `flashes`, `double_vision`, `color_changes`, `halos`, `tunnel_vision`, `light_sensitivity` |
| `notes` | text | Additional context |

#### Storage
Vision change entries are stored in `items/eye-health.md` as an appended log:

```markdown
## Vision Log

### 2026-03-22
- **Test type:** self_check
- **Symptoms:** blurring_distance
- **Notes:** Noticed difficulty reading road signs while driving at night
```

#### Eye Exam Reminders
| Population | Recommended Frequency |
|-----------|----------------------|
| Adults 18-39, no risk factors | Every 2 years |
| Adults 40-64, no risk factors | Every 1-2 years |
| Adults 65+ | Annually |
| Diabetes or family history of glaucoma | Annually at any age |
| Contact lens wearers | Annually |
| High myopia (>-6.00 D) | Annually (retinal exam) |
| Post-LASIK/refractive surgery | Per surgeon's schedule, then annually |

When the user has not logged an eye exam in over the recommended interval, flag a reminder.

---

### 5. Eye Health Score (0-100)

Calculate an overall eye health score based on recent behavior and symptom data.

#### Score Components

| Component | Weight | Description | Scoring |
|-----------|--------|-------------|---------|
| Screen Habits | 30% | Screen time, setup ergonomics, blue light management | 0-30 based on daily hours (<6h=30, 6-8h=22, 8-10h=15, 10-12h=8, >12h=0) and ergonomic setup compliance |
| Break Compliance | 25% | Adherence to 20-20-20 rule and hourly breaks | 0-25 based on ratio of breaks taken to recommended (target: 3 per hour of screen time) |
| Symptom Frequency | 25% | Frequency and severity of eye-related symptoms | 25=no symptoms, 18=occasional mild, 12=frequent mild, 6=moderate, 0=severe/persistent |
| Preventive Care | 20% | Eye exams, supplements, exercises, protective measures | 0-20 based on: recent eye exam (8pts), daily exercises (4pts), UV protection (4pts), adequate hydration/nutrition (4pts) |

#### Score Interpretation
| Score Range | Rating | Guidance |
|-------------|--------|----------|
| 85-100 | Excellent | Maintain current habits. Continue regular checkups. |
| 70-84 | Good | Minor improvements possible. Review break compliance. |
| 50-69 | Fair | Multiple areas need attention. Create an improvement plan. |
| 30-49 | Poor | Significant changes needed. Prioritize breaks and symptom management. |
| 0-29 | Critical | Seek professional evaluation. Substantially reduce screen time. |

---

### 6. Eye Exercise Library

Recommend exercises based on symptoms and goals. Each exercise includes instructions, duration, and frequency.

#### Palming
- **Purpose:** Relaxation, relief from strain and fatigue.
- **Instructions:**
  1. Rub your hands together briskly for 10-15 seconds to generate warmth.
  2. Close your eyes and gently cup your palms over them. Do not press on the eyeballs.
  3. Fingers rest on your forehead; the heel of each hand rests on your cheekbone.
  4. Breathe deeply and focus on the darkness for 1-2 minutes.
- **Frequency:** Every 1-2 hours during screen work, or whenever eyes feel fatigued.

#### Figure-8 Tracking
- **Purpose:** Improve eye muscle flexibility and coordination.
- **Instructions:**
  1. Imagine a large figure-8 (infinity symbol) lying on its side, about 10 feet in front of you.
  2. Slowly trace the figure-8 with your eyes, following the path smoothly.
  3. Trace 5 times in one direction, then 5 times in the opposite direction.
- **Frequency:** 2-3 times daily.

#### Near-Far Focus Shifting
- **Purpose:** Strengthen accommodation (focus-shifting ability), reduce strain from prolonged near work.
- **Instructions:**
  1. Hold your thumb or a pen 15-20 cm from your face.
  2. Focus on it for 5 seconds until the detail is sharp.
  3. Shift your gaze to an object 20+ feet away. Focus for 5 seconds.
  4. Alternate back and forth 10-15 times.
- **Frequency:** 3-4 times daily, especially during screen work.

#### Circular Eye Movements
- **Purpose:** Improve range of motion, reduce stiffness in extraocular muscles.
- **Instructions:**
  1. Sit comfortably. Keep your head still.
  2. Slowly roll your eyes in a large clockwise circle. Complete 5 rotations.
  3. Pause, then roll 5 times counterclockwise.
  4. Keep movements smooth and controlled; do not strain.
- **Frequency:** 2-3 times daily.

#### Pencil Push-Ups (Convergence Exercise)
- **Purpose:** Strengthen convergence ability, helpful for convergence insufficiency.
- **Instructions:**
  1. Hold a pencil at arm's length, tip pointing up, at eye level.
  2. Focus on the tip of the pencil.
  3. Slowly bring the pencil toward your nose while maintaining a single, clear image.
  4. Stop when the pencil appears to double. Hold for 3 seconds.
  5. Slowly move the pencil back to arm's length.
  6. Repeat 10-15 times.
- **Frequency:** 2-3 sets daily, especially if experiencing convergence issues.

---

### 7. Age-Related Eye Health Awareness

Provide age-appropriate eye health information and screening reminders.

#### Presbyopia (Age 40+)
- **What it is:** Gradual loss of the eye's ability to focus on near objects, caused by hardening of the lens.
- **Signs:** Difficulty reading small print, needing to hold reading material farther away, eye strain during close work.
- **Management:** Reading glasses, bifocals, progressive lenses, or multifocal contact lenses. Ensure adequate lighting for near tasks.

#### Cataract Risk Factors
- **Age:** Risk increases significantly after age 60.
- **Modifiable risk factors:** UV exposure (wear UV-blocking sunglasses), smoking, excessive alcohol, diabetes, prolonged corticosteroid use, eye trauma.
- **Prevention:** UV protection, smoking cessation, blood sugar control, antioxidant-rich diet (vitamins C, E, lutein, zeaxanthin).
- **When to seek care:** Cloudy/blurry vision, faded colors, glare sensitivity, poor night vision, frequent prescription changes.

#### Glaucoma Screening
- **Why it matters:** Glaucoma causes irreversible optic nerve damage, often without symptoms until vision loss is significant.
- **Risk factors:** Age >60, family history, African or Hispanic ancestry, high myopia, elevated intraocular pressure, thin corneas.
- **Screening:** Comprehensive dilated eye exam including tonometry (pressure measurement) and optic nerve evaluation.
- **Frequency:** Every 1-2 years after age 40; annually if high risk.

#### Macular Degeneration Prevention
- **What it is:** Age-related macular degeneration (AMD) affects central vision and is a leading cause of vision loss in adults over 50.
- **Risk factors:** Age, smoking (2-3x increased risk), family history, UV exposure, cardiovascular disease, obesity.
- **Prevention strategies:**
  - Wear UV-blocking sunglasses with broad-spectrum protection.
  - Eat antioxidant-rich foods: dark leafy greens (lutein, zeaxanthin), colorful fruits and vegetables, fish (omega-3s).
  - Do not smoke. If you smoke, seek cessation support.
  - Maintain healthy blood pressure and cholesterol.
  - Consider AREDS2 supplements if advised by your eye doctor (for intermediate or advanced AMD).
- **Self-monitoring:** Use an Amsler grid monthly to check for distortions in central vision.

---

### 8. Blue Light & Sleep

#### Blue Light and Circadian Rhythm
- Blue light (wavelength ~450-495 nm) is the strongest suppressor of melatonin production.
- Daytime blue light exposure is beneficial: it promotes alertness and regulates the sleep-wake cycle.
- Evening blue light exposure delays melatonin onset and disrupts sleep architecture.

#### Evening Screen Use Recommendations
- **2-3 hours before bed:** Activate blue light filters (warm/night mode) on all devices.
- **1 hour before bed:** Ideally, stop using screens entirely. Switch to non-screen activities (reading a physical book, stretching, journaling).
- If screen use is unavoidable in the last hour, maximize blue light filtering, reduce brightness to minimum comfortable level, and keep sessions brief.

#### Blue Light Filter Guidance
| Method | Description | Effectiveness |
|--------|-------------|---------------|
| Software filters (Night Shift, Night Light, f.lux) | Shifts screen color temperature to warmer tones | Moderate; reduces but does not eliminate blue light |
| Blue light filtering glasses | Lenses with coatings that block a portion of blue light | Moderate; useful for those who cannot use software filters |
| Screen protectors with blue light filtering | Physical filter applied to the screen | Moderate; always-on protection |
| Amber-tinted glasses | Block most blue and some green light | High; most effective for evening use |

**Note:** Blue light glasses are not a substitute for reducing overall screen time and maintaining good screen habits. Their benefit is most significant in the evening hours.

---

## Output Format

### Daily Log Response
When recording a daily log, confirm with a structured summary:

```
Eye Health Daily Log - [DATE]
------------------------------
Screen Time:    [X] hours
Breaks Taken:   [X] / [recommended]
Symptoms:       [list or "None"]
Screen Types:   [list]
Notes:          [any notes]

Tip: [contextual tip based on today's data]
```

### Eye Health Check Response
When performing an eye health assessment:

```
Eye Health Check - [DATE]
==========================
Overall Score: [X]/100 ([Rating])

Breakdown:
  Screen Habits:     [X]/30
  Break Compliance:  [X]/25
  Symptom Frequency: [X]/25
  Preventive Care:   [X]/20

Top Recommendations:
1. [Most impactful improvement]
2. [Second priority]
3. [Third priority]

Next Eye Exam: [date or "Overdue - schedule soon"]
```

### Weekly Summary Response
When providing a weekly overview:

```
Eye Health Weekly Summary - [DATE RANGE]
==========================================
Avg Daily Screen Time:  [X] hours (trend: up/down/stable)
Total Breaks Taken:     [X] / [recommended]
Most Common Symptoms:   [list]
Score Trend:            [X] -> [Y] (improving/declining/stable)

Highlights:
- [Notable positive behavior]
- [Area of concern]

Next Week's Focus:
- [Specific actionable goal]
```

---

## Data Persistence

### Daily Log Files
- **Path:** `items/eye-health-daily/YYYY-MM-DD.md`
- One file per day with YAML frontmatter containing structured data and a markdown body for notes.
- Read previous entries to compute trends and weekly summaries.

### Master Eye Health File
- **Path:** `items/eye-health.md`
- Contains:
  - Vision change log (appended entries)
  - Eye exam history
  - Current corrective lens prescription (if shared by user)
  - Ongoing conditions or treatments
  - Personal risk factors
  - Preferred exercises and routines
- Use Glob and Read to find existing entries before writing updates. Use Edit to append new entries without overwriting existing data.

---

## Alerts and Safety

### Seek Immediate Medical Attention For:
- **Sudden vision loss** in one or both eyes (partial or complete)
- **Flashing lights accompanied by a sudden increase in floaters** (possible retinal detachment)
- **Eye injury** from impact, chemicals, or foreign objects
- **Severe eye pain**, especially with redness, nausea, or vomiting (possible acute glaucoma)
- **Sudden onset of double vision**
- **A dark curtain or shadow** moving across your field of vision

If the user reports any of these symptoms, **immediately advise them to seek emergency eye care or go to an emergency room.** Do not attempt to diagnose or manage these conditions.

### General Safety Notes
- This skill provides educational information based on widely accepted eye care guidelines.
- It is **not a replacement for professional eye examinations** or medical advice.
- Never advise the user to stop prescribed medications or treatments.
- If the user describes persistent or worsening symptoms, always recommend professional evaluation.
- Remind users that early detection is key for conditions like glaucoma, diabetic retinopathy, and macular degeneration.
