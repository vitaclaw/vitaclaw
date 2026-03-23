# VitaClaw Health Memory Contract

这份文档定义 VitaClaw Iteration 3 的健康记忆契约。它不是“建议文档”，而是 chief-led 团队层、工作区、共享层、模板、脚本和技能都应遵守的统一约定。

## 1. 固定读取顺序

进入主健康工作区时，按以下顺序建立上下文：

1. `BOOTSTRAP.md`
2. `SOUL.md`
3. `MEMORY.md`（仅 direct chat 或用户明确授权时自动加载）
4. `memory/health/_health-profile.md`
5. 最近 1-3 天 `memory/health/daily/*.md`
6. 与当前任务相关的 `memory/health/items/*.md`
7. 必要时读取 `memory/health/files/*.md`、病历桥接摘要和统一时间轴
8. 若任务是团队协作或 heartbeat，再读取 `memory/health/team/*.md` 与 `memory/health/team/audit/*.jsonl`

## 2. 长期记忆保守默认

- Iteration 1 默认 `direct chats only`
- group / public 场景默认不加载 `MEMORY.md`
- 不启用 QMD
- 若用户明确授权，可临时扩大读取范围，但应在输出中说明

## 3. 写回边界

### `MEMORY.md`

只写长期稳定、未来大概率仍然成立的事实：

- 健康目标
- 已知慢病与风险因素
- 长期用药 / 补剂 / 禁忌
- 常用医院 / 医生 / 科室
- 提醒偏好与长期阈值策略

### `memory/health/daily/`

只写当天发生的内容：

- 指标测量
- 症状变化
- 当日执行（用药、补剂、运动、睡眠、饮食）
- 异常事件与临时处理
- 门诊前 briefing / 门诊后 follow-up 的当天动作

### `memory/health/items/`

只写纵向聚合内容：

- 最近状态
- 历史表
- 阈值
- 汇总规则
- 趋势和滚动摘要
- 行为计划
- 执行障碍

### 病历档案目录

只存原始证据与结构化患者主档：

- PDF / 图像 / 扫描件 / 化验单
- `INDEX.md`
- `timeline.md`
- 患者级 profile

主健康工作区只同步最小必要摘要到 `memory/health/files/`。

### `memory/health/files/`

除了病历桥接摘要、门诊 briefing / follow-up、统一时间轴外，Iteration 2 新增：

- 场景化输出文件
- `write-audit.md`

### `memory/health/team/`

只写团队协作层产物：

- 角色任务单
- specialist brief
- chief summary
- team board
- dispatch / escalation / writeback audit

这层不直接改长期画像，只承担协作、可见性和审计。

## 4. Item 文件标准模板

每个 `memory/health/items/*.md` 必须至少包含：

1. YAML frontmatter
2. `## Recent Status`
3. `## History`

可选但推荐统一包含：

4. `## Thresholds`
5. `## Rollup Rules`

### 必需段含义

- `## Recent Status`：给当前会话快速读取的最新状态
- `## History`：用于纵向分析和周/月汇总的标准表

### 可选段含义

- `## Thresholds`：提醒阈值、升级边界、默认目标
- `## Rollup Rules`：周报 / 月报 / 季度归档 / 长期蒸馏使用的口径

## 5. Iteration 1 核心 item 清单

Iteration 1 约定以下核心 item 模板必须存在：

- `blood-pressure.md`
- `blood-sugar.md`
- `weight.md`
- `sleep.md`
- `heart-rate-hrv.md`
- `kidney-function.md`
- `liver-function.md`
- `blood-lipids.md`
- `tumor-markers.md`
- `medications.md`
- `supplements.md`
- `mental-health-score.md`
- `appointments.md`
- `annual-checkup.md`
- `behavior-plans.md`
- `execution-barriers.md`

## 6. 固定蒸馏链

Iteration 3 的固定蒸馏链为：

`daily -> weekly -> monthly -> quarterly -> MEMORY.md`

- `daily/` 记录原始当天事实
- `weekly/` 输出一周趋势、依从性、断点和下周重点
- `monthly/` 输出月度趋势、风险变化、待办、执行障碍和下月重点
- `quarterly/` 预留季度稳定事实整理窗口
- `MEMORY.md` 只吸收跨周、跨月仍然成立的稳定结论

行为计划和执行障碍不应直接跳写到 `MEMORY.md`，而应先经过 weekly/monthly/quarterly 蒸馏。
团队 brief 与 dispatch log 也不应直接跳写到 `MEMORY.md`。

## 7. 输出层级

健康工作区默认输出层级固定为：

- `记录`
- `解读`
- `趋势`
- `风险`
- `建议`
- `必须就医`

其中：

- `必须就医` 只在明显红旗、危急值、急性危险症状、严重精神危机时使用
- 不做明确诊断，不直接给处方调整结论

## 8. 配套脚本入口

- workspace 初始化：`python3 scripts/init_health_workspace.py --template health-team-agent --packages core --onboard`
- chief-led 入口：`python3 scripts/run_health_chief_of_staff.py`
- 高血压场景：`python3 scripts/run_hypertension_daily_copilot.py`
- 糖尿病场景：`python3 scripts/run_diabetes_control_hub.py`
- 年度体检场景：`python3 scripts/run_annual_checkup_advisor.py`
- 心理支持场景：`python3 scripts/run_mental_wellness_companion.py`
- 周报 / 月报：`python3 skills/weekly-health-digest/weekly_health_digest.py`
- heartbeat：`python3 scripts/run_health_heartbeat.py`
- 后台运营：`python3 scripts/run_health_operations.py`
- 长期画像蒸馏：`python3 scripts/distill_health_memory.py`
- 病历归档桥接：`python3 scripts/sync_patient_archive.py`
- 病历支持 workflow：`python3 scripts/run_patient_records_workflow.py`
- Apple Health 导入：`python3 scripts/import_apple_health_export.py`
- 统一时间轴：`python3 scripts/generate_health_timeline.py`
