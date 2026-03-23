# OpenClaw Health Research Agent Template

这是 VitaClaw 的健康研究工作区模板包，适合做指南追踪、文献梳理、药物比较和诊疗问题研究。

## 适用场景

- 长期追踪某个病种或药物的指南变化
- 为 `health-main` 准备就医前的研究 briefing
- 对同一问题做多来源证据对照

## 包含内容

- 研究版 `AGENTS.md`
- 研究版 `SOUL.md`
- 研究版 `MEMORY.md`
- 研究版 `HEARTBEAT.md`
- `memory/research/watchlist.md`
- `memory/research/topics/` 与 `memory/research/briefs/` 骨架

## 初始化方式

```bash
python3 scripts/init_health_workspace.py /path/to/workspace --template health-research-agent
```

## 使用建议

- 默认不要往这个 workspace 放真实个人长期病历
- 把它当作证据仓和研究雷达，而不是主健康档案
- 若需要结合个体资料，请只同步最小必要上下文
