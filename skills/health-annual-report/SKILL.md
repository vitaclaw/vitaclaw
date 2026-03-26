---
name: health-annual-report
description: "生成年度健康回顾报告：指标轨迹、用药依从性、健康事件时间线、改善领域和相关性洞察"
version: 1.0.0
user-invocable: true
allowed-tools:
  - Edit
  - Read
  - Write
  - Bash
metadata: {"openclaw":{"emoji":"📊","category":"health"}}
---

# 年度健康报告

生成全面的年度健康回顾报告，帮助用户了解一整年的健康追踪成果。报告包含 7 个核心部分，输出为自包含的 HTML 文件。

## 适用场景

- 年末健康回顾，了解一年来的健康变化趋势
- 评估长期追踪的价值和成果
- 为下一年设定健康改善目标提供数据支持
- 就医时向医生展示完整的年度健康概况

## 报告内容

### 1. 年度概览
总记录数、追踪天数、就医次数、追踪指标数等关键统计

### 2. 指标轨迹
血压、血糖、体重、睡眠的 12 个月趋势图表（嵌入为 base64 图片）

### 3. 用药依从性
按药物分组的服药记录统计，月度依从率热力图

### 4. 健康事件时间线
从日志中提取的就医、症状、用药变化等重要事件的时间线

### 5. 改善领域
Q1 与 Q4 关键指标均值对比，标识改善和恶化的指标

### 6. 相关性洞察
跨指标统计相关性分析结果（如血压与睡眠、血糖与体重）

### 7. 目标回顾
对照健康档案中设定的目标，回顾实际达成情况

## 使用方式

### CLI 命令

```bash
python scripts/generate_annual_report.py --year 2025
python scripts/generate_annual_report.py --year 2025 --person-id mom
python scripts/generate_annual_report.py --year 2025 --output ~/Desktop/report.html
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--year` | 报告年份 | 当前年份 |
| `--person-id` | 家庭成员 ID | 无（主用户） |
| `--data-dir` | 数据目录 | 自动检测 |
| `--memory-dir` | 记忆目录 | 自动检测 |
| `--output` | 输出文件路径 | `memory/health/files/annual-report-{year}.html` |

## 输出格式

- 单个自包含 HTML 文件，内联 CSS，无外部依赖
- 图表以 base64 编码嵌入
- 支持手机查看（响应式布局）
- 支持打印（print-friendly CSS）

## 数据不足时的处理

- 追踪天数不足时会在报告顶部显示提示
- 某项数据为空时显示"本年度暂无相关记录"
- 不会因数据缺失而崩溃
