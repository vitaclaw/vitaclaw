# 热量与健身管理 (Calorie & Fitness Manager)

## 概述

综合管理热量收支和运动数据的场景编排技能。整合体重分析、营养评估、食物查询、运动分析、趋势追踪和SMART目标管理，提供日/周/月三级报告和智能预警。

## 适用场景

- 减脂期需要精确追踪每日热量缺口
- 增肌期需要确保蛋白质摄入和训练容量达标
- 想了解饮食和运动模式与体重/体脂变化的关联
- 设定健身目标并追踪进度
- 科学管理体重而非盲目节食或过量运动

## 使用方式

- 手动调用: `/calorie-fitness-manager [daily-log | weekly-review | goal-setup]`
- 自动触发: 当用户记录饮食、运动数据或询问热量/健身相关问题时

## 输入格式

**每日记录模式 (daily-log)**:
- 三餐 + 加餐内容（食物名称、估计分量）
- 运动类型、时长、强度
- 体重 (kg)，体脂率 (%) 可选

**每周回顾模式 (weekly-review)**: 无需额外输入，自动汇总本周数据

**目标设定模式 (goal-setup)**: 目标类型（减脂/增肌）、目标数值、目标日期

## 输出示例

每日报告包括：热量收支表（BMR/TDEE/摄入/净缺口）、宏量营养素达标情况、运动摘要、今日建议。每周报告包括体重趋势、热量汇总、最佳训练日分析、营养评分。

## 调用的子技能

| 技能 | 用途 |
|------|------|
| weightloss-analyzer | BMR/TDEE计算、能量收支、体重预测、平台期检测 |
| nutrition-analyzer | 宏量/微量营养素分析、营养评分 |
| food-database-query | 食物热量/GI/营养素查询 |
| fitness-analyzer | 运动消耗计算、训练分析、WHO/ACSM合规评估 |
| health-trend-analyzer | 多维趋势关联分析 |
| goal-analyzer | SMART目标设定与进度追踪 |
| wearable-analysis-agent | 可穿戴设备数据整合（可选） |
| tcm-constitution-analyzer | 中医体质运动/饮食偏好（可选） |
| health-memory | 数据持久化 |

## 数据存储

- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 指标文件: `memory/health/items/weight.md`, `memory/health/items/body-fat.md`, `memory/health/items/calories.md`

## 医学免责声明

本技能仅供健康参考，不构成医疗建议。如有健康问题，请咨询专业医疗人员。
