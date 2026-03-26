---
name: xiaomi-health-import
description: "Import health data from Xiaomi/Mi Fitness via account data export. Supports heart rate, steps, sleep sessions (with deep/light/REM stages), and weight. Handles CSV files from both legacy Mi Fit and new Mi Fitness apps with fuzzy dedup to prevent duplicates across devices. Trigger phrases: import Xiaomi health data, Mi Fitness import, import Mi Fit data, Xiaomi heart rate, Xiaomi steps, Xiaomi sleep."
version: 1.0.0
user-invocable: true
allowed-tools: [Bash]
metadata: {"openclaw":{"emoji":"","category":"health-data","requires":{"anyBins":["python3","python"]}}}
---

# Xiaomi/Mi Fitness Import Skill

You help the user import their Xiaomi/Mi Fitness health data from an account data export into VitaClaw's local health data store.

## Prerequisites

The user needs a Xiaomi account data export:
1. Go to https://account.xiaomi.com
2. Navigate to Privacy settings > Data download
3. Select health/fitness data categories
4. Request and download the export ZIP file
5. Transfer the ZIP file to the computer

Alternative: Some users may export from the Mi Fitness (or Zepp Life) app directly.

## Import Process

### Step 1: Locate the export file

Ask the user for the path to their Xiaomi/Mi Fitness export ZIP file.

### Step 2: Run the import

```bash
$PYTHON scripts/import_xiaomi_health_export.py /path/to/xiaomi_export.zip
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
- Breakdown by type (heart rate, steps, sleep, weight)
- Any errors encountered

## Supported Data Types

| Type | Source Files | Record Type |
|------|------------|-------------|
| Heart Rate | HEARTRATE_AUTO_*.csv | heart_rate |
| Steps/Activity | ACTIVITY_MINUTE_*.csv | steps |
| Sleep | SLEEP_*.csv (with deep/light/REM stages) | sleep_session |
| Weight | BODY_*.csv | weight |

## Deduplication

The importer uses fuzzy deduplication to prevent duplicate records:
- Timestamps within 60 seconds are considered the same event
- Numeric values within 5% tolerance are considered equivalent
- The first-imported record wins (existing records are preserved)

This means you can safely re-import the same export file or import from multiple devices without creating duplicates.

## Notes

- The importer handles both legacy Mi Fit and new Mi Fitness export formats
- Column names are discovered defensively from CSV headers
- Unrecognized file formats or columns are logged as warnings and skipped
- Xiaomi typically uses local time timestamps
- Sleep data includes deep/light/REM stage breakdown when available

## Python Command Detection

Before running the script, determine the available Python 3 command:
1. Try `python3 --version`
2. Try `python --version` (must be Python 3.x)
3. Try `py -3 --version` (Windows)

Use the first working command as `$PYTHON`.
