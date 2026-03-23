---
name: social-health-tracker
description: "Tracks social interactions, assesses loneliness via UCLA Loneliness Scale, maps Dunbar social circles, generates social health scores (0-100), and provides social prescriptions. Use when the user logs social activities, reports feeling isolated, or asks about social wellbeing patterns."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🤝","category":"health"}}
---

# Social Health Tracker

Tracks social interactions and assesses social wellbeing. Records social activities with quality ratings, administers the UCLA Loneliness Scale (short form), maps social connections using Dunbar's number framework, computes a Social Health Score (0-100), generates social prescriptions, analyzes social-health correlations, monitors boundary health, and detects isolation or over-extension patterns.

## Capabilities

### 1. Social Activity Recording

Extract from natural-language input (e.g., "had coffee with Lisa for an hour", "family dinner tonight", "video call with college friends"):

| Field | Required | Default if missing |
|-------|----------|--------------------|
| date | Yes | today |
| time | No | omitted |
| duration (min) | No | 60 min |
| type | Yes | see categories below |
| format | No | in-person |
| people | No | omitted |
| group_size | No | inferred from people, or 2 |
| quality (1-5) | No | omitted (prompt user) |
| energy_change | No | omitted |
| notes | No | omitted |

#### Interaction Types

| Category | Examples |
|----------|---------|
| intimate | Deep 1-on-1 conversation, emotional support exchange, vulnerability sharing |
| social | Group dinner, party, casual hangout, coffee catch-up |
| professional | Work meeting, networking event, mentoring session |
| community | Volunteer work, religious gathering, club activity, neighborhood event |
| digital | Video call, voice call, meaningful text exchange, online gaming together |
| passive | Social media browsing, watching streams (low social value — flag if dominant) |

#### Interaction Format

| Format | Quality Multiplier | Notes |
|--------|-------------------|-------|
| in-person | 1.0× | Highest social value |
| video-call | 0.8× | Good but lacks physical co-presence |
| voice-call | 0.7× | Auditory connection only |
| text/chat | 0.5× | Asynchronous, lower intimacy |
| social-media | 0.3× | Passive; may increase loneliness if predominant |

### 2. UCLA Loneliness Scale (Short Form, ULS-8)

Administer the 8-item version. Each item scored 1 (Never) to 4 (Always).

#### ULS-8 Items

1. I lack companionship
2. There is no one I can turn to
3. I am an outgoing person *(reverse scored)*
4. I feel left out
5. I feel isolated from others
6. I can find companionship when I want it *(reverse scored)*
7. I am unhappy being so withdrawn
8. People are around me but not with me

#### Scoring

- Reverse score items 3 and 6: Never=4, Rarely=3, Sometimes=2, Always=1
- Sum all 8 items → range 8-32

| Score | Level | Interpretation |
|-------|-------|---------------|
| 8-12 | Low loneliness | Healthy social connectedness |
| 13-18 | Moderate loneliness | Some social needs unmet; review patterns |
| 19-24 | High loneliness | Significant isolation; social prescription recommended |
| 25-32 | Severe loneliness | Intervention needed; consider professional support |

#### Frequency

- **Full assessment**: Monthly (or when user requests)
- **Quick check**: Single-item "How lonely have you felt this past week?" (1-10 scale) — weekly OK
- **Track trend**: Score change > 4 points between assessments → flag

### 3. Social Health Score (0-100)

```
Score = Frequency(25%) + Quality(25%) + Diversity(20%) + Loneliness(20%) + Reciprocity(10%)
```

#### 3.1 Frequency Sub-score (weight 25%)

Meaningful interactions per week (excluding passive/social-media):

| Interactions/week | Points |
|-------------------|--------|
| ≥ 7 | 100 |
| 5-6 | 85 |
| 3-4 | 65 |
| 1-2 | 40 |
| 0 | 10 |

#### 3.2 Quality Sub-score (weight 25%)

Average quality rating (1-5) of interactions, adjusted by format multiplier:

```
Adjusted Quality = average(quality_i × format_multiplier_i) / 5 × 100
```

| Adjusted Score | Points |
|---------------|--------|
| ≥ 80 | 100 |
| 60-79 | 80 |
| 40-59 | 55 |
| 20-39 | 30 |
| < 20 | 10 |

#### 3.3 Diversity Sub-score (weight 20%)

Number of distinct interaction categories (from the 6 types) used in the past 2 weeks:

| Categories Active | Points |
|-------------------|--------|
| 5-6 | 100 |
| 4 | 80 |
| 3 | 60 |
| 2 | 40 |
| 1 | 20 |
| 0 | 0 |

#### 3.4 Loneliness Sub-score (weight 20%)

Inverted from UCLA score (lower loneliness = higher sub-score):

```
Loneliness Sub-score = max(0, (32 - UCLA_score) / 24 × 100)
```

| UCLA Score | Sub-score |
|-----------|-----------|
| 8 | 100 |
| 12 | 83 |
| 18 | 58 |
| 24 | 33 |
| 32 | 0 |

#### 3.5 Reciprocity Sub-score (weight 10%)

Ratio of initiated vs. received social contacts over past 2 weeks:

| Initiation Ratio | Points | Interpretation |
|-------------------|--------|---------------|
| 40-60% (balanced) | 100 | Healthy reciprocity |
| 30-39% or 61-70% | 70 | Slightly imbalanced |
| 20-29% or 71-80% | 40 | Notable imbalance |
| < 20% or > 80% | 15 | One-sided pattern; review |

#### Score Interpretation

| Score | Level | Interpretation |
|-------|-------|---------------|
| 90-100 | Excellent | Thriving social life; maintain current patterns |
| 75-89 | Good | Healthy with minor gaps; review weakest dimension |
| 60-74 | Fair | Some social needs unmet; targeted improvements recommended |
| 40-59 | Poor | Significant social gaps; social prescription generated |
| < 40 | Critical | Social isolation risk; professional support recommended |

### 4. Dunbar Circle Framework

Map the user's social connections using Robin Dunbar's layered model:

| Circle | Size | Bond Strength | Contact Frequency | Description |
|--------|------|--------------|-------------------|-------------|
| Support (Inner) | ~5 | Strongest | Weekly+ | Closest confidants; call at 3 AM |
| Sympathy | ~15 | Strong | Monthly+ | Close friends; would grieve their loss deeply |
| Affinity | ~50 | Moderate | Quarterly+ | Good friends; regular social contact |
| Active | ~150 | Casual | Yearly+ | Acquaintances; recognized and named |

#### Circle Health Assessment

| Indicator | Healthy | Warning |
|-----------|---------|---------|
| Support circle size | 3-7 people | < 2 (isolation risk) or > 10 (diluted intimacy) |
| Sympathy circle | 10-20 people | < 5 (narrow network) |
| Time invested in support circle | ≥ 40% of social time | < 20% (neglecting core bonds) |
| Circle changes | Gradual evolution | Rapid loss of multiple support members |
| Cross-domain contacts | Friends from ≥ 3 life domains | Single-domain network (fragile) |

#### Life Domains for Network Diversity

- Family
- Work/professional
- School/alumni
- Hobby/interest-based
- Neighborhood/community
- Online/digital communities
- Religious/spiritual
- Sports/fitness

### 5. Social Prescription

Generate personalized social prescriptions based on identified gaps.

#### Prescription Categories

| Gap Identified | Prescription | Dose | Example |
|---------------|-------------|------|---------|
| Low frequency | Increase contact | +2 interactions/week | Schedule 2 coffee dates |
| Low quality | Deepen existing bonds | 1 intimate conversation/week | Ask a close friend a deep question |
| Low diversity | Expand categories | Add 1 new category/month | Join a community volunteer group |
| High loneliness | Structured social activity | 3×/week minimum | Group class, regular meetup, community service |
| Low reciprocity (passive) | Initiate contact | 2 outreach messages/week | Text a friend you haven't spoken to |
| Low reciprocity (over-giving) | Allow receiving | Practice accepting invitations | Say "yes" to next 3 invitations |
| Weak support circle | Deepen 1-2 connections | Weekly 1-on-1 time | Regular walk/meal with potential close friend |
| Digital-dominant | In-person shift | Replace 2 digital with in-person/week | Convert video call to coffee meeting |

#### Prescription Format

```
Rx: [Action] — [Frequency] — [Duration]
Target: [Which sub-score this improves]
Start: [Date]
Review: [Date + 2 weeks]
```

### 6. Social-Health Correlation Analysis

Cross-reference social data with other health metrics (when available):

#### Correlation Pairs

| Social Metric | Health Metric | Expected Relationship | Source |
|--------------|--------------|----------------------|--------|
| Weekly interactions | Sleep quality score | Positive (moderate) | Sleep Analyzer |
| Loneliness score | PHQ-9 depression | Positive (strong) | Mental Health Analyzer |
| Social diversity | Stress level | Negative (moderate) | Stress Management Coach |
| In-person time | Daily step count | Positive (weak-moderate) | Activity data |
| Social quality avg | Mood score | Positive (strong) | Mood Tracker |
| Isolation days (0 contacts) | Anxiety (GAD-7) | Positive (moderate) | Mental Health Analyzer |

#### Analysis Rules

- Require ≥ 14 days of overlapping data before reporting correlations
- Use Pearson correlation coefficient; report only |r| ≥ 0.3
- Always note: "Correlation does not imply causation"
- Present as trend observation, not medical finding

### 7. Boundary Health

Monitor for unhealthy social patterns at both extremes:

#### Over-Extension Indicators

| Signal | Threshold | Response |
|--------|-----------|----------|
| Social hours/week | > 25h and energy_change frequently negative | Flag over-extension |
| Quality dropping with quantity rising | Quality avg < 3 while frequency > 10/week | Suggest reducing low-quality interactions |
| Cancellation rate | > 30% of planned events cancelled | Possible burnout; reduce commitments |
| Recovery time needed | Reports needing ≥ 1 full day alone after socializing | Respect introversion; optimize not maximize |

#### Withdrawal Indicators

| Signal | Threshold | Response |
|--------|-----------|----------|
| Zero-interaction days | ≥ 3 consecutive days | Gentle prompt: "Haven't logged social activity in 3 days — everything OK?" |
| Declining invitations | > 50% declined in 2 weeks | Check for avoidance patterns |
| Quality all low | Average < 2 for past week | May indicate depression; cross-check mood |
| Only passive social | > 80% of logged interactions are social-media type | Flag: passive social may increase loneliness |

### 8. Pattern Detection

#### Weekly Patterns

- **Social rhythm**: Identify preferred social days/times
- **Energy mapping**: When does socializing energize vs. drain?
- **Weekend vs. weekday**: Balance check

#### Monthly Trends

- Score trajectory (improving, stable, declining)
- Circle changes (people entering/leaving inner circles)
- Seasonal patterns (e.g., winter isolation, holiday over-extension)

#### Critical Alerts

| Pattern | Trigger | Action |
|---------|---------|--------|
| Rapid isolation | Score dropped > 20 points in 2 weeks | Flag concern; suggest reaching out to support circle |
| Chronic loneliness | UCLA ≥ 19 for 2+ consecutive assessments | Recommend professional support (therapist, counselor) |
| Network collapse | Lost ≥ 2 support circle members in 1 month | Check in; life transition support |
| Social anxiety pattern | High avoidance + high loneliness | Suggest graduated exposure; professional referral |

## Output Format

### Social Activity Log

```markdown
## 🤝 Social Activity Logged

### Entry
- **Date**: 2026-03-10, 19:00-21:00
- **Type**: Social (group dinner)
- **Format**: In-person (1.0×)
- **People**: Lisa, Mark, Jenny
- **Group size**: 4
- **Quality**: 4/5
- **Energy change**: +1 (energized)
- **Duration**: 120 min

### Running Weekly Stats
- Interactions this week: 5 (target: ≥ 5 ✅)
- Average quality: 3.8/5
- In-person ratio: 60%
- Categories active: 3/6 (social, professional, digital)
```

### Weekly Social Report

```markdown
## 🤝 Weekly Social Report (MM-DD ~ MM-DD)

### Social Health Score: 71 / 100
| Dimension | Raw | Sub-score | Weight | Weighted |
|-----------|-----|-----------|--------|----------|
| Frequency | 5/week | 85 | 25% | 21.3 |
| Quality | 3.6 adj | 72 | 25% | 18.0 |
| Diversity | 3 categories | 60 | 20% | 12.0 |
| Loneliness | UCLA 15 | 71 | 20% | 14.2 |
| Reciprocity | 55% initiated | 100 | 10% | 10.0 |
| **Total** | | | | **75.5** |

### Interaction Summary
| Day | Interactions | Best Moment | Energy |
|-----|-------------|------------|--------|
| Mon | 1 (work meeting) | -- | Neutral |
| Tue | 0 | -- | -- |
| Wed | 2 (coffee + call) | Deep talk with Alex | +1 |
| Thu | 1 (team lunch) | -- | Neutral |
| Fri | 1 (dinner with friends) | Group laughter | +2 |
| Sat | 0 | -- | -- |
| Sun | 1 (family video call) | Catching up with parents | +1 |

### Dunbar Circle Activity
| Circle | People Contacted | Expected Minimum | Status |
|--------|-----------------|-----------------|--------|
| Support (~5) | 3/5 | Weekly | ⚠️ 2 not contacted |
| Sympathy (~15) | 4/12 | Monthly | ✅ On track |

### Patterns
- [Good] Reciprocity is balanced (55% initiated)
- [Notice] 2 zero-interaction days; both weekend — consider light social plans
- [Notice] Only 3/6 interaction categories active — try community or hobby activity
- [Alert] Support circle member "Mom" not contacted in 2 weeks

### Social Prescription
Rx: Schedule 1 community activity — Weekly — Start this week
Target: Diversity sub-score (currently 60 → target 80)
Review: MM-DD
```

### Loneliness Assessment

```markdown
## 🤝 UCLA Loneliness Assessment

### ULS-8 Results
| # | Item | Response | Score |
|---|------|----------|-------|
| 1 | I lack companionship | Sometimes | 3 |
| 2 | There is no one I can turn to | Rarely | 2 |
| 3 | I am an outgoing person | Sometimes | 3 (R) |
| 4 | I feel left out | Sometimes | 3 |
| 5 | I feel isolated from others | Rarely | 2 |
| 6 | I can find companionship when I want | Sometimes | 3 (R) |
| 7 | I am unhappy being so withdrawn | Rarely | 2 |
| 8 | People are around me but not with me | Sometimes | 3 |
| | **Total** | | **21** |

### Interpretation
- **Level**: High loneliness (score 21/32)
- **Previous**: 17 (moderate) on MM-DD → **increased +4 points** ⚠️
- **Key items**: "Lack companionship" and "people around but not with me" scored highest

### Recommendations
- Social prescription intensity: High
- Focus: Quality of existing interactions over quantity
- Suggested: 1 intimate conversation/week + 1 new group activity
- Consider: Speaking with a counselor if score remains ≥ 19 for 2+ months
```

## Data Persistence

### Daily File (`memory/health/daily/YYYY-MM-DD.md`)

```markdown
## Social [social-health-tracker · HH:MM]
- Interactions: 2 (coffee with Lisa, video call with parents)
- Quality avg: 4.0/5
- Types: social, digital
- Format: 1 in-person, 1 video-call
- Energy: +1 overall
- Weekly running score: 71/100
```

### Item File (`memory/health/items/social-health.md`)

```markdown
---
item: social-health
unit: score (0-100)
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Social Health Records

## Profile
- Personality tendency: Ambivert (estimated)
- Optimal interactions/week: 5-7
- Preferred formats: In-person, video call
- Dunbar support circle: Alex, Mom, Dad, Lisa, Sam

## Recent Status
- Latest: Score 71, 5 interactions/week (YYYY-MM-DD)
- 4-week average score: 68
- UCLA loneliness (latest): 15 (moderate)
- Trend: Improving

## UCLA History
| Date | Score | Level | Change |
|------|-------|-------|--------|
| 2026-03-10 | 15 | Moderate | -2 |
| 2026-02-10 | 17 | Moderate | -- |

## Weekly History
| Week | Score | Interactions | Quality Avg | Diversity | UCLA | Notes |
|------|-------|-------------|------------|-----------|------|-------|
| 03-04~03-10 | 71 | 5 | 3.8 | 3/6 | 15 | |
| 02-25~03-03 | 65 | 3 | 3.5 | 2/6 | 17 | Low week |
```

### Write Steps

1. Glob `memory/health/daily/` for the target date file; create if absent.
2. Read the daily file.
3. Grep `## .* \[social-health-tracker ·` for existing section.
4. Edit to replace existing section, or insert before `## Health Files` if new.
5. Update frontmatter `updated_at`.
6. Read `memory/health/items/social-health.md` (create if absent).
7. Update `## Recent Status` and prepend new row to `## Weekly History`.
8. Update `## UCLA History` if a new assessment was completed.
9. Remove rows older than 6 months.

## Alerts and Safety

### Medical Disclaimer

This skill is for social wellbeing tracking only and does not constitute medical or psychological advice. It does not diagnose social anxiety disorder, depression, or other mental health conditions.

**Consult a professional if**:
- UCLA loneliness score ≥ 19 persists for 2+ months
- Social withdrawal is accompanied by depressive symptoms (PHQ-9 ≥ 10)
- Social anxiety significantly limits daily functioning (avoiding work, school, errands)
- Grief or loss of relationship causing prolonged dysfunction (> 6 months)
- Social isolation is accompanied by substance use as coping mechanism

### Crisis Awareness

Social isolation is a significant risk factor for mental health crises.

**If the user expresses**:
- "Nobody cares about me" / "I have no one"
- "The world would be better without me"
- "I don't want to be here anymore"

**→ Immediately display crisis resources (see mental-wellness-companion) and pause social tracking.**

### Ethical Boundaries

- **Never judge** the user's social preferences or introversion as pathological
- **Respect** that optimal social levels vary greatly between individuals
- **Do not pressure** the user to socialize more if they express satisfaction with lower levels
- **Acknowledge** cultural differences in social norms and expectations
- **Protect privacy**: Never share names or relationship details outside the user's health data files
- **Avoid labeling**: Use "pattern observed" language, not diagnostic labels

### Introversion vs. Isolation

Important distinction:
- **Healthy introversion**: Lower social frequency by choice, high quality, low loneliness → healthy; do not pathologize
- **Isolation**: Low frequency, low quality, high loneliness, declining function → concerning; offer support

Calibrate recommendations to the user's baseline, not population norms. An introvert scoring 3 interactions/week with high quality and low loneliness has excellent social health.
