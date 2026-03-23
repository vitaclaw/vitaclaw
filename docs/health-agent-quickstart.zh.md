# VitaClaw Health Agent Quickstart

这份文档对应 Iteration 3 的 chief-led 用法：你只需要和 `health-chief-of-staff` 对话，后台 specialist 会自动分工。

## 1. 选择模板

当前推荐模板：

- `health-team-agent`
  默认 chief-led 团队模板，适合本人长期健康管理
- `health-family-agent`
  适合家人照护 / 家庭协作
- `health-research-agent`
  适合证据整理与研究支撑
- `health-checkup-agent`
  适合年度体检基线与 follow-up
- `health-chronic-agent`
  适合高血压 / 糖尿病连续追踪
- `health-mental-support-agent`
  适合支持型心理健康追踪
- `health-postop-agent`
  适合术后恢复与照护
- `health-oncology-agent`
  适合肿瘤线和高密度病历场景

## 2. 初始化 chief-led workspace

最常用的是 core 包：

```bash
python3 scripts/init_health_workspace.py ~/openclaw/workspace-health-main --template health-team-agent --packages core --onboard
```

如果还要家庭照护：

```bash
python3 scripts/init_health_workspace.py ~/openclaw/workspace-health-family --template health-family-agent --packages core,family-care --onboard
```

如果需要肿瘤线：

```bash
python3 scripts/init_health_workspace.py ~/openclaw/workspace-health-oncology --template health-oncology-agent --packages core,oncology,labs --onboard
```

查看可用模板：

```bash
python3 scripts/init_health_workspace.py --list-templates
```

初始化完成后，会自动生成：

- `openclaw.health.json5`
- `memory/health/team/team-board.md`
- `memory/health/team/tasks/`
- `memory/health/team/briefs/`
- `memory/health/team/audit/dispatch-log.jsonl`

## 3. 第一轮运行什么

先跑一次 chief-led heartbeat：

```bash
python3 scripts/run_health_chief_of_staff.py heartbeat --memory-dir ~/openclaw/workspace-health-main/memory/health
```

然后跑一个旗舰闭环：

```bash
python3 scripts/run_health_chief_of_staff.py hypertension-daily \
  --memory-dir ~/openclaw/workspace-health-main/memory/health \
  --systolic 148 \
  --diastolic 96 \
  --pulse 80 \
  --diet-summary "外卖偏咸" \
  --exercise-summary "晚饭后快走30分钟" \
  --medication "Amlodipine|5mg|qd|on-time"
```

或者：

```bash
python3 scripts/run_health_chief_of_staff.py diabetes-daily ...
python3 scripts/run_health_chief_of_staff.py annual-checkup --report-date 2026-03-10 --item "血糖|空腹血糖|6.4|mmol/L|3.9-6.1|偏高"
```

## 4. 你应该看到什么

运行后至少会出现 4 类用户可感知产物：

- 场景输出文件
- `memory/health/team/team-board.md`
- `memory/health/team/briefs/*.md`
- `memory/health/team/audit/dispatch-log.jsonl`

这意味着 chief 已经把任务分派给 specialist，并把结果收口到了主健康 workspace。

## 5. 默认团队分工

- `health-chief-of-staff`
  单入口，总协调、优先级、持续跟进
- `health-main`
  长期事实和最终写回中枢
- `health-records`
  病历、体检、时间线
- `health-metrics`
  指标趋势与阈值
- `health-lifestyle`
  饮食、运动、作息、执行障碍
- `health-safety`
  危急值和必须就医
- `health-research`
  证据后援
- `health-mental`
  支持型心理健康守门

可选扩展：

- `health-family`
- `health-oncology`

## 6. 日常运行建议

- 轻巡检：`python3 scripts/run_health_chief_of_staff.py heartbeat`
- 高血压 / 糖尿病 / 体检：统一走 `run_health_chief_of_staff.py`
- 周报 / 月报 / 蒸馏：`python3 scripts/run_health_operations.py`
- 门诊前 briefing：`python3 scripts/generate_visit_briefing.py`
- 门诊后 follow-up：`python3 scripts/record_visit_followup.py`
- 病历同步：`python3 scripts/sync_patient_archive.py`
- 统一时间线：`python3 scripts/generate_health_timeline.py`

## 7. 什么时候需要新包

- 只管理自己：`core`
- 管理家人照护：`core + family-care`
- 肿瘤线和专科重场景：`core + oncology + labs`

分层发行说明见：

- [health-release-packages.zh.md](/Users/baozhiwei/Library/CloudStorage/坚果云-452858265@qq.com/我的坚果云/其他项目/vitaclaw-main/docs/health-release-packages.zh.md)
