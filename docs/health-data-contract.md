# VitaClaw Health Data Contract

This document defines the Iteration 3 contract shared by `skills/_shared/health_data_store.py`, `HealthMemoryWriter`, the chief-led team runtime, workspace templates, heartbeat, and reporting scripts.

## 1. JSONL envelope contract

Every structured record written by `HealthDataStore` uses the same outer shape:

```json
{
  "id": "intake_20260315T124949_dc9a1908",
  "type": "intake",
  "timestamp": "2026-03-15T12:49:49",
  "skill": "caffeine-tracker",
  "note": "",
  "data": {
    "drink": "americano",
    "mg": 96,
    "time": "08:30"
  }
}
```

Required envelope fields:

- `id`
- `type`
- `timestamp`
- `skill`
- `data`

Optional envelope fields:

- `note`

The JSONL envelope is intentionally minimal. Skill-specific semantics live in `type + data` and are translated into markdown memory by the shared writer.

## 2. Markdown memory contract

Structured records are written back into markdown through four distinct layers:

- `MEMORY.md`: long-term stable facts only
- `memory/health/daily/`: same-day events and execution
- `memory/health/items/`: longitudinal aggregates, thresholds, history, rollup rules
- patient archive directories: raw evidence and structured patient master files

Iteration 3 keeps those layers and adds a chief-led team layer:

- `memory/health/items/behavior-plans.md`: active behavior plans with due time, cadence, risk policy, and consequence
- `memory/health/items/execution-barriers.md`: recurring blockers, execution debt, and recovery next steps
- `memory/health/items/care-team.md`: public doctor-match shortlist, preferred departments, and booking strategy
- `memory/health/files/write-audit.md`: audit trail for automatic scenario writebacks
- `memory/health/team/tasks/`: chief-dispatched role tasks
- `memory/health/team/briefs/`: specialist briefs and chief summaries
- `memory/health/team/team-board.md`: user-visible team status card
- `memory/health/team/audit/dispatch-log.jsonl`: dispatch, escalation, and writeback audit

### Item file requirements

Every `memory/health/items/*.md` file must contain:

1. YAML frontmatter
2. `## Recent Status`
3. `## History`

Optional standardized sections:

4. `## Thresholds`
5. `## Rollup Rules`

## 3. Fixed distillation chain

Iteration 3 keeps the same distillation chain, but team artifacts do not directly bypass it:

`daily -> weekly -> monthly -> quarterly -> MEMORY.md`

Rules:

- daily entries do not directly overwrite long-term memory
- weekly/monthly outputs summarize trend and adherence, not diagnosis
- behavior plans and execution barriers are summarized in weekly/monthly outputs
- team briefs and dispatch logs support coordination and audit, but do not directly overwrite long-term memory
- quarterly is the stability checkpoint for long-term promotion
- only stable conclusions move into `MEMORY.md`

## 4. Retrieval defaults

The default long-term memory policy is conservative:

- direct chats only
- do not auto-load `MEMORY.md` in group/public contexts
- QMD disabled in Iteration 1

## 5. Health-core item inventory

Iteration 3 requires these core item files in initialized workspaces:

- `blood-pressure.md`
- `blood-sugar.md`
- `weight.md`
- `sleep.md`
- `heart-rate-hrv.md`
- `kidney-function.md`
- `liver-function.md`
- `blood-lipids.md`
- `tumor-markers.md`
- `medications.md`
- `supplements.md`
- `mental-health-score.md`
- `appointments.md`
- `annual-checkup.md`
- `behavior-plans.md`
- `execution-barriers.md`
- `care-team.md`

## 6. Safety output contract

Health-facing outputs should map to the same six layers everywhere:

- `记录`
- `解读`
- `趋势`
- `风险`
- `建议`
- `必须就医`

The system must not present explicit diagnosis or direct prescription adjustment as a completed conclusion.

Iteration 3 product outputs must also include:

- `Sources`: explicit file refs used by the scenario
- `Evidence`: threshold or rule-level basis for the risk conclusion
- `Writebacks`: what was written automatically
- `Follow-up Tasks`: user-visible next actions pushed into the task board

Chief-led team outputs additionally require:

- `task_id`
- `role`
- `scenario`
- `privacy_tier`
- `execution_mode`
