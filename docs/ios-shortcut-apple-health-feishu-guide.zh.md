# iOS 快捷指令 — Apple Health 每日同步到 VitaClaw (飞书)

## 整体架构

```
┌─────────────────────┐      HTTP POST       ┌──────────────────────────┐
│  iPhone              │  ──────────────────→  │  VitaClaw Bridge Server  │
│                      │   JSON (健康数据)     │                          │
│  每天 08:00 自动运行  │                      │  1. 写入 data/*.jsonl    │
│  快捷指令采集         │  ←──────────────────  │  2. 发飞书卡片给用户     │
│  Apple Health 数据    │   200 OK (结果)       │                          │
└─────────────────────┘                       └──────────────────────────┘
                                                        │
                                                        ▼
                                               ┌────────────────┐
                                               │  飞书消息       │
                                               │  📊 每日健康报告 │
                                               └────────────────┘
```

---

## 第一步：服务端部署

### 1.1 创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，登录后点击「创建企业自建应用」
2. 填写应用名称：`VitaClaw Health Bridge`
3. 进入应用 → 「权限管理」→ 开通以下权限：
   - `im:message:send_as_bot` — 以机器人身份发送消息
4. 进入「凭证与基础信息」→ 记录：
   - `App ID` (格式: `cli_xxxxx`)
   - `App Secret`
5. 进入「机器人」→ 启用机器人功能
6. 发布应用（审核通过后可用）
7. 获取接收人的 `open_id`：
   - 在飞书中让目标用户给机器人发一条消息
   - 或通过飞书 API 查询：`GET /open-apis/contact/v3/users/find?user_id_type=open_id`

### 1.2 启动 Bridge Server

```bash
cd /path/to/vitaclaw-main

# 基本启动 (自动生成 auth token)
python3 scripts/apple_health_feishu_bridge.py \
  --feishu-app-id cli_your_app_id \
  --feishu-app-secret your_app_secret \
  --feishu-user-id ou_target_user_open_id

# 或用环境变量
export FEISHU_APP_ID=cli_your_app_id
export FEISHU_APP_SECRET=your_app_secret
export FEISHU_RECEIVE_USER_ID=ou_target_user_open_id
export AUTH_TOKEN=your_secret_token_here
python3 scripts/apple_health_feishu_bridge.py
```

启动后会打印：
```
[INFO] Auto-generated auth token: a1b2c3d4e5f6...
[INFO] Add this to your iOS Shortcut 'X-Auth-Token' header
[INFO] VitaClaw Health Bridge started on 0.0.0.0:8470
[INFO] Endpoint: POST /api/health-sync
[INFO] Feishu notification: enabled → ou_xxxxx
```

**记下 auth token，配置快捷指令时需要。**

### 1.3 让 iPhone 能访问到服务

选一种方式：

| 方式 | 适合场景 | 说明 |
|---|---|---|
| 同局域网 | 家用 | iPhone 和服务器在同一 WiFi，用内网 IP 如 `http://192.168.1.100:8470` |
| 内网穿透 | 通用 | 用 [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) 或 [frp](https://github.com/fatedier/frp) 或 [ngrok](https://ngrok.com) 暴露到公网 |
| 部署到云服务器 | 生产 | 部署到 VPS，配 HTTPS + 域名 |

**示例 (ngrok 快速测试)：**
```bash
ngrok http 8470
# 得到地址如: https://abc123.ngrok-free.app
```

---

## 第二步：创建 iOS 快捷指令

打开 iPhone「快捷指令」App，点右上角 `+` 新建，按以下步骤逐一添加操作：

### 2.1 获取当前日期

```
操作: 日期
  → 选择「当前日期」
操作: 格式化日期
  → 日期格式: 自定义
  → 格式字符串: yyyy-MM-dd
  → 将结果设为变量: today
```

### 2.2 查找健康样本（逐个采集每种指标）

对以下每种指标，添加一个「查找健康样本」操作：

---

**步数 (Steps)**
```
操作: 查找健康样本
  → 类型: 步数
  → 分组方式: 天
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: steps
```

**心率 (Heart Rate)**
```
操作: 查找健康样本
  → 类型: 心率
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1 (最近一次)
操作: 获取变量的「值」
  → 将结果设为变量: heart_rate
```

**静息心率**
```
操作: 查找健康样本
  → 类型: 静息心率
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: resting_hr
```

**心率变异性 (HRV)**
```
操作: 查找健康样本
  → 类型: 心率变异性
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: hrv
```

**血氧**
```
操作: 查找健康样本
  → 类型: 血氧饱和度
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: spo2
```

**体重**
```
操作: 查找健康样本
  → 类型: 体重
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: weight
```

**血压 (如果有蓝牙血压计同步)**
```
操作: 查找健康样本
  → 类型: 收缩压 (高压)
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: bp_sys

操作: 查找健康样本
  → 类型: 舒张压 (低压)
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: bp_dia
```

**睡眠**
```
操作: 查找健康样本
  → 类型: 睡眠分析
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「持续时间（小时）」
  → 将结果设为变量: sleep_hours
```

**活动能量消耗**
```
操作: 查找健康样本
  → 类型: 活动能量
  → 分组方式: 天
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: active_energy
```

**体能训练时间**
```
操作: 查找健康样本
  → 类型: 体能训练分钟数 (Apple Exercise Minutes)
  → 分组方式: 天
  → 排序方式: 开始日期 (最新优先)
  → 限制: 1
操作: 获取变量的「值」
  → 将结果设为变量: exercise_min
```

### 2.3 组装 JSON

```
操作: 字典
  → 添加以下键值对 (类型全部选「数字」，变量为空时留 0 或删除该行):

  date          →  (文本) today
  device        →  (文本) iPhone
  metrics       →  (字典):
    steps                       →  (数字) steps
    heart_rate                  →  (字典): avg → (数字) heart_rate
    resting_heart_rate          →  (数字) resting_hr
    hrv                         →  (数字) hrv
    blood_oxygen                →  (数字) spo2
    body_mass                   →  (数字) weight
    blood_pressure_systolic     →  (数字) bp_sys
    blood_pressure_diastolic    →  (数字) bp_dia
    sleep_hours                 →  (数字) sleep_hours
    active_energy               →  (数字) active_energy
    exercise_minutes            →  (数字) exercise_min

→ 将结果设为变量: health_payload
```

### 2.4 发送 HTTP 请求

```
操作: 获取 URL 内容
  → URL: https://你的服务器地址/api/health-sync
  → 方法: POST
  → 请求体: JSON
  → 请求体内容: health_payload
  → 头部:
    Content-Type  →  application/json
    X-Auth-Token  →  你的auth_token（启动服务时打印的那个）
```

### 2.5 (可选) 显示结果通知

```
操作: 如果
  → 输入: 获取 URL 内容的结果
  → 条件: 包含 "success": true

  操作: 显示通知
    → 标题: ✅ VitaClaw 健康同步完成
    → 正文: 今日数据已发送到飞书

否则:
  操作: 显示通知
    → 标题: ⚠️ VitaClaw 同步异常
    → 正文: 获取 URL 内容的结果
```

### 2.6 命名并保存

- 快捷指令名称：`VitaClaw 每日健康同步`

---

## 第三步：设置每天早 8 点自动运行

1. 打开「快捷指令」App → 底部点「自动化」
2. 点右上角 `+` → 「创建个人自动化」
3. 选择「特定时间」
   - 时间: `08:00`
   - 重复: `每天`
4. 操作: 选择「运行快捷指令」→ 选择 `VitaClaw 每日健康同步`
5. **关键**：关闭「运行前询问」开关 → 这样才能真正全自动
6. 完成

> **注意**：iOS 会在后台静默运行，但如果手机重启后未解锁、处于低电量模式、
> 或设备长时间未使用"快捷指令"App，可能会错过自动化。
> 建议保持「快捷指令」App 在后台刷新中开启（设置 → 通用 → 后台 App 刷新）。

---

## 第四步：验证

### 4.1 手动测试快捷指令

在「快捷指令」App 中手动运行一次 `VitaClaw 每日健康同步`，检查：
- 服务端控制台是否打印收到请求
- `data/apple-health-sync/records.jsonl` 是否有新写入
- `data/blood-pressure-tracker/records.jsonl` 是否有新写入（如果有血压数据）
- 飞书是否收到卡片消息

### 4.2 用 curl 测试服务端

```bash
curl -X POST http://localhost:8470/api/health-sync \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: 你的token" \
  -d '{
    "date": "2026-03-16",
    "device": "test",
    "metrics": {
      "steps": 8234,
      "heart_rate": {"avg": 72, "min": 55, "max": 128},
      "resting_heart_rate": 58,
      "hrv": 42,
      "blood_pressure_systolic": 125,
      "blood_pressure_diastolic": 82,
      "blood_oxygen": 98,
      "body_mass": 72.5,
      "sleep_hours": 7.2,
      "active_energy": 420,
      "exercise_minutes": 35
    }
  }'
```

预期返回：
```json
{
  "success": true,
  "date": "2026-03-16",
  "records_written": 10,
  "details": [...],
  "feishu": {"code": 0, "msg": "success", ...}
}
```

### 4.3 飞书卡片效果

收到的飞书消息会是一张蓝色卡片，显示：

```
📊 每日健康报告 — 2026-03-16
─────────────────────────────
日期: 2026-03-16  |  来源: Apple Health 自动同步
─────────────────────────────
🚶 步数         ❤️ 心率
8234 步          72 bpm

💚 静息心率      📈 HRV
58 bpm           42 ms

🫁 血氧          ⚖️ 体重
98 %             72.5 kg

😴 睡眠          🔥 消耗
7.2 小时         420 kcal

🏃 运动          🩸 血压
35 分钟          125/82 mmHg
─────────────────────────────
✅ 已写入 | 写入 10 条记录到 VitaClaw
```

---

## 数据流向 (与 VitaClaw 现有架构的关系)

```
iOS 快捷指令
  │
  ▼ POST JSON
apple_health_feishu_bridge.py
  │
  ├─→ HealthDataStore("apple-health-sync") → data/apple-health-sync/records.jsonl
  │     (steps, heart_rate, resting_hr, hrv, spo2, weight, energy, exercise)
  │
  ├─→ HealthDataStore("blood-pressure-tracker") → data/blood-pressure-tracker/records.jsonl
  │     (bp_reading: systolic + diastolic)
  │
  ├─→ HealthDataStore("sleep-analyzer") → data/sleep-analyzer/records.jsonl
  │     (sleep_record)
  │
  └─→ 飞书 API → 用户收到 Interactive Card
```

写入的 JSONL 记录格式与现有 VitaClaw 数据契约完全一致：
```json
{
  "id": "steps_20260316T000000_a1b2c3d4",
  "type": "steps",
  "timestamp": "2026-03-16T00:00:00",
  "skill": "apple-health-sync",
  "note": "Auto-sync from Apple Health via iOS Shortcut",
  "data": {"value": 8234, "source": "apple_health", "device": "iPhone"}
}
```

这意味着后续 `run_health_heartbeat.py`、`weekly-health-digest`、`run_health_chief_of_staff.py`
等现有脚本可以直接消费这些数据。

---

## 常见问题

### Q: 快捷指令查不到某个健康数据类型怎么办？
iOS 快捷指令的「查找健康样本」支持的类型取决于 iOS 版本。如果找不到某个类型（如 HRV），
可以先跳过那个字段，JSON 中不包含即可，服务端会正常处理。

### Q: 数据为空或为 0 怎么办？
服务端对 `None` 和 `0` 的字段会跳过不写入。不会产生脏数据。

### Q: 能同时发给多个飞书用户吗？
可以。修改服务端 `--feishu-user-id` 为群 `chat_id`（配合 `--feishu-receive-id-type chat_id`），
或改代码循环发送给多个 `open_id`。

### Q: 没有飞书，能用其他通知方式吗？
服务端现在只实现了飞书。但架构上预留了扩展点（参见 Action Layer TODO），
后续可以加 Telegram Bot / 企业微信 / Email 等 Provider。

### Q: 服务器重启后 auth token 丢了？
建议通过环境变量 `AUTH_TOKEN=xxx` 固定设置，而不是每次自动生成。
