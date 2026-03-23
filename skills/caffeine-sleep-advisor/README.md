# 咖啡因与睡眠影响分析 (Caffeine & Sleep Advisor)

## 概述

追踪咖啡因摄入与睡眠质量关系的场景编排技能。通过半衰期衰减模型预测安全入睡时间，分析个人咖啡因敏感度阈值，结合基因数据（如有）提供精准的咖啡因管理建议。

## 适用场景

- 每天喝咖啡/茶但经常失眠，想知道是否与咖啡因有关
- 想找到适合自己的咖啡因截止时间
- 想了解自己的咖啡因敏感度属于什么水平
- 有基因检测数据，想知道自己是快代谢还是慢代谢
- 想在享受咖啡的同时保证睡眠质量

## 使用方式

- 手动调用: `/caffeine-sleep-advisor [log-beverage | sleep-report | weekly-analysis]`
- 自动触发: 当用户记录咖啡/茶饮用情况或询问咖啡因对睡眠的影响时

## 输入格式

**记录饮品模式 (log-beverage)**: 饮品类型、杯量、饮用时间（如"美式 350ml 08:30"）

**睡眠报告模式 (sleep-report)**: 入睡时间、起床时间、主观睡眠质量(1-10)，可选智能手环数据

**每周分析模式 (weekly-analysis)**: 无需额外输入，自动分析本周咖啡因-睡眠关联

## 输出示例

每日报告包括：今日咖啡因摄入表、体内残留量状态及安全入睡时间预测、昨晚睡眠回顾、今日建议。每周报告包括7天概览表、相关系数分析、个人敏感度发现。

## 调用的子技能

| 技能 | 用途 |
|------|------|
| caffeine-tracker | 咖啡因摄入记录与半衰期衰减计算 |
| sleep-analyzer | 睡眠效率、评分、入睡潜伏期分析 |
| sleep-optimizer | 个性化睡眠改善建议 |
| health-trend-analyzer | 咖啡因-睡眠关联分析与敏感度阈值识别 |
| nutrigx_advisor | CYP1A2基因型分析（可选，需基因数据） |
| nutrition-analyzer | 饮品隐藏热量和糖分分析 |
| health-memory | 数据持久化 |

## 数据存储

- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 指标文件: `memory/health/items/caffeine.md`, `memory/health/items/sleep.md`

## 医学免责声明

本技能仅供健康参考，不构成医疗建议。如有健康问题，请咨询专业医疗人员。
