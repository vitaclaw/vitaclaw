---
name: daily-health-briefing
description: "Generates a concise daily health briefing by aggregating today's data (vitals, sleep, medication, activity) from memory/health/ and wearable sources. Use when the user asks 'how am I doing today' or as part of the morning/evening routine."
version: 1.0.0
user-invocable: true
argument-hint: "[today | yesterday | YYYY-MM-DD]"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
metadata: {"openclaw":{"emoji":"📋","category":"health"}}
---

# Daily Health Briefing

汇总当天（或指定日期）的健康数据，生成一页式健康简报。

## 触发条件

- 用户说"今天身体怎么样"、"日报"、"daily briefing"
- Heartbeat 调度的晨间/晚间例行检查
- 用户指定日期："昨天的健康情况"

## 执行步骤

### Step 1: 确定目标日期

从用户输入提取日期，默认今天。

### Step 2: 读取数据源

```
# 1. 当日记录
Read memory/health/daily/YYYY-MM-DD.md

# 2. 关键指标最新值
Read memory/health/items/blood-pressure.md    → 最新值 + 趋势
Read memory/health/items/blood-sugar.md       → 最新值 + 趋势
Read memory/health/items/weight.md            → 最新值
Read memory/health/items/heart-rate-hrv.md    → 静息心率 + HRV
Read memory/health/items/sleep.md             → 昨夜睡眠评分 + 时长
Read memory/health/items/medications.md       → 今日用药完成情况
Read memory/health/items/supplements.md       → 今日补剂完成情况

# 3. 待办提醒（从 heartbeat task-board）
Read memory/health/heartbeat/task-board.md    → 今日待处理事项
```

### Step 3: 生成简报

按以下模板输出：

```markdown
## 每日健康简报 [daily-health-briefing · HH:MM]

### 概览
| 指标 | 数值 | 状态 | 趋势 |
|------|------|------|------|
| 血压 | 128/82 mmHg | 正常 | → 稳定 |
| 心率 | 68 bpm (静息) | 正常 | → 稳定 |
| 血糖 | 5.4 mmol/L (空腹) | 正常 | ↓ 改善 |
| 体重 | 72.5 kg | -- | → 稳定 |
| 睡眠 | 7h15min / 85分 | 良好 | ↑ 改善 |

### 用药 & 补剂
- [v] 氨氯地平 5mg (08:00)
- [v] 二甲双胍 500mg (08:00, 20:00)
- [ ] 阿托伐他汀 20mg (21:00) ← 待服

### 今日关注
- [高] 血压连续偏高第 3 天，建议今天加测一次午间血压
- [中] 周报未生成，建议今天完成

### 一句话总结
今天整体状态良好，血压需要持续关注。
```

### Step 4: 偏离检测

对比历史基线（items/*.md 中的 Rollup Rules / Thresholds），判断是否偏离"个人正常轨道"：

- **短期波动**：数值偏高/低但 7 日趋势稳定 → 标注为"短期波动，继续观察"
- **趋势偏离**：连续 3+ 天向同一方向移动 → 给出原因假设 + 下一步建议
- **急性异常**：超出阈值 → 直接输出风险提示

### Step 5: 写入 daily 文件

将简报写入 `memory/health/daily/YYYY-MM-DD.md`（插入或替换 `## 每日健康简报` 段落）。

## 与其他 Skill 的关系

- 数据来源：血压、血糖、睡眠、用药等 skill 各自写入 daily 和 items 文件
- 上层调用：`hypertension-daily-copilot` 可在其流程中内嵌本 skill
- Heartbeat：heartbeat 可在晨间和晚间自动触发本 skill

## 安全声明

本简报为健康参考，不构成医学诊断。如有异常指标持续偏离，请咨询医生。
