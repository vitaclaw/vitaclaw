---
name: health-memory-mcp
description: MCP server exposing the VitaClaw personal health data node — read-only resources (profile, items, daily, graph) plus consent-checked tools (record_measurement, query_trend, prepare_share, ingest_fhir). Use when an external AI agent needs governed access to local health data over Model Context Protocol.
version: 1.0.0
user-invocable: false
allowed-tools: [Read]
metadata:
  openclaw:
    emoji: "🔌"
    category: health-records
    domain: health
    input: MCP JSON-RPC requests
    output: MCP resource bodies and tool results
---

# Health Memory MCP

This skill is the **runtime contract** for `server.py`, the Model Context Protocol server that lets external AI agents talk to a VitaClaw personal health data node.

## Resources (read-only)

| URI | Returns |
|-----|---------|
| `health://profile` | Health profile summary from `memory/health/_health-profile.md` |
| `health://items/{concept}` | Longitudinal data for the given concept (e.g. blood-pressure, sleep) |
| `health://daily/{date}` | Daily health log for `YYYY-MM-DD` |
| `health://graph/entity/{name}` | Knowledge graph entity by canonical name |

## Tools (consent-checked)

All tools route through `ConsentManager`. The caller must hold an active grant for the requested scope; otherwise the call is denied with an explanatory message.

- `record_measurement` — Append a measurement record (blood pressure, weight, sleep, etc.) under the matching skill's JSONL store
- `query_trend` — Return a windowed trend for a concept (recent values + slope + thresholds)
- `prepare_share` — Build a redacted sharing package for export to a clinician or family member
- `ingest_fhir` — Import FHIR R4 bundle from an external EHR

## Environment

The server resolves paths from these env vars (with sensible defaults):

- `VITACLAW_WORKSPACE` — Workspace root, defaults to the repo
- `VITACLAW_DATA_DIR` — JSONL data root, defaults to `<workspace>/data`
- `VITACLAW_MEMORY_DIR` — Markdown memory root, defaults to `<workspace>/memory/health`

## Safety boundary

- **Read-only by default.** Mutating tools always pass through `ConsentManager` first.
- **Local-first.** No outbound network calls from this server; FHIR ingest only reads bundles the caller hands in.
- **No diagnosis output.** Tool responses surface raw or aggregated records, never clinical conclusions.
