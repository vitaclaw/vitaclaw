---
name: follow-up-reminder
description: "Manages follow-up appointment reminders by disease type, supporting checkup scheduling, periodic reminders, and completion tracking. Use when the user wants to set up or manage medical follow-up reminders."
version: 1.0.0
user-invocable: true
argument-hint: "[set-reminder | list | mark-done]"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
metadata: {"openclaw":{"emoji":"🔔","category":"health"}}
---

# Follow-Up Reminder — 复诊/复查提醒管理

管理复诊预约提醒，支持按病种设置检查清单、定期提醒和完成追踪。

## 用法

### 设置新提醒

用户说"帮我设个复查提醒"或"3 个月后查血常规"时触发。

运行 Python CLI 添加提醒：

```bash
$PYTHON follow_up_reminder.py add \
  --disease "[病种]" \
  --item "[检查项目]" \
  --interval "[间隔天数]" \
  --note "[备注]"
```

支持的病种预设清单（`checklist` 子命令可查看）：
- **高血压**：血压监测、肾功能、电解质、心电图
- **糖尿病**：糖化血红蛋白、肾功能、眼底检查、足部检查、血脂
- **肿瘤/术后**：影像复查、肿瘤标志物、血常规、肝肾功能

### 查看待办提醒

```bash
$PYTHON follow_up_reminder.py due
```

列出即将到期或已过期的复查项目。

### 标记完成

```bash
$PYTHON follow_up_reminder.py done --id "[提醒ID]"
```

标记完成后自动计算下次复查日期。

### 查看所有提醒

```bash
$PYTHON follow_up_reminder.py list
```

## 数据持久化

**重要**：每次通过 Python CLI 执行操作（add / done）后，Agent **必须**同步更新 `memory/health/`，确保 heartbeat 和其他 skill 可以读取到最新的复查提醒数据。Python CLI 仅写入 JSONL 数据文件，不会更新 Markdown 文件。

按 health-memory 写入协议同步：

1. **更新 daily 文件**：在 `memory/health/daily/YYYY-MM-DD.md` 中插入/替换段落：
   ```markdown
   ## 复查提醒 [follow-up-reminder · HH:MM]
   - 已设置：[病种] [项目]，下次复查 YYYY-MM-DD
   ```

2. **更新 items 文件**（`memory/health/items/appointments.md`）：
   - `## Upcoming` 表格中追加新行
   - `## History` 表格中记录已完成的复查

## 与 Heartbeat 的协作

Heartbeat 系统的 `_issues_due_schedule()` 会独立检查 `items/appointments.md` 中的到期项目。本 skill 设置的提醒应同时写入 `items/appointments.md`，确保 heartbeat 能感知到。
