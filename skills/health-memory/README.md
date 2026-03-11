# health-memory — 健康记忆中枢

## 简介

`health-memory` 是一个纯指令型 skill（无 Python 脚本），定义了 `memory/health/` 下所有健康数据的存储格式和读写规范。所有健康相关 skill 共享这套格式，agent 使用内置工具（Read/Write/Edit/Grep/Glob）直接操作文件。

## 目标

1. **统一数据源** — `memory/health/` 作为所有健康数据的唯一存储位置
2. **按天日志聚合** — 每天一个文件，多个 skill 各自写入自己的 section
3. **按项纵向追踪** — 血压、肿瘤标志物、用药等各有独立文件，保留 90 天滚动历史
4. **健康文件索引** — PDF/图片存入 `files/`，memory 中只放摘要（不放全文）
5. **格式契约** — 任何健康 skill 只需遵循格式规范即可读写，无代码依赖

---

## 目录结构

```
memory/health/
├── _health-profile.md              # 长期健康基线（手动/agent 维护）
├── daily/                           # 按天日志
│   ├── 2026-03-10.md
│   ├── 2026-03-09.md
│   └── ...
├── items/                           # 按健康项纵向追踪
│   ├── blood-pressure.md            # 血压历史
│   ├── blood-sugar.md               # 血糖历史
│   ├── blood-lipids.md              # 血脂历史
│   ├── tumor-markers.md             # 肿瘤标志物历史
│   ├── kidney-function.md           # 肾功能历史
│   ├── weight.md                    # 体重历史
│   ├── medications.md               # 用药记录
│   ├── supplements.md               # 补剂记录
│   └── ...                          # agent 按需自动新建
└── files/                           # 健康文件存放（PDF/图片等）
    ├── 2026-03-10_blood_routine.pdf
    └── ...
```

---

## Daily 文件格式

**路径**: `memory/health/daily/YYYY-MM-DD.md`

```markdown
---
date: YYYY-MM-DD
updated_at: YYYY-MM-DDTHH:MM:SS
---

# YYYY-MM-DD

## 血压 [blood-pressure-tracker · 09:15]
- 120/80 mmHg, 脉搏 72
- 分级: 正常

## 咖啡因 [caffeine-tracker · 14:30]
- 体内残留: ~230mg
- 安全入睡: 22:30
- 今日摄入: Espresso 150mg (08:30), Latte 80mg (14:30)

## 健康文件
| 文件 | 类型 | 摘要 | 路径 |
|------|------|------|------|
| 血常规 | 检验报告 | WBC 6.2, Hb 135, PLT 210 均正常 | memory/health/files/2026-03-10_blood_routine.pdf |
```

### 格式规则

- **Section 标题**: `## 标题 [skill-name · HH:MM]` — 固定格式，便于 Grep 定位
- **同 skill 当天多次更新**: 用 Edit 替换该 section，不重复追加
- **`## 健康文件` section**: 始终在文件末尾，用表格索引文件摘要+路径
- **文件全文绝不放入 memory**: 只放摘要（1-2 行），agent 按需用 Read 去看原文件

---

## Item 文件格式

**路径**: `memory/health/items/{item}.md`

```markdown
---
item: blood-pressure
unit: mmHg
updated_at: YYYY-MM-DDTHH:MM:SS
---

# 血压记录

## 最近状态
- 最新: 120/80 mmHg (2026-03-10 09:15)
- 7日均值: 118/78 mmHg
- 趋势: 稳定

## 历史记录
| 日期 | 收缩压 | 舒张压 | 脉搏 | 备注 |
|------|--------|--------|------|------|
| 2026-03-10 | 120 | 80 | 72 | 晨起 |
| 2026-03-09 | 125 | 82 | 75 | 晨起 |
| 2026-03-08 | 118 | 78 | 70 | |
```

### 格式规则

- **`## 最近状态`**: 最新值 + 短期趋势摘要（供快速浏览）
- **`## 历史记录`**: 表格形式，最新在前，保留最近 90 天
- **超过 90 天的旧数据**: agent 在更新时删除表格尾部行
- **Item 文件名**: 由 agent 自行决定（按健康项中文名 → 英文 slug），遇到新健康项则自动新建
- **表格列**: 根据健康项不同，表格列可以不同（如血压有收缩压/舒张压，肿瘤标志物有 CEA/CA199 等）

---

## 写入时机

**任何健康 skill 更新数据后，执行以下步骤**:

1. 用 Glob 找到 `memory/health/daily/` 下当日文件（如不存在则用 Write 新建，含 frontmatter 和 `## 健康文件` 空表格）
2. 用 Read 读取当日文件
3. 找到对应 skill 的 section（用 Grep 匹配 `## .* \[{skill-name} ·`），用 Edit 替换；如不存在则在 `## 健康文件` 之前追加新 section
4. 更新 frontmatter 的 `updated_at`
5. 同时更新对应的 `memory/health/items/{item}.md`:
   - 用 Read 读取 item 文件（如不存在则 Write 新建，含 frontmatter、`## 最近状态`、`## 历史记录` 空表格）
   - 更新 `## 最近状态` section
   - 在 `## 历史记录` 表格表头后首行插入新记录
   - 如表格超过 90 天，删除尾部旧行

---

## 文件收录时机

**用户提供健康文件（PDF/图片）时**:

1. 读取文件生成摘要（1-2 行关键指标/结论）
2. 将原始文件保存/移动到 `memory/health/files/`，命名格式: `YYYY-MM-DD_{描述}.{ext}`
3. 在当日 daily 文件的 `## 健康文件` 表格追加一行（文件名 + 类型 + 摘要 + 路径）
4. 如涉及具体健康项数据（如血常规中的 WBC），同步更新对应 item 文件

---

## 读取时机

**用户问健康问题时，按需逐步加载**:

1. 先用 Read 加载 `memory/health/_health-profile.md`（基线）
2. 用 Read 加载 `memory/health/daily/{今天日期}.md`（当日状态）
3. 如果问题涉及特定健康项趋势 → 用 Read 加载对应 `memory/health/items/{item}.md`
4. 如果问题涉及历史日期 → 用 Glob `memory/health/daily/*.md` 找到相关日期文件，用 Read 加载
5. 如果 daily 或 item 文件中引用了健康文件 → 按需用 Read 查看具体文件（PDF 等）
6. **不要一次加载所有文件**，按需逐步加载，避免撑爆上下文

---

## 给其他 skill 的集成说明

**集成方式**: 你的 health skill 在更新数据后，应同时按本 skill 的格式规范更新 memory 文件。

不需要 import 任何 Python 模块，不需要调用任何脚本。Agent 执行你的 skill 时，在完成数据操作后，直接使用 Read/Edit/Write 工具按上述格式更新 `memory/health/daily/` 和 `memory/health/items/` 下的对应文件即可。

### 常用 Grep 模式速查

| 场景 | 模式 | 搜索路径 |
|------|------|----------|
| 查找当日某 skill 的 section | `## .* \[{skill-name} ·` | `memory/health/daily/{date}.md` |
| 查找所有包含某健康项的 daily 文件 | `## {健康项名}` | `memory/health/daily/` |
| 查找 item 文件中的最新值 | `最新:` | `memory/health/items/{item}.md` |

### 新建 item 文件模板

```markdown
---
item: {english-slug}
unit: {单位}
updated_at: {ISO时间}
---

# {中文名}记录

## 最近状态
- 最新: （待填充）

## 历史记录
| 日期 | {列1} | {列2} | 备注 |
|------|-------|-------|------|
```
