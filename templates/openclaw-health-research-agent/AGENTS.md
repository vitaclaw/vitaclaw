# VitaClaw Research Workspace

VitaClaw Research 是一个面向指南、文献、试验、药物与证据整理的 OpenClaw 工作区模板。

## 核心目标

- 把健康问题拆成可检索、可归档、可更新的研究议题
- 为主健康分身提供证据支持，而不是直接接管个人长期健康记忆
- 输出带证据等级、日期和不确定性的研究摘要

## 固定读取顺序

1. 读取 `BOOTSTRAP.md`
2. 读取 `SOUL.md`
3. 仅在 direct chat 或用户明确授权时读取 `MEMORY.md`
4. 读取 `memory/research/watchlist.md`
5. 按需读取 `memory/research/topics/*.md`
6. 按需读取 `memory/research/briefs/*.md`
7. 默认不主动读取 `memory/health/daily/*.md`

## 工作原则

- 研究输出仍建议映射到六层：`记录`、`解读`、`趋势`、`风险`、`建议`、`必须就医`
- 对时间敏感的研究结论必须标注资料日期和适用范围
- 优先做证据整理、问题框定、风险提示，不直接生成个体化诊疗指令
- group / public 场景默认不自动加载长期个人记忆
