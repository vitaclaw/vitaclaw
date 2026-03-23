---
name: doctor-fit-finder
description: "Ranks public doctor candidates for a specific patient profile by combining department fit, location, continuity potential, public profile matching, and optional PubMed evidence. Use when the user wants doctor recommendations rather than a generic top-doctor list."
version: 1.0.0
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🩺","category":"health"}}
---

# Doctor Fit Finder

This skill is for public-information doctor matching, not for automatic booking.

## Best Use Cases

- 体检异常后，不知道该挂哪个科、找哪类医生
- 高血压 / 糖前期 / 脂肪肝等慢病，想找更适合长期随访的医生
- 需要在指定城市 / 区域内，从多个公开医生资料里筛 shortlist
- 需要把医院官网信息和 PubMed 学术信号结合起来看，但不想被“论文数量”误导

## Input Files

### `patient.json`

Suggested fields:

- `city`
- `district`
- `conditions`
- `symptoms`
- `abnormal_findings`
- `goals`
- `preferred_hospitals`
- `continuity_preference`

### `doctors.json`

Array of doctor candidates, each with fields such as:

- `name`
- `english_name`
- `hospital`
- `department`
- `city`
- `district`
- `specialties`
- `official_profile_url`
- `schedule`
- `accepts_long_term_followup`
- `pubmed_query`

If you do not already have `doctors.json`, run `doctor-profile-harvester` first against official hospital pages.

## CLI

```bash
python3 doctor_fit_finder.py \
  --patient-json /path/to/patient.json \
  --doctors-json /path/to/doctors.json \
  --pubmed-mode auto
```
