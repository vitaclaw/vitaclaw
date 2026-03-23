---
name: doctor-evidence-profiler
description: "Profiles a doctor using public official pages and optional PubMed evidence. Use when you want a conservative public-information view of a doctor's specialty fit, continuity potential, and academic signal."
version: 1.0.0
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🔎","category":"health"}}
---

# Doctor Evidence Profiler

Use this skill when the user asks:

- “这个医生适不适合我？”
- “他公开资料主要擅长什么？”
- “能不能看看这个医生公开论文和方向是不是跟我问题贴合？”

## What It Does

- Reads structured doctor info or a public profile URL
- Extracts a concise public-profile summary
- Optionally searches PubMed through official NCBI E-utilities
- Treats publication signal as a *supporting* factor, not an absolute ranking

## CLI

```bash
python3 doctor_evidence_profiler.py --doctor-json /path/to/doctor.json
```

Optional PubMed mode:

```bash
python3 doctor_evidence_profiler.py --doctor-json /path/to/doctor.json --pubmed-mode auto
```
