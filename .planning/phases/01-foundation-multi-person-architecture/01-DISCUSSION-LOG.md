# Phase 1: Foundation + Multi-Person Architecture - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 01-foundation-multi-person-architecture
**Areas discussed:** Person identity model, Data migration strategy

---

## Person Identity Model

### Person ID Scheme

| Option | Description | Selected |
|--------|-------------|----------|
| Relationship-based | Use relationship labels: self, mom, dad, child-1, wife | |
| Name-based | Use real names: zhiwei, mama, baba | |
| You decide | Claude picks the best approach | ✓ |

**User's choice:** You decide
**Notes:** Claude decided on flexible slug scheme combining both approaches — user-defined kebab-case slugs.

### Person Switching

| Option | Description | Selected |
|--------|-------------|----------|
| Natural language in chat | Say "record blood pressure for mom" — AI resolves from context | ✓ |
| Explicit switch command | Run "switch to mom" first, then all operations apply | |
| You decide | Claude picks the best approach | |

**User's choice:** Natural language in chat
**Notes:** Person resolution handled at SKILL.md prompt layer, not Python code.

---

## Data Migration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Auto on first run | Migration happens automatically, existing data tagged as "self" | ✓ |
| Explicit command | User runs migration script manually | |
| You decide | Claude picks the best approach | |

**User's choice:** Auto on first run
**Notes:** Zero-cost migration — absence of person_id field IS the "self" marker, no file rewriting needed.

---

## Claude's Discretion

- Test framework migration strategy (keep unittest, add pytest runner)
- CI additional checks scope
- Package naming and import paths for skills/_shared/
- CI scope (GitHub Actions, pytest + ruff)
- Package structure (pyproject.toml with extras)

## Deferred Ideas

None
