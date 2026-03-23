# OpenClaw Health Family Agent Template

这是 VitaClaw 的家人照护工作区模板包，适合家庭成员、照护者、陪诊场景和长期慢病陪伴。

## 适用场景

- 给父母或长辈做长期健康记录
- 家庭多成员共享复诊、用药、体检和提醒任务
- 需要把陪诊、住院、出院、随访资料长期整理起来

## 包含内容

- 家庭照护版 `AGENTS.md`
- 家庭照护版 `SOUL.md`
- 家庭照护版 `MEMORY.md`
- 家庭照护版 `HEARTBEAT.md`
- 家庭照护版 `BOOTSTRAP.md`
- `memory/health/_care-team.md`
- 药物、血压、睡眠、复诊等核心跟踪模板
- `behavior-plans.md`、`execution-barriers.md`
- `heartbeat/task-board.md`

## 初始化方式

```bash
python3 scripts/init_health_workspace.py /path/to/workspace --template health-family-agent --onboard
```

## 使用建议

- 最稳妥的方式是“一位主要照护对象一个 workspace”
- 若家庭成员很多，建议把 `health-family` 当照护协调中枢，再给重病种单独开 workspace
- 对隐私敏感内容，优先写入最小必要信息
- 初始化后优先跑：`run_annual_checkup_advisor.py`、`run_patient_records_workflow.py`、`generate_visit_briefing.py`
