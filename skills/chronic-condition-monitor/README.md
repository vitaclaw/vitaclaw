# 慢病指标监测 (Chronic Condition Monitor)

## 概述
记录和追踪多项慢病指标（血压、血糖、HbA1c、血脂、尿酸、肌酐、eGFR、肝功能），对照中国临床指南判定异常，检测趋势恶化，执行联合分析（代谢综合征、共病告警），并生成就诊摘要。

## 适用场景
- 用户记录血压、血糖等日常慢病指标
- 用户录入化验单结果（肾功能、血脂、肝功能等）
- 需要查看指标趋势和联合分析
- 就诊前需要生成指标汇总摘要

## 使用方式
- 自动触发: 当用户提供慢病相关指标数值时自动调用
- 由场景技能调用: hypertension-daily-copilot、diabetes-control-hub 等场景技能可调用本技能记录指标

## 输入格式
自然语言输入指标值，例如：
- "血压 135/88，空腹血糖 6.8，尿酸 398"
- "化验结果：肌酐 95，TC 5.5，TG 1.9，LDL 3.6，HDL 1.15，ALT 35，AST 28"
- "生成就诊摘要"

## 输出示例
输出包含指标仪表盘、趋势告警、联合分析、严重程度评估。严重程度分三级：
- Level 1 (轻度): 1项指标轻度异常
- Level 2 (中度): 多项异常或进行性恶化
- Level 3 (重度): 危急值或代谢综合征

## 数据存储
- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 指标文件: `memory/health/items/blood-pressure.md`, `blood-sugar.md`, `weight.md`, `uric-acid.md`, `kidney-function.md`, `blood-lipids.md`, `liver-function.md`
- 健康档案: `memory/health/_health-profile.md`

## 医学免责声明
本技能仅供健康参考，不构成医疗建议。如有健康问题，请咨询专业医疗人员。
