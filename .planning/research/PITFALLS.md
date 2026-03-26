# Domain Pitfalls

**Domain:** Health data management -- OCR pipeline, multi-device import, multi-person support, health visualization
**Researched:** 2026-03-26

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or user-harmful outcomes.

### Pitfall 1: OCR Results Silently Written to Health Store Without Confirmation

**What goes wrong:** OCR extracts a blood glucose of "5.6" but the actual value is "15.6" (the leading "1" was cut off by a photo edge or misread). The value is written directly to the health data store. Downstream analysis, heartbeat alerts, and visit briefings all use the wrong number. The user never sees the raw OCR output.

**Why it happens:** Developers treat OCR as a reliable input source (like a typed form) and skip the human-in-the-loop confirmation step. The PROJECT.md key decision ("extract -> display -> confirm -> store") gets dropped during implementation because showing intermediate results in a conversational AI interface feels awkward.

**Consequences:** Incorrect health records silently pollute the data store. Wrong medication dosages or lab values could cause inappropriate health advice. Users lose trust when they discover errors days later. Rolling back bad data from JSONL files is painful.

**Prevention:**
1. OCR extraction must produce a **staging record** (separate from the health store) that includes the raw image region, OCR confidence score, and extracted value side-by-side.
2. The AI must present extracted values to the user in a structured format and explicitly ask for confirmation before calling `HealthDataStore.add()`.
3. Set a confidence threshold (e.g., 0.85). Below threshold: highlight the value in the confirmation prompt with a warning. Below 0.6: refuse to auto-fill and ask the user to type the value.
4. Add a `source: "ocr"` and `ocr_confidence: float` field to every OCR-originated record so they can be audited later.

**Detection:** Check if any code path calls `HealthDataStore.add()` directly from OCR output without an intermediate user-facing confirmation step. If the OCR pipeline has no "pending" or "staging" state, this pitfall is active.

**Phase relevance:** OCR Pipeline phase -- must be the core design constraint from day one.

---

### Pitfall 2: Deduplication Across Devices Produces False Positives or False Negatives

**What goes wrong:** A user imports Apple Health data (which includes heart rate from their Apple Watch) and then imports Xiaomi data (which also recorded heart rate from Mi Band). Same person, same time window, but slightly different timestamps (Apple records at :00, Xiaomi at :02) and slightly different values (72 vs 73 bpm). The current `HealthDataStore` dedup uses exact `(type, timestamp, data_hash)` matching -- these are NOT detected as duplicates. The user ends up with doubled heart rate entries, corrupting trend analysis.

**Why it happens:** The existing dedup in `health_data_store.py` (line 183) uses exact hash matching. This works for re-importing the same Apple Health export twice, but fails completely for cross-device scenarios where timestamps differ by seconds and values differ by measurement noise.

**Consequences:** Doubled data points distort averages, trend lines, and anomaly detection. Sleep data is particularly prone to this -- overlapping sleep sessions from different devices create impossible "32 hours of sleep" reports. Users see nonsensical visualizations and lose trust.

**Prevention:**
1. Implement **fuzzy dedup** for multi-device imports: for the same `record_type`, if two records have timestamps within a configurable window (e.g., 5 minutes) and values within a plausible noise margin (e.g., +/- 5% for heart rate, +/- 0.1kg for weight), flag as potential duplicate.
2. Add a `source_device` field to every record (e.g., "apple_watch", "mi_band_7", "manual"). Use this for dedup scope -- if same device, use exact dedup; if different devices, use fuzzy dedup.
3. When fuzzy dedup finds a match, keep the record from the "preferred" source (user-configurable, default: first imported) and store the alternative as a `_duplicate_ref`.
4. For sleep and workout data specifically, use time-range overlap detection (not point-in-time matching).

**Detection:** After importing from two different devices, query all records for a single day. If record count roughly doubles compared to single-device import, fuzzy dedup is missing.

**Phase relevance:** Multi-device import phase -- must be designed before the second device importer is built. Retrofitting fuzzy dedup after three importers exist is painful.

---

### Pitfall 3: Family Member Data Leaks Through Shared Code Paths

**What goes wrong:** The existing `FamilyManager` creates per-member data directories and has `can_read()`/`can_write()` checks. But the rest of the codebase -- `HealthDataStore`, `HealthMemoryWriter`, `HealthHeartbeat`, `generate_visit_briefing.py` -- all assume a single-user context. They read from `data/` and `memory/health/` without consulting `FamilyManager`. A parent managing their child's data accidentally writes data to the default (parent's) directory. Or heartbeat checks mix up which person's blood pressure is overdue.

**Why it happens:** `FamilyManager` was built as an isolated module but never integrated into the data flow. The 36 shared modules in `_shared/` have no concept of "current person context." Adding multi-person support requires threading `member_id` through every function that reads or writes health data -- but developers add it only to the new code (OCR, visualization) and forget the 115 existing Python implementations.

**Consequences:** Health data attributed to the wrong family member. A child's medication record appears in the parent's visit briefing. Heartbeat alerts fire for the wrong person. Worst case: medical decisions based on mixed-up data.

**Prevention:**
1. Define a **PersonContext** object (or similar) that wraps `member_id` + their data directory + their memory directory. Every data-accessing function must accept this context.
2. Add a `current_person` concept to the AI conversation state. When the user says "record my mom's blood pressure," the system switches context. All subsequent operations use mom's data directory until explicitly switched back.
3. **Never use default paths** in multi-person mode. If `PersonContext` is not provided and family mode is enabled, raise an error rather than falling back to the default directory.
4. Add integration tests that verify: write data for person A, switch to person B, query data -- person A's data must NOT appear.
5. Audit every call site of `HealthDataStore()` and `HealthMemoryWriter()` for hardcoded paths. The `CONCERNS.md` already flags the single-user architecture as a scaling limit.

**Detection:** Grep for `HealthDataStore()` or `HealthMemoryWriter()` constructor calls. If they use default `data_dir` without passing a person-scoped path, data isolation is broken.

**Phase relevance:** Family/multi-person phase -- but the `PersonContext` abstraction should be designed early (engineering foundation phase) even if multi-person is implemented later. Retrofitting context-threading through 36 shared modules after the fact is a rewrite.

---

### Pitfall 4: Chinese Medical Document OCR Fails on Tables and Handwriting

**What goes wrong:** PaddleOCR (already a project dependency) works well on printed Chinese text in standard layouts. But Chinese medical documents have: (a) tables with borders and merged cells (lab reports, blood test results), (b) handwritten annotations by doctors, (c) stamps and seals overlapping text, (d) thermal-printed receipts with faded text. PaddleOCR's table recognition produces garbled results or loses the key-value relationship between test names and results.

**Why it happens:** The existing `redact_ocr.py` uses PaddleOCR for text detection and PII classification -- it processes text line by line. But extracting structured medical data (e.g., "hemoglobin: 135 g/L, reference: 130-175") requires understanding table layout, not just recognizing individual text lines. Standard PaddleOCR text detection returns bounding boxes without table structure awareness.

**Consequences:** Lab results are extracted as a jumbled list of numbers and test names with no pairing. "135" appears in the OCR output but it's unclear whether it's hemoglobin, white blood cell count, or a patient ID number. The user must manually re-enter every value, defeating the purpose of OCR.

**Prevention:**
1. Use PaddleOCR's **PP-StructureV2** table recognition model (or PP-DocLayout) specifically for documents that contain tables. Detect layout first (table vs. free text vs. header), then apply the appropriate extraction strategy.
2. For lab reports: define a **template matching** approach. Common Chinese lab reports (blood routine, liver function, kidney function, lipid panel) follow predictable formats. Create extraction templates that map table columns to semantic fields. Fall back to generic table extraction for unknown formats.
3. For handwritten text: set a separate (lower) confidence threshold and always flag handwritten regions for user confirmation. Do not attempt to auto-structure handwritten notes.
4. For thermal receipts: add image preprocessing -- contrast enhancement, deskewing, noise removal -- before OCR. PaddleOCR accuracy drops significantly on low-contrast thermal prints.
5. Test the OCR pipeline against at least 5 real Chinese medical document types: blood test report, imaging report (CT/MRI text), prescription, outpatient summary, and discharge summary.

**Detection:** Run the OCR pipeline on a lab report with a table. If the output is a flat list of strings rather than structured key-value pairs with test names matched to values and reference ranges, table extraction is broken.

**Phase relevance:** OCR Pipeline phase -- table extraction capability is the difference between a useful and useless OCR feature for health data.

---

## Moderate Pitfalls

### Pitfall 5: Device Export Formats Change Without Warning, Breaking Importers

**What goes wrong:** Huawei Health, Mi Fitness, and Google Fit periodically change their export data formats. Huawei has blocked Google Fit integration entirely. Xiaomi changed from "Mi Fit" to "Mi Fitness" app with different data schemas. An importer that works today silently produces empty or partial imports after a format change.

**Why it happens:** These are proprietary formats with no stability guarantee. Unlike Apple Health (which has a relatively stable XML schema), Android health platforms treat export as a secondary feature and change schemas during app updates.

**Prevention:**
1. Each importer must have a **schema version detection** step that checks expected fields/structure before processing. If the schema doesn't match, fail loudly with "format version not recognized" rather than silently producing garbage.
2. Add **import result validation**: after import, check that the imported record count is reasonable (not zero, not suspiciously low). Compare against file size heuristics.
3. Keep the Apple Health importer as the **reference implementation** pattern. New importers should follow the same `Importer.import_export()` interface.
4. Document the exact export steps for each platform (with screenshots if possible) so users know which format version they're exporting.
5. Pin importers to "last verified format date" and warn users if their export file appears newer than the verified date.

**Detection:** After every major app update of Huawei Health or Mi Fitness, run a test import with a fresh export file. If field names or structure have changed, the importer will either fail or produce empty results.

**Phase relevance:** Multi-device import phase. Build each importer with format validation from day one.

---

### Pitfall 6: Health Visualization Uses Wrong Y-Axis Scale or Missing Clinical Context

**What goes wrong:** A blood pressure trend chart shows values from 120-140 mmHg on a y-axis scaled 0-300, making the trend look flat and insignificant. Or worse, the y-axis auto-scales to 120-140, making a normal 5 mmHg fluctuation look like a dramatic spike. No reference lines for normal ranges are shown. The user can't tell whether their values are good or concerning.

**Why it happens:** matplotlib auto-scales axes by default. Developers use `plt.plot()` without setting clinically meaningful axis ranges. Blood pressure, blood glucose, and weight each need different scale strategies. Generic charting code treats all metrics the same.

**Consequences:** Users misinterpret their health trends. A stable blood pressure looks alarming due to y-axis compression. A genuinely concerning upward trend in fasting glucose looks flat because the scale is too wide.

**Prevention:**
1. Define **per-metric chart configurations** with:
   - Fixed y-axis ranges (blood pressure: 60-200 mmHg; fasting glucose: 3-15 mmol/L; weight: auto with +/- 20% padding)
   - Reference range bands (green zone for normal, yellow for borderline, red for concerning)
   - Clinically meaningful labels (not just "mmHg" but "Normal < 120 / Elevated 120-129 / Stage 1 130-139")
2. Use **dual-line charts** for blood pressure (systolic + diastolic on same chart, not separate).
3. Time axis must be **proportional** -- data points 2 hours apart should not be rendered at the same spacing as data points 2 weeks apart.
4. Always include data point count and date range in chart title/subtitle.
5. Handle the **CJK font problem** upfront: matplotlib does not render Chinese characters by default. Configure `rcParams['font.family']` to use Noto Sans CJK or platform-appropriate CJK font. Test on macOS (PingFang SC), Windows (Microsoft YaHei), and Linux (Noto Sans CJK). Include a fallback font file bundled with VitaClaw if system fonts are unavailable.

**Detection:** Generate a blood pressure chart and check: (a) can you read Chinese labels? (b) are normal range bands visible? (c) does the y-axis start at a clinically sensible minimum (not zero)?

**Phase relevance:** Visualization phase. Define the per-metric config structure before building any charts.

---

### Pitfall 7: Cross-Metric Correlation Analysis Produces Spurious Correlations

**What goes wrong:** The system reports "your blood pressure drops when you take more steps" because both happen to trend in opposite directions over the same 30-day window. But the correlation is coincidental -- the user also started a new medication during that period. Or the system finds a "strong correlation" between sleep duration and blood glucose based on 5 data points.

**Why it happens:** Simple Pearson/Spearman correlation between two time series is statistically naive. Health data has confounders (medication changes, seasonal variation, stress events), small sample sizes, and irregular measurement intervals. Developers apply `pandas.corr()` and report the result as if it's clinically meaningful.

**Consequences:** Users make health decisions based on spurious correlations. "My blood pressure is better when I sleep less" could cause harmful behavior changes. The system loses credibility when correlations are obviously wrong.

**Prevention:**
1. **Minimum sample size**: require at least 14 paired data points before computing any correlation. Below that, show "not enough data for trend analysis."
2. **Always state correlation, never causation**: output must say "these tend to move together" not "X causes Y."
3. **Control for known confounders**: if medication was added/changed during the analysis window, flag the correlation as unreliable.
4. **Use rolling windows**: show how the correlation changes over time (e.g., 30-day rolling correlation) rather than a single number.
5. **Lag analysis**: some correlations have a time lag (medication takes days to affect blood pressure). Don't just correlate same-day values.
6. **Clinical plausibility filter**: only compute correlations between metric pairs that have known clinical relationships (sleep-glucose, exercise-blood pressure, weight-blood pressure). Don't correlate everything with everything.

**Detection:** Run correlation analysis on two unrelated metrics (e.g., step count and body temperature). If the system reports a "significant correlation" from random co-variation, the analysis lacks proper safeguards.

**Phase relevance:** Cross-metric correlation phase. This feature is high-risk/high-value -- better to ship it late and correct than early and misleading.

---

### Pitfall 8: Memory and Heartbeat Systems Break When Data Directory Moves to Per-Person Paths

**What goes wrong:** The existing `HealthMemoryWriter` writes daily/weekly/monthly markdown files to `memory/health/`. The `HealthHeartbeat` reads from this same location. When multi-person support moves data to `data/{member_id}/`, the memory and heartbeat systems either (a) still read from the old single-user path (showing stale data) or (b) crash because the expected directory structure doesn't exist under the new path.

**Why it happens:** Hardcoded paths. `health_memory.py` (1,814 lines) and `health_heartbeat.py` (1,221 lines) likely have path construction scattered throughout rather than centralized in one configuration point. The `CONCERNS.md` already flags these as "fragile areas" with regex-based markdown parsing.

**Consequences:** Memory distillation (daily -> weekly -> monthly summaries) stops working for family members. Heartbeat checks silently miss overdue measurements because they're looking in the wrong directory. No alerts fire for family members' health data gaps.

**Prevention:**
1. Before implementing multi-person, **audit and centralize all path construction** in `health_memory.py` and `health_heartbeat.py`. Every path must derive from a single `base_dir` parameter, not from `_repo_root()`.
2. The `FamilyManager.get_member_data_dir()` already returns per-person paths. Make `HealthDataStore`, `HealthMemoryWriter`, and `HealthHeartbeat` all accept this path as their root.
3. Add an **integration test**: create data for two family members, run heartbeat, verify each person's alerts reference only their own data.
4. Consider a lightweight **registry** that maps `member_id` -> `{data_dir, memory_dir, config}` so all modules resolve paths through one lookup.

**Detection:** After implementing multi-person paths, run the full heartbeat cycle. If alerts still reference the default user or mention the wrong person's medications, path routing is broken.

**Phase relevance:** Engineering foundation phase should centralize path construction. Multi-person phase implements per-person routing.

---

## Minor Pitfalls

### Pitfall 9: OCR Image Preprocessing Ignored, Destroying Accuracy on Phone Photos

**What goes wrong:** Users photograph medical documents with their phone -- resulting in images with shadows, perspective distortion, uneven lighting, and partial page captures. The OCR pipeline processes these directly, producing 60-70% accuracy instead of the 90%+ possible with preprocessing.

**Prevention:**
1. Add a preprocessing pipeline: auto-rotate (deskew), perspective correction, contrast normalization, shadow removal.
2. Pillow (already a dependency) handles basic transformations. For perspective correction, consider OpenCV if not already available.
3. Detect and warn about low-quality input images (too dark, too blurry, too small resolution) before running OCR.

**Phase relevance:** OCR Pipeline phase.

---

### Pitfall 10: Annual Health Report Generates Misleading Year-Over-Year Comparisons

**What goes wrong:** The annual report compares 2025 vs 2024 averages for blood pressure. But in 2024, the user measured once a month; in 2025, they measured daily. The 2024 average is based on 12 data points with a morning measurement bias; 2025 has 365 points with all-day coverage. The comparison is statistically meaningless.

**Prevention:**
1. Always show sample size alongside averages: "Average systolic BP: 128 mmHg (n=12)" vs "Average systolic BP: 132 mmHg (n=365)."
2. When sample sizes differ by more than 5x, add a caveat: "Comparison may not be meaningful due to different measurement frequencies."
3. For year-over-year, compare same-time-of-day measurements if possible (morning BP vs morning BP).

**Phase relevance:** Annual report phase.

---

### Pitfall 11: Visit Briefing Includes Stale or Irrelevant Data

**What goes wrong:** The one-click visit briefing pulls the last 90 days of all health data. For a dermatology visit, the doctor sees 90 days of blood pressure, glucose, sleep, and step count data -- none of which is relevant. The briefing is 5 pages long and the doctor ignores it.

**Prevention:**
1. Allow the user to specify visit type/department. Filter the briefing to relevant metrics (cardiology: BP, heart rate, medications; endocrinology: glucose, HbA1c, weight; general: everything).
2. Keep the default briefing to 1 page maximum. Use progressive disclosure: summary on page 1, full data available on request.
3. Mark data older than 30 days as "historical context" with lighter visual weight.

**Phase relevance:** Visit briefing upgrade phase.

---

### Pitfall 12: JSONL Performance Degrades With Multi-Person, Multi-Device Data Volume

**What goes wrong:** The current dedup in `health_data_store.py` iterates all records (`_iter_records()`) for every new record insertion to check for duplicates. With 3 family members, 2 devices each, recording heart rate every 5 minutes, that's ~2,500 records/day per person, ~7,500/day total. After 1 year: ~2.7 million records. Every insert scans all records.

**Prevention:**
1. Partition JSONL files by date AND person (e.g., `data/{member_id}/2026-03.jsonl`).
2. Dedup only within the relevant partition (same person, same day/month).
3. If performance is still an issue after partitioning, add an in-memory index (loaded on startup) of `(type, timestamp_rounded, data_hash)` for fast dedup lookups.
4. Set a retention policy: raw high-frequency data (heart rate every 5 min) can be downsampled to hourly averages after 90 days.

**Phase relevance:** Engineering foundation phase (partitioning) and multi-device import phase (dedup optimization).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Engineering Foundation | Path centralization breaks existing tests | Run full test suite after every path refactor; golden tests in `test_health_memory_golden.py` are the canary |
| Engineering Foundation | `pyproject.toml` migration breaks cloud-sync users (NutStore) | Ensure `.gitignore` covers `*.egg-info`, `__pycache__`; address NSConflict artifacts first |
| OCR Pipeline | PaddleOCR installation fails on Apple Silicon (M1/M2/M3) | PaddlePaddle has Apple Silicon wheels but they lag behind; test installation on macOS ARM64 early; provide fallback to CPU-only mode |
| OCR Pipeline | Large image files (phone cameras produce 4000x3000+ images) cause OOM | Resize to max 2048px on longest side before OCR; this also speeds up processing with minimal accuracy loss |
| Multi-device Import | Timezone mismatches between devices | Apple Health uses UTC internally, Xiaomi uses local time, Huawei varies. Normalize all timestamps to user's local timezone on import. Store timezone offset in metadata. |
| Multi-device Import | Xiaomi data export requires logging into web portal (not in-app) | Document the exact export path with screenshots; users will get stuck at "how do I export?" before they even reach the import step |
| Multi-person Support | FamilyManager config stored as YAML but YAML is optional dependency | If `pyyaml` is not installed, `FamilyManager` silently falls back to JSON. The family config format may differ between users depending on whether they have pyyaml installed. Standardize on one format. |
| Multi-person Support | Existing single-user data needs migration path to multi-person | First-time multi-person setup should auto-create a "self" member and move existing data into `data/self/` rather than requiring manual migration |
| Visualization | Charts saved as PNG lose resolution on high-DPI screens | Use `dpi=200` or higher for chart output; consider SVG for web display |
| Visualization | matplotlib is not thread-safe | If multiple visualizations are generated concurrently (e.g., heartbeat generates charts for all family members), use `matplotlib.use('Agg')` backend and create separate `Figure` objects per chart |
| Cross-metric Correlation | Irregular measurement intervals make time-series correlation unreliable | Resample to regular intervals (e.g., daily) using interpolation before computing correlations; flag days with no data as missing, don't interpolate across gaps > 3 days |
| Annual Report | First-year users have partial data | Don't generate year-over-year comparison if less than 6 months of data exists for either year; show "your first year summary" instead |

## Sources

- [Pharma Document AI & OCR Accuracy Benchmark](https://intuitionlabs.ai/pdfs/pharma-document-ai-ocr-accuracy-a-benchmark-analysis.pdf) - MEDIUM confidence
- [OCR Healthcare Use Cases and Drawbacks](https://www.shaip.com/blog/ocr-in-healthcare/) - MEDIUM confidence
- [PaddleOCR Table Recognition Discussion](https://github.com/PaddlePaddle/PaddleOCR/discussions/15090) - HIGH confidence (primary source)
- [PaddleOCR 3.0 Technical Report](https://arxiv.org/html/2507.05595v1) - HIGH confidence
- [Duplicate Medical Records: Causes and Solutions](https://verato.com/blog/duplicate-medical-records/) - MEDIUM confidence
- [Patient Deduplication Architectures](https://www.medplum.com/docs/fhir-datastore/patient-deduplication) - HIGH confidence
- [Matplotlib CJK Font Rendering Guide](https://ayeung.dev/2020/03/15/matplotlib-cjk-fonts.html) - HIGH confidence
- [Matplotlib CJK Issue #22536](https://github.com/matplotlib/matplotlib/issues/22536) - HIGH confidence
- [Patient-Facing Visualizations of Personal Health Data](https://pmc.ncbi.nlm.nih.gov/articles/PMC6785326/) - HIGH confidence
- [Building HIPAA-Compliant OCR Pipeline](https://intuitionlabs.ai/articles/hipaa-compliant-ocr-pipeline) - MEDIUM confidence
- [Xiaomi Mi Fitness Export Guide](https://www.mi.com/global/support/article/KA-11566/) - HIGH confidence (primary source)
- [Huawei Health / Google Fit Integration Issues](https://consumer.huawei.com/en/community/details/Huawei-health-Google-fit-integration/topicId_72902/) - MEDIUM confidence
- Codebase analysis: `health_data_store.py`, `family_manager.py`, `redact_ocr.py`, `health_memory.py` - HIGH confidence (direct source inspection)

---

*Pitfalls audit: 2026-03-26*
