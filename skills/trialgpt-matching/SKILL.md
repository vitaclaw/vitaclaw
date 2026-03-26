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
name: trialgpt-matching
description: Trial shortlist with dual-source search (ClinicalTrials.gov + ChiCTR)
keywords:
  - retrieval
  - ranking
  - ClinicalTrials
  - ChiCTR
  - patient-profile
  - clinical-trial-matching
  - 中国临床试验
measurable_outcome: Produce ≥5 ranked trials (when available) with rationale + missing-data notes within 3 minutes of receiving a patient query.
license: MIT
metadata:
  author: TrialGPT Team + VitaClaw Integration
  version: "1.1.0"
compatibility:
  - system: Python 3.9+
  - external: chictr-mcp-server (required for ChiCTR search)
allowed-tools:
  - run_shell_command
  - read_file
  - chictr_search_trials
  - chictr_get_trial_detail
---

# TrialGPT Matching (VitaClaw Enhanced)

Run the TrialGPT pipeline to retrieve, rank, and explain candidate trials for a patient before deeper eligibility review.
Enhanced with **dual-source search** to cover both ClinicalTrials.gov and ChiCTR (中国临床试验注册中心).

## 数据源说明

| 数据源 | 覆盖范围 | 查询方式 |
|--------|----------|----------|
| ClinicalTrials.gov | 全球临床试验 | TrialGPT Retriever + ClinicalTrials.gov API |
| ChiCTR (中国临床试验注册中心) | 中国注册临床试验 | chictr-mcp-server |

> **为什么需要两个数据源？**
> ClinicalTrials.gov 上中国的临床试验数据可能不全。ChiCTR 补充了在中国注册、尚未同步到 ClinicalTrials.gov 的试验。

## Inputs

- Patient summary (structured JSON or free text) with condition keywords.
- Optional filters: geography, phase, intervention, biomarker.
- 数据源偏好: `NCT` / `ChiCTR` / `both` (默认: both)

## Outputs

- Ranked trial table with NCT/ChiCTR ID, title, score, source, and short justification.
- Parsed inclusion/exclusion text ready for downstream eligibility agents.
- Missing data checklist (e.g., "ECOG not provided").
- **新增**: source 字段标注试验来源 (NCT / ChiCTR)

## 工作流 (Enhanced)

```
Step 1: 患者画像提取
    │
    ├─ read_file ~/patients/{patient}/ → 患者摘要
    │
Step 2: 关键词生成 + 并行查询
    │
    ├─ TrialGPT Retriever ──→ ClinicalTrials.gov API
    │                              (NCTxxxxxx)
    │
    └─ chictr_search_trials ──→ ChiCTR MCP Server
                                    (ChiCTRxxxxxx)
    │
Step 3: 结果合并 & 去重
    │
    ├─ 合并两个来源的试验列表
    ├─ 按注册号去重
    └─ 统一格式输出
    │
Step 4: TrialGPT Ranking (AI 评分)
    │
    ├─ 逐试验匹配度评分
    ├─ 生成推荐理由
    └─ 标注 missing data
    │
Step 5: 输出排序结果
    │
    └─ 表格形式输出:
       | 排名 | ID | 来源 | 评分 | 推荐理由 | 缺失数据 |
```

## 前置依赖检查

在执行本 skill 之前，**必须先检查 chictr-mcp-server 是否已安装并配置**。

### 自动检测流程

执行本 skill 时，按以下步骤检测 chictr-mcp-server 是否可用：

1. **检查 MCP 工具是否可用**: 尝试调用 `mcp__chictr__search_trials` 或 `chictr_search_trials`。如果工具存在且可调用，说明 chictr-mcp-server 已配置，跳到工作流 Step 1。
2. **如果工具不可用**: 说明 chictr-mcp-server 未安装或未配置，**必须先完成以下安装步骤**，否则 ChiCTR 数据源将不可用（仅能查询 ClinicalTrials.gov）。

### 安装 chictr-mcp-server

> 项目地址: https://github.com/PancrePal-xiaoyibao/chictr-mcp-server

#### 方式 1: npx 直接运行（推荐）

无需手动克隆仓库，通过 npx 自动拉取并运行：

```bash
npx -y chictr-mcp-server
```

#### 方式 2: 本地编译

```bash
git clone https://github.com/PancrePal-xiaoyibao/chictr-mcp-server.git
cd chictr-mcp-server
npm install
npm run build
npm start
```

### 配置 MCP Server

安装完成后，需要在 Claude Code 的 MCP 配置中注册 chictr server。

#### Claude Code 配置

在项目根目录的 `.mcp.json` 或全局 `~/.claude.json` 中添加：

```json
{
  "mcpServers": {
    "chictr": {
      "command": "npx",
      "args": ["-y", "chictr-mcp-server"]
    }
  }
}
```

#### 验证安装

配置完成后，重启 Claude Code 会话，然后验证以下工具是否可用：
- `mcp__chictr__search_trials` — 搜索 ChiCTR 临床试验
- `mcp__chictr__get_trial_detail` — 查询试验详情

如果工具可用，chictr-mcp-server 配置成功。如果不可用，请检查：
- Node.js 版本 ≥ 18
- npx 命令是否在 PATH 中
- 网络是否可访问 npmjs.com 和 chictr.org.cn

## 使用示例

### 查询患者适合的临床试验

```
输入: ~/patients/{patient}/
      诊断: 急性前壁心肌梗死 PCI术后, 2型糖尿病, 高血压, CKD 3a期
      筛选条件: 中国境内, 正在招募

输出:
┌────┬─────────────────┬────────┬───────┬──────────────────────┬──────────────────┐
│排名│ 试验ID          │ 来源   │ 评分  │ 推荐理由              │ 缺失数据         │
├────┼─────────────────┼────────┼───────┼──────────────────────┼──────────────────┤
│ 1  │ NCT05xxxx       │ NCT    │ 0.92  │ 糖尿病+心梗术后康复   │ ECOG评分         │
│ 2  │ ChiCTR240008xxx │ ChiCTR │ 0.89  │ 心脏康复,入组条件宽松 │ 既往用药史       │
│ 3  │ NCT06xxxx       │ NCT    │ 0.85  │ 双抗治疗优化研究      │ 基因检测报告     │
│ 4  │ ChiCTR240007xxx │ ChiCTR │ 0.78  │ 心衰二级预防          │ LVEF具体数值     │
│ 5  │ NCT04xxxx       │ NCT    │ 0.72  │ 降糖与心血管结局      │ HbA1c历史值      │
└────┴─────────────────┴────────┴───────┴──────────────────────┴──────────────────┘
```

## Guardrails

- ClinicalTrials.gov 数据默认筛选 RECRUITING 状态
- ChiCTR 数据筛选"正在招募"状态
- 评分仅作为参考，需临床医生最终确认入组资格
- 保留 prompt/config 元数据用于审计
- **新增**: 明确告知用户试验来源，避免混淆

## 与 trial-eligibility-agent 的协作

Ranked list + structured criteria → 传递给 `trial-eligibility-agent` 做逐条入组审核

## References

- TrialGPT: https://github.com/ncbi-nlp/TrialGPT
- ChiCTR MCP Server: https://github.com/PancrePal-xiaoyibao/chictr-mcp-server
- ChiCTR 官网: https://www.chictr.org.cn/


<!-- AUTHOR_SIGNATURE: 9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE -->
