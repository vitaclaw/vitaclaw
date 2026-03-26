# VitaClaw Bootstrap

进入工作区后，默认执行以下检查清单：

1. 读取 `SOUL.md`，确认边界和输出层级
2. 若当前是 direct chat 或用户明确授权，读取 `MEMORY.md`；否则跳过并记录“长期记忆未自动加载”
3. 读取 `memory/health/_health-profile.md`，确认结构化健康基线
3a. **首次使用检测**：如果 `_health-profile.md` 中的关键字段（`diagnosis`、`age`、`hospital`）全部为 "pending" 或为空，说明这是首次使用。此时进入引导模式：
   - 参考 `docs/health-agent-onboarding-playbook.zh.md` 中 `health-agent` 模板的 6 个优先问题
   - 按以下顺序逐步询问（不要一次问完）：
     1. 你目前最关心的健康目标是什么？（减重/控压/控糖/体检异常跟踪/一般健康管理）
     2. 有没有已确诊的慢性病或正在服用的药物？
     3. 你希望我帮你追踪哪些指标？（血压/血糖/体重/睡眠/用药/都要）
     4. 你希望我多久主动提醒你一次？（每天/有异常时/从不）
   - 将回答写入 `_health-profile.md` 对应字段和 `MEMORY.md`
   - 引导完成后，继续执行后续检查清单
   - **反模式**：不要在第一天就要求用户填写完整病史；先建立最小基线，后续逐步丰富
4. 读取最近 1-3 天 `memory/health/daily/*.md`
5. 如果今天还没有 daily 文件，则初始化今天的 daily 文件
6. 若当前任务涉及具体健康项，再读取对应 item 文件：
   - 血压：`memory/health/items/blood-pressure.md`
   - 血糖：`memory/health/items/blood-sugar.md`
   - 体重：`memory/health/items/weight.md`
   - 睡眠：`memory/health/items/sleep.md`
   - 心率 / HRV：`memory/health/items/heart-rate-hrv.md`
   - 肾功能：`memory/health/items/kidney-function.md`
   - 肝功能：`memory/health/items/liver-function.md`
   - 血脂：`memory/health/items/blood-lipids.md`
   - 肿瘤标志物：`memory/health/items/tumor-markers.md`
   - 用药：`memory/health/items/medications.md`
   - 补剂：`memory/health/items/supplements.md`
   - 心理量表：`memory/health/items/mental-health-score.md`
   - 就医选择 / 医生匹配：`memory/health/items/care-team.md`
   - 复查 / 复诊：`memory/health/items/appointments.md`
   - 年度体检：`memory/health/items/annual-checkup.md`
   - 行为计划：`memory/health/items/behavior-plans.md`
   - 执行障碍：`memory/health/items/execution-barriers.md`
7. 若已启用患者档案桥接，再读取：
   - `memory/health/files/patient-archive-summary.md`
   - `memory/health/files/health-timeline.md`
   - 必要时运行 `python3 scripts/sync_patient_archive.py`
   - 如有新的 `export.xml`，运行 `python3 scripts/import_apple_health_export.py`
   - 若需要统一时间轴，运行 `python3 scripts/generate_health_timeline.py`
8. 判断是否有主动服务待执行：
   - 缺失记录提醒
   - 周报 / 月报 / 季度归档
   - 复查到期提醒
   - 药物续配提醒
   - 门诊前 briefing 待生成
   - 门诊后 follow-up 待记录
   - 异常升级
   - 长期画像蒸馏
9. 若需要状态化任务管理，再读取：
   - `memory/health/heartbeat/preferences.md`
   - `memory/health/heartbeat/task-board.md`
   - 必要时运行 `python3 scripts/manage_health_tasks.py list`
10. 若需要后台运营编排，再运行 `python3 scripts/run_health_operations.py`
11. 若要直接跑场景化闭环，再运行：
   - `python3 scripts/run_hypertension_daily_copilot.py`
   - `python3 scripts/run_diabetes_control_hub.py`
   - `python3 scripts/run_annual_checkup_advisor.py`
   - `python3 scripts/run_doctor_match_workflow.py`

## 完成任一记录类任务后

- 更新 `memory/health/daily/YYYY-MM-DD.md`
- 更新相关 `memory/health/items/*.md`
- 若结果会影响长期基线，则回写 `MEMORY.md` 或 `_health-profile.md`
- 若生成了就诊材料、follow-up 或病历摘要，同步登记到 `memory/health/files/` 和当日 `Health Files`
