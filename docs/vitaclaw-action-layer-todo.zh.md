# VitaClaw Action Layer — 从"提醒器"到"健康管家" 完整 TODO

> 版本：v0.2 (基于全球 API 可用性调研修订) | 起草日期：2026-03-16
>
> **北极星目标**：用户充值一笔健康预算，VitaClaw 像真正的私人健康管理团队一样，
> 替你规划、采购、预约、执行，用户只需确认或否决。
>
> **一句话定位升级**：
> - 现在的 VitaClaw：数据采集 → 分析/趋势 → 提醒/报告 → **断了**
> - 目标 VitaClaw：数据采集 → 分析/趋势 → **决策 → 执行 → 闭环确认**

---

## 全球 API 可用性实况（决策依据）

在设计之前，我们对全球 23 个中国平台 + 48 个全球平台做了逐一调研。
**核心发现：绝大多数消费端平台没有公开的"替用户下单" API。**
以下是基于事实的分层：

### Tier 1 — 现在就能用，成熟稳定，个人开发者可接入

| 服务 | API | 能力 | 限制 |
|---|---|---|---|
| **Google Calendar** | REST API | 完整 CRUD 日历事件 | 中国大陆需翻墙 |
| **Microsoft Outlook Calendar** | Graph API | 完整 CRUD 日历事件 | 需 Azure AD 注册 |
| **Apple EventKit / CalDAV** | Native + CalDAV | 读写日历和提醒事项 | EventKit 仅限 Apple 设备端 |
| **飞书/Lark** | REST API | 消息、日历、文档、审批、机器人 | 飞书(中国)和 Lark(国际)分开 |
| **企业微信 WeCom** | REST API | 消息推送、群机器人 Webhook、日历、审批 | 需注册企业 |
| **Telegram Bot** | Bot API | 收发消息、按钮交互、支付 | 最开放的消息 API，完全免费 |
| **WhatsApp Business** | Cloud API (Meta) | 模板消息、通知、交互按钮 | 1000 条/月免费，之后按条计费 |
| **Twilio** | SMS/Voice API | 短信、语音、WhatsApp | 按量付费，~$0.008/条 |
| **SendGrid** | Email API | 事务邮件、模板、分析 | 免费 100 封/天 |
| **Pushover / ntfy** | Push Notification | 推送到手机/桌面 | Pushover $5 一次性，ntfy 免费开源 |
| **Strava** | REST API | 运动记录读取/上传 | 100 请求/15 分钟 |
| **Fitbit** | Web API | 活动、睡眠、心率、SpO2、食物记录 | 150 请求/用户/小时 |
| **Oura Ring** | REST API | 睡眠、就绪度、活动、压力、HRV | 免费，需 OAuth2 |
| **Whoop** | REST API | 恢复、负荷、睡眠、心率、HRV | 较新，文档仍在完善 |
| **Apple HealthKit** | Native (iOS) | 100+ 健康数据类型读写 | 仅限 iOS 设备端，需 App |
| **Google Health Connect** | Android API | 50+ 健康数据类型 | 仅限 Android |
| **Stripe** | Payment API | 收付款、订阅、发票 | 2.9%+$0.30/笔 |
| **PayPal** | Payment API | 支付、订阅、退款 | 2.99%+$0.49/笔 |
| **Slack** | Bot API | 消息、频道、交互组件、Workflow | 免费，非常成熟 |
| **Open mHealth / Shimmer** | 开源 | 归一化 Fitbit/Google Fit/Withings 等数据 | 社区维护 |

### Tier 2 — 有 API 但限制较多（需要商业合作或特定条件）

| 服务 | API | 能力 | 限制 |
|---|---|---|---|
| **Kroger (美国超市)** | Developer API | **产品搜索 + 加入购物车** | 唯一有消费端购物车 API 的主流超市；用户需在 Kroger 网站完成结账 |
| **Mindbody** | REST API | **健身课程搜索 + 预约** | 最佳健身预约 API；需要合作健身房是 Mindbody 客户 |
| **Epic (MyChart)** | FHIR R4 API | 患者数据、临床记录、（部分）预约 | 每家医院需单独审批；预约功能不是所有机构都开 |
| **Cerner (Oracle Health)** | FHIR R4 API | 患者数据、临床记录 | 同 Epic，需医院侧配合 |
| **NHS (英国)** | 多个 API | 患者身份、处方、机构查询、GP 预约 | 全球最成熟的公共医疗 API 体系 |
| **Garmin** | Health API | 日常摘要、活动、睡眠、压力 | 推送模式（Garmin 推数据给你），个人开发者较难拿到 |
| **京东开放平台** | REST API | 产品搜索、商详、订单管理 | 需商家/ISV 资质，消费端下单能力有限 |
| **Shopify** | Storefront + Admin API | 完整电商能力 | 适合自建健康产品商店，不适合从别人店买 |
| **美团外卖/饿了么** | 商户 API | 店铺管理、订单管理 | 仅商户侧，不能替消费者下单 |

### Tier 3 — 没有公开 API，需要 RPA 或完全不可行

| 服务 | 现状 |
|---|---|
| 盒马 / 叮咚 / 美团买菜 | 无消费端 API，中国所有生鲜平台均无 |
| Keep / 超级猩猩 / 乐刻 | 无 API，仅小程序/App |
| 叮当快药 / 美团买药 | 无 API |
| 微医 / 好大夫 / Zocdoc / Doctolib | 无公开预约 API |
| 美年大健康 / 爱康国宾 / iKang | 无 API |
| 简单心理 / Calm / Headspace | 无 API |
| iHerb | 仅有联盟推广链接，无下单 API |
| 微信个人消息 | 无合法 API，非官方方案(itchat/wechaty)已被封堵 |
| Amazon Fresh / Instacart / Walmart 生鲜 | 无消费端下单 API |
| CVS / Walgreens 药房 | API 已关闭或极度受限 |
| Peloton / ClassPass | 无官方 API |

---

## 战略决策：基于现实的三层执行架构

面对以上现实，我们不能假装可以 API 调用一切。
正确的架构是**三层递进**：

```
Layer 1: 全自动 (API 直连)
  → 日历写入、通知推送、健康数据读取、支付、可穿戴数据同步
  → 这些现在就能做到无人干预

Layer 2: 半自动 (生成 + 一键跳转)
  → VitaClaw 生成购物清单/食谱/预约建议
  → 一键打开对应平台的 DeepLink / 小程序 / 网页，预填好信息
  → 用户只需点一下"确认"
  → 不依赖任何平台 API，但用户体验接近全自动

Layer 3: 辅助决策 (信息整理 + 行动建议)
  → 对于完全无法自动化的场景（如就医），
  → VitaClaw 做到极致的信息准备：最优医生推荐、问题清单、资料整理
  → 用户拿着"武器"去做，而不是赤手空拳
```

---

## 第〇阶段：架构设计与规范制定

> 目标：在写任何代码之前，把三个新引擎的边界、接口、安全模型全部定义清楚。

### 0.1 Action Layer 总体架构文档

- [ ] 编写 `docs/action-layer-architecture.zh.md`
  - [ ] 定义三层执行模型：全自动 / 半自动(一键跳转) / 辅助决策
  - [ ] 定义三个新引擎的职责边界：Budget Engine / Autonomy Engine / Action Bridge
  - [ ] 定义与现有架构的关系：chief-of-staff 如何调度 action layer
  - [ ] 定义与现有 memory 层的关系：执行记录写哪里、预算记录写哪里
  - [ ] 定义与现有 6 层输出的关系：新增「执行」层（记录/解读/趋势/风险/建议/执行/必须就医）
  - [ ] 画出完整数据流图：用户意图 → chief 路由 → specialist 分析 → autonomy 判级 → action 执行 → 闭环回写
  - [ ] **全球 Provider 可用性矩阵**——按国家/地区标注哪些 Provider 可用
  - [ ] **国际化策略**——同一个场景在不同国家如何落地（如：美国用 Kroger API 买菜，中国用 DeepLink 跳转盒马）

### 0.2 Budget Engine 规范

- [ ] 编写 `docs/budget-engine-spec.zh.md`
  - [ ] 预算模型设计
    - [ ] 总预算池：月度充值 / 季度充值 / 年度充值
    - [ ] 多币种支持：CNY / USD / EUR / GBP / JPY / AUD 等
    - [ ] 分类预算：营养/食材、运动/健身、医疗/检查、药品/补剂、心理/放松、储备金
    - [ ] 动态分配规则：根据当前健康状态自动调整比例
    - [ ] 预算继承与结转：月度未用完的钱怎么处理
  - [ ] 预算消耗追踪
    - [ ] 每笔支出的记录格式（JSONL）
    - [ ] 实时余额查询
    - [ ] 分类消耗统计
    - [ ] 预算超支预警规则
  - [ ] 预算报告
    - [ ] 日度消耗明细（写入 daily）
    - [ ] 周度预算摘要（嵌入周报）
    - [ ] 月度预算报告（嵌入月报）
    - [ ] 预算 vs 健康改善的 ROI 分析

- [ ] 编写 `schemas/budget-record.schema.json`
  - [ ] 字段：id, timestamp, category, subcategory, amount, currency, vendor, item_description, skill_source, autonomy_level, execution_layer (auto/semi-auto/assisted), status (pending/approved/executed/cancelled/refunded)
  - [ ] 与现有 `health-data-record.schema.json` 信封格式保持一致

- [ ] 新增 `memory/health/items/budget.md`

### 0.3 Autonomy Engine 规范

- [ ] 编写 `docs/autonomy-engine-spec.zh.md`
  - [ ] 决策权分级模型（四级）
    - [ ] **Level 0 — 全自动执行**：限于 Tier 1 API 操作（写日历、发通知、同步数据），或已确认过的低金额重复采购
    - [ ] **Level 1 — 通知即执行**：中等金额，推送通知，N 分钟内不反对则执行
    - [ ] **Level 2 — 需确认**：高金额 / 首次消费 / 医疗类操作
    - [ ] **Level 3 — 需讨论**：涉及医疗决策（换药、加查项目、新方案）
  - [ ] 金额阈值按币种/地区可配置
  - [ ] 安全兜底：单日/单月上限、异常检测、紧急冻结

- [ ] 新增 `memory/health/items/autonomy-preferences.md`
- [ ] 编写 `schemas/autonomy-decision.schema.json`

### 0.4 Action Bridge 规范

- [ ] 编写 `docs/action-bridge-spec.zh.md`
  - [ ] 统一执行接口设计
    - [ ] `ActionRequest` 格式：action_type, execution_layer (auto/deeplink/assisted), provider, payload, budget_record_id, autonomy_level, locale
    - [ ] `ActionResult` 格式：status, provider_order_id, actual_amount, receipt, deeplink_url, error
    - [ ] 幂等性要求
  - [ ] Provider 抽象层
    - [ ] `BaseProvider` 接口：`check_availability()`, `estimate_cost()`, `execute()`, `cancel()`, `get_status()`
    - [ ] **`DeepLinkProvider`** 子类：不直接执行，而是生成预填好参数的跳转链接
    - [ ] **`AssistedProvider`** 子类：只生成信息包（购物清单、预约建议、问题单），不做任何外部调用
    - [ ] Provider 注册表：`configs/action-providers.json5`（支持按 locale 选择）
  - [ ] **Provider 清单重新整理（只列真实可行的）**：

    **全自动 Provider（Tier 1 API）**：
    - [ ] `google_calendar_provider.py` — Google Calendar API
    - [ ] `outlook_calendar_provider.py` — Microsoft Graph API
    - [ ] `apple_calendar_provider.py` — CalDAV / EventKit
    - [ ] `feishu_provider.py` — 飞书消息 + 日历
    - [ ] `wecom_provider.py` — 企业微信 Webhook + 消息
    - [ ] `telegram_provider.py` — Telegram Bot API
    - [ ] `whatsapp_provider.py` — WhatsApp Business Cloud API
    - [ ] `twilio_sms_provider.py` — Twilio SMS
    - [ ] `email_provider.py` — SendGrid / Mailgun
    - [ ] `pushover_provider.py` — Pushover 推送
    - [ ] `ntfy_provider.py` — ntfy 开源推送
    - [ ] `strava_provider.py` — Strava 运动数据同步
    - [ ] `fitbit_provider.py` — Fitbit 健康数据同步
    - [ ] `oura_provider.py` — Oura Ring 数据同步
    - [ ] `whoop_provider.py` — Whoop 数据同步
    - [ ] `healthkit_bridge_provider.py` — Apple HealthKit 桥接（通过 iOS 配套 App）
    - [ ] `health_connect_provider.py` — Google Health Connect 桥接（通过 Android App）
    - [ ] `stripe_provider.py` — Stripe 支付（用于预算充值和托管）

    **半自动 Provider（有部分 API 或 DeepLink）**：
    - [ ] `kroger_provider.py` — Kroger 产品搜索 + 加购物车（用户去 Kroger 结账）[仅美国]
    - [ ] `mindbody_provider.py` — Mindbody 健身课程搜索 + 预约 [全球，取决于健身房]
    - [ ] `fhir_appointment_provider.py` — FHIR R4 标准预约接口（对接 Epic/Cerner 等）[主要美国/英国]
    - [ ] `nhs_provider.py` — NHS 预约 + 处方 + 机构查询 [仅英国]
    - [ ] `shopify_storefront_provider.py` — Shopify 商店产品搜索 + 加购物车（可自建补剂商店）
    - [ ] `amazon_product_provider.py` — Amazon PA API 产品搜索 + 联盟链接（不能下单，但能推荐+跳转）

    **DeepLink 跳转 Provider（无 API 但可一键跳转）**：
    - [ ] `deeplink_generator.py` — 通用 DeepLink 生成框架
      - [ ] 支持 URL Scheme：`hema://`, `dingdong://`, `meituan://`, `jd://`, `taobao://`
      - [ ] 支持 Universal Links / App Links
      - [ ] 支持微信小程序跳转 `weixin://dl/business/?appid=...`
      - [ ] 支持 Web fallback URL（如果 App 未安装则跳网页版）
    - [ ] 场景化 DeepLink 模板：
      - [ ] 买菜：生成购物清单 → 一键跳转盒马/叮咚/美团买菜搜索页
      - [ ] 买药：生成药品清单 → 一键跳转叮当快药/美团买药
      - [ ] 挂号：生成推荐科室+医生 → 一键跳转微医/好大夫/医院 App
      - [ ] 运动：生成推荐课程 → 一键跳转 Keep/超级猩猩/ClassPass
      - [ ] 外卖：生成营养需求 → 一键跳转美团/Uber Eats 并搜索对应关键词
      - [ ] 体检：生成推荐套餐 → 一键跳转美年/爱康/本地体检机构

  - [ ] 降级策略
    - [ ] 全自动不可用 → 降级为半自动（DeepLink）
    - [ ] DeepLink 不可用 → 降级为辅助决策（生成纯文本行动清单）
    - [ ] 按用户 locale 自动选择最优 Provider

- [ ] 编写 `schemas/action-request.schema.json`
- [ ] 编写 `schemas/action-result.schema.json`
- [ ] 编写 `schemas/action-provider.schema.json`

### 0.5 数据契约扩展

- [ ] 更新 `docs/health-data-contract.md`
  - [ ] 新增 Section 7：Budget Record Contract
  - [ ] 新增 Section 8：Autonomy Decision Contract
  - [ ] 新增 Section 9：Action Execution Contract（含三层执行模型）
  - [ ] 新增 Section 10：Provider Integration Contract（含 DeepLink 规范）
  - [ ] 更新 Section 6：新增「执行」输出层

- [ ] 更新 `docs/health-memory-spec.zh.md`
  - [ ] 新增 writeback 文件：budget.md, autonomy-preferences.md, action-history.md, shopping-lists.md, meal-plans.md, inventory.md

### 0.6 国际化基础 (i18n)

- [ ] 编写 `docs/internationalization-spec.zh.md`
  - [ ] locale 定义：`zh-CN`, `en-US`, `en-GB`, `ja-JP`, `de-DE` 等
  - [ ] 按 locale 自动选择：货币、Provider、DeepLink 模板、通知语言
  - [ ] Provider 可用性矩阵按 locale 维护
  - [ ] 食材/药品数据库按 locale 分离

- [ ] 新建 `configs/locale/`
  - [ ] `zh-CN.json5` — 中国：盒马/叮咚/美团/京东 DeepLink + 企业微信/飞书通知
  - [ ] `en-US.json5` — 美国：Kroger API + Amazon 推荐 + Twilio SMS + Google Calendar
  - [ ] `en-GB.json5` — 英国：NHS API + Tesco DeepLink + WhatsApp 通知
  - [ ] `ja-JP.json5` — 日本：待扩展
  - [ ] `default.json5` — 默认 fallback（通知+日历+辅助决策模式）

---

## 第一阶段：Budget Engine 实现

> 目标：让 VitaClaw 能接收、追踪、分配、报告用户的健康预算。
> 这是一切执行能力的前提——没有钱，就执行不了任何事。

### 1.1 核心运行时

- [ ] 新建 `skills/_shared/budget_engine.py`
  - [ ] `BudgetManager` 类
    - [ ] `init(monthly_budget, currency, allocation_rules)`
    - [ ] `allocate()` — 根据当前健康状态动态计算各分类配额
    - [ ] `can_spend(category, amount)` → bool
    - [ ] `record_spend(category, amount, details)` — 记录支出
    - [ ] `record_refund(spend_id, amount)` — 记录退款
    - [ ] `get_balance(category=None)` — 查询余额
    - [ ] `get_spend_history(start_date, end_date, category=None)`
    - [ ] `get_budget_report(period='weekly'|'monthly')`
    - [ ] `adjust_allocation(trigger_event)` — 健康事件触发动态调整
    - [ ] `check_alerts()` — 超支预警
  - [ ] 预算数据持久化（JSONL，写入 `data/budget-engine/`）
  - [ ] 多币种支持

### 1.2 预算初始化与配置

- [ ] 扩展 `scripts/init_health_workspace.py`
  - [ ] 新增 onboarding：是否启用预算？月度金额？币种？分类偏好？
  - [ ] 自动生成 `memory/health/items/budget.md`
  - [ ] 自动生成 `configs/budget-allocation.json5`

### 1.3 预算与现有系统集成

- [ ] 扩展 `scripts/run_health_chief_of_staff.py` — 新增 budget 子命令
- [ ] 扩展 `scripts/run_health_operations.py` — heartbeat 加入预算异常检查
- [ ] 扩展 `skills/weekly-health-digest/` — 周报/月报加入预算板块

### 1.4 预算 Skill

- [ ] 新建 `skills/budget-manager/` — 交互式预算管理
- [ ] 测试：`tests/test_budget_manager.py`

---

## 第二阶段：Autonomy Engine 实现

> 目标：让 VitaClaw 能根据操作类型、金额、历史行为，自动决定需不需要问用户。

### 2.1 核心运行时

- [ ] 新建 `skills/_shared/autonomy_engine.py`
  - [ ] `AutonomyDecider` 类（四级分类 + 安全兜底 + 信任升级）

### 2.2 用户交互层

- [ ] 设计通知与确认协议
  - [ ] Level 0：写入 daily，不打断
  - [ ] Level 1：通过 Telegram/WhatsApp/WeCom/飞书 推送，倒计时执行
  - [ ] Level 2：推送确认请求，等待 approve/deny
  - [ ] Level 3：触发交互式对话

### 2.3 信任学习

- [ ] 新建 `skills/_shared/trust_learner.py`
- [ ] 测试：`tests/test_autonomy_engine.py`

---

## 第三阶段：Action Bridge 实现

> 目标：建立统一的执行框架，支持三层执行模型。
> 策略：**先做通知和日历（Tier 1），再做 DeepLink（Tier 2），最后做采购（Tier 3）。**

### 3.1 Provider 抽象框架

- [ ] 新建 `skills/_shared/action_bridge.py`
  - [ ] `ActionBridge` 类 — 统一执行入口
  - [ ] `BaseProvider` 抽象类
  - [ ] `DeepLinkProvider` — 不调 API，生成跳转链接
  - [ ] `AssistedProvider` — 不做任何外部调用，生成信息包
  - [ ] Provider 注册表 + locale 感知选择
  - [ ] Fallback 链：auto → deeplink → assisted
  - [ ] 全局审计日志

- [ ] 新建 `configs/action-providers.json5`
- [ ] 测试：`tests/test_action_bridge.py`

### 3.2 第一批：通知 + 日历 Provider（全自动，零成本，最先落地）

> 这批全部基于成熟稳定的公开 API，个人开发者可直接接入。

- [ ] `providers/calendar/google_calendar_provider.py`
  - [ ] Google Calendar REST API
  - [ ] 创建/更新/删除事件、查询空闲时段、设置提醒
  - [ ] OAuth2 授权流程

- [ ] `providers/calendar/outlook_calendar_provider.py`
  - [ ] Microsoft Graph API
  - [ ] 同上能力 + FindMeetingTimes（智能推荐空闲时间）

- [ ] `providers/calendar/apple_caldav_provider.py`
  - [ ] CalDAV 协议对接 iCloud Calendar
  - [ ] 服务端创建/更新事件

- [ ] `providers/calendar/feishu_calendar_provider.py`
  - [ ] 飞书 Calendar API
  - [ ] 创建事件 + 推送提醒

- [ ] `providers/notification/telegram_bot_provider.py`
  - [ ] Telegram Bot API
  - [ ] 发送格式化消息、交互按钮（用户可直接在 Telegram 里点"批准"/"拒绝"）
  - [ ] 支持图片/文件发送（如发送周报 PDF）

- [ ] `providers/notification/whatsapp_provider.py`
  - [ ] WhatsApp Business Cloud API (Meta)
  - [ ] 模板消息（提醒、确认请求）
  - [ ] 交互按钮

- [ ] `providers/notification/wecom_provider.py`
  - [ ] 企业微信 Webhook（最简单的方式，一个 URL 就能发消息）
  - [ ] 企业微信应用消息（更丰富的交互）

- [ ] `providers/notification/feishu_bot_provider.py`
  - [ ] 飞书自定义机器人 Webhook
  - [ ] 飞书 Interactive Card（卡片式交互消息）

- [ ] `providers/notification/twilio_sms_provider.py`
  - [ ] Twilio SMS API
  - [ ] 简单文本通知

- [ ] `providers/notification/email_provider.py`
  - [ ] SendGrid API
  - [ ] 模板邮件（日报、周报、确认请求）

- [ ] `providers/notification/pushover_provider.py`
  - [ ] Pushover API
  - [ ] 推送通知到手机/桌面

- [ ] `providers/notification/ntfy_provider.py`
  - [ ] ntfy 开源推送
  - [ ] 零注册、零成本的推送方案

### 3.3 第二批：健康数据同步 Provider（全自动）

> 把用户已有的可穿戴设备和健康 App 数据自动拉进来。

- [ ] `providers/health_data/fitbit_provider.py`
  - [ ] Fitbit Web API：活动、睡眠、心率、SpO2、体重、食物/水记录
  - [ ] 增量同步机制

- [ ] `providers/health_data/strava_provider.py`
  - [ ] Strava API：运动记录读取 + 上传
  - [ ] Webhook 订阅新活动

- [ ] `providers/health_data/oura_provider.py`
  - [ ] Oura API：睡眠、就绪度、活动、HRV、温度

- [ ] `providers/health_data/whoop_provider.py`
  - [ ] Whoop API：恢复、负荷、睡眠、心率

- [ ] `providers/health_data/open_mhealth_shimmer.py`
  - [ ] Open mHealth Shimmer 归一化层
  - [ ] 统一不同来源的数据格式

- [ ] `providers/health_data/healthkit_bridge.py`
  - [ ] 通过 iOS 配套 App 桥接 HealthKit 数据
  - [ ] 定义 iOS App ↔ VitaClaw 同步协议

- [ ] `providers/health_data/health_connect_bridge.py`
  - [ ] 通过 Android 配套 App 桥接 Health Connect 数据

### 3.4 第三批：半自动 Provider（有部分 API 的平台）

- [ ] `providers/shopping/kroger_provider.py` [美国]
  - [ ] Kroger API：产品搜索、加入购物车
  - [ ] 用户在 Kroger 网站/App 完成最终结账
  - [ ] 根据食谱自动生成购物车

- [ ] `providers/fitness/mindbody_provider.py` [全球]
  - [ ] Mindbody API：搜索课程、查看时间、预约
  - [ ] 根据运动计划自动推荐并预约课程

- [ ] `providers/medical/fhir_provider.py` [美国/英国/欧洲]
  - [ ] FHIR R4 标准客户端
  - [ ] 对接 Epic/Cerner/其他 FHIR 服务器
  - [ ] 读取临床数据（检查结果、用药、诊断）
  - [ ] 预约查询和创建（取决于医院配置）

- [ ] `providers/medical/nhs_provider.py` [英国]
  - [ ] NHS Digital API
  - [ ] 患者身份验证（NHS Login）
  - [ ] GP Connect 预约查询
  - [ ] 电子处方查询

- [ ] `providers/shopping/amazon_affiliate_provider.py` [全球]
  - [ ] Amazon PA API 5.0：产品搜索、价格查询
  - [ ] 生成购买链接（用户跳转 Amazon 完成购买）
  - [ ] 补剂/OTC 药品查找最优价格

- [ ] `providers/shopping/shopify_provider.py` [全球]
  - [ ] Shopify Storefront API
  - [ ] 可自建 VitaClaw 健康产品商店
  - [ ] 或对接已有的 Shopify 健康产品商店

### 3.5 第四批：DeepLink 跳转 Provider（无 API 平台的最佳方案）

> 核心思路：VitaClaw 准备好一切信息，生成一个链接/按钮，用户一点就跳转到对应 App。
> 虽然不是全自动，但用户体验比"告诉你去买什么"好 10 倍。

- [ ] `providers/deeplink/deeplink_engine.py` — 通用 DeepLink 生成引擎
  - [ ] URL Scheme 注册表（按平台 + 版本维护）
  - [ ] Universal Links / App Links 支持
  - [ ] Web fallback（App 未安装时跳网页）
  - [ ] 跳转追踪（记录用户是否点击了链接）

- [ ] `providers/deeplink/templates/` — 按国家/平台的 DeepLink 模板
  - [ ] **中国生鲜**：
    - [ ] 盒马 `hema://` / 盒马 Universal Link
    - [ ] 叮咚买菜 `dingdong://`
    - [ ] 美团买菜（美团 App 内）
    - [ ] 京东到家 `openapp.jdmobile://`
  - [ ] **中国医疗**：
    - [ ] 微医小程序跳转
    - [ ] 好大夫 App `haodf://`
    - [ ] 各省市预约挂号平台 Web URL
  - [ ] **中国药品**：
    - [ ] 叮当快药 App
    - [ ] 美团买药（美团 App 内）
    - [ ] 京东健康 `openapp.jdmobile://`
  - [ ] **中国运动**：
    - [ ] Keep `keep://`
    - [ ] 超级猩猩小程序
  - [ ] **全球通用**：
    - [ ] Uber Eats `ubereats://`
    - [ ] DoorDash `doordash://`
    - [ ] ClassPass (`classpass://`)
    - [ ] Instacart Web URL
    - [ ] Walmart Grocery Web URL
    - [ ] CVS/Walgreens Web URL

### 3.6 凭证管理

- [ ] 新建 `skills/_shared/credential_manager.py`
  - [ ] macOS Keychain / Linux Secret Service / Windows Credential Manager
  - [ ] Provider 凭证 CRUD
  - [ ] OAuth2 token 刷新管理
  - [ ] 凭证过期提醒
  - [ ] 绝不写入 git

- [ ] 更新 `.gitignore` — 排除所有凭证相关文件

---

## 第四阶段：场景闭环——三层执行模型实战

> 目标：在真实场景中验证三层执行架构。
> 每个场景同时实现全自动 + 半自动 + 辅助决策三条路径。

### 4.1 场景一：智能食材/营养管理（全球首个闭环场景）

- [ ] 新建 `skills/smart-nutrition-planner/`
  - [ ] 输入：健康状态 + 饮食原则 + 药物禁忌 + 预算 + locale
  - [ ] 输出：7 天食谱 + 购物清单
  - [ ] 三层执行：
    - [ ] **全自动路径 [美国]**：Kroger API 加入购物车 → 用户去 Kroger 结账
    - [ ] **半自动路径 [中国/其他]**：生成购物清单 → 一键跳转盒马/叮咚/Instacart/Walmart
    - [ ] **辅助路径 [通用]**：生成购物清单 Markdown/PDF + 分类 + 估价 → 用户自行采购
  - [ ] 智能联动：
    - [ ] 血压升高 → 低钠食谱
    - [ ] 血糖波动 → 低 GI 食谱
    - [ ] 华法林 → 控制维 K 摄入
    - [ ] 肾功能异常 → 控制蛋白质/钾
  - [ ] 预算联动：Budget Engine 检查 + 自动优化性价比
  - [ ] 日历联动：将"备餐日"写入日历
  - [ ] 通知联动：购物日前一天通过 Telegram/WeChat 发送购物清单
  - [ ] 闭环：用户确认采购完成 → 写入 daily + 更新 budget

- [ ] 新建 `memory/health/items/meal-plans.md`
- [ ] 新建 `memory/health/items/shopping-lists.md`
- [ ] 测试：`tests/test_smart_nutrition_planner.py`

### 4.2 场景二：药品/补剂库存与复购

- [ ] 新建 `skills/medication-inventory/`
  - [ ] 库存追踪：名称、剂量、日用量、余量、预计耗尽日
  - [ ] 三层执行：
    - [ ] **全自动 [通用]**：耗尽前 7 天通知（Telegram/Email/SMS）
    - [ ] **半自动 [美国]**：Amazon 搜索最优价格 → 生成购买链接
    - [ ] **半自动 [中国]**：生成药品清单 → 一键跳转叮当快药/京东健康
    - [ ] **辅助 [通用]**：生成复购清单 + 比价信息 + 写入日历提醒
  - [ ] 处方药特殊逻辑：绝不自动购买，只提醒续方 + 联动就医协助
  - [ ] 日历联动：药品耗尽预警写入日历

- [ ] 新建 `memory/health/items/inventory.md`
- [ ] 扩展现有 `skills/medication-reminder/` 和 `skills/supplement-manager/`
- [ ] 测试：`tests/test_medication_inventory.py`

### 4.3 场景三：智能就医协助

- [ ] 扩展 `scripts/generate_visit_briefing.py`
  - [ ] 三层执行：
    - [ ] **全自动 [英国]**：NHS API 查询 GP 可用时段 → 用户确认 → 创建预约
    - [ ] **全自动 [美国 Epic 用户]**：FHIR API 查询可用时段 → 用户确认 → 创建预约
    - [ ] **半自动 [中国]**：推荐科室+医生 → 一键跳转微医/好大夫/医院 App
    - [ ] **半自动 [全球]**：推荐科室 → 一键跳转 Zocdoc/Doctolib
    - [ ] **辅助 [通用]**：生成完整就诊准备包
      - [ ] 本次就诊问题清单
      - [ ] 需要带的检查资料
      - [ ] 近期指标变化趋势图
      - [ ] 目前用药清单
      - [ ] 想问医生的问题（用户可编辑）
  - [ ] 日历联动：就诊事件 + 前一天提醒
  - [ ] 门诊后闭环：解析医嘱 → 触发药品采购 + 复查预约

- [ ] 新建 `skills/smart-visit-assistant/`
- [ ] 测试：`tests/test_smart_visit_assistant.py`

### 4.4 场景四：运动计划执行

- [ ] 新建 `skills/smart-exercise-planner/`
  - [ ] 输入：健康状态 + 运动偏好 + 天气 + 日程 + 可穿戴数据
  - [ ] 三层执行：
    - [ ] **全自动 [Mindbody 用户]**：搜索 + 预约健身课程
    - [ ] **全自动 [通用]**：写入日历 + 运动前 1 小时推送提醒
    - [ ] **半自动 [中国]**：推荐课程 → 一键跳转 Keep/超级猩猩
    - [ ] **半自动 [全球]**：推荐课程 → 一键跳转 ClassPass
    - [ ] **辅助 [通用]**：生成本周运动计划 + 每日具体项目
  - [ ] 健康联动：
    - [ ] 从 Fitbit/Strava/Oura/Whoop 读取昨日运动+恢复数据
    - [ ] 血压偏高 → 降低强度，推荐瑜伽/步行
    - [ ] 睡眠差 → 推荐低强度运动 + 推后运动时间
  - [ ] 运动完成闭环：从可穿戴设备自动获取运动数据 → 写入 daily

### 4.5 场景五：联动决策（杀手级场景）

- [ ] 新建 `skills/health-situation-response/`
  - [ ] 当 chief-of-staff 检测到健康状态变化，跨场景联动响应
  - [ ] 示例——"血压连续 3 天升高"：
    - [ ] 调整食谱为低钠 → 触发购物清单更新 → 推送到用户
    - [ ] 调整运动为低强度 → 更新日历中的运动事件
    - [ ] 评估是否需要就医 → 如需要，生成就诊准备包 + DeepLink
    - [ ] 调整预算分配 → 增加饮食预算，减少运动预算
    - [ ] 给用户一条汇总消息（通过 Telegram/WeChat/Email）
  - [ ] 示例——"库存药品即将耗尽 + 临近复诊"：
    - [ ] 推送复购提醒 + 购买链接
    - [ ] 推送复诊预约建议 + 跳转链接
    - [ ] 生成门诊 briefing（含续方需求）

---

## 第五阶段：配套 App（打通 HealthKit / Health Connect）

> 轻量级移动 App，核心目的是桥接设备端 API（HealthKit/Health Connect），
> 而不是重新做一个完整的健康 App。

### 5.1 iOS 配套 App

- [ ] 功能清单：
  - [ ] HealthKit 数据读取 → 同步到 VitaClaw 本地文件/API
  - [ ] EventKit 日历操作
  - [ ] 推送通知接收 + 确认/否决交互
  - [ ] DeepLink 跳转入口
  - [ ] 极简 UI：只展示今日健康摘要 + 待办 + 预算余额
- [ ] 技术选型：Swift / SwiftUI
- [ ] 隐私政策（HealthKit 强制要求）

### 5.2 Android 配套 App

- [ ] 功能清单：
  - [ ] Health Connect 数据读取 → 同步到 VitaClaw
  - [ ] 日历操作
  - [ ] 推送通知 + 交互
  - [ ] DeepLink 跳转入口
- [ ] 技术选型：Kotlin / Jetpack Compose

### 5.3 跨平台替代方案

- [ ] 评估 Flutter / React Native 一次开发的可行性
- [ ] HealthKit 和 Health Connect 的跨平台插件成熟度评估

---

## 第六阶段：安全、合规与用户信任

### 6.1 执行安全

- [ ] 编写 `docs/action-layer-safety.zh.md`
  - [ ] 金融安全：审计、额度上限、异常冻结、对账
  - [ ] 医疗安全：处方药禁止自动购买、用药建议必须标注"需医生确认"
  - [ ] 数据安全：Provider 最小权限、HTTPS、凭证轮换
  - [ ] 误操作防护：重复下单检测、大额二次确认、撤回窗口

### 6.2 合规

- [ ] GDPR 合规（欧洲用户）
  - [ ] 数据导出
  - [ ] 数据删除权
  - [ ] 明确的数据处理同意
- [ ] HIPAA 考虑（美国用户）
  - [ ] PHI（受保护的健康信息）的处理边界
  - [ ] 与 FHIR Provider 交互的安全要求
- [ ] 中国个人信息保护法
  - [ ] 健康数据作为敏感个人信息的处理规则

### 6.3 审计系统

- [ ] 扩展 `memory/health/team/audit/`
  - [ ] `budget-audit.jsonl` — 预算变动
  - [ ] `action-audit.jsonl` — 外部执行记录
  - [ ] `autonomy-audit.jsonl` — 决策记录

### 6.4 用户控制面板

- [ ] 新建 `skills/control-panel/`
  - [ ] 预算总览 + 消耗进度
  - [ ] 自动执行历史 + 一键撤回
  - [ ] Provider 连接状态 + 测试
  - [ ] 紧急冻结
  - [ ] 数据导出

---

## 第七阶段：智能进化

### 7.1 个性化学习

- [ ] `skills/_shared/personalization_engine.py`
  - [ ] 消费偏好（品牌、渠道、价格敏感度）
  - [ ] 行为模式（运动时间、就医偏好、响应速度）
  - [ ] 健康-行为关联（哪些食谱对血压最有效）

### 7.2 预算优化

- [ ] `skills/budget-optimizer/` — ROI 分析 + 优化建议

### 7.3 主动服务升级

- [ ] 扩展 `HEARTBEAT.md` — 新增基于 Action Layer 的触发规则

---

## 第八阶段：发行与生态

### 8.1 Release Packaging

- [ ] 新建 `packages/vitaclaw-action.json` — Action Layer 独立包
- [ ] 更新 `packages/vitaclaw-core.json`
- [ ] 构建更新

### 8.2 Provider 生态

- [ ] 编写 `docs/provider-development-guide.zh.md` — 第三方 Provider 开发指南
- [ ] 社区 Provider 贡献框架
- [ ] 按国家/地区的 Provider Bundle
  - [ ] `provider-bundle-china` — 中国 DeepLink 全家桶
  - [ ] `provider-bundle-us` — 美国 API 全家桶（Kroger + Amazon + Epic FHIR）
  - [ ] `provider-bundle-uk` — 英国全家桶（NHS + Tesco）

### 8.3 文档

- [ ] 更新 README.md / README.zh.md
- [ ] 更新架构文档
- [ ] 新增 Action Layer 用户指南（中英双语）

---

## 里程碑与优先级

| 里程碑 | 内容 | 关键交付 | 用户感知 |
|---|---|---|---|
| **M0** | 架构设计 + 规范 | 文档 + schema | 无 |
| **M1** | Budget + Autonomy 引擎 | 预算管理可用 | "我能看到我的健康花费了" |
| **M2** | 通知 + 日历 Provider | 全自动通知 + 日历事件 | "它自动把事情加到我日历了" |
| **M3** | 健康数据同步 Provider | Fitbit/Oura/Strava 数据自动进来 | "我不用手动记录了" |
| **M4** | DeepLink 引擎 + 营养场景 | 食谱 + 一键跳转购物 | "它帮我列好清单，我一点就打开了买菜 App" |
| **M5** | 药品库存 + 就医协助 | 复购提醒 + 就诊准备包 | "它比我更记得我的药什么时候吃完" |
| **M6** | Kroger/Mindbody/FHIR | 部分全自动采购和预约 | "它直接帮我把购物车加好了" |
| **M7** | 安全审计 + 配套 App | 完整审计 + HealthKit 对接 | "我能看到它替我做了什么" |
| **M8** | 个性化 + 优化 | 越用越懂用户 | "它建议的食谱越来越合我口味了" |
| **M9** | 发行 + Provider 生态 | 国际化包 + 社区贡献 | "我在英国也能用" |

---

## 与现有架构的兼容性承诺

1. **不破坏现有 6 层输出**——新增「执行」作为第 7 层
2. **不破坏现有 Agent 分工**——三引擎由 chief-of-staff 统一调度
3. **不破坏现有 memory 层级**——新增 items 遵循现有 schema
4. **不破坏现有 distillation chain**——执行记录同样走 daily → weekly → monthly → MEMORY.md
5. **不破坏现有隐私模型**——外部 Provider 调用单独审计，group/public 不自动执行
6. **渐进式启用**——用户不开启预算管理时，一切行为与现有版本完全一致
7. **全球化优先**——同一场景在不同国家/地区有不同的最优执行路径，通过 locale 自动选择

---

## 设计原则总结

### 务实三原则

1. **能 API 的 API，不能 API 的 DeepLink，都不行的给信息包**
   —— 永远不假装能做到做不到的事

2. **通知和日历先行，采购和预约后做**
   —— 先把 100% 能做好的做好，再攻坚困难的

3. **全球化从第一天开始，不要等最后才补**
   —— locale 感知的 Provider 选择是架构层的决策
