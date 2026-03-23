# VitaClaw Heartbeat

Heartbeat 负责把 VitaClaw 从“被动问答”升级为“主动服务”。

## 触发规则

- 每日：检查血压 / 血糖 / 体重 / 睡眠 / 用药 / 补剂等关键记录缺失
- 每周：生成健康周报，识别趋势、断点、依从性变化
- 每月：生成健康月报，检查复查、续药、体检、care plan 更新
- 季度：为长期画像蒸馏预留固定窗口，必要时回写 `MEMORY.md`
- 事件触发：连续恶化、风险值越阈、病历新增、连续失访、门诊前后任务未闭环

## 输出要求

- 提醒必须说明：为什么提醒、风险级别、现在该做什么、何时再跟进
- 轻提醒可以简洁，但中高风险提醒必须明确写出“需医生确认”或“建议尽快就医”
- 输出仍遵循六层：`记录`、`解读`、`趋势`、`风险`、`建议`、`必须就医`
- 提醒默认带上阈值依据和来源文件，便于回溯
- 读取 `memory/health/heartbeat/preferences.md` 控制语气、频率、安静时段和高风险优先级
- 将当前待办同步到 `memory/health/heartbeat/task-board.md`

## 推荐脚本入口

- 巡检：`python3 scripts/run_health_heartbeat.py`
- 任务管理：`python3 scripts/manage_health_tasks.py list|complete|snooze|reopen`
- 后台运营：`python3 scripts/run_health_operations.py`
- 周报 / 月报：`python3 skills/weekly-health-digest/weekly_health_digest.py`
- 长期画像蒸馏：`python3 scripts/distill_health_memory.py`
- 门诊前摘要：`python3 scripts/generate_visit_briefing.py`
- 门诊后执行回写：`python3 scripts/record_visit_followup.py`
- 病历归档同步：`python3 scripts/sync_patient_archive.py`
- Apple Health 导入：`python3 scripts/import_apple_health_export.py`
- 统一时间轴：`python3 scripts/generate_health_timeline.py`
