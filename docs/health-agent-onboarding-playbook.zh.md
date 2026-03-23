# VitaClaw Health Agent Onboarding Playbook

这份文档定义第一次启用健康分身时，应该补齐哪些信息，以及推荐的对话节奏。

## 1. onboarding 目标

- 让用户第一次对话后就拥有可工作的 workspace
- 不要求一次填完所有健康史，但至少建立能跑起来的最小基线
- 从第一天开始区分“长期事实”和“临时记录”

## 2. 三类模板的首轮问题

### `health-agent`

第一轮建议优先补这 6 件事：

1. 你最想管理的健康目标是什么
2. 是否有慢病、长期用药或补剂
3. 你最愿意持续记录哪些指标
4. 你希望多久收到一次提醒
5. 哪些情况希望强提醒
6. 常用医院 / 医生 / 科室是什么

### `health-family-agent`

第一轮建议优先补这 6 件事：

1. 主要照护对象是谁
2. 你和 TA 的关系是什么
3. 当前最重要的照护目标是什么
4. 谁负责药物、复诊、记录和紧急联络
5. 哪些信息家庭内部可以共享，哪些不可以
6. 哪些风险情况必须立刻升级

### `health-research-agent`

第一轮建议优先补这 5 件事：

1. 你最关心的研究主题是什么
2. 你偏好哪套指南体系
3. 哪些药物 / 检查 / 病种需要长期跟踪
4. 你希望多久刷新一次研究摘要
5. 是否允许为某个具体问题临时接入最小必要个体信息

## 3. 建议的落点

### `health-agent`

- 长期信息写入 `MEMORY.md`
- 基线信息写入 `memory/health/_health-profile.md`
- 当天执行与症状写入 `memory/health/daily/YYYY-MM-DD.md`
- 如已有患者档案，先运行 `python3 scripts/sync_patient_archive.py` 把病历摘要同步到 `memory/health/files/patient-archive-summary.md`
- 如已有 Apple Health `export.xml`，再运行 `python3 scripts/import_apple_health_export.py` 补全可穿戴数据层

### `health-family-agent`

- 家庭分工和边界写入 `memory/health/_care-team.md`
- 复诊和安排写入 `memory/health/items/appointments.md`

### `health-research-agent`

- 研究主题和规则写入 `MEMORY.md`
- 研究队列写入 `memory/research/watchlist.md`
- 临时研究草稿写入 `memory/research/topics/`

## 4. 首次对话的成功标准

首次 onboarding 完成后，至少应满足：

- 有一个清楚的主目标
- 有一个可执行的记录节奏
- 有最少一条提醒偏好
- 有至少一个下一步动作

## 5. 不要在首次对话里做的事

- 不要逼用户一次性补完全部病史
- 不要把研究摘要直接当个体化结论
- 不要在信息极少时生成过度具体的 care plan
- 不要忽略隐私和家庭共享边界

## 6. 推荐节奏

- 第一次：只建最小基线和记录路径
- 第一周：建立连续记录和提醒
- 第二周：开始周报和异常识别
- 第三周以后：再逐步补足长期画像和研究支持
