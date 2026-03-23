# 肾功能追踪 (Kidney Function Tracker)

## 概述
记录肌酐、eGFR、尿蛋白等肾功能指标，使用 CKD-EPI 2021 无种族系数公式自动计算 eGFR，判定 CKD G1-G5 分期，监测白蛋白尿分类 A1-A3，计算 eGFR 衰退速率，并提供复查提醒。

## 适用场景
- 用户提供肌酐或 eGFR 化验结果
- 用户询问肾功能状况或 CKD 分期
- 需要查看 eGFR 衰退趋势
- 需要复查提醒

## 使用方式
- 自动触发: 当用户提供肌酐或 eGFR 数值时自动调用
- 由场景技能调用: chronic-condition-monitor、diabetes-control-hub 等场景技能可调用本技能

## 输入格式
自然语言输入，例如：
- "今天肌酐 95"
- "肌酐 95，尿微量白蛋白/肌酐比 45"
- "查看 eGFR 趋势"
- "下次什么时候该复查？"

## 输出示例
输出包含当前指标、CKD 分期、白蛋白尿分类、eGFR 衰退速率分析、趋势表格、告警和监测计划。

## 数据存储
- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 指标文件: `memory/health/items/kidney-function.md`
- 健康档案: `memory/health/_health-profile.md`

## 医学免责声明
本技能仅供健康参考，不构成医疗建议。如有健康问题，请咨询专业医疗人员。
