---
name: tumor-marker-trend
description: "Tracks tumor markers such as CEA, CA199, and AFP over time, supporting trend analysis, spike detection, and multi-marker comparison. Use when the user wants to log or analyze tumor marker values."
version: 1.0.0
user-invocable: true
argument-hint: "[log | trend | spike-detect | compare | report]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"📈","category":"health-scenario"}}
---
