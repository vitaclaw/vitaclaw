# Workspace Health Example

这个目录展示 VitaClaw 推荐的健康 workspace 结构，不存放真实个人数据。

## 推荐目录

```text
workspace-health/
  AGENTS.md
  SOUL.md
  MEMORY.md
  HEARTBEAT.md
  BOOTSTRAP.md
  IDENTITY.md
  USER.md
  memory/
    health/
      _health-profile.md
      daily/
      items/
      weekly/
      monthly/
      quarterly/
      heartbeat/
      files/
```

## 推荐用法

- 用 `scripts/init_health_workspace.py` 初始化真实 workspace
- 用旗舰场景入口脚本直接跑第一条闭环：高血压 / 糖尿病 / 年度体检
- 用这里的目录说明做二次定制
- 不要把真实病历、报告和 daily 记录提交到公开仓库
