---
name: medical-record-organizer
description: Archive and organize patient medical records for any condition — optimized for oncology and chronic disease management. Auto-classifies PDFs and scanned photos into a structured per-patient directory: imaging (CT/MRI/PET-CT/ultrasound), lab results (CBC, tumor markers CEA/CA-199/AFP/CA-125), pathology, gene panel (NGS/KRAS/EGFR/BRCA/TMB/MSI), immunohistochemistry (IHC/PD-L1/HER2/Ki-67), and discharge summaries. Supports bulk import via zip/rar/7z archives. Builds a navigable INDEX.md for each patient — ideal for patients and family caregivers managing multi-year records. Supports both Chinese and English medical documents. Trigger phrases: "整理这份报告", "归档这个检查单", "帮我存这份CT", "存这份化验单", "添加出院小结", "organize this report", "file this lab result", "save this CT scan", "archive discharge summary", "store medical record".
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
      anyBins:
        - unrar
        - unar
    emoji: "🏥"
    install:
      - kind: uv
        package: pdfplumber
      - kind: uv
        package: rarfile
---

# Medical Record Organizer — 病历整理与归档

本技能将医疗文档（PDF 报告、纸质扫描件照片、化验单等）自动分类、提取关键信息，并归档到结构化的患者病历目录中。

## 整体流程

```
输入文件 → 检测类型 → 提取文本 → 分类文档 → 提取关键字段 → 写入 Markdown → 更新索引
```

---

## Step 1 — 初始化患者目录

如果用户未提供患者姓名，先询问：

> "请问患者姓名是？"

获取姓名后，运行初始化脚本：

```bash
python3 ~/.openclaw/skills/medical-record-organizer/scripts/init_patient.py "[患者姓名]"
```

脚本会在 `~/.openclaw/patients/[患者姓名]/` 下创建完整的目录树，并输出患者目录路径。如果目录已存在，脚本会直接返回路径（幂等操作）。

记住输出的患者目录路径，后续步骤中用 `$PATIENT_DIR` 表示。

---

## Step 2 — 检测输入类型

根据用户提供的文件或内容，确定输入类型：

### 2a. 压缩包文件（`.zip` / `.rar` / `.7z`）

如果文件扩展名是 `.zip`、`.rar` 或 `.7z`，进入 **批量归档模式**（见下方"Batch Archive Mode"）。

### 2b. PDF 文件（`.pdf`）

运行 PDF 文本提取脚本：

```bash
python3 ~/.openclaw/skills/medical-record-organizer/scripts/extract_pdf.py "[文件路径]"
```

脚本输出 JSON，包含 `success`、`pages`、`text` 字段。如果 `image_only` 为 `true`，说明 PDF 是扫描件，无可提取文本——此时使用你的视觉能力直接读取 PDF 内容。

### 2c. 图片文件（`.jpg` / `.jpeg` / `.png`）

直接使用你的视觉能力（vision capability）读取图片中的文字内容。注意中文医疗文档中可能有手写体、印章等干扰元素。

### 2d. 用户粘贴的文本

直接使用粘贴的文本内容进行后续处理。

---

## Batch Archive Mode — 批量归档模式

**并行配置**：
- `MAX_PARALLEL = 4`（默认值，用户可在触发时口头覆盖，如"最多3个并行"）

当输入为压缩包时：

1. **解压缩**：

```bash
python3 ~/.openclaw/skills/medical-record-organizer/scripts/unpack_archive.py "[压缩包路径]"
```

脚本返回 JSON，包含 `tmp_dir`（临时目录）和 `files`（文件列表）。

2. **分批并行处理**：将 `files` 列表按 `MAX_PARALLEL` 分批，每批同时处理：

   ```
   batch_count = ceil(文件总数 / MAX_PARALLEL)
   ```

   对每一批（第1批 … 第 batch_count 批）：
   - 同时为该批内的**每个文件各启动一个 subagent**，每个 subagent 独立执行：
     - Step 2（检测类型并提取文本）
     - Step 3（分类）
     - Step 4（提取关键字段）
     - Step 5（写入 Markdown 归档文件）
   - 等待该批**所有** subagent 完成后，向用户报告进度：
     > `[第N批/共M批] 已完成：文件1 (CT报告)、文件2 (血常规)、文件3 (肿瘤标志物)、...`
   - 再开始下一批

   **示例**（MAX_PARALLEL=4，共9个文件）：
   ```
   第1批：文件1、2、3、4 → 并行处理 → 完成后报告进度
   第2批：文件5、6、7、8 → 并行处理 → 完成后报告进度
   第3批：文件9           → 单独处理 → 完成后报告进度
   ```

3. **批量更新索引**：所有批次完成后，**仅执行一次** Step 6（更新 INDEX.md）和 Step 7（更新 timeline.md）。

4. **清理临时文件**：

```bash
rm -rf [tmp_dir]
```

5. **输出汇总报告**：

> "共处理 X 份文档：Y 份影像报告、Z 份检验报告、W 份其他文档"

---

## Step 3 — 分类文档

根据提取的文本内容，参照分类法对文档进行归类。分类参考文件：

```
~/.openclaw/skills/medical-record-organizer/assets/document-taxonomy.md
```

### 分类对照表

| 文档类型 | 目标目录 | 关键词 |
|----------|----------|--------|
| 出院小结 | `08_出院小结/` | 出院小结、入院诊断、出院诊断、住院号 |
| CT 报告 | `04_影像学/CT/` | CT、计算机断层、增强CT、平扫 |
| MRI 报告 | `04_影像学/MRI/` | MRI、磁共振、核磁 |
| PET-CT 报告 | `04_影像学/PET-CT/` | PET、PET-CT、PET/CT、代谢 |
| 超声报告 | `04_影像学/超声/` | 超声、B超、彩超、腹部超声 |
| 血常规 | `05_检验检查/血常规/` | 血常规、CBC、白细胞、红细胞、血红蛋白、血小板 |
| 生化/肝肾功能 | `05_检验检查/生化肝肾功/` | 生化、肝功能、肾功能、ALT、AST、肌酐、尿素氮 |
| 肿瘤标志物 | `05_检验检查/肿瘤标志物/` | 肿瘤标志物、CEA、CA-199、CA199、AFP、CA-125、CA125 |
| 基因检测/NGS | `03_分子病理/基因检测/` | 基因检测、NGS、二代测序、KRAS、EGFR、BRCA、MSI、TMB |
| 免疫组化 | `03_分子病理/免疫组化/` | 免疫组化、IHC、PD-L1、HER2、Ki-67、MLH1、MSH2 |
| 病理报告 | `02_诊断与分期/病理报告/` | 病理、活检、组织学、腺癌、鳞癌、分化 |
| 处方/门诊记录 | `10_原始文件/门诊记录/` | 处方、门诊、Rx、用法用量 |
| 无法判断 | `10_原始文件/未分类/` | — |

### 分类优先级规则

1. 如果文档同时包含"基因检测"和"免疫组化"关键词，以文档主体内容为准——如果主要是基因突变位点列表，归入基因检测；如果主要是蛋白表达结果，归入免疫组化。
2. 出院小结优先级最高：如果文档包含"出院小结"字样，直接归类为出院小结，即使内容中提到了检验或影像结果。
3. 如果病理报告中包含免疫组化结果，仍归类为病理报告（完整病理报告 > 单独免疫组化）。
4. 对于无法确定的文档，归入 `10_原始文件/未分类/`，并提示用户确认。

---

## Step 4 — 提取关键字段

从文档内容中提取以下字段：

| 字段 | 说明 | 格式 |
|------|------|------|
| `date` | 文档日期 | YYYY-MM-DD（部分日期可估算） |
| `hospital` | 医院/机构名称 | 字符串 |
| `department` | 科室 | 字符串 |
| `doc_type` | 分类后的文档类型 | 中文，如"CT报告" |
| `summary` | 关键发现一句话摘要 | 中文，不超过80字 |
| `key_values` | 重要数值 | 字典，如 `{"CEA": "5.2 ng/mL"}` |
| `abnormal_items` | 异常项列表 | 字符串数组 |
| `conclusion` | 医生结论/印象 | 字符串 |

**注意事项**：
- 日期格式统一为 `YYYY-MM-DD`。如果文档只有"2024年3月"，记为 `2024-03-01`。
- 如果某个字段无法提取，留空或标记为"未提供"。
- 对于检验报告，`key_values` 应包含所有数值结果及参考范围。
- 对于影像报告，`summary` 应包含最关键的影像学发现。

---

## Step 5 — 写入 Markdown 归档文件

### 文件命名

```
YYYY-MM-DD_[doc_type]_[brief_desc].md
```

示例：`2024-03-15_CT报告_腹部增强.md`

### 文件存放位置

放入 Step 3 确定的目标目录下：

```
$PATIENT_DIR/[目标目录]/YYYY-MM-DD_[doc_type]_[brief_desc].md
```

### 文件模板

```markdown
# [doc_type] — [hospital] [date]

**医院**：[hospital]
**科室**：[department]
**日期**：[date]
**类型**：[doc_type]

## 主要发现
[根据文档内容，用简洁中文描述关键发现，每个发现一个要点]

## 关键数值
| 项目 | 数值 | 参考范围 | 状态 |
|------|------|----------|------|
| [指标名] | [数值] | [参考范围] | ↑/↓/→ |

（如无数值项可省略此节）

## 异常项
- [异常项1]
- [异常项2]

（如无异常可写"未见明显异常"）

## 医生结论
[conclusion]

## 原文摘录
> [摘录文档中最关键的原始文字段落，保留原文表述]
```

---

## Step 6 — 更新 INDEX.md

> **批量模式下**：所有文件处理完毕后只执行**一次**索引更新。

1. 读取 `$PATIENT_DIR/INDEX.md`。
2. 找到对应分类的小节标题（如 `### 04_影像学/CT/`）。
3. 在该小节的 `<!-- 新文档条目插入此处 -->` 注释**之后**插入新条目：

```markdown
- [YYYY-MM-DD_doc_type_desc.md](04_影像学/CT/YYYY-MM-DD_doc_type_desc.md) — 一句话摘要
```

4. 如果文档包含被追踪的检验指标（CEA、CA-199、血红蛋白、肌酐等），同时更新 INDEX.md 中"关键指标（最新值）"表格对应行。

5. 更新"最近更新"日期。

6. 如果 `INDEX.md` 不存在，从模板创建：

```bash
cp ~/.openclaw/skills/medical-record-organizer/assets/templates/INDEX-template.md $PATIENT_DIR/INDEX.md
```

并将 `{{PATIENT_NAME}}` 替换为患者姓名，`{{UPDATE_DATE}}` 替换为当前日期。

---

## Step 7 — 更新 timeline.md

> **批量模式下**：所有文件处理完毕后只执行**一次**时间线更新。

在 `$PATIENT_DIR/timeline.md` 的表格中追加新行（按时间倒序，最新的在最前）：

```markdown
| [date] | [doc_type] | [one-line summary] | [相对路径] |
```

---

## 特殊处理：肿瘤标志物

当文档被分类为 `肿瘤标志物` 时，除常规归档外，还需更新趋势表：

**文件**：`$PATIENT_DIR/05_检验检查/肿瘤标志物/肿标趋势.md`

在表格中追加新行：

```markdown
| [date] | [CEA值] | [CA-199值] | [AFP值] | [CA-125值] | [其他标志物] | [趋势↑↓→] | [备注] |
```

趋势判断规则：
- 与上一次数值比较，升高标记 `↑`，降低标记 `↓`，稳定标记 `→`
- 如果是首次记录，趋势标记为 `—`（首次）

---

## 特殊处理：当前状态更新

当新录入的文档是以下类型时：
- 影像报告（CT / MRI / PET-CT / 超声）
- 肿瘤标志物检验报告

处理完毕后，提示用户：

> "本次录入了[影像报告/肿瘤标志物]，是否要更新当前状态快照？(y/n)"

如果用户确认（y），则更新 `$PATIENT_DIR/01_当前状态/当前状态.md`，将最新的影像学发现或标志物数值写入对应小节。同时将旧版本的当前状态复制到 `01_当前状态/历史快照/` 目录保存。

---

## 错误处理

- 如果 PDF 提取失败（加密、损坏），告知用户并建议拍照后用图片模式重试。
- 如果无法判断文档分类，归入 `10_原始文件/未分类/` 并提示用户手动确认。
- 如果关键字段无法提取，在 Markdown 文件中标注"未提供"并继续流程。
- 所有文件操作使用 UTF-8 编码。
