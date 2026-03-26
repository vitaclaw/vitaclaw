---
name: multimodal-medical-imaging
description: Analyzes medical images (X-ray, MRI, CT) using multimodal LLMs to identify anomalies and generate reports.
version: 1.0.0
user-invocable: false
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
metadata:
  openclaw:
    category: medical-imaging
    measurable_outcome: Execute skill workflow successfully with valid output within 15 minutes.
---

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

# Multimodal Medical Imaging Analysis

The **Multimodal Medical Imaging Analysis Skill** leverages state-of-the-art Vision-Language Models (VLMs) like Gemini 1.5 Pro and GPT-4o to interpret medical imagery alongside clinical text.

## When to Use This Skill

*   When you need a preliminary screening of medical images.
*   When correlating visual findings with textual clinical notes.
*   To generate structured reports (DICOM-SR-like) from raw images.

## Core Capabilities

1.  **Anomaly Detection**: Identify potential pathologies in X-rays, CTs, etc.
2.  **Report Generation**: Draft radiology reports in standard formats.
3.  **VQA (Visual Question Answering)**: Answer specific questions about an image (e.g., "Is there a fracture in the left femur?").

## Workflow

1.  **Input**: Provide an image file path (JPG, PNG) and a specific clinical question or "generate report" instruction.
2.  **Analyze**: The agent sends the image and prompt to the VLM.
3.  **Output**: Returns a JSON object with findings, confidence scores, and reasoning.

## Workflow

Agent 自身具备多模态视觉能力，可直接读取医学影像并分析。**无需外部 Python 脚本。**

1. 使用 `Read` 工具加载用户提供的影像文件（JPG/PNG）
2. Agent 视觉分析图像，结合临床问题进行解读
3. 输出结构化 JSON 结果（findings / severity / confidence / recommendation）

## Example Usage

**User**: "帮我看看这张胸片有没有肺炎。"

**Agent Action**: 直接用 Read 工具读取图片，用自身视觉能力分析，输出结构化报告。
