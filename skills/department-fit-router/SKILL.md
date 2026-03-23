---
name: department-fit-router
description: "Routes a user's health problem to the most suitable department path using symptoms, chronic conditions, abnormal findings, goals, and continuity needs. Use before doctor recommendation when the user is unsure which specialty to see."
version: 1.0.0
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🧭","category":"health"}}
---

# Department Fit Router

Use this skill when the user asks questions like:

- “我这种情况应该挂什么科？”
- “体检有几项异常，先看哪个科最合适？”
- “高血压、糖前期、脂肪肝一起存在，应该先找谁看？”

## What It Does

- Routes the case to 1-3 likely departments
- Explains *why* those departments fit
- Highlights when full acute-care escalation should come before routine doctor matching
- Outputs visit preparation suggestions for the chosen department path

## Input

- `patient.json` with fields such as:
  - `conditions`
  - `symptoms`
  - `abnormal_findings`
  - `goals`
  - `city`
  - `district`
  - `summary`

## CLI

```bash
python3 department_fit_router.py --patient-json /path/to/patient.json
```

Or inline:

```bash
python3 department_fit_router.py \
  --condition 高血压 \
  --condition 糖前期 \
  --abnormal-finding ALT偏高 \
  --goal 找能长期管理的门诊
```
