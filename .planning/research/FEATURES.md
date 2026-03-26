# Feature Landscape

**Domain:** Personal health record / health data management (AI skill library)
**Researched:** 2026-03-26
**Context:** VitaClaw Iteration 2 -- adding OCR, wearable import, visit summaries, onboarding, visualization, correlation, annual reports, and family management to an existing 222-skill health AI system running on OpenClaw.

---

## Table Stakes

Features users expect from a health data management tool at this level. Missing any of these makes the product feel incomplete for the target personas (chronic disease managers, health-conscious individuals, family health managers).

| # | Feature | Why Expected | Complexity | Dependencies | Notes |
|---|---------|--------------|------------|--------------|-------|
| T1 | **Medical document OCR: photo to structured data** | Users have paper reports (体检报告, 检验单). Every major PHR app (CareClinic, Tidy Health, MediTrack) supports scan-and-store. Without this, users must type everything manually. | High | None (PaddleOCR already a dependency) | PP-OCRv5 has 13pp improvement over v4. Chinese medical docs may need fine-tuning for lab-specific terminology and table layouts. |
| T2 | **OCR result confirmation before storage** | Health data accuracy is safety-critical. Auto-storing misread lab values is dangerous. PROJECT.md already mandates "extract -> display -> confirm -> store" flow. | Medium | T1 | Industry standard: no health app auto-commits OCR results. Must show extracted fields with original image side-by-side for user verification. |
| T3 | **Google Fit data import (file-based)** | Google Fit is the Android health data hub. Data exports via Google Takeout as CSV + TCX files. This follows the Apple Health import pattern already established. | Medium | None (Apple Health import exists as reference) | Takeout produces dated CSV files (YYYY-MM-DD.csv) + Daily Summaries.csv + TCX for activities. Map to existing HealthDataStore JSONL format. |
| T4 | **Basic health trend visualization** | Time-series charts for BP, blood glucose, weight, sleep are expected by every health app. Users need to see whether they are improving. matplotlib already in stack. | Medium | Data exists in HealthDataStore | Line charts for trends over time. Must support: blood pressure (systolic/diastolic dual-line), blood glucose (with target range bands), weight, sleep duration. |
| T5 | **Doctor-ready visit summary** | Existing `generate_visit_briefing.py` produces text. Users need a format they can show a doctor on phone or print. Every competitive PHR (CareClinic, Heart Reports, MediTrack) offers shareable summaries. | Medium | Data in HealthDataStore + memory system | Output: Markdown (editable) + HTML (phone display) + optional PDF (print). Must include: recent vitals with trends, current medications, key concerns, recent lab results. |
| T6 | **User onboarding / cold start profile** | New users face an empty system with 222 skills. Without guided setup, they have no idea where to start. Health apps that skip onboarding see 60%+ abandonment. | Medium | None | Conversational flow: basic demographics -> chronic conditions -> current medications -> tracking priorities -> preferred reminder cadence. Populates USER.md + IDENTITY.md + _health-profile.md. |
| T7 | **Multi-person data isolation** | Family health managers (e.g., a parent tracking elderly parents + children) need strict data separation. MediTrack, FAMHLTH, and MyDigiRecords all support family profiles. | High | T6 (each person needs a profile) | Per-person data directories under data/{person-id}/. Person switcher context. Must prevent cross-person data leaks. Template already exists: `health-family-agent`. |

## Differentiators

Features that set VitaClaw apart. Not expected by default, but create significant value when present. These leverage VitaClaw's unique position as an AI-native, local-first health skill library.

| # | Feature | Value Proposition | Complexity | Dependencies | Notes |
|---|---------|-------------------|------------|--------------|-------|
| D1 | **Cross-metric correlation analysis** | Most apps show single-metric trends. VitaClaw can correlate medication timing with BP changes, sleep quality with blood glucose, exercise with weight -- revealing causal patterns. SmartBP does basic BP-HRV correlation; VitaClaw can do it across ALL tracked metrics. | High | T4 (visualization), sufficient data history | Use pandas for statistical correlation. Present as: "When you sleep <6h, next-day blood glucose averages 15% higher." Must include confidence level and sample size to avoid spurious correlations. |
| D2 | **Annual health report (year-in-review)** | "Health Wrapped" (inspired by Spotify Wrapped) is a new category. HealthWrapped and HealthReview apps exist but are Apple Health-only. VitaClaw can generate richer narrative reports because it has AI context + cross-metric data + medical records. | Medium | T4 (visualization), 1+ year of data | Include: key metric trajectories, medication adherence stats, notable health events timeline, doctor visit summary, improvement areas, risk flags. Output as styled HTML. |
| D3 | **AI-powered OCR field extraction with medical knowledge** | Generic OCR gives text. VitaClaw can understand that "GLU 5.8 mmol/L" is fasting glucose, map it to the health-concepts.yaml registry, and auto-suggest which skill should track it. No consumer PHR does concept-level medical OCR. | High | T1 (basic OCR), health-concepts.yaml | Leverage LLM post-processing after PaddleOCR text extraction. Map extracted lab items to LOINC codes via ConceptResolver. This is the "intelligent" layer on top of OCR. |
| D4 | **Huawei Health data import** | Large Chinese user base with Huawei wearables. No direct API -- must use Huawei's data export (CSV/JSON via Settings > Data export, or full data request ZIP). Few international PHR apps support this. | Medium | T3 architecture (reuse import pattern) | Export formats: CSV for metrics, GPX/TCX for activities, JSON for detailed records. Password-protected ZIP for full export. Must handle Chinese field names in exports. |
| D5 | **Xiaomi/Mi Fitness data import** | Another huge Chinese wearable ecosystem. Export via account.xiaomi.com > Privacy > Manage Your Data produces CSV in ZIP. Same import architecture as Google Fit/Huawei. | Medium | T3 architecture (reuse import pattern) | CSV files in ZIP. May need to handle Zepp/Mi Fit legacy formats. Official export method is most reliable. |
| D6 | **Conversational health profiling (not form-based)** | Most apps use static forms for onboarding. VitaClaw runs on an AI runtime -- it can have a natural conversation to build the health profile, ask follow-up questions, and explain why each question matters. This builds trust (key for health data sharing). | Low | T6 (basic onboarding flow) | Implement as a SKILL.md with structured prompts. AI asks, user answers naturally, skill extracts structured data. Much lower implementation cost than building UI forms. |
| D7 | **Proactive correlation alerts** | Beyond showing correlations on demand (D1), automatically detect when a pattern emerges (e.g., "3 consecutive days of poor sleep correlate with elevated morning glucose") and surface it via heartbeat. | High | D1 (correlation engine), heartbeat system | Integrate with existing HealthHeartbeat. Must avoid alert fatigue -- only surface statistically significant patterns with actionable advice. |

## Anti-Features

Features to deliberately NOT build. These are tempting but wrong for VitaClaw's architecture, constraints, or philosophy.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time API sync with Google Fit / Huawei / Xiaomi** | Requires OAuth server, persistent network connection, API keys -- violates local-first principle. Google Fit API is being deprecated in favor of Health Connect anyway. | File-based import: user exports from platform, imports into VitaClaw. Matches Apple Health pattern. PROJECT.md already decided this. |
| **Built-in camera / photo capture UI** | VitaClaw is a skill library running inside OpenClaw, not a standalone app. No UI layer to build camera features on. | Accept image file paths as input. The AI runtime handles image capture; VitaClaw processes what it receives. |
| **FHIR / HL7 integration with hospital EHR systems** | Massive compliance burden (HIPAA, regional regulations). Requires institutional agreements. Way beyond scope of a personal tool. | OCR from paper documents. Manual data entry. If user has Apple Health records synced from their hospital, those come in via Apple Health import. |
| **Diagnostic AI / treatment recommendations** | Medical liability. VitaClaw's SOUL.md explicitly prohibits diagnoses. Six-layer output already has "must-see-doctor" as the safety boundary. | Trend analysis, pattern detection, risk flagging -- always ending with "discuss with your doctor." |
| **Cloud sync / multi-device access** | Violates local-first architecture. Introduces data security complexity. Not the product VitaClaw is. | All data stays local. If user needs multi-device, they can use file sync tools (iCloud, Syncthing) at the filesystem level. |
| **Interactive web dashboards (D3.js, Plotly)** | Adds JavaScript/web stack complexity. VitaClaw is Python-only. matplotlib is already in the stack and sufficient for static charts. | Generate static PNG/SVG charts with matplotlib. For HTML reports, embed charts as images. |
| **Wearable real-time streaming** | Requires Bluetooth stack, background services, platform-specific code. VitaClaw runs as a skill library, not a daemon. | Periodic file-based import. Daily or weekly is sufficient for trend analysis. |
| **Gamification (badges, streaks, leaderboards)** | Trivializes health management. Target users are chronic disease managers and health-conscious adults, not fitness gamers. | Meaningful progress indicators: "Your 30-day BP average improved from 145/92 to 138/88" is more valuable than a badge. |

## Feature Dependencies

```
T1 (OCR basic) --> T2 (OCR confirmation) --> D3 (AI-powered field extraction)
T3 (Google Fit import) --> D4 (Huawei import) --> D5 (Xiaomi import)
                           [shared import architecture]
T4 (trend visualization) --> D1 (cross-metric correlation) --> D7 (proactive alerts)
T6 (onboarding) --> D6 (conversational profiling)
T6 (onboarding) --> T7 (multi-person: each person needs profile)
T5 (visit summary) -- uses --> T4 (charts embedded in summary)
D2 (annual report) -- uses --> T4 (charts) + D1 (correlations)
```

**Critical path:** T1/T3/T4/T6 are foundation features with no upstream dependencies. Build these first.

## MVP Recommendation

### Phase 1: Foundation (build first, unblocks everything else)

1. **T6 - User onboarding/profiling** -- Without this, new users are lost. Low-hanging fruit with high impact. Enables multi-person later.
2. **T4 - Health trend visualization** -- Users need to SEE their data. Existing data in HealthDataStore is invisible without charts. Unblocks correlation, annual reports, visit summaries.
3. **T3 - Google Fit import** -- Establishes the file-based import pattern that Huawei and Xiaomi will reuse. Paired with existing Apple Health import, covers majority of wearable users.

### Phase 2: Medical Documents + Visit Support

4. **T1 + T2 - OCR pipeline (extract -> confirm -> store)** -- High complexity but high value. PaddleOCR is already a dependency; the gap is the end-to-end pipeline.
5. **T5 - Doctor-ready visit summary** -- Builds on T4 charts + OCR data. Direct user-facing value: saves time before every doctor visit.

### Phase 3: Wearable Ecosystem + Intelligence

6. **D4 + D5 - Huawei + Xiaomi import** -- Reuses T3 architecture. Medium effort, expands Chinese user coverage.
7. **D1 - Cross-metric correlation** -- Requires enough data history. This is VitaClaw's biggest differentiator vs. single-metric apps.
8. **D3 - AI-powered OCR field extraction** -- Enhances OCR pipeline with medical knowledge mapping.

### Phase 4: Advanced Features

9. **T7 - Multi-person/family management** -- High complexity. Needs stable single-user experience first.
10. **D2 - Annual health report** -- Needs 1+ year of data. Perfect for end-of-year timing.
11. **D7 - Proactive correlation alerts** -- Needs mature correlation engine + tuning to avoid alert fatigue.

### Defer indefinitely:
- **D6 - Conversational profiling** -- Nice enhancement to T6 but basic structured onboarding is sufficient for now. Can be added as a polish pass anytime.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Table stakes features | HIGH | Validated against multiple competitor apps (CareClinic, MediTrack, FAMHLTH, Heart Reports, SmartBP) |
| OCR pipeline | HIGH | PaddleOCR PP-OCRv5 capabilities verified via official docs. Medical document fine-tuning need confirmed. |
| Wearable data formats | MEDIUM | Google Fit Takeout format well-documented. Huawei/Xiaomi export formats verified but may vary by app version and region. |
| Cross-metric correlation | MEDIUM | Few consumer apps do this well. SmartBP does basic BP-HRV. Statistical approach needs careful implementation to avoid spurious findings. |
| Family management | MEDIUM | Competitor features verified. Implementation complexity in VitaClaw's file-based architecture needs phase-specific research. |
| Annual reports | LOW | "Health Wrapped" is emerging category. No established best practices. Design will need iteration. |

## Sources

- [Healthcare App Trends 2026 - TATEEDA](https://tateeda.com/blog/healthcare-mobile-apps-trends)
- [OCR for Medical Documents - Klippa](https://www.klippa.com/en/ocr/medical-documents/)
- [PaddleOCR PP-OCRv5 Documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5.en.md)
- [Google Fit Data Export - Google Support](https://support.google.com/fit/answer/3024190?hl=en)
- [Huawei Health Data Export - Worksmile](https://worksmile.zendesk.com/hc/en-us/articles/16772796471185-Huawei-Health-Export-activities-to-gpx-tcx)
- [Xiaomi Mi Fitness Data Export - Xiaomi Support](https://www.mi.com/global/support/article/KA-11566/)
- [Health Wrapped - App Store](https://apps.apple.com/us/app/health-wrapped-yearly-review/id6739070492)
- [FAMHLTH Family Health Tracker - App Store](https://apps.apple.com/us/app/famhlth-family-health-tracker/id6757278047)
- [SmartBP - Blood Pressure App](https://smartbp.app/)
- [Health App Onboarding Best Practices - Specode](https://www.specode.ai/blog/health-app-onboarding)
- [Healthcare Data Visualization - KMS Technology](https://kms-technology.com/blog/healthcare-data-visualization/)
- [Apple Health Records - Apple Support](https://support.apple.com/guide/iphone/view-health-records-iph2b3a37ddd/ios)
- [CareClinic PHR App](https://careclinic.io/phr/)
- [AI Medical Record Summaries - Abridge](https://www.abridge.com/blog/patient-visit-summaries--now-generated-in-real-time)
