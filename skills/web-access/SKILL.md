---
name: web-access
description: "Controlled browser and network access for VitaClaw public-health workflows. Use when official hospital pages, doctor profile pages, dynamic health portals, or other public medical pages require browser fallback beyond static fetch. Do not use for social posting, payment, or sensitive account automation."
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🌐","category":"health-infrastructure"}}
license: MIT
---

# Web Access

This is a VitaClaw-adapted vendor integration of the upstream `eze-is/web-access` skill.

## Purpose

Use this skill as a controlled capability layer for:

- official hospital public pages
- doctor public profile pages
- public clinic schedules / department pages
- public health instructions or checkup preparation pages

It is intentionally **not** configured as a free-form consumer browser automation layer inside VitaClaw.

## Runtime

The health workflows use:

- `scripts/check-deps.sh` for Node + Chrome remote-debugging readiness
- `scripts/cdp-proxy.mjs` for browser CDP access
- `references/cdp-api.md` for endpoint behavior

## Guardrails

- Only public `http(s)` pages should be harvested by default
- Do not use this skill for social publishing, payment, account settings, or anything that mutates a user's personal browser state
- In VitaClaw, this skill is primarily consumed by `doctor-profile-harvester` and other public-info health workflows

## Attribution

- Upstream project: [eze-is/web-access](https://github.com/eze-is/web-access)
- Upstream author: 一泽 Eze
- Upstream license: MIT
