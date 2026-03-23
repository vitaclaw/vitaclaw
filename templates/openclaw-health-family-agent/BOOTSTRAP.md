# VitaClaw Family Bootstrap

进入工作区后，默认执行以下检查清单：

1. 读取 `SOUL.md`，确认照护边界和输出层级
2. 若当前是 direct chat 或用户明确授权，读取 `MEMORY.md`
3. 读取 `memory/health/_health-profile.md` 与 `memory/health/_care-team.md`
4. 读取最近 1-3 天 `memory/health/daily/*.md`
5. 若任务涉及照护执行，再读取：`medications.md`、`appointments.md`、`annual-checkup.md`、`blood-pressure.md`、`blood-sugar.md`、`weight.md`
6. 若涉及照护计划与执行断点，再读取：`behavior-plans.md`、`execution-barriers.md`
7. 若要核查主动服务，再读取 `memory/health/heartbeat/preferences.md` 和 `task-board.md`
8. 如需门诊前后材料，运行 `python3 scripts/generate_visit_briefing.py` / `python3 scripts/record_visit_followup.py`
9. 如需体检 / 病历支持 workflow，可运行 `python3 scripts/run_annual_checkup_advisor.py` / `python3 scripts/run_patient_records_workflow.py`

## 完成任一照护任务后

- 更新当天 `daily` 文件
- 更新对应 `items` 文件
- 若影响长期照护基线，再回写 `MEMORY.md` 或 `_health-profile.md`
- 若涉及资料归档或陪诊材料，同步登记到 `memory/health/files/`
