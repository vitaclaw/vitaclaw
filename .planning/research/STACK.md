# Technology Stack

**Project:** VitaClaw Iteration 2
**Researched:** 2026-03-26

## Python Version Decision

**Recommendation: Python >= 3.11** (raise from current 3.10+)

| Reason | Detail |
|--------|--------|
| pandas 2.3+ requires 3.10, pandas 3.x requires 3.11 | Future-proofs dependency range |
| Python 3.10 EOL is October 2026 | Less than 7 months remaining |
| Type hint improvements (3.11+) | `Self`, `StrEnum`, `ExceptionGroup` |
| Performance | 3.11 is 10-60% faster than 3.10 (CPython Faster project) |

**Confidence: HIGH** -- pandas 3.x Python requirement verified via PyPI.

---

## Recommended Stack

### OCR Pipeline (Medical Documents)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PaddleOCR | >= 3.4.0 | Text detection + recognition for medical docs | Already used in project (`redact_ocr.py`, `privacy_desensitize.py`). PP-OCRv5 shipped in 3.0, adds 13-point accuracy gain over v4. Chinese medical document support is best-in-class. PaddleOCR-VL adds layout understanding for tables/forms. |
| PyMuPDF (fitz) | >= 1.24 | PDF page rendering to images | Already a dependency. Fast, no external binary needed. Renders PDF pages to PIL images for OCR input. |
| Pillow | >= 10.0 | Image preprocessing | Already a dependency. Needed for image rotation, contrast enhancement, cropping before OCR. |
| pillow-heif | >= 0.16 | HEIC/HEIF support | Already a dependency. iPhone photos default to HEIC format. |

**What NOT to use:**
- **Tesseract / pytesseract**: Poor on complex layouts, tables, and Chinese handwriting. No built-in table extraction. Requires external binary installation.
- **EasyOCR**: PyTorch dependency is heavy (~2GB). Slower than PaddleOCR on structured documents. Less accurate on Chinese medical text.
- **RapidOCR**: While lighter (ONNX-based), it's a downstream consumer of PaddleOCR models. Since VitaClaw already depends on PaddleOCR directly, adding RapidOCR creates redundancy with no benefit.
- **Cloud OCR APIs (Google Vision, Azure, AWS Textract)**: Violates local-first privacy constraint. Health data must not leave the device.

**Confidence: HIGH** -- PaddleOCR already in project, versions verified via PyPI and GitHub releases.

### Document Structure Extraction (Post-OCR)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PaddleOCR PP-Structure | (bundled in paddleocr >= 3.0) | Table extraction, layout analysis | Built into PaddleOCR 3.x. Extracts tables from lab reports, separates header/body/footer in medical documents. No additional dependency. |
| re (stdlib) | -- | Regex-based field extraction | Already used in `redact_ocr.py` for PII patterns. Extend with medical field patterns (lab values, reference ranges, units). |

**What NOT to use:**
- **LLM-based extraction as primary**: Too slow for batch processing, non-deterministic. Use LLM as a secondary verification/correction step, not the primary parser.
- **Camelot / Tabula**: Designed for digitally-created PDFs, not scanned documents. Medical documents are mostly scanned.

**Confidence: MEDIUM** -- PP-Structure capability verified via docs, but medical-specific extraction patterns need custom development.

### Multi-Device Health Data Import

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| csv (stdlib) | -- | Parse Google Fit daily aggregation CSVs | Google Takeout exports Fit data as CSV files in `Daily Aggregations/YYYY-MM-DD.csv`. Stdlib is sufficient. |
| json (stdlib) | -- | Parse Huawei Health JSON exports | Huawei exports health data as JSON files in ZIP archives. |
| zipfile (stdlib) | -- | Extract ZIP archives from all platforms | Google Takeout, Huawei, and Xiaomi all deliver data as ZIP files. |
| xml.etree.ElementTree (stdlib) | -- | Parse TCX activity files | Google Fit also exports TCX (XML-based) activity data. Already used pattern from Apple Health XML import. |
| pandas | >= 2.2.3 | Normalize heterogeneous data formats | Align timestamps, resample time series, merge data from different sources into unified JSONL schema. Use 2.2.x to maintain Python 3.10 compat if needed, or 2.3+ for 3.11+. |

**Import architecture**: Follow the existing `AppleHealthImporter` pattern -- each device gets its own importer class (`GoogleFitImporter`, `HuaweiHealthImporter`, `XiaomiHealthImporter`) with a shared base class handling JSONL output, patient archive writing, and workspace sync.

**Data format notes:**
- **Google Fit**: ZIP from Google Takeout containing CSV daily aggregations and TCX activity files. Fields include steps, heart rate, blood pressure, weight, blood glucose.
- **Huawei Health**: ZIP from Huawei ID portal containing JSON files per activity, HiTrack raw files, and optional TCX conversions. Includes GPS, heart rate, pace, sleep data.
- **Xiaomi/Mi Fitness**: ZIP from account.xiaomi.com containing CSV files. Includes steps, heart rate, sleep, SpO2 data.

**What NOT to use:**
- **OAuth API sync**: Violates local-first architecture. Requires running an HTTP server for OAuth callbacks. Google Fit API was deprecated (replaced by Health Connect on Android). Huawei Health Kit requires HMS integration.
- **Third-party aggregator libraries**: Most are abandoned or tightly coupled to specific API versions. Roll your own parsers -- the formats are simple CSV/JSON/XML.

**Confidence: MEDIUM** -- Export formats verified via official docs and community tools. Exact field schemas may vary by export date and region; parsers need to be defensive.

### Health Data Visualization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| matplotlib | >= 3.10 | Static trend charts (blood pressure, glucose, weight, sleep) | Already a project dependency. Generates PNG images embeddable in markdown memory files. No browser/JS runtime needed. |
| pandas | >= 2.2.3 | Time series resampling, rolling averages | `DataFrame.resample()` for daily/weekly aggregation. `rolling()` for smoothed trend lines. |

**Chart types needed:**
- Blood pressure: dual-line (systolic/diastolic) with normal range shading
- Blood glucose: line with meal markers and hypo/hyper range bands
- Weight: line with trend (rolling average)
- Sleep: stacked bar (deep/light/REM/awake)
- Multi-metric overlay: shared x-axis subplots for correlation visualization

**What NOT to use:**
- **Plotly**: Generates interactive HTML requiring a browser. VitaClaw outputs to markdown and terminal. Adds ~50MB dependency for no benefit in this context.
- **Seaborn**: Good for statistical plots but overkill for time series trends. matplotlib alone is sufficient.
- **Altair/Vega**: Requires a Vega runtime. Same browser dependency problem as Plotly.

**Confidence: HIGH** -- matplotlib already in project, time-series charting is well-documented.

### Cross-Metric Correlation Analysis

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pandas | >= 2.2.3 | `DataFrame.corr()` for correlation matrices | Pearson/Spearman/Kendall correlation between health metrics. |
| scipy | >= 1.13 | `scipy.stats.pearsonr`, `scipy.stats.spearmanr` | P-value calculation for statistical significance. Important to distinguish real correlations from noise in health data. |
| numpy | >= 1.26 | Array operations, NaN handling | Already an indirect dependency via pandas/matplotlib. |

**Analysis patterns needed:**
- Medication adherence vs. blood pressure changes (time-lagged correlation)
- Sleep quality vs. blood glucose (cross-correlation with `statsmodels.tsa.stattools.ccf`)
- Exercise vs. weight trends (rolling correlation)
- Multi-metric heatmap (correlation matrix visualization)

**What NOT to use:**
- **statsmodels** (full package): Only needed for `ccf()` cross-correlation function. If this is the only use, copy the algorithm (~20 lines) rather than adding a 30MB dependency. If more statistical modeling is needed later, add it then.
- **scikit-learn**: Overkill for correlation analysis. Reserve for future ML features.

**Confidence: MEDIUM** -- scipy/pandas correlation APIs well-documented. The medical interpretation of correlations (what's clinically meaningful vs. statistical noise) requires domain knowledge baked into skill logic, not just library calls.

### Family Multi-Person Support

No new libraries needed. This is an architecture concern, not a dependency concern.

**Implementation approach:**
- Per-person subdirectories under `data/` and `memory/health/` (e.g., `data/{person_id}/`, `memory/health/{person_id}/`)
- Person registry in a `family.json` or `FAMILY.md` file
- All existing importers, analyzers, and visualizers accept a `person_id` parameter
- Default person = primary user (backward compatible)

**Confidence: HIGH** -- Pure file-system organization. No new dependencies.

### Engineering Foundation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| setuptools | >= 75.0 | Build backend for pyproject.toml | Most widely adopted, best documentation, no new tool to learn. Project is a library (not an app), so Poetry's lock-file benefits are minimal. |
| pytest | >= 8.0 | Test framework | 52%+ Python developer adoption. Simpler syntax than unittest. Runs existing unittest.TestCase tests without modification (backward compatible). Fixtures, parametrize, and plugin ecosystem (pytest-cov, pytest-xdist). |
| pytest-cov | >= 5.0 | Coverage reporting | Integrates with pytest. Generates HTML/terminal coverage reports. |
| ruff | >= 0.9 | Linting + formatting | Replaces flake8 + isort + black. 10-100x faster (Rust-based). Single tool, single config in pyproject.toml. |
| pre-commit | >= 4.0 | Git hooks for quality gates | Runs ruff, pytest on commit. Prevents broken code from entering repo. |
| GitHub Actions | -- | CI pipeline | Free for public repos. Run tests, lint, build on push/PR. |

**What NOT to use:**
- **Poetry**: Adds complexity (poetry.lock, virtual env management) for a skill library that isn't distributed via PyPI. setuptools + pyproject.toml is simpler and standard.
- **Hatch**: Good tool but less ecosystem adoption than setuptools. Not worth the learning curve for this project.
- **tox**: pytest + GitHub Actions matrix covers multi-version testing without tox's configuration overhead.
- **black + isort + flake8**: Three tools doing what ruff does alone, 100x slower. No reason to use them in 2026.
- **mypy**: VitaClaw's codebase doesn't use type annotations extensively. Adding mypy would create massive churn. Consider adding gradually in future iterations.

**Confidence: HIGH** -- All tools are industry standard, versions verified.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| OCR engine | PaddleOCR 3.4+ | Tesseract 5 | Poor table extraction, weak on Chinese medical docs, requires external binary |
| OCR engine | PaddleOCR 3.4+ | EasyOCR | 2GB PyTorch dependency, slower, less accurate on structured documents |
| OCR engine | PaddleOCR 3.4+ | RapidOCR | Redundant -- uses same PaddleOCR models via ONNX. Project already has PaddleOCR. |
| Visualization | matplotlib | Plotly | Requires browser for interactive charts. VitaClaw is terminal/markdown-first. |
| Visualization | matplotlib | Seaborn | Overkill for time-series trends. matplotlib is already a dependency. |
| Test framework | pytest | unittest (keep) | unittest works but pytest runs it AND adds better DX. Gradual migration. |
| Linter | ruff | flake8+black+isort | Three tools replaced by one, 100x slower |
| Build backend | setuptools | Poetry | Lock files unnecessary for a skill library. Adds complexity. |
| Build backend | setuptools | Hatch | Less ecosystem adoption. No compelling advantage here. |
| Stats | scipy (targeted) | statsmodels (full) | 30MB for one function. Copy ccf() if needed. |
| Data format | pandas 2.2/2.3 | polars | pandas already used in project. Polars API is different. Migration cost > performance benefit for this data scale. |

---

## Full Dependency List

### Core (always installed)

```bash
pip install \
  requests \
  PyYAML \
  pandas>=2.2.3 \
  numpy>=1.26 \
  matplotlib>=3.10
```

### OCR Pipeline (optional, for medical document import)

```bash
pip install \
  paddleocr>=3.4.0 \
  PyMuPDF>=1.24 \
  Pillow>=10.0 \
  pillow-heif>=0.16
```

### Analysis (optional, for correlation features)

```bash
pip install \
  scipy>=1.13
```

### Development

```bash
pip install \
  pytest>=8.0 \
  pytest-cov>=5.0 \
  ruff>=0.9 \
  pre-commit>=4.0
```

### pyproject.toml skeleton

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "vitaclaw"
version = "2.0.0"
description = "Modular health AI skill library for OpenClaw"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
analysis = [
    "pandas>=2.2.3",
    "numpy>=1.26",
    "matplotlib>=3.10",
    "scipy>=1.13",
]
ocr = [
    "paddleocr>=3.4.0",
    "PyMuPDF>=1.24",
    "Pillow>=10.0",
    "pillow-heif>=0.16",
]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.9",
    "pre-commit>=4.0",
]

[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.coverage.run]
source = ["skills/_shared"]
```

---

## Sources

- [PaddleOCR GitHub releases](https://github.com/PaddlePaddle/PaddleOCR/releases) -- v3.4.0 (2026-01-29), PP-OCRv5 in 3.0 (2025-05-20)
- [paddleocr PyPI](https://pypi.org/project/paddleocr/) -- latest 3.4.0
- [pandas PyPI](https://pypi.org/project/pandas/) -- 3.0.1 requires Python >=3.11, 2.2.3 supports >=3.9
- [matplotlib PyPI](https://pypi.org/project/matplotlib/) -- 3.10.8, requires Python >=3.10
- [Google Fit Takeout](https://support.google.com/fit/answer/3024190) -- CSV/TCX export format
- [Huawei Health export](https://developer.huawei.com/consumer/en/doc/HMSCore-Guides/data-export-0000001078524336) -- JSON/ZIP format
- [Xiaomi Mi Fitness export](https://www.mi.com/global/support/article/KA-11566/) -- CSV/ZIP from account.xiaomi.com
- [Python Packaging User Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [PaddleOCR vs alternatives comparison](https://www.koncile.ai/en/ressources/paddleocr-analyse-avantages-alternatives-open-source)
- [pytest vs unittest 2026](https://quashbugs.com/blog/pytest-vs-unittest) -- 52%+ adoption
- [Python packaging best practices 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)
