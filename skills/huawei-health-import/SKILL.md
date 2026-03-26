---
name: huawei-health-import
description: "Import health data from Huawei Health via Settings data export. Supports heart rate, steps, sleep sessions, weight, blood pressure, and GPX activities. Handles CSV, JSON, and GPX file formats with fuzzy dedup to prevent duplicates across devices. Trigger phrases: import Huawei Health data, Huawei export import, import fitness data from Huawei, Huawei heart rate, Huawei steps, Huawei sleep."
version: 1.0.0
user-invocable: true
allowed-tools: [Bash]
metadata: {"openclaw":{"emoji":"","category":"health-data","requires":{"anyBins":["python3","python"]}}}
---

# Huawei Health Import Skill

You help the user import their Huawei Health data from a Settings data export file into VitaClaw's local health data store.

## Prerequisites

The user needs a Huawei Health data export:
1. Open Huawei Health app on the phone
2. Go to Me > Settings > Data and Privacy > Request Data
3. Select all health data categories
4. Download the export ZIP file
5. Transfer the ZIP file to the computer

## Import Process

### Step 1: Locate the export file

Ask the user for the path to their Huawei Health export ZIP file.

### Step 2: Run the import

```bash
$PYTHON scripts/import_huawei_health_export.py /path/to/huawei_export.zip
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
- Breakdown by type (heart rate, steps, sleep, weight, blood pressure, activities)
- Any errors encountered

## Supported Data Types

| Type | Source Format | Record Type |
|------|-------------|-------------|
| Heart Rate | CSV/JSON (bpm values with timestamps) | heart_rate |
| Steps | CSV (daily step counts) | steps |
| Sleep | CSV (sleep sessions with duration) | sleep_session |
| Weight | CSV (body weight measurements) | weight |
| Blood Pressure | CSV (systolic/diastolic readings) | bp |
| Activities | GPX (running, cycling routes) | activity |

## Deduplication

The importer uses fuzzy deduplication to prevent duplicate records:
- Timestamps within 60 seconds are considered the same event
- Numeric values within 5% tolerance are considered equivalent
- The first-imported record wins (existing records are preserved)

This means you can safely re-import the same export file or import from multiple devices without creating duplicates.

## Notes

- Huawei Health export format varies by app version and region
- The importer discovers column names defensively from CSV headers
- Unrecognized file formats or columns are logged as warnings and skipped
- Both CSV and JSON data files are supported (Huawei uses mixed formats)
- GPX files provide activity routes with timestamps and duration

## Python Command Detection

Before running the script, determine the available Python 3 command:
1. Try `python3 --version`
2. Try `python --version` (must be Python 3.x)
3. Try `py -3 --version` (Windows)

Use the first working command as `$PYTHON`.
