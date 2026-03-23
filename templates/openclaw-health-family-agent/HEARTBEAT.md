# VitaClaw Family Heartbeat

Heartbeat 负责把家庭照护从“有事才想起”升级为“有人持续盯着”。

## 每日巡检

- 检查今天是否缺失以下任一关键记录：
  - 药物 / 补剂服用
  - 关键生命体征或病种相关指标
  - 睡眠、进食、排便、症状变化或复健执行
- 若照护对象本周出现异常，提醒补充诱因、症状和处理结果
- 若照护者连续多天高负担，提醒简化任务并优先保留关键项目

## 每周巡检

- 生成家庭照护周报
- 输出以下变化：
  - 指标是否稳定
  - 依从性是否下降
  - 哪些事项反复遗漏
  - 下周最值得提前安排的事项

## 每月巡检

- 生成家庭照护月报
- 检查复诊、续方、续药、检查预约、体检、医保材料是否临近
- 更新 `MEMORY.md`、`memory/health/_health-profile.md` 与 `_care-team.md`
- 评估提醒是否对家庭造成过度打扰，适度收敛
- 将当前照护待办同步到 `memory/health/heartbeat/task-board.md`
- 使用 `memory/health/heartbeat/preferences.md` 调整提醒频率、语气与安静时段
- 将行为计划和执行障碍同步进照护任务板

## 事件触发

- 连续缺失关键药物或监测记录
- 出现危急症状或明显进行性恶化
- 新增住院、出院、手术、重要检查报告
- 照护者反馈“撑不住了”或出现明显 burnout 信号

## 输出要求

- 每次提醒必须说明原因、优先级、最小下一步和需要谁来跟进
- 中高风险提醒必须明确写出“需医生确认”或“建议尽快就医”
- 对家庭协作任务尽量给出可直接转发的短提醒版本
- 若需要后台自动运营，运行 `python3 scripts/run_health_operations.py`
- 照护任务静默和再次跟进可运行 `python3 scripts/manage_health_tasks.py`
- 门诊前摘要可运行 `python3 scripts/generate_visit_briefing.py`
- 门诊后执行回写可运行 `python3 scripts/record_visit_followup.py`
- 体检顾问入口可运行 `python3 scripts/run_annual_checkup_advisor.py`
- 病历支持 workflow 可运行 `python3 scripts/run_patient_records_workflow.py`
- 月度画像蒸馏可运行 `python3 scripts/distill_health_memory.py`
