---
name: google-fit-import
description: "Import health data from Google Fit via Google Takeout export. Supports heart rate, daily steps, sleep sessions, and activities (TCX). Handles CSV and TCX file formats with fuzzy dedup to prevent duplicates across devices. Trigger phrases: import Google Fit data, Google Takeout import, import fitness data, Google Fit heart rate, Google Fit steps, Google Fit sleep."
version: 1.0.0
user-invocable: true
allowed-tools: [Bash]
metadata: {"openclaw":{"emoji":"","category":"health-data","requires":{"anyBins":["python3","python"]}}}
---

# Google Fit Import Skill

You help the user import their Google Fit health data from a Google Takeout export file into VitaClaw's local health data store.

## Prerequisites

The user needs a Google Takeout export containing their Fit data:
1. Go to https://takeout.google.com
2. Select only "Fit" data
3. Choose ZIP format and download
4. The ZIP file contains CSV files (heart rate, daily activity, sleep) and TCX files (activities)

## Import Process

### Step 1: Locate the export file

Ask the user for the path to their Google Takeout ZIP file.

### Step 2: Run the import

```bash
$PYTHON scripts/import_google_fit_export.py /path/to/takeout.zip
```

Optional flags:
- `--person-id <id>`: For family multi-person mode (e.g., `--person-id mom`)
- `--start-date YYYY-MM-DD`: Import only records after this date
- `--end-date YYYY-MM-DD`: Import only records before this date
- `--data-dir <path>`: Override the data storage directory
- `--format json`: Output results as JSON instead of markdown

### Step 3: Report results

Show the user the import summary including:
- Total records imported
- Records skipped as duplicates
- Breakdown by type (heart rate, steps, sleep, activities)
- Any errors encountered

## Supported Data Types

| Type | Source Format | Record Type |
|------|-------------|-------------|
| Heart Rate | CSV (bpm values with timestamps) | heart_rate |
| Daily Steps | CSV (daily activity metrics) | steps |
| Sleep | CSV (sleep sessions with duration) | sleep_session |
| Activities | TCX (running, cycling, etc.) | activity |

## Deduplication

The importer uses fuzzy deduplication to prevent duplicate records:
- Timestamps within 60 seconds are considered the same event
- Numeric values within 5% tolerance are considered equivalent
- The first-imported record wins (existing records are preserved)

This means you can safely re-import the same export file or import from multiple devices without creating duplicates.

## Python Command Detection

Before running the script, determine the available Python 3 command:
1. Try `python3 --version`
2. Try `python --version` (must be Python 3.x)
3. Try `py -3 --version` (Windows)

Use the first working command as `$PYTHON`.
