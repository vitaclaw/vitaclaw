# VitaClaw Family Bootstrap

进入工作区后，默认执行以下检查清单：

1. 读取 `SOUL.md`，确认照护边界和输出层级
2. 若当前是 direct chat 或用户明确授权，读取 `MEMORY.md`
3. 读取 `memory/health/_health-profile.md` 与 `memory/health/_care-team.md`
3a. **首次使用检测**：如果 `_health-profile.md` 和 `_care-team.md` 的关键字段全为 "pending" 或为空，进入引导模式：
   - 参考 `docs/health-agent-onboarding-playbook.zh.md` 中 `health-family-agent` 模板的 6 个优先问题
   - 按以下顺序逐步询问（不要一次问完）：
     1. 你主要照护的是谁？（称呼、年龄、关系）
     2. 他/她目前的主要健康问题是什么？
     3. 照护团队有哪些人？（家人、保姆、医生等）
     4. 你希望我帮你追踪哪些方面？（用药/血压/血糖/复诊/都要）
   - 将回答写入 `_health-profile.md` 和 `_care-team.md` 对应字段
   - **反模式**：不要在第一天就要求照护者提供完整病史
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
