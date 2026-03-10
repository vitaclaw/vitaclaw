---
name: mental-wellness-companion
description: "Provides daily mental health support by coordinating PHQ-9/GAD-7 assessment, crisis detection, sleep-mood correlation, exercise prescription, and behavioral activation. CRITICAL: Crisis detection runs FIRST every interaction. Use when the user tracks mood, reports stress, or needs psychological support."
version: 1.0.0
user-invocable: true
argument-hint: "[mood-entry | weekly-assessment | crisis-check]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🧠","category":"health-scenario"}}
---

# Mental Wellness Companion

Scenario orchestration skill for daily mental health support. Coordinates crisis detection, PHQ-9/GAD-7 standardized assessment, sleep-mood correlation, exercise-mood correlation, cognitive-behavioral support, and behavioral activation goal tracking. Targets users who want a closed-loop pipeline from daily tracking to pattern recognition to risk detection to intervention support.

This skill does not perform analysis directly. It orchestrates multiple sub-skills in sequence.

**CRITICAL: Crisis detection runs FIRST on every interaction, before any other processing.**

## Crisis Resources -- Call Immediately If Needed

> **If you or someone near you is in crisis, contact help now:**
>
> - **China 24h Mental Health Hotline**: 400-161-9995
> - **Beijing Psychological Crisis Research & Intervention Center**: 010-82951332
> - **Lifeline (China)**: 400-821-1215
> - **988 Suicide & Crisis Lifeline (US)**: 988 (call or text)
> - **Emergency**: 120 (China) / 911 (US)
>
> **You are not alone. Asking for help is a sign of strength.**

## Medical Disclaimer

**This skill is a mental health support tool and does not replace professional counseling or psychiatric care.**

- This skill does not diagnose mental illness.
- PHQ-9/GAD-7 scores are screening tools only; confirmed diagnosis requires professional evaluation.
- Medication adjustments (antidepressants, anxiolytics, etc.) must be guided by a psychiatrist.
- Severe psychological crisis (self-harm/suicidal ideation): contact professional crisis intervention services immediately.
- All suggestions from this skill are supplementary and cannot substitute for in-person psychotherapy.

## PHQ-9 Depression Screening Scoring

| Score Range | Severity | Recommendation |
|-------------|----------|----------------|
| 0-4 | Minimal | Continue daily tracking |
| 5-9 | Mild depression | Monitor mood changes; strengthen self-care |
| 10-14 | Moderate depression | Recommend seeking counseling |
| 15-19 | Moderately severe depression | Strongly recommend professional psychotherapy |
| 20-27 | Severe depression | Immediate professional intervention required |

## GAD-7 Anxiety Screening Scoring

| Score Range | Severity | Recommendation |
|-------------|----------|----------------|
| 0-4 | Minimal | Continue daily tracking |
| 5-9 | Mild anxiety | Monitor anxiety triggers |
| 10-14 | Moderate anxiety | Recommend seeking counseling |
| 15-21 | Severe anxiety | Professional intervention required |

## Crisis Detection Rules -- Triggers for Immediate Action

**When ANY of the following is detected, immediately interrupt normal flow and display crisis resources:**

| Indicator | Condition | Action |
|-----------|-----------|--------|
| PHQ-9 total score | >= 20 | Display crisis resources + recommend immediate professional intervention |
| GAD-7 total score | >= 15 | Display crisis resources + recommend immediate professional intervention |
| PHQ-9 Question 9 (self-harm ideation) | >= 1 | **Immediately** display crisis resources; do NOT continue assessment |
| Self-harm/suicide-related expression | Any mention of self-harm, suicide, "life is meaningless", "don't want to live" | **Immediately** display crisis resources |
| Score spike | PHQ-9 or GAD-7 increased > 5 points from previous assessment | Display crisis resources + recommend urgently contacting a professional |
| Hopelessness expression | Mentions "no hope", "will never get better", "no way out" | Display crisis resources + gently validate feelings |

**Crisis detection has the highest priority. Complete crisis screening before outputting any analysis results.**

## Skill Chain

| Step | Skill | Trigger | Purpose |
|------|-------|---------|---------|
| 0 | `crisis-detection-intervention-ai` | **Every session (runs first)** | Text emotional safety scan, crisis signal detection |
| 1 | `mental-health-analyzer` | Every session | PHQ-9/GAD-7 assessment, mood pattern recognition |
| 2 | `sleep-analyzer` | Every session (when sleep data present) | Sleep quality analysis |
| 3 | `sleep-optimizer` | Every session (when sleep data present) | Sleep improvement recommendations |
| 4 | `fitness-analyzer` | Every session (when exercise data present) | Exercise-mood correlation analysis |
| 5 | `wearable-analysis-agent` | When wearable data is provided | HRV stress biomarker analysis, sleep staging, resting HR trend |
| 6 | `psychologist-analyst` | Every session | Cognitive distortion identification, coping strategy suggestions |
| 7 | `goal-analyzer` | Every session | Behavioral activation goal tracking |
| 8 | `adhd-daily-planner` | When ADHD needs are present | Executive function support |
| 9 | `health-memory` | Every session | Data persistence |

## Workflow

### Pre-Step -- Crisis Safety Screening (Mandatory Every Interaction)

- [ ] **Step 0 -- Crisis detection.** Invoke `crisis-detection-intervention-ai`. Scan user input text for emotional safety. Detect self-harm/suicide/hopelessness signals. If a crisis signal is detected: **immediately interrupt all subsequent steps**, display the crisis resources panel, and guide the user to contact professional help. If no crisis signal is detected: proceed to subsequent steps.

### Mode 1: Mood Entry (Daily)

- [ ] **Step 1 -- Mood and assessment.** Invoke `mental-health-analyzer`. If a periodic assessment is due (recommended every 2 weeks), guide the user through PHQ-9 and GAD-7 questionnaires. Record scores and compare against historical scores. Identify mood patterns (intraday fluctuations, weekly patterns, trigger factors). Identify common cognitive distortions (catastrophizing, black-and-white thinking, overgeneralization, etc.). Assess coping strategy effectiveness.
- [ ] **Step 2a -- Sleep quality analysis.** Invoke `sleep-analyzer`. Analyze sleep duration, sleep onset time, and number of awakenings. Compute sleep quality score. Identify sleep problem patterns (difficulty falling asleep, early waking, sleep fragmentation).
- [ ] **Step 2b -- Sleep optimization.** Invoke `sleep-optimizer`. Generate sleep improvement recommendations based on sleep data and mental state. Analyze correlation between sleep quality and mood scores. Provide specialized recommendations for anxiety/depression-related sleep issues (e.g., coping with pre-sleep rumination).
- [ ] **Step 3 -- Exercise prescription.** Invoke `fitness-analyzer`. Analyze exercise frequency, type, and duration. Calculate exercise-mood score correlation. Generate exercise prescription (research shows 150 min/week moderate-intensity aerobic exercise can match SSRI efficacy for mild-moderate depression). Track exercise-day vs rest-day mood differences.
- [ ] **Step 5 (optional) -- Wearable biometric analysis.** Invoke `wearable-analysis-agent` (when wearable data is provided). Analyze HRV metrics (SDNN, RMSSD) as validated stress and anxiety biomarkers; correlate HRV trends with PHQ-9/GAD-7 scores. Extract resting heart rate trend as an indicator of autonomic nervous system state. If wearable sleep data is available, provide device-measured sleep staging (deep/light/REM/awake) to enhance Step 2a's sleep quality analysis with objective data. Validate exercise prescription compliance from Step 3 using device-measured activity data.
- [ ] **Step 6a -- Cognitive-behavioral support.** Invoke `psychologist-analyst`. Identify cognitive distortion patterns. Provide CBT (Cognitive Behavioral Therapy) technique suggestions. Provide behavioral activation suggestions (break large goals into small, completable steps). Recommend mindfulness/relaxation techniques based on current stress level.
- [ ] **Step 6b -- Behavioral activation goal tracking.** Invoke `goal-analyzer`. Set and track daily micro-goals (e.g., "walk 15 minutes today", "talk to a friend"). Assess goal completion rate. Provide positive reinforcement for completed goals. Adjust goal difficulty to avoid adding to feelings of failure.
- [ ] **Step 7 -- Persist data.** Invoke `health-memory`. Write mental health data to `memory/health/daily/{YYYY-MM-DD}.md`. Update `memory/health/items/mental-health.md` (PHQ-9/GAD-7 longitudinal scores). Update `memory/health/items/sleep.md` (sleep quality longitudinal tracking).

### Mode 2: Weekly Assessment

- [ ] Execute all Mode 1 steps.
- [ ] Additionally, generate a weekly mood-sleep-exercise correlation report with PHQ-9/GAD-7 trend comparison.

### Mode 3: Crisis Check

- [ ] Execute Step 0 (crisis detection) only.
- [ ] If no crisis detected, confirm safety and offer to proceed to a full mood entry.

### ADHD Support (Conditionally Triggered)

- [ ] **Step A1 -- Executive function support.** Invoke `adhd-daily-planner` (if user has ADHD diagnosis or related needs). Provide daily task planning and prioritization. Offer time management aids (Pomodoro technique, etc.). Provide coping strategies for executive function difficulties. Recognize and support ADHD-specific emotional regulation patterns.

## Conversation Principles

This skill follows these principles when interacting with users:

1. **Warm, not clinical**: Use gentle, empathetic language. Avoid cold medical jargon.
2. **Validate feelings first**: Before offering advice, acknowledge the user's emotional experience ("It sounds like today was tough for you").
3. **Non-judgmental**: Make no moral judgments about any emotional state.
4. **Empower, not create dependency**: Help users develop their own coping abilities rather than creating dependency on the tool.
5. **Safety first**: Crisis detection always takes priority over all other functions.
6. **Clear boundaries**: State clearly that this is not a therapist; recommend professional help at appropriate moments.
7. **Positive reinforcement**: Focus on what the user has accomplished, not only on problems.
8. **Respect pace**: Never pressure the user to share what they are not ready to share.

## Input Format

### Daily Mood Entry

The user provides any combination of the following in natural language:

```
Mood: Felt okay today, a bit anxious during the morning meeting, better in the afternoon
Sleep: Slept at 11pm, woke at 7am, woke once in the middle, sleep quality average
Social: Had lunch chat with colleagues, video called a friend for 30 min in the evening
Exercise: Ran 3km in the afternoon
Stress event: Project deadline is next Monday, feeling nervous
```

| Input | Required | Description |
|-------|----------|-------------|
| Wearable device data | No | Exported data from Apple Watch / Fitbit / Oura (HRV, heart rate, sleep stages, activity) |

### Periodic Assessment (Recommended Every 2 Weeks)

Guide the user through PHQ-9 and/or GAD-7 standardized questionnaires.

## Output Format

### Daily Mood Briefing Template

```markdown
# Mood Briefing -- YYYY-MM-DD

## Today's Mood
- Overall score: 6/10 (moderate-positive)
- Mood keywords: calm, mild anxiety
- Anxiety trigger: project deadline pressure

## Today's Highlights
- Lunch chat with colleagues (social connection +1)
- Afternoon 3km run (exercise +1)

## Suggestions for Today
- Try 4-7-8 breathing before bed (ease sleep-onset anxiety)
- Try 10 min mindfulness meditation tomorrow (cope with deadline stress)
- Walk outdoors during lunch break (sunlight + exercise dual benefit)

## Weekly Progress
- Exercise goal: 3/5 days (keep it up)
- Social interactions: 4 times (good)
- Sleep quality avg: 6.5/10
```

### Weekly Mental Health Report Template

```markdown
# Weekly Mental Health Analysis -- YYYY-MM-DD to YYYY-MM-DD

## PHQ-9/GAD-7 Trend
| Date | PHQ-9 | Level | GAD-7 | Level |
|------|-------|-------|-------|-------|
| 03-10 | 7 | Mild | 6 | Mild |
| 02-24 | 9 | Mild | 8 | Mild |
| 02-10 | 11 | Moderate | 10 | Moderate |

Trend: Both PHQ-9 and GAD-7 are declining; sustained improvement.

## Sleep-Mood Correlation
- Days with sleep >= 7h: avg mood score 7.2/10
- Days with sleep < 6h: avg mood score 4.8/10
- Correlation: Sleep quality and mood score show strong positive correlation (r=0.72)

## Exercise-Mood Correlation
- Exercise days: avg mood score 7.0/10
- Rest days: avg mood score 5.5/10
- Most effective exercise type: running (most significant mood boost)

## Social Activity
- This week's social interactions: 6 times
- Social-day avg mood: 7.1/10
- Non-social-day avg mood: 5.3/10
- Recommendation: Maintain at least 1 meaningful social interaction per day

## Cognitive Pattern Observations
- Primary cognitive distortion this week: catastrophizing (3 instances)
- Most common trigger: work pressure
- Recommended coping: cognitive restructuring + progressive muscle relaxation

## Behavioral Activation Goal Completion
- Walking goal: 5/7 days (71%)
- Meditation goal: 3/7 days (43%, needs strengthening)
- Social goal: 6/7 days (86%, excellent)
```

### Crisis Safety Net Output (Triggered by Crisis Detection)

```markdown
# Important Notice

I noticed something in what you shared that concerns me. What you are feeling matters, and I want to make sure you get the best support possible.

## Please Contact Professional Help Now

- **24h Mental Health Hotline (China)**: 400-161-9995
- **Beijing Psychological Crisis Center**: 010-82951332
- **Lifeline (China)**: 400-821-1215
- **988 Suicide & Crisis Lifeline (US)**: 988
- **Emergency**: 120 / 911

## What You Can Do Right Now
1. Call one of the hotlines above and talk to a professional
2. Reach out to someone you trust (family, friend, colleague)
3. If you feel unsafe, call 120/911

**You do not have to face this alone. Asking for help is a sign of strength.**
```

### Monthly Review Template

```markdown
# Monthly Mental Health Review -- YYYY-MM

## Summary
- PHQ-9 change: 11 -> 7 (improved 4 points, moderate to mild)
- GAD-7 change: 10 -> 6 (improved 4 points, moderate to mild)
- Avg mood score: 6.3/10 (vs previous month 5.8, improved)
- Avg sleep quality: 6.5/10

## Monthly Trend Description
- Mood scores: fluctuated early month (4-7), stabilized late month (6-7.5)
- Sleep quality: sustained improvement, median rose from 5.5 to 6.8
- Exercise frequency: increased from 2 days/week to 4 days/week

## Most Effective Coping Strategies
1. Running (most significant mood improvement)
2. 4-7-8 breathing (improved sleep onset)
3. Social activity (good mood stabilization effect)

## Professional Consultation Recommendation
- Current status: mild depression/anxiety, sustained improvement
- Recommendation: continue current self-management strategies
- If PHQ-9 remains >= 10 for over 4 weeks, strongly recommend seeking professional counseling
```

## Alert Rules

| Severity | Condition | Action |
|----------|-----------|--------|
| **Crisis** | PHQ-9 >= 20 or GAD-7 >= 15 | Immediately display crisis resources panel |
| **Crisis** | PHQ-9 Q9 (self-harm ideation) >= 1 | Immediately display crisis resources panel |
| **Crisis** | Text detects self-harm/suicide expression | Immediately display crisis resources panel |
| **Crisis** | Score spike > 5 points from previous assessment | Display crisis resources + recommend urgently contacting a professional |
| **High** | PHQ-9 15-19 or GAD-7 10-14 | Strongly recommend professional psychotherapy |
| **High** | PHQ-9 >= 10 sustained for 4+ weeks | Recommend scheduling a counseling appointment soon |
| **Medium** | Mood score <= 4/10 for 5+ consecutive days | Review sleep/exercise/social activity; increase self-care |
| **Medium** | Sleep quality <= 4/10 for 7+ consecutive days | Recommend sleep evaluation; consult physician if needed |
| **Low** | Exercise frequency < 2 days/week for 2+ weeks | Gently remind of the positive effect of exercise on mood |

## Data Persistence

All data is stored via the `health-memory` skill following its format conventions:

- **Daily records**: `memory/health/daily/YYYY-MM-DD.md` -- daily summary of mood, sleep, social, exercise
- **Mental health longitudinal**: `memory/health/items/mental-health.md` -- PHQ-9/GAD-7 score history
- **Sleep longitudinal**: `memory/health/items/sleep.md` -- sleep quality longitudinal tracking
- **Mood diary**: `memory/health/items/mood.md` -- daily mood scores and keywords
