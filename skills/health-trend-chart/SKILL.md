---
name: health-trend-chart
description: "Generate health metric trend charts with clinical reference bands. Supports blood pressure, blood glucose, weight, and sleep visualization over configurable time ranges."
version: 1.0.0
user-invocable: true
allowed-tools:
  - Read
  - Write
metadata:
  openclaw:
    category: health
    iteration: 2
---

# Health Trend Chart

Generate clinically contextualized trend charts for key health metrics. Charts include clinical reference bands, Chinese labels, and configurable time ranges.

## Supported Metrics

| Metric | Chart Type | Reference Bands |
|--------|-----------|----------------|
| Blood Pressure (bp) | Dual-line (systolic + diastolic) | Normal <120, Elevated 120-129, Stage 1 130-139, Stage 2 >=140 |
| Blood Glucose (glucose) | Line chart | Normal 3.9-6.1, Pre-diabetic 6.1-7.0, Diabetic >7.0 mmol/L |
| Weight (weight) | Line + 7-day moving average | Trend only (no fixed bands) |
| Sleep (sleep) | Bar chart (hours per day) | Recommended 7-9 hours |

## Time Ranges

- 7 days (7d) -- recent snapshot
- 30 days (30d) -- default, monthly view
- 90 days (90d) -- quarterly trends
- 365 days (1y) -- annual overview

## Usage Examples

- "Show my blood pressure trend for the past 30 days"
- "Generate a 90-day sleep chart"
- "Let me see my weight trend over the past 3 months"
- "Show my blood glucose chart for the last week"

## Implementation

Use the `HealthChartEngine` from `skills/_shared/health_chart_engine.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_chart_engine import HealthChartEngine

engine = HealthChartEngine(data_dir=None, person_id=None)

# Generate chart for the requested metric
path = engine.generate_blood_pressure_chart(days=30)
# or: engine.generate_blood_glucose_chart(days=30)
# or: engine.generate_weight_chart(days=30)
# or: engine.generate_sleep_chart(days=30)
```

## Output

Charts are saved as PNG files to `data/{skill-name}/charts/` and can be displayed inline by the AI runtime. The chart file path is returned for reference.

If no data exists for the requested metric and time range, inform the user that there are no records to visualize.

## CLI

```bash
python scripts/generate_health_chart.py --metric bp --days 30
python scripts/generate_health_chart.py --metric glucose --days 90 --format json
python scripts/generate_health_chart.py --metric sleep --days 7 --person-id mom
```
