# 心理健康伴侣 (Mental Wellness Companion)

## 概述

日常心理健康支持场景技能，协调危机检测、PHQ-9/GAD-7标准化评估、睡眠-情绪关联分析、运动处方、认知行为支持和行为激活目标追踪。危机检测在每次交互中优先执行。

## 适用场景

- 每日记录情绪、睡眠、社交和运动情况
- 需要定期完成PHQ-9/GAD-7标准化筛查评估
- 想了解睡眠质量与情绪波动的相关性
- 需要认知行为疗法（CBT）技巧建议和行为激活支持
- 感到压力或焦虑，需要个性化应对策略

## 使用方式

- 手动调用: `/mental-wellness-companion [mood-entry | weekly-assessment | crisis-check]`
- 自动触发: 当用户提到情绪追踪、心理压力或需要心理支持时

## 输入格式

### 每日情绪记录
自然语言描述当日心情、睡眠情况、社交活动、运动和压力事件。

### 周度评估
引导完成PHQ-9和GAD-7标准化问卷。

### 危机检查
任何文本输入均会先通过危机安全检测。

## 输出示例

每日输出包含：今日情绪评分和关键词、亮点、建议和本周进度。周度输出包含：PHQ-9/GAD-7趋势、睡眠-情绪关联、运动-情绪关联、社交活动分析、认知模式观察和行为激活目标完成率。

## 调用的子技能

| 技能 | 用途 |
|------|------|
| crisis-detection-intervention-ai | 文本情绪安全检测、危机信号识别（每次优先执行） |
| mental-health-analyzer | PHQ-9/GAD-7评估、情绪模式识别 |
| sleep-analyzer | 睡眠质量分析 |
| sleep-optimizer | 睡眠改善建议 |
| fitness-analyzer | 运动与情绪关联分析 |
| psychologist-analyst | 认知扭曲识别、应对策略建议 |
| goal-analyzer | 行为激活目标追踪 |
| adhd-daily-planner | 执行功能支持（条件触发） |
| health-memory | 数据持久化 |

## 数据存储

- 每日文件: `memory/health/daily/YYYY-MM-DD.md`
- 心理健康纵向: `memory/health/items/mental-health.md`
- 睡眠纵向: `memory/health/items/sleep.md`
- 情绪日记: `memory/health/items/mood.md`

## 医学免责声明

本技能是心理健康辅助工具，不替代专业心理咨询或精神科诊疗。PHQ-9/GAD-7评分仅为筛查工具，确诊需专业评估。如有心理健康问题，请咨询专业医疗人员。如遇紧急危机，请立即拨打心理援助热线（400-161-9995）或急救电话（120/911）。
