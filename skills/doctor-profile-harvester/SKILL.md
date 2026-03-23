---
name: doctor-profile-harvester
description: "Harvest public doctor candidates from hospital public pages and doctor profile pages, using controlled web-access browser fallback only when static fetch is insufficient. Use before doctor-fit-finder when the user has official hospital pages but not a ready-made doctors.json shortlist."
version: 1.0.0
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏥","category":"health-records"}}
license: MIT
---

# Doctor Profile Harvester

This skill turns official public hospital pages into a structured `doctors.json` candidate list.

## Use It When

- 用户已经有医院官网 / 科室页 / 医生页，但还没有 `doctors.json`
- 用户想先采集医生公开资料，再交给 `doctor-fit-finder` 做适配排序
- 静态抓取不够时，需要受控使用 `web-access` 做浏览器级读取

## Inputs

### `doctor-sources.json`

Each item can contain:

- `source_url` (required)
- `hospital`
- `city`
- `district`
- `department_hint`
- `allowed_domains`
- `entry_selector` (optional, for browser mode)
- `link_substrings` (optional)
- `profile_urls` (optional explicit doctor pages)
- `limit` (optional)
- `mode` (`auto` / `static` / `browser`)

## CLI

```bash
python3 doctor_profile_harvester.py \
  --sources-json /path/to/doctor-sources.json \
  --mode auto \
  --output-json /path/to/doctors.json
```

## Notes

- `web-access` is integrated as a controlled public-page capability layer, not a free-form social/browser automation layer.
- This skill only targets public hospital / clinic / doctor pages. It must not be used for social posting, login-heavy account actions, or payment flows.
- Output is conservative: if the page does not expose enough public profile text, the harvester skips that doctor instead of inventing details.
