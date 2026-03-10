# 高血压每日管理搭档 (Hypertension Daily Copilot)

## 概述

高血压患者综合日常管理的场景编排技能。整合血压监测、用药提醒、DASH饮食评分、运动达标评估和多维趋势分析，提供每日简报、每周健康报告和异常预警。

## 适用场景

- 高血压患者需要每日记录和管理血压
- 正在服用降压药，需要追踪用药依从性
- 想了解饮食（钠/钾摄入）和运动对血压的实际影响
- 需要定期生成健康报告供就诊时参考
- 多药联用，需要定期检查药物相互作用

## 使用方式

- 手动调用: `/hypertension-daily-copilot [daily-entry | weekly-review | medication-review]`
- 自动触发: 当用户记录血压读数、用药情况或询问血压管理相关问题时

## 输入格式

**每日记录模式 (daily-entry)**:
- 血压读数：收缩压/舒张压 mmHg、脉搏、测量时间（建议晨起+睡前各一次）
- 用药记录：药名、剂量、服用时间
- 饮食摘要：三餐概要（重点关注高钠/高钾食物）
- 运动记录：运动类型、时长、强度

**每周回顾模式 (weekly-review)**: 无需额外输入，自动汇总本周数据

**用药审查模式 (medication-review)**: 当前完整用药清单

## 输出示例

每日简报包括：今日血压表（晨起/睡前读数+分级）、用药情况和依从性、DASH饮食评分及钠钾分析、运动评估、今日建议。每周报告包括血压控制率、综合评分、关联分析发现。

## 调用的子技能

| 技能 | 用途 |
|------|------|
| blood-pressure-tracker | 血压记录、分级、晨峰检测、昼夜变异分析 |
| medication-reminder | 用药依从性追踪 |
| nutrition-analyzer | DASH饮食评分（钠/钾分析） |
| fitness-analyzer | 运动合规评估（WHO高血压运动指南） |
| health-trend-analyzer | 多维趋势关联分析 |
| health-memory | 数据持久化 |
| weekly-health-digest | 每周健康摘要（周触发） |
| drug-interaction-checker | 药物相互作用审查（月触发） |
| emergency-card | 急救信息卡更新（换药触发） |

## 数据存储

- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 指标文件: `memory/health/items/blood-pressure.md`, `memory/health/items/medications.md`

## 医学免责声明

本技能仅供健康参考，不构成医疗建议。如有健康问题，请咨询专业医疗人员。
