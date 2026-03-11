---
name: health-memory
description: "Centralized health memory hub — manages daily logs and per-item longitudinal tracking files under memory/health/. WHEN TO USE: After any health skill records data, or when answering health questions that need historical context."
version: 1.0.0
user-invocable: false
metadata: {"openclaw":{"emoji":"🧠","category":"health"}}
---

# health-memory — Centralized Health Memory Hub

Instruction-only skill with no Python scripts. All operations are performed by the agent using built-in tools (Read/Write/Edit/Grep/Glob).

---

## Goals

1. **Single source of truth** — Provide one canonical location (`memory/health/`) for all health data across skills
2. **Daily log aggregation** — One file per day, multi-skill; each skill writes its own section
3. **Per-item longitudinal tracking** — Dedicated files for blood pressure, tumor markers, medications, etc. with rolling 90-day history
4. **Health file indexing** — PDFs, images, and lab reports stored in `files/`; only summaries appear in memory (never full text)
5. **Shared format contract** — Any health skill can read/write without code dependencies, just by following the format rules below

---

## Directory Structure

```
memory/health/
├── _health-profile.md              # Long-term health baseline (manual / agent-maintained)
├── daily/                           # Daily logs (one file per day)
│   ├── 2026-03-10.md
│   ├── 2026-03-09.md
│   └── ...
├── items/                           # Per-item longitudinal tracking
│   ├── blood-pressure.md            # Blood pressure history
│   ├── blood-sugar.md               # Blood sugar history
│   ├── blood-lipids.md              # Blood lipid history
│   ├── tumor-markers.md             # Tumor marker history
│   ├── kidney-function.md           # Kidney function history
│   ├── weight.md                    # Weight history
│   ├── medications.md               # Medication records
│   ├── supplements.md               # Supplement records
│   └── ...                          # Agent creates new files as needed
└── files/                           # Health documents (PDFs, images, etc.)
    ├── 2026-03-10_blood_routine.pdf
    └── ...
```

---

## Daily File Format

**Path**: `memory/health/daily/YYYY-MM-DD.md`

```markdown
---
date: YYYY-MM-DD
updated_at: YYYY-MM-DDTHH:MM:SS
---

# YYYY-MM-DD

## Blood Pressure [blood-pressure-tracker · 09:15]
- 120/80 mmHg, pulse 72
- Grade: Normal

## Caffeine [caffeine-tracker · 14:30]
- Residual: ~230mg
- Safe to sleep: 22:30
- Today's intake: Espresso 150mg (08:30), Latte 80mg (14:30)

## Health Files
| File | Type | Summary | Path |
|------|------|---------|------|
| Blood routine | Lab report | WBC 6.2, Hb 135, PLT 210 all normal | memory/health/files/2026-03-10_blood_routine.pdf |
```

### Format Rules

- **Section header**: `## Title [skill-name · HH:MM]` — fixed format for easy Grep lookup
- **Same skill, same day, multiple updates**: Use Edit to replace the existing section; do NOT duplicate
- **`## Health Files` section**: Always at the end of the file; table indexing file summaries + paths
- **Never put full file contents in memory**: Only 1-2 line summaries; agent reads the original file on demand

---

## Item File Format

**Path**: `memory/health/items/{item}.md`

```markdown
---
item: blood-pressure
unit: mmHg
updated_at: YYYY-MM-DDTHH:MM:SS
---

# Blood Pressure Records

## Recent Status
- Latest: 120/80 mmHg (2026-03-10 09:15)
- 7-day average: 118/78 mmHg
- Trend: Stable

## History
| Date | Systolic | Diastolic | Pulse | Notes |
|------|----------|-----------|-------|-------|
| 2026-03-10 | 120 | 80 | 72 | Morning |
| 2026-03-09 | 125 | 82 | 75 | Morning |
| 2026-03-08 | 118 | 78 | 70 | |
```

### Format Rules

- **`## Recent Status`**: Latest value + short-term trend summary (for quick glance)
- **`## History`**: Table format, newest first, keep last 90 days
- **Data older than 90 days**: Agent removes trailing rows during updates
- **Item file names**: Agent decides (health item name → English slug); creates new files automatically for new items
- **Table columns**: Vary by item type (e.g., blood pressure has systolic/diastolic; tumor markers have CEA/CA199, etc.)

---

## Health Profile

**Path**: `memory/health/_health-profile.md`

Long-term health baseline. Maintain the existing format. Agent may update as needed.

---

## Write Protocol

**After any health skill updates data, execute these steps:**

1. **Find or create daily file**: Glob `memory/health/daily/` for today's file. If it doesn't exist, Write a new one with frontmatter and an empty `## Health Files` table
2. **Read the daily file**: Read the full content
3. **Update the skill section**: Grep for `## .* \[{skill-name} ·` to find the existing section. If found, Edit to replace it. If not found, insert a new section before `## Health Files`
4. **Update frontmatter**: Set `updated_at` to current ISO timestamp
5. **Update the corresponding item file** (`memory/health/items/{item}.md`):
   - Read the item file (if it doesn't exist, Write a new one with frontmatter, `## Recent Status`, and an empty `## History` table)
   - Update the `## Recent Status` section
   - Insert a new row at the top of the `## History` table (after the header row)
   - If the table exceeds 90 days, delete trailing old rows

---

## File Intake Protocol

**When the user provides a health document (PDF, image, etc.):**

1. Read the file and generate a summary (1-2 lines of key indicators / conclusions)
2. Save or move the original file to `memory/health/files/`, naming format: `YYYY-MM-DD_{description}.{ext}`
3. Append a row to the `## Health Files` table in today's daily file (file name + type + summary + path)
4. If the document contains specific health item data (e.g., WBC from a blood routine), also update the corresponding item file

---

## Read Protocol

**When the user asks a health question, load context incrementally:**

1. Read `memory/health/_health-profile.md` (baseline)
2. Read `memory/health/daily/{today's date}.md` (current day status)
3. If the question involves a specific health item trend → Read `memory/health/items/{item}.md`
4. If the question involves a historical date → Glob `memory/health/daily/*.md` to find relevant date files, then Read
5. If a daily or item file references a health document → Read the specific file (PDF, etc.) on demand
6. **Do NOT load all files at once** — load incrementally to avoid overwhelming the context window

---

## Integration Guide for Other Skills

**How to integrate**: After your health skill finishes its data operations, update the memory files following the format rules above.

No Python imports needed. No scripts to call. The agent executing your skill simply uses Read/Edit/Write tools to update `memory/health/daily/` and `memory/health/items/` files per this spec.

**Useful Grep patterns**:
- Find a skill's section in today's daily file: `## .* \[{skill-name} ·` in `memory/health/daily/{date}.md`
- Find all daily files mentioning a health item: `## {item-name}` in `memory/health/daily/`

**New item file template**:
```markdown
---
item: {english-slug}
unit: {unit}
updated_at: {ISO-timestamp}
---

# {Item Name} Records

## Recent Status
- Latest: (pending)

## History
| Date | {Col1} | {Col2} | Notes |
|------|--------|--------|-------|
```
