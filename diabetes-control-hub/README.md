# 糖尿病综合控制中心 (Diabetes Control Hub)

## 概述

综合糖尿病管理场景技能，协调血糖追踪、饮食GI/GL分析、运动关联分析、体重代谢监测、肾功能监控及并发症风险评估，为糖尿病患者提供从日常记录到周度分析到体检解读的完整闭环。

## 适用场景

- 糖尿病患者记录每日血糖、饮食和运动数据
- 需要分析饮食GI/GL对血糖的影响并获取低GI替代建议
- 上传体检报告后需要解读HbA1c、肾功能、眼底检查等指标
- 调整降糖药物时需要检查药物相互作用
- 希望了解运动对血糖控制的量化影响

## 使用方式

- 手动调用: `/diabetes-control-hub [daily-log | weekly-review | checkup-report]`
- 自动触发: 当用户提到血糖记录、糖尿病饮食管理或降糖药物时

## 输入格式

### 每日记录
自然语言描述当日血糖（空腹/餐后）、饮食内容、运动情况、用药和体重。

### 周度回顾
无需额外输入，自动汇总过去7天数据。

### 体检报告
上传或描述体检结果（HbA1c、微量白蛋白、肌酐、eGFR、眼底检查、血脂等）。

## 输出示例

每日输出包含：今日血糖表格（各时点、状态）、eHbA1c和TIR计算、饮食GI评分、运动建议和告警信息。周度输出包含：血糖达标率、最佳/最差餐食排名、运动-血糖关联分析和体重趋势。

## 调用的子技能

| 技能 | 用途 |
|------|------|
| chronic-condition-monitor | 血糖趋势追踪、eHbA1c和TIR计算 |
| nutrition-analyzer | 碳水计数、宏量营养素分析 |
| food-database-query | 食物GI/GL查询、低GI替代建议 |
| fitness-analyzer | 运动与血糖关联分析 |
| weightloss-analyzer | BMR/TDEE计算、体重趋势追踪 |
| health-trend-analyzer | 多指标联合趋势分析 |
| kidney-function-tracker | 肌酐/eGFR/UACR追踪 |
| checkup-report-interpreter | 体检报告解读 |
| lab-results | 异常指标趋势对比 |
| drug-interaction-checker | 药物相互作用检查 |
| gwas-prs | T2D遗传风险评估（可选） |
| health-memory | 数据持久化 |

## 数据存储

- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 血糖纵向: `memory/health/items/blood-sugar.md`
- 体重纵向: `memory/health/items/weight.md`
- 肾功能纵向: `memory/health/items/kidney-function.md`
- 用药记录: `memory/health/items/medications.md`

## 医学免责声明

本技能仅供健康参考，不构成医疗建议。所有控糖方案需经内分泌科医生确认，胰岛素剂量调整必须由医生指导。如有健康问题，请咨询专业医疗人员。
