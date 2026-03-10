---
name: sleep-optimizer
description: "Generates prioritized, personalized sleep improvement recommendations based on sleep metrics, caffeine data, screen time, and exercise timing. Use after sleep-analyzer identifies issues or when the user asks how to improve sleep."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🌙","category":"health"}}
---

# Sleep Optimizer

Generates rule-driven, prioritized sleep improvement recommendations and a 7-day improvement plan by integrating sleep-analyzer metrics, caffeine-tracker data, and user-reported lifestyle factors (screen time, exercise, bedroom environment, stress, alcohol, late meals).

## Capabilities

### 1. Data Collection and Integration

**From health-memory** (read automatically):

| Source | Path | Key Fields |
|--------|------|------------|
| Sleep data | `memory/health/items/sleep.md` | score, efficiency, duration, latency, consistency, stages |
| Caffeine data | `memory/health/items/caffeine.md` | daily total, last intake time, bedtime residual |
| Daily files | `memory/health/daily/*.md` | Sleep and Caffeine sections |

**From conversation** (optional; skip dimension if not provided):

| Factor | Example Input |
|--------|---------------|
| Screen time | "Scrolled phone for 1 hour before bed" |
| Exercise timing | "Ran 5 km at 8 pm" |
| Bedroom environment | "Room is hot, lights on" |
| Stress level (1-10) | "Work stress 7/10" |
| Alcohol | "Two glasses of wine at dinner" |
| Late meal | "Had hotpot at 21:00" |

### 2. Problem Identification and Prioritization

Rule engine evaluates conditions in priority order:

| Priority | Condition | Category |
|----------|-----------|----------|
| P1 | Caffeine after 14:00 AND bedtime residual > 100 mg | Caffeine management |
| P1 | Sleep efficiency < 80% | Sleep hygiene |
| P2 | Sleep onset latency > 30 min | Relaxation techniques |
| P2 | Bedtime SD > 60 min | Schedule regularity |
| P3 | Screen time > 30 min within 1 h of bed | Screen management |
| P3 | Vigorous exercise within 3 h of bed | Exercise timing |
| P3 | Bedroom temp > 26C or light/noise interference | Environment optimization |
| P4 | Stress level >= 7/10 | Relaxation / stress reduction |
| P4 | Large meal within 3 h of bed | Meal timing |
| P4 | Alcohol before bed | Alcohol management |
| P5 | TST < 7 h but efficiency normal | Increase time in bed |

### 3. Recommendation Generation

For each identified problem, generate actionable recommendations with expected effect and evidence basis.

#### 3.1 Caffeine Management

| Condition | Recommendation | Expected Effect |
|-----------|----------------|-----------------|
| Caffeine after 14:00 | Move caffeine cutoff to 14:00 | Latency -10-15 min |
| Daily total > 400 mg | Reduce to < 300 mg | Overall sleep quality improvement |
| Last intake > 16:00 AND bedtime residual > 50 mg | Switch to decaf or herbal tea after cutoff | Lower bedtime residual |

#### 3.2 Sleep Hygiene

| Condition | Recommendation | Expected Effect |
|-----------|----------------|-----------------|
| Efficiency < 80% | Sleep restriction: only go to bed when sleepy; remove non-sleep activities from bedroom | Efficiency +5-15% |
| Non-sleep activities in bed | Reserve bedroom for sleep only; remove TV/work devices | Strengthen bed-sleep association |
| Irregular wake time | Set fixed wake time (weekends max +1 h) | Stabilize circadian rhythm |

#### 3.3 Relaxation Techniques

| Condition | Recommendation | Method |
|-----------|----------------|--------|
| Latency > 30 min | Progressive Muscle Relaxation (PMR) | 15 min before bed, tense-release muscle groups feet to head |
| Latency > 30 min | 4-7-8 breathing | Inhale 4 s, hold 7 s, exhale 8 s, repeat 4 cycles |
| Stress >= 7/10 | Mindfulness meditation | 10-15 min daily (app-assisted optional) |
| Racing thoughts at bedtime | Cognitive offloading | Write worry list + paired action items 30 min before bed |

#### 3.4 Exercise Timing

| Condition | Recommendation | Expected Effect |
|-----------|----------------|-----------------|
| Vigorous exercise within 3 h of bed | Move high-intensity exercise to morning or afternoon | Reduce pre-sleep sympathetic arousal |
| No regular exercise | 30 min moderate aerobic exercise daily | Improved deep sleep, shorter latency |
| Evening exercise | Keep to light-moderate only (yoga/walking) | Moderate exercise aids relaxation |

#### 3.5 Environment Optimization

| Factor | Recommendation | Optimal Parameter |
|--------|----------------|-------------------|
| Temperature too high | Cool to 18-22C | Optimal: 18-20C |
| Light interference | Blackout curtains or sleep mask | < 5 lux |
| Noise interference | Earplugs or white noise machine | < 30 dB |
| Dry air | Use humidifier | 40-60% humidity |

#### 3.6 Supplement Reference

| Supplement | Dose | Timing | Evidence | Notes |
|------------|------|--------|----------|-------|
| Melatonin | 0.5-3 mg | 30-60 min before bed | A (systematic reviews) | Short-term use; best evidence for jet lag |
| Magnesium Glycinate | 200-400 mg | 1 h before bed | B (clinical trials) | Caution with renal impairment |
| L-Theanine | 200 mg | 30-60 min before bed | B (clinical trials) | Promotes relaxation, not directly sedating |
| GABA | 100-200 mg | 30 min before bed | C (preliminary) | BBB permeability debated |
| Valerian Root | 300-600 mg | 30-60 min before bed | C (inconsistent) | 2-4 weeks to take effect |

Evidence levels: A = multiple RCTs / systematic reviews; B = at least 1 RCT; C = preliminary or inconsistent.

#### 3.7 Diet and Alcohol

| Condition | Recommendation |
|-----------|----------------|
| Dinner after 20:00 | Move to before 19:00; if unavoidable, choose light, easily digestible foods |
| Large dinner | Reduce portion; avoid spicy/greasy foods |
| Alcohol before bed | Avoid alcohol within 3 h of bed; alcohol aids onset but disrupts late-night REM |

### 4. Seven-Day Improvement Plan

**Principles**:
- Day 1-2: implement only the top 1-2 priority changes
- Day 3-4: add second-priority changes
- Day 5-7: add environment / supplement measures
- Fixed wake time every day (anchor point)
- Gradual change; do not overhaul everything at once

## Output Format

### Optimization Report

```markdown
# Sleep Optimization Report

## Data Overview
- Analysis period: last 7 days
- Average sleep score: 72/100
- Average efficiency: 84%
- Average latency: 28 min
- Average duration: 6h 45min
- Caffeine: avg 280 mg/day, last intake avg 16:30
- Schedule consistency: SD = 52 min

## Identified Problems (by priority)

### P1 - Late Caffeine Intake
- Current: last intake avg 16:30, bedtime residual ~95 mg
- Impact: extended latency, reduced efficiency
- Correlation: high-caffeine days score 11 points lower

### P2 - Long Sleep Onset Latency
- Current: avg 28 min, 3 days > 30 min
- Impact: reduced efficiency and TST

### P3 - Irregular Schedule
- Current: bedtime SD = 52 min (23:00-01:00 range)
- Impact: unstable circadian rhythm, low consistency score

## Recommendations

### 1. [High Priority] Advance Caffeine Cutoff
- **Action**: No caffeine after 14:00
- **Alternative**: Decaf coffee, herbal tea after cutoff
- **Expected**: Latency -10-15 min, efficiency +3-5%

### 2. [Medium Priority] Pre-Sleep Relaxation Routine
- **Action**: 30 min routine: put away phone -> warm foot soak/shower -> 4-7-8 breathing x4
- **Expected**: Latency < 15 min

### 3. [Medium Priority] Fixed Wake Time
- **Action**: 07:00 alarm every day including weekends
- **Expected**: Consistency improvement within 2 weeks

## 7-Day Plan

### Day 1-2: Caffeine Adjustment
- 07:00 fixed wake time
- No caffeine after 14:00
- Log sleep time and subjective quality

### Day 3-4: Add Relaxation Routine
- Maintain Day 1-2 changes
- 22:30 screens off
- 30 min relaxation routine before bed
- Try 4-7-8 breathing

### Day 5-7: Environment Optimization
- Maintain Day 1-4 changes
- Adjust bedroom temperature to ~20C
- Add blackout curtains if light is an issue
- Optional: try 200 mg L-Theanine + 200 mg Magnesium

### Daily Checklist
- [ ] No caffeine after 14:00?
- [ ] Screens off by 22:30?
- [ ] Completed relaxation routine?
- [ ] Woke at 07:00?
- [ ] Logged sleep data?

## Expected Improvement
- 1 week: shorter latency, score +5-10
- 2 weeks: stable schedule, efficiency 88%+
- 4 weeks: habit formed, score stable 80+
```

## Data Access

This skill is read-only; it does not write to health-memory. Output is a recommendation report for the user.

**Read steps**:
1. Read `memory/health/items/sleep.md` -- sleep trends and history.
2. Read `memory/health/items/caffeine.md` -- caffeine trends.
3. Glob `memory/health/daily/*.md` for last 7 days -- daily detail.
4. Grep `## .* \[sleep-analyzer ·` and `## .* \[caffeine-tracker ·` in daily files.
5. Collect additional lifestyle factors from conversation context.

## Alerts and Safety

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice. It does not diagnose sleep disorders, prescribe medication, or replace professional CBT-I therapy.

**Consult a doctor if**:
- Insomnia persists > 1 month and severely impairs daily function
- Suspected sleep apnea (loud snoring + daytime sleepiness)
- Co-occurring depression or anxiety symptoms
- Sleep medication is needed
- Before starting supplements if you have chronic conditions or take other medications

### Supplement Disclaimer

Supplement recommendations are informational only, with evidence levels noted. Before use: confirm no contraindications, check drug interactions, start at lowest dose, and consult a pharmacist or doctor when in doubt.
