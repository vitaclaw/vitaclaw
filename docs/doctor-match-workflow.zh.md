# VitaClaw 医生匹配工作流

这条工作流的目标不是“给医生排名”，而是用公开信息帮助用户完成更现实的决策：

1. 先判断该看哪个科
2. 再从公开候选医生中找更适合的人
3. 再把 shortlist 变成真正的就诊准备动作

## 适合解决的问题

- 体检有多项异常，不知道先看哪个科
- 想找适合长期管理高血压 / 糖前期 / 代谢问题的医生
- 同一个城市里有多位医生，不知道谁更适合自己的情况
- 想把医院官网资料和公开论文一起看，但不想被“论文多 = 一定更适合”误导

## 包含的 skills

- `department-fit-router`
- `doctor-evidence-profiler`
- `doctor-fit-finder`

chief-led 场景入口：

- `python3 scripts/run_health_chief_of_staff.py doctor-match ...`
- `python3 scripts/run_doctor_match_workflow.py ...`

## 输入文件

### `patient.json`

建议字段：

```json
{
  "city": "上海",
  "district": "徐汇",
  "conditions": ["高血压", "糖前期"],
  "symptoms": ["晨起头胀"],
  "abnormal_findings": ["ALT 78 U/L", "甘油三酯 2.7 mmol/L"],
  "goals": ["找适合长期管理高血压和代谢风险的门诊"],
  "preferred_hospitals": ["瑞和国际门诊"],
  "continuity_preference": "需要长期随访和沟通清晰的医生"
}
```

### `doctors.json`

建议字段：

```json
[
  {
    "name": "李明",
    "english_name": "Ming Li",
    "hospital": "瑞和国际门诊",
    "department": "心内科 / 高血压门诊",
    "city": "上海",
    "district": "徐汇",
    "specialties": ["hypertension", "lipid management", "chronic disease follow-up"],
    "official_profile_url": "https://hospital.example/doctor-li",
    "schedule": "Tue pm / Fri am",
    "accepts_long_term_followup": true,
    "pubmed_query": "\"Ming Li\"[Author] AND (hypertension OR lipid)"
  }
]
```

## 推荐运行方式

### 直接跑工作流

```bash
python3 scripts/run_doctor_match_workflow.py \
  --workspace-root ~/openclaw/workspace-health-main \
  --memory-dir ~/openclaw/workspace-health-main/memory/health \
  --patient-json /path/to/patient.json \
  --doctors-json /path/to/doctors.json \
  --pubmed-mode auto
```

### 走 chief-led 单入口

```bash
python3 scripts/run_health_chief_of_staff.py doctor-match \
  --workspace-root ~/openclaw/workspace-health-main \
  --memory-dir ~/openclaw/workspace-health-main/memory/health \
  --patient-json /path/to/patient.json \
  --doctors-json /path/to/doctors.json \
  --pubmed-mode auto
```

## 输出产物

运行后会生成：

- `memory/health/files/doctor-match-YYYY-MM-DD.md`
- `memory/health/items/care-team.md`
- `memory/health/items/behavior-plans.md`
- `memory/health/team/briefs/*.md`
- `memory/health/team/team-board.md`

## 评分逻辑

当前版本综合考虑 5 类信号：

- 科室路径是否正确
- 医生公开专长和患者问题是否匹配
- 城市 / 区域 / 医院偏好是否匹配
- 是否适合长期随访
- 公共学术信号是否支持当前问题

其中，PubMed 只是加分项，不是决定项。

## 边界

- 不自动挂号，不替用户点微信小程序
- 不做医生能力绝对排名
- 不把公开论文数量当成唯一标准
- 不替代急症分诊
- 若出现急性危险症状，应优先线下急诊或尽快就医
