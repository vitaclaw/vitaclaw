# OpenClaw Health Agent Template

这是 VitaClaw 的官方健康工作区模板包。

## 包含内容

- `AGENTS.md`
- `SOUL.md`
- `MEMORY.md`
- `HEARTBEAT.md`
- `BOOTSTRAP.md`
- `IDENTITY.md`
- `USER.md`
- `memory/health/` 默认目录骨架
- 血压、睡眠、咖啡因、补剂、药物等核心 item 模板
- `behavior-plans.md`、`execution-barriers.md`
- `heartbeat/task-board.md` 与 `task-state.json`

## 使用方式

### 方式 1：脚本初始化

```bash
python3 scripts/init_health_workspace.py /path/to/your/workspace --template health-agent --onboard
```

### 方式 2：手动复制

把本目录全部内容复制到你的 OpenClaw agent workspace 根目录。

## 推荐搭配

- 健康 agent 配置样例：
  [configs/openclaw.health.json5](/Users/baozhiwei/Library/CloudStorage/坚果云-452858265@qq.com/我的坚果云/其他项目/vitaclaw-main/configs/openclaw.health.json5)
- 兄弟模板：
  - `health-family-agent`
  - `health-research-agent`
- 初始化后优先补全：
  - `MEMORY.md`
  - `memory/health/_health-profile.md`
  - 你的提醒偏好和风险阈值
  - `memory/health/items/behavior-plans.md`
  - `memory/health/heartbeat/task-board.md`
  - 场景入口脚本：`run_hypertension_daily_copilot.py` / `run_diabetes_control_hub.py` / `run_annual_checkup_advisor.py`

## 隐私建议

- 真实使用时建议把 workspace 放在私有仓库或本地目录中
- `memory/health/files/` 内通常会放 PDF、图片、病历等敏感材料
- 若需要公开分享模板，请只分享模板，不分享真实 `memory/health/daily/*.md` 与原始文件
