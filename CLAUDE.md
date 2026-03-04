# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A monorepo of **OpenClaw skills** — published individually to ClawHub. OpenClaw is an autonomous AI Agent platform (not a Claude Code plugin). Skills are `SKILL.md` files (YAML frontmatter + Markdown instructions) that teach the Agent how to complete tasks using shell commands, filesystem access, and external services.

This repo targets Chinese-language medical record management for cancer/chronic disease patients.

## Validating Python Scripts

```bash
# Syntax-check all scripts at once
py -3 -m py_compile medical-record-organizer/scripts/init_patient.py
py -3 -m py_compile medical-record-organizer/scripts/extract_pdf.py
py -3 -m py_compile medical-record-organizer/scripts/unpack_archive.py
py -3 -m py_compile health-timeline/scripts/update_timeline.py
py -3 -m py_compile apple-health-digest/scripts/parse_apple_health.py
```

Use `py -3` (Windows py launcher), not `python3`, on this machine.

## Skill File Format

Every `SKILL.md` must have a valid YAML frontmatter block:

```yaml
---
name: skill-name          # matches directory name
description: ...          # shown in ClawHub; include trigger phrases
version: 1.0.0
metadata:
  openclaw:
    emoji: "🏥"
    requires:
      bins:               # required executables (hard requirement)
        - python3
      anyBins:            # at least one of these must exist
        - unrar
        - unar
    install:              # packages installed via `uv`
      - kind: uv
        package: pdfplumber
---
```

The body (after `---`) is Markdown instructions written as direct imperatives to the Agent. The Agent reads and executes these instructions at runtime.

## Runtime Paths

When a skill is installed by OpenClaw, its files land at:
```
~/.openclaw/skills/[skill-name]/   ← skill files (SKILL.md, scripts/, assets/)
~/.openclaw/patients/[name]/       ← patient data written by the skills
```

All script paths in SKILL.md bodies use the `~/.openclaw/skills/...` prefix. Scripts themselves use `pathlib.Path.home()` for cross-platform compatibility.

## Architecture: Three Independent Skills

### `medical-record-organizer` 🏥 (most complex)
Intake pipeline: classify → extract → archive → update index. Two upload modes:
- **Batch** (archive file): unpack → process each file → update INDEX.md + timeline.md once
- **Incremental** (individual files): same "process all first, update once" strategy

Scripts communicate via stdout JSON. The Agent reads JSON output to get `tmp_dir`, `files`, etc.

### `health-timeline` 📅
Read-only querier over the patient directory. Five query modes (full, lab tracking, treatment phase, date range, document type). Calls `update_timeline.py` only when the user explicitly adds a new entry.

### `apple-health-digest` 🍎
Parses `export.xml` from Apple Health using `iterparse` (streaming, no extra dependencies). Writes 6 Markdown report files into `09_Apple_Health/`, then generates a correlation report against treatment history.

## Patient Directory Structure

`init_patient.py` creates this tree (idempotent — safe to re-run):

```
~/.openclaw/patients/[name]/
├── INDEX.md               ← LLM navigation entry point (read this first)
├── profile.json           ← structured patient info
├── timeline.md            ← chronological event table
├── 01_当前状态/
├── 02_诊断与分期/
├── 03_分子病理/            ← gene tests + IHC (separate from 02 intentionally)
├── 04_影像学/              ← CT / MRI / PET-CT / 超声
├── 05_检验检查/            ← 血常规 / 生化 / 肿瘤标志物
│   └── 肿瘤标志物/肿标趋势.md   ← cumulative trend table, appended each intake
├── 06_治疗决策历史/         ← 治疗决策总表.md + per-line subdirs
├── 07_合并症与用药/
├── 08_出院小结/
├── 09_Apple_Health/
└── 10_原始文件/
```

**INDEX.md** uses the PageIndex pattern: every archived file has a one-line summary entry so the LLM can navigate without opening files. Skills always update INDEX.md last, after all files are written.

## Key Conventions

- **All files UTF-8**, Chinese directory names preserved as-is
- **Scripts output JSON to stdout** on success/failure; the Agent reads this to branch logic
- **Idempotent init**: `init_patient.py` skips files that already exist
- **Trend arrows**: `↑↓→` used consistently across all output Markdown
- **Abnormal values**: flagged with `⚠ 异常` in health-timeline displays
- **Classification priority** (medical-record-organizer): 出院小结 > 完整病理报告 > 子类型; ambiguous docs go to `10_原始文件/未分类/`
- **document-taxonomy.md** is the classification reference — the Agent reads it during Step 3 of intake
