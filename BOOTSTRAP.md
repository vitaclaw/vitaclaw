# VitaClaw Bootstrap

进入工作区后，默认执行以下检查清单：

1. 读取 `SOUL.md`，确认边界和输出层级
2. 若当前是 direct chat 或用户明确授权，读取 `MEMORY.md`；否则跳过并记录“长期记忆未自动加载”
3. 读取 `memory/health/_health-profile.md`，确认结构化健康基线
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
   - 复查 / 复诊：`memory/health/items/appointments.md`
   - 年度体检：`memory/health/items/annual-checkup.md`
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

## 完成任一记录类任务后

- 更新 `memory/health/daily/YYYY-MM-DD.md`
- 更新相关 `memory/health/items/*.md`
- 若结果会影响长期基线，则回写 `MEMORY.md` 或 `_health-profile.md`
- 若生成了就诊材料、follow-up 或病历摘要，同步登记到 `memory/health/files/` 和当日 `Health Files`
