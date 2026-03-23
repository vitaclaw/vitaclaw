# VitaClaw Workspace

这是 chief-led 的默认健康团队模板。

## 默认单入口

- 默认聊天入口：`health-chief-of-staff`
- 长期事实写回：`health-main`
- specialist 只产出 brief / task / 审计，不直接改长期画像

## 固定读取顺序

1. 读取 `BOOTSTRAP.md`
2. 读取 `SOUL.md`
3. 仅在 direct chat 或用户明确授权时读取 `MEMORY.md`
4. 读取 `memory/health/_health-profile.md`
5. 读取最近 1-3 天 `memory/health/daily/*.md`
6. 按需读取 `memory/health/items/*.md`
7. 若涉及病历、Apple Health 或统一时间轴，再读取 `memory/health/files/*.md`
8. 若涉及团队协作或 heartbeat，再读取：
   - `memory/health/team/team-board.md`
   - `memory/health/team/tasks/`
   - `memory/health/team/briefs/`
   - `memory/health/team/audit/dispatch-log.jsonl`
9. chief-led 入口脚本：
   - `python3 scripts/run_health_chief_of_staff.py heartbeat`
   - `python3 scripts/run_health_chief_of_staff.py hypertension-daily ...`
   - `python3 scripts/run_health_chief_of_staff.py diabetes-daily ...`
   - `python3 scripts/run_health_chief_of_staff.py annual-checkup ...`

## 工作原则

- 输出固定分成六层：`记录`、`解读`、`趋势`、`风险`、`建议`、`必须就医`
- 不做明确诊断，不直接给处方调整结论，不替代医生或急救系统
- 高风险生命体征、急性危险症状、严重精神危机必须优先中断普通建议
- group / public 场景默认不自动加载 `MEMORY.md`

## 默认角色

- `health-chief-of-staff`
- `health-main`
- `health-records`
- `health-metrics`
- `health-lifestyle`
- `health-safety`
- `health-research`
- `health-mental`

可选扩展：

- `health-family`
- `health-oncology`
