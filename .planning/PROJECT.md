# VitaClaw

## What This Is

VitaClaw 是一个运行在 OpenClaw 平台上的模块化健康 AI 技能库，222+ 个 SKILL.md 技能覆盖日常健康追踪、主动提醒、就医支持和医学研究。v1.0 (Iteration 2) 完成了工程基础、数据流通（onboarding + 设备导入 + OCR）、可视化与关联分析、临床输出（就医摘要 + 年报）。v1.1 聚焦于让系统对 Agent 更可操作——机械化架构约束、Skill 质量治理、数据可观测性，同时增加 AI 辅助 OCR 和主动关联预警。

## Current Milestone: v1.1 Agent-First Governance

**Goal:** 让 VitaClaw 对 Agent 更可操作，同时交付 AI 辅助 OCR 和主动关联预警

**Target features:**
- Skill 结构 linter（YAML frontmatter、import 方向、数据层使用验证）
- Skill 质量评分系统（222 个 skill 健康度评分 + 自动修复）
- HealthDataStore.stats() 数据可观测性
- SOUL.md 安全边界测试化
- 文档治理自动化（stale SKILL.md 扫描）
- AI 辅助 OCR 字段提取（LLM 后处理 + LOINC 概念映射）
- 主动关联预警（Heartbeat 自动发现显著相关性并推送）

## Core Value

比用户记得更全、追得更连续、整理得更系统——在需要就医或决策时，能快速调出完整上下文。

## Requirements

### Validated

- ✓ Chief-led 多 agent 架构（health-chief-of-staff 单入口路由） — Iteration 1
- ✓ JSONL 结构化健康数据存储（HealthDataStore） — Iteration 1
- ✓ Markdown 分层记忆系统（daily/weekly/monthly/quarterly 蒸馏链） — Iteration 1
- ✓ 222 个健康技能（37 core + 15 scenario + 14 analyzer + 9 research + 2 records） — Iteration 1
- ✓ Heartbeat 主动巡检与缺失提醒 — Iteration 1
- ✓ Apple Health XML 导入 — Iteration 1
- ✓ 门诊前摘要与门诊后跟进基础流程 — Iteration 1
- ✓ 六层输出（记录/解读/趋势/风险/建议/必须就医） — Iteration 1
- ✓ 隐私脱敏工具（privacy_desensitize.py） — Iteration 1
- ✓ 发布构建系统（skill manifest + release packages） — Iteration 1
- ✓ 工程基础加固（pyproject.toml + CI + ruff linter） — Phase 1
- ✓ 家庭/多人数据层（person_id 贯穿 HealthDataStore/HealthMemoryWriter/CrossSkillReader） — Phase 1
- ✓ 用户冷启动引导（对话式建档 SKILL.md → USER.md + IDENTITY.md + _health-profile.md） — Phase 2
- ✓ 体检报告/病历/检验单 OCR 流水线（PaddleOCR PPStructureV3 + 确认后入库） — Phase 2
- ✓ Google Fit / 华为健康 / 小米健康数据导入（HealthImporterBase + 模糊去重） — Phase 2
- ✓ 健康趋势可视化（HealthChartEngine + 临床参考范围 + CJK 支持） — Phase 3
- ✓ 跨指标关联分析（scipy Pearson+Spearman + 中文自然语言 insight） — Phase 3

- ✓ 就医摘要一键生成（HealthVisitSummary → Markdown/HTML/PDF + 嵌入趋势图） — Phase 4
- ✓ 年度健康报告（HealthAnnualReport → 7 节自包含 HTML + 嵌入图表） — Phase 4

### Active

- [ ] Skill 结构 linter（验证 YAML frontmatter schema、import 方向、数据层调用规范）
- [ ] Skill 质量评分系统（222 个 skill 的健康度评分 + 自动修复 PR 机制）
- [ ] HealthDataStore.stats() 数据可观测性（per-skill/per-person 记录数、时间跨度）
- [ ] SOUL.md 安全边界测试化（红旗→必须就医、隐私边界等规则变成可执行测试）
- [ ] 文档治理自动化（stale SKILL.md 扫描 + 修复建议）
- [ ] AI 辅助 OCR 字段提取（LLM 后处理 + LOINC 概念映射 via ConceptResolver）
- [ ] 主动关联预警（Heartbeat 集成 CorrelationEngine，自动发现显著相关性并推送）

### Out of Scope

- 快捷录入入口（Widget/快捷指令/Telegram bot） — 当前阶段不需要，AI 对话录入已够用
- 推送通道扩展（微信/Telegram/邮件） — 现有飞书 + Bark 满足需求
- Heartbeat 跨平台部署（Linux/Docker） — macOS launchd 当前够用
- 移动端原生 App — VitaClaw 是技能库不是 App，运行在 OpenClaw 内
- 多用户网络服务 — 本地优先架构，不做 SaaS

## Context

**现有代码基础：**
- 222 个技能，其中 115 个有 Python 实现
- `skills/_shared/` 36 个共享模块（~12,000+ 行），是整个系统的运行时基础
- OCR 能力已存在于 `privacy_desensitize.py` 和 `medical-record-organizer`，但没有串成端到端流水线
- Apple Health 导入已完整实现（`scripts/import_apple_health_export.py`），可作为新设备导入的参考模式
- `generate_visit_briefing.py` 已有门诊前摘要能力，需要升级输出格式
- 无 `pyproject.toml`，依赖管理靠 ad-hoc 安装
- 无 CI，测试需手动运行
- 无数据格式迁移工具

**技术栈：**
- Python 3.10+，无 web 框架
- JSONL + Markdown 文件存储，无数据库
- 可选依赖：requests, PyYAML, matplotlib, pandas, Pillow, PyMuPDF, PaddleOCR
- 运行在 OpenClaw 兼容的 AI 运行时内（Claude, GPT, Gemini, Llama）

**用户场景参考：**
- 慢病管理者（高血压、糖尿病）需要每日追踪 + 趋势 + 就医支持
- 健康关注者需要体检报告解读 + 年度总结
- 家庭健康管理者需要同时追踪多人

## Constraints

- **本地优先**：所有数据必须存储在本地文件系统，不依赖云服务 — 这是 VitaClaw 的核心差异化
- **技能格式**：新能力必须以 SKILL.md + 可选 Python 的形式实现 — 保持与 OpenClaw 运行时的兼容性
- **隐私边界**：健康数据不得未经用户同意离开本地 — SOUL.md 安全边界
- **向后兼容**：Iteration 1 的数据格式和记忆结构必须能平滑迁移 — 避免用户数据丢失
- **Python only**：不引入新语言 — 保持贡献者门槛低

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 多设备导入采用文件导入模式（非 API 同步） | 本地优先架构不适合 OAuth 服务器；用户手动导出文件后导入，与 Apple Health 模式一致 | — Pending |
| OCR 流水线：提取→展示→确认→入库 | 健康数据准确性要求高，自动提取后必须给用户确认机会再写入 | — Pending |
| 家庭多人：单工作区 + per-person 数据隔离 | 管理者（妈妈）在一个 VitaClaw 里管理全家，比多工作区更自然 | — Pending |
| 就医摘要：生成 Markdown + 可选 HTML/PDF | Markdown 保持可编辑性，HTML/PDF 适合打印和手机展示 | — Pending |
| 趋势可视化用 matplotlib | 项目已有 matplotlib 依赖，且不需要交互式图表 | — Pending |
| 工程基础作为第一个 phase | 没有可靠的包管理和 CI，后续功能开发都是在沙上建楼 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-26 after v1.1 milestone start*
