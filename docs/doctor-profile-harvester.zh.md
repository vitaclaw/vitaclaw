# VitaClaw 医生公开资料采集

这条链路解决的是一个很现实的问题：

- 用户手上只有医院官网 / 科室页 / 医生页
- 但还没有可用于 `doctor-fit-finder` 的 `doctors.json`

`doctor-profile-harvester` 会先把公开医院页面采成结构化医生候选，再交给医生匹配工作流。

## 设计原则

- 只采公开医院 / 门诊 / 医生介绍页
- 优先静态抓取；静态信息不足时，再受控切换到 `web-access` 浏览器 fallback
- 不做挂号、支付、登录态复用、社媒发布
- 采集不到稳定信息时，宁可跳过，也不编造医生画像

## 输入

使用 `schemas/doctor-match/doctor-sources.example.json` 作为模板：

```json
[
  {
    "source_url": "https://hospital.example/cardiology",
    "hospital": "瑞和国际门诊",
    "city": "上海",
    "district": "徐汇",
    "department_hint": "心内科 / 高血压门诊",
    "allowed_domains": ["hospital.example"],
    "entry_selector": "a",
    "link_substrings": ["doctor", "expert", "医生", "专家"],
    "limit": 6,
    "mode": "auto"
  }
]
```

## 运行

### 只做采集

```bash
python3 scripts/run_doctor_profile_harvester.py \
  --sources-json schemas/doctor-match/doctor-sources.example.json \
  --mode auto \
  --output-json /tmp/doctors.json
```

### 采集后直接进入医生匹配

```bash
python3 scripts/run_doctor_match_workflow.py \
  --workspace-root ~/openclaw/workspace-health-main \
  --memory-dir ~/openclaw/workspace-health-main/memory/health \
  --patient-json schemas/doctor-match/patient.example.json \
  --doctor-seeds-json schemas/doctor-match/doctor-sources.example.json \
  --harvest-mode auto \
  --harvest-output /tmp/doctors.json \
  --pubmed-mode auto
```

### 走 chief-led 单入口

```bash
python3 scripts/run_health_chief_of_staff.py doctor-match \
  --workspace-root ~/openclaw/workspace-health-main \
  --memory-dir ~/openclaw/workspace-health-main/memory/health \
  --patient-json schemas/doctor-match/patient.example.json \
  --doctor-seeds-json schemas/doctor-match/doctor-sources.example.json \
  --harvest-mode auto \
  --harvest-output /tmp/doctors.json
```

## 输出

- 结构化医生候选：`doctors.json`
- 医生匹配结果：`memory/health/files/doctor-match-YYYY-MM-DD.md`
- care-team 纵向记录：`memory/health/items/care-team.md`
- 团队简报与 team board

## 适合场景

- 体检异常后，不知道该找哪类医生
- 想基于公开医院资料筛选同城长期随访医生
- 想把医院官网简介和 PubMed 学术信号结合起来，但不想手工整理

## 不适合场景

- 微信小程序挂号自动化
- 需要登录态的患者门户
- 医生评价站/社交平台“口碑爬取”
- 社媒、支付、账号设置等非健康公开信息任务
