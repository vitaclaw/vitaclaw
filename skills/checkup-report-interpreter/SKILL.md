---
name: checkup-report-interpreter
description: "Interprets physical examination reports by parsing PDF files into structured data, identifying abnormalities with severity grading, generating clinical explanations with health recommendations, and optionally syncing key findings into memory/health for long-term tracking. Supports year-over-year comparison of two reports. Use when the user uploads a checkup report or asks for help understanding lab results."
version: 1.0.0
user-invocable: true
argument-hint: "[report <pdf> | parse <pdf> | extract <pdf> | compare <pdf1> <pdf2>]"
allowed-tools: Read, Grep, Glob, Write, Edit
metadata: {"openclaw":{"emoji":"🏥","category":"health-scenario"}}
---

# Checkup Report Interpreter

Automatically parses physical examination report PDFs into structured data, then uses LLM for abnormality identification, clinical interpretation, and health recommendation generation.

## Features

- **Smart PDF Parsing**: Uses PyMuPDF to extract text from checkup reports, supporting multi-page reports
- **Structured Extraction**: LLM identifies all examination items (laboratory tests, imaging findings, physical examination), returning standardized JSON
- **Abnormality Grading**: Automatically determines abnormality severity based on reference ranges (urgent / important / moderate / minor), with 40+ built-in common indicator reference values
- **Clinical Interpretation**: Groups abnormal indicators by organ system and explains their clinical significance in plain language
- **Health Recommendations**: Generates personalized health recommendations and suggested follow-up items
- **Annual Comparison**: Supports item-by-item comparison of two reports, highlighting new abnormalities, worsening trends, and improvements
- **Memory Sync**: When `--memory-dir` or `--workspace-root` is supplied, writes checkup summary + key indicators back into `memory/health/`

## 推荐工作流（Agent 优先）

Agent 自身具备 LLM 推理能力，**推荐仅使用 Python 做 PDF 文本提取**，解读工作由 Agent 完成：

1. **提取 PDF 文本**（Python 负责二进制解析）：
   ```bash
   python checkup_report_interpreter.py parse checkup_report.pdf
   ```

2. **Agent 阅读提取的文本**，按以下六层输出格式进行解读：
   - 记录：列出所有检查项目及数值
   - 解读：识别异常项，按器官系统分组解释临床意义
   - 趋势：如有历史数据，对比变化趋势
   - 风险：评估异常项的严重程度（紧急/重要/中度/轻度）
   - 建议：个性化健康建议和复查项目
   - 必须就医：如有紧急异常，优先输出就医建议

3. **同步到 memory/health/**：Agent 将关键指标写入 `items/*.md` 和 `daily/YYYY-MM-DD.md`

## 备选：完全 Python 流程

如设置了 `OPENROUTER_API_KEY`，可使用 Python 完成全流程（PDF 解析 + LLM 解读）：

```bash
# Full report interpretation
python checkup_report_interpreter.py report checkup_report.pdf

# Extract structured examination items
python checkup_report_interpreter.py extract checkup_report.pdf

# Compare two years of reports
python checkup_report_interpreter.py compare 2026_checkup.pdf 2025_checkup.pdf

# Persist key findings into memory/health
python checkup_report_interpreter.py extract checkup_report.pdf \
  --report-date 2026-03-10 \
  --memory-dir /path/to/workspace/memory/health
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | 仅 Python 全流程需要 | OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | API endpoint (default: `https://openrouter.ai/api/v1/chat/completions`) |
| `LLM_MODEL` | No | Model name (default: `google/gemini-2.5-flash`) |
