---
name: caffeine-tracker
description: "Tracks daily caffeine intake from beverages, models residual caffeine using half-life decay (t1/2=5.7h), and predicts safe sleep time. Use when the user logs coffee, tea, or energy drink consumption, asks about caffeine levels, or wants to know when it is safe to sleep."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"☕","category":"health"}}
---

# Caffeine Tracker

Records daily caffeine intake, estimates residual body caffeine via first-order elimination kinetics (half-life 5.7 h), predicts safe sleep time, and provides daily intake summaries with health alerts.

## Capabilities

### 1. Record Caffeine Intake

Extract and record beverage type, caffeine content (mg), and intake time from natural-language input.

**Record fields**: intake time (HH:MM 24h), beverage name, caffeine amount (mg), optional notes (e.g. "double shot").

### 2. Estimate Residual Caffeine

Use a first-order elimination model to compute current residual caffeine.

**Core formula**:

```
C(t) = C0 * 0.5^(t / 5.7)
```

- `C(t)` -- residual after t hours (mg)
- `C0` -- initial dose (mg)
- `5.7` -- mean half-life in hours (healthy adults)

**Cumulative calculation** (multiple doses in one day):

```
Total_residual = SUM[ dose_i * 0.5^((now - time_i) / 5.7) ]   for all i
```

### 3. Predict Safe Sleep Time

Solve for the time when total residual decays below the safe-sleep threshold (50 mg).

```
hours_until_safe = 5.7 * log2(C_current / 50)
```

- If current residual < 50 mg: safe to sleep now.
- Otherwise: safe sleep time = now + hours_until_safe (round up to nearest 15 min).

For full accuracy, simulate cumulative decay from all active doses until total < 50 mg.

### 4. Daily Statistics and Alerts

**Statistics**: total intake (mg), number of beverages, current residual (mg), estimated safe sleep time.

**Alert rules**:

| Condition | Alert |
|-----------|-------|
| Daily total > 400 mg | `[Warning] Daily caffeine exceeds 400 mg (FDA adult daily limit)` |
| Intake after 18:00 AND residual > 100 mg | `[Warning] Evening caffeine intake; high residual at bedtime may impair sleep` |
| Single dose > 200 mg | `[Notice] High single dose; consider splitting intake` |

## Beverage Caffeine Database

| Beverage | Default (mg) | Notes |
|----------|-------------|-------|
| Espresso | 63 | per shot (30 ml) |
| Drip Coffee | 95 | per cup (240 ml) |
| Latte | 80 | single shot + milk |
| Cappuccino | 80 | single shot |
| Cold Brew | 120 | per cup (240 ml) |
| Green Tea | 30 | per cup (240 ml) |
| Black Tea | 47 | per cup (240 ml) |
| Matcha | 70 | per serving (2 g powder) |
| Cola | 34 | per can (355 ml) |
| Energy Drink | 80 | per can (250 ml) |
| Decaf Coffee | 3 | per cup (240 ml) |
| Double Espresso | 126 | 2 shots |
| Dark Chocolate | 20 | per 30 g |

**Size modifiers**: "large" = default x 1.5; "two cups" = default x 2; explicit mg from user overrides lookup.

## Input Format

Natural language, e.g.:
- "Just had a latte"
- "08:30 drank an americano"
- "Had a Red Bull at 3 pm"

## Output Format

### Intake Confirmation

```markdown
## Caffeine Intake [caffeine-tracker · HH:MM]

Recorded: Latte 80 mg (14:30)

### Current Status
- Today's intake: 230 mg / 400 mg
- Current residual: ~185 mg
- Safe sleep time: 22:45

### Today's Detail
| Time | Beverage | Dose (mg) | Residual (mg) |
|------|----------|-----------|---------------|
| 08:30 | Drip Coffee | 95 | ~42 |
| 11:00 | Green Tea | 30 | ~18 |
| 14:30 | Latte | 80 | ~125 |
| **Total** | | **230** | **~185** |
```

### Status Query (no new intake)

```markdown
## Caffeine Status [caffeine-tracker · HH:MM]

### Current Status
- Today's intake: 230 mg / 400 mg
- Current residual: ~120 mg
- Safe sleep time: 22:15

### Today's Detail
| Time | Beverage | Dose (mg) | Residual (mg) |
|------|----------|-----------|---------------|
| 08:30 | Drip Coffee | 95 | ~28 |
| 11:00 | Green Tea | 30 | ~12 |
| 14:30 | Latte | 80 | ~80 |
| **Total** | | **230** | **~120** |
```

## Data Persistence

### Daily File (`memory/health/daily/YYYY-MM-DD.md`)

Update the `## Caffeine [caffeine-tracker · HH:MM]` section:

```markdown
## Caffeine [caffeine-tracker · HH:MM]
- Residual: ~185mg
- Safe to sleep: 22:45
- Today's intake: Americano 95mg (08:30), Green tea 30mg (11:00), Latte 80mg (14:30)
- Total: 230mg / 400mg
```

### Item File (`memory/health/items/caffeine.md`)

```markdown
---
item: caffeine
unit: mg
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Caffeine Records

## Recent Status
- Latest: 230mg total, ~185mg residual (YYYY-MM-DD 14:30)
- Safe sleep time: 22:45
- Trend: Moderate intake

## History
| Date | Total Intake (mg) | Peak Residual (mg) | Safe Sleep Time | Drinks | Notes |
|------|-------------------|--------------------:|-----------------|--------|-------|
| 2026-03-10 | 230 | 185 | 22:45 | Americano, Green tea, Latte | |
| 2026-03-09 | 190 | 150 | 21:30 | Latte x2 | |
```

### Write Steps

1. Glob `memory/health/daily/` for today's file; create if absent.
2. Read the daily file.
3. Grep `## .* \[caffeine-tracker ·` for existing section.
4. Edit to replace existing section, or insert before `## Health Files` if new.
5. Update frontmatter `updated_at`.
6. Read `memory/health/items/caffeine.md` (create if absent).
7. Update `## Recent Status` and prepend new row to `## History` table.
8. Remove rows older than 90 days.

## Alerts and Safety

### Half-Life Variability

The 5.7 h half-life is a population mean for healthy adults. Individual variation:
- Smokers: ~3 h
- Pregnant women: 9-11 h
- Liver impairment: significantly prolonged

This skill uses the population mean without individual adjustment.

### Medical Disclaimer

This skill is for health reference only and does not constitute medical advice.

**Consult a doctor if**:
- Cardiac arrhythmia or heart disease
- Anxiety or panic disorder
- Pregnancy or breastfeeding
- Taking medications that interact with caffeine
- Experiencing palpitations, tremors, or insomnia
