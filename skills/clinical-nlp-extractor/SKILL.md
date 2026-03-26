<!--
# COPYRIGHT NOTICE
# This file is part of the "Universal Biomedical Skills" project.
# Copyright (c) 2026 MD BABU MIA, PhD <md.babu.mia@mssm.edu>
# All Rights Reserved.
#
# This code is proprietary and confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Provenance: Authenticated by MD BABU MIA

-->

---
name: 'clinical-nlp-extractor'
description: 'Extracts medical entities (Diseases, Medications, Procedures) from unstructured clinical text using regex and simple rules (or LLM wrappers).'
measurable_outcome: Execute skill workflow successfully with valid output within 15 minutes.
allowed-tools:
  - read_file
  - run_shell_command
---


# Clinical NLP Entity Extractor

The **Clinical NLP Skill** converts free-text clinical notes into structured data. It identifies key medical entities like problems/diagnoses, medications, and procedures.

## When to Use This Skill

*   When analyzing unstructured EHR notes.
*   To populate a patient's problem list or medication reconciliation.
*   To de-identify text (phi-removal) - *Basic version*.

## Core Capabilities

1.  **NER (Named Entity Recognition)**: Extracts Problems, Drugs, Procedures.
2.  **Negation Detection**: (Basic) Checks if a finding is denied ("No fever").
3.  **Structuring**: Returns JSON format compatible with FHIR/USDL.

## Workflow

Agent 自身具备医学 NLP 能力，可直接从临床文本中提取实体。**无需外部 Python 脚本。**

1. **Input**: 用户提供临床文本或文本文件路径
2. **Process**: Agent 直接阅读文本，识别疾病、药物、手术等医学实体，检测否定表述
3. **Output**: 以 JSON 格式返回实体列表，包含类型（PROBLEM/MEDICATION/PROCEDURE/TEST）、否定标志、原文位置

## Example Usage

**User**: "Extract entities from this note: Patient has diabetes type 2. Prescribed Metformin 500mg. No chest pain."

**Agent Action**: 直接分析文本，输出：
```json
[
  {"text": "diabetes type 2", "type": "PROBLEM", "negated": false},
  {"text": "Metformin 500mg", "type": "MEDICATION", "negated": false},
  {"text": "chest pain", "type": "PROBLEM", "negated": true}
]
```