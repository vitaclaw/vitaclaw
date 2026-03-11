# 营养与补剂方案优化 (Nutrition Supplement Optimizer)

## 概述

评估膳食营养缺口并优化补剂方案的场景技能，协调营养分析、食物替代查询、补剂间及补剂-药物相互作用检查、不良事件筛查和效果追踪，形成从评估到优化到跟踪的完整闭环。

## 适用场景

- 想了解当前补剂方案是否安全、合理、必要
- 需要检查补剂与药物之间的相互作用（如钙/铁与甲状腺药物）
- 希望通过饮食调整减少不必要的补剂
- 想优化补剂服用时间以最大化吸收效果
- 拥有基因检测数据，希望获取个性化营养建议

## 使用方式

- 手动调用: `/nutrition-supplement-optimizer [补剂清单和饮食概况]`
- 自动触发: 当用户提到补剂方案、营养缺口或补剂安全性时

## 输入格式

自然语言描述当前补剂清单（名称、剂量、服用时间）、饮食概况（每日三餐内容）、健康目标和现有用药。

## 输出示例

输出包含7个章节：当前补剂评估（必要/可选/冗余/需复查/风险）、相互作用警告、服用时间优化方案、食物替代建议、剂量建议（对比RDA和UL）、基因个性化调整（可选）和30天追踪计划。

## 调用的子技能

| 技能 | 用途 |
|------|------|
| nutrition-analyzer | 膳食营养分析、RDA达标评估 |
| food-database-query | 食物营养素查询、替代方案 |
| tooluniverse-drug-drug-interaction | 补剂间及补剂-药物相互作用检查 |
| tooluniverse-adverse-event-detection | 补剂不良事件信号检测 |
| nutrigx_advisor | 基因-营养代谢个性化（可选） |
| health-trend-analyzer | 补剂效果关联分析 |
| goal-analyzer | 依从性追踪、目标评估 |
| health-memory | 数据持久化 |

## 数据存储

- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 补剂纵向: `memory/health/items/supplements.md`
- 用药记录: `memory/health/items/medications.md`

## 医学免责声明

本技能仅供营养管理参考，不构成医疗建议。补剂方案调整不替代医学营养治疗，高剂量补剂应在医生指导下使用。如有健康问题，请咨询专业医疗人员。
