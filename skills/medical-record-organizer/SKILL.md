---
name: medical-record-organizer
description: "Archive and organize patient medical records for any condition — optimized for oncology and chronic disease management. Auto-classifies PDFs and scanned photos into a structured per-patient directory: imaging (CT/MRI/PET-CT/ultrasound), lab results (CBC, tumor markers CEA/CA-199/AFP/CA-125), pathology, gene panel (NGS/KRAS/EGFR/BRCA/TMB/MSI), immunohistochemistry (IHC/PD-L1/HER2/Ki-67), and discharge summaries. Supports bulk import via zip/rar/7z archives. Builds a navigable INDEX.md for each patient — ideal for patients and family caregivers managing multi-year records. Supports both Chinese and English medical documents. Trigger phrases: 整理这份报告, 归档这个检查单, 帮我存这份CT, 存这份化验单, 添加出院小结, organize this report, file this lab result, save this CT scan, archive discharge summary, store medical record."
version: 1.0.0
metadata: {"openclaw":{"emoji":"🏥","requires":{"bins":["python3"],"anyBins":["unrar","unar"]},"install":[{"kind":"uv","package":"pdfplumber"},{"kind":"uv","package":"rarfile"},{"kind":"uv","package":"pillow"},{"kind":"uv","package":"python-docx"},{"kind":"uv","package":"openpyxl"},{"kind":"uv","package":"paddlepaddle"},{"kind":"uv","package":"paddleocr"},{"kind":"uv","package":"paddlenlp"}]}}
---

# Medical Record Organizer — 病历整理与归档

本技能将医疗文档（PDF 报告、纸质扫描件照片、化验单等）自动分类、提取关键信息，并归档到结构化的患者病历目录中。

## 整体流程

```
输入文件 → 检测类型 → 提取文本 → 分类文档 → [图片?] 隐私遮挡 → 提取关键字段 → 复制并重命名 → 更新索引 → 更新 profile → [触发?] 更新当前状态
```

> **严格顺序执行**：Agent 必须按 Step 0 → Step 1 → Step 2 → … → Step 10 的编号顺序依次执行。每个 Step 完成后方可进入下一个 Step，不得跳过或乱序。批量模式下 subagent 内部同样遵守 Step 2 → Step 3 → Step 4 → Step 5 → Step 6 的顺序。

---

## 执行模型约束（全局生效）

> **本 SKILL 的所有步骤由 Agent（你）亲自按Step编号顺序依次执行，前一个 Step 完成后才能进入下一个 Step。批量模式下每个 subagent 也必须按 Step 2 → 3 → 4 → 5 → 6 的顺序执行。不是由你编写脚本来执行。**

### 绝对禁止

1. **禁止编写"一键运行"脚本**：不得编写 Python/Shell 脚本来串联 Step 2-8 的流程。每个步骤由你（Agent）直接执行 shell 命令或调用已有脚本。
2. **禁止脚本化分类**：Step 3 的文档分类必须由你阅读内容后判断。不得用关键词匹配、正则表达式、if-else 规则、文件名推断代替你的理解能力。
3. **禁止脚本化字段提取**：Step 5 的关键字段（summary、doc_type、conclusion 等）必须由你阅读文档后生成，不得用正则或模板拼接。
4. **禁止脚本修改索引**：INDEX.md、timeline.md、肿标趋势.md 的更新必须由你直接读写，不得由脚本程序修改。
5. **禁止脚本实现并行**：批量模式的并行处理通过 subagent 机制实现，不得编写 threading/multiprocessing/asyncio 脚本。
6. **禁止跳步或乱序执行**：必须按 Step 编号顺序（0 → 1 → 2 → … → 10）依次执行，前一个 Step 完成后才能进入下一个 Step。批量模式下每个 subagent 也必须按 Step 2 → 3 → 4 → 5 → 6 的顺序执行。

### 允许调用的脚本（仅限以下）

只有 `scripts/` 目录下的**已有脚本**可以被调用，且仅用于数据提取：
- `check_gpu.py` — GPU 检测
- `init_patient.py` — 初始化患者目录
- `unpack_archive.py` — 解压压缩包
- `extract_pdf.py` — 提取 PDF 文本
- `extract_docx.py` — 提取 Word 文本
- `extract_excel.py` — 提取 Excel 文本
- `redact_ocr.py` — 图片 PII 遮挡

**你不得创建新的 `.py` 或 `.sh` 文件。**

---

## Step 0 — 检测 Python 命令

在执行任何脚本之前，先确定当前系统可用的 Python 3 命令。按以下优先级依次尝试：

1. `python3 --version`
2. `python --version`（需确认输出为 Python 3.x）
3. `py -3 --version`（Windows py launcher）

将第一个成功返回 Python 3.x 版本号的命令记为 `$PYTHON`，后续所有脚本调用均使用 `$PYTHON` 代替 `python3`。

如果三个命令均不可用，告知用户需要安装 Python 3。

### GPU 检测（自动）

确定 `$PYTHON` 后，运行 GPU 诊断：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/check_gpu.py
```

根据输出的 `status` 字段：
- `ok` / `no_gpu`：静默继续，无需提示用户。
- `gpu_not_enabled` / `version_mismatch`：向用户显示 `message` 和 `install_command`，询问是否安装。用户确认后执行安装命令，再次运行诊断脚本验证。用户拒绝则继续使用 CPU 模式。

---

## Step 1 — 初始化匿名患者目录（默认隐私模式开启）

默认**隐私模式开启**：

- 目录名、文件名、INDEX、timeline、profile 等生成内容中，禁止写入真实姓名、身份证号、手机号、详细地址等PII。
- 若用户提供真实姓名，只用于当前会话内映射，不得写入归档文件。

如果用户未提供患者代号，先询问：

> "请提供患者代号（如 PT-001）。如仅提供真实姓名，系统会自动转换为匿名ID。"

获取代号（或姓名）后，运行初始化脚本：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/init_patient.py "[患者代号或姓名]"
```

脚本会自动生成匿名患者ID（例如 `PT-1A2B3C4D5E`）并在 `~/.openclaw/patients/[匿名ID]/` 下创建完整目录树；若目录已存在会直接返回路径（幂等）。

记住输出的患者目录路径，后续步骤中用 `$PATIENT_DIR` 表示。

---

## Step 2 — 检测输入类型

根据用户提供的文件或内容，确定输入类型：

### 2a. 压缩包文件（`.zip` / `.rar` / `.7z`）

如果文件扩展名是 `.zip`、`.rar` 或 `.7z`，进入 **批量归档模式**（见下方"Batch Archive Mode"）。

### 2a+. 多文件输入（非压缩包）

如果用户一次提供多个文件（例如多张图片、多个 PDF，或混合格式），即使不是压缩包，也进入 **批量归档模式**。

### 2b. PDF 文件（`.pdf`）

运行 PDF 文本提取脚本：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/extract_pdf.py "[文件路径]"
```

脚本输出 JSON，包含 `success`、`pages`、`text` 字段。如果 `image_only` 为 `true`，说明 PDF 是扫描件，无可提取文本——此时使用你的视觉能力直接读取 PDF 内容。

### 2c. 图片文件（`.jpg` / `.jpeg` / `.png`）

直接使用你的视觉能力（vision capability）读取图片中的文字内容。注意中文医疗文档中可能有手写体、印章等干扰元素。

### 2d. 用户粘贴的文本

直接使用粘贴的文本内容进行后续处理。

### 2e. 纯文本文件（`.txt`）

直接读取文件内容：

```bash
cat "[文件路径]"
```

将读取的文本用于后续步骤。注意：医院系统导出的 TXT 文件可能使用 GBK 编码，如出现乱码，提示用户将文件转存为 UTF-8 后重试。

### 2f. Word 文件（`.doc` / `.docx`）

运行 Word 文本提取脚本：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/extract_docx.py "[文件路径]"
```

脚本输出 JSON，包含 `success`、`text`、`paragraphs` 字段。注意：仅支持 `.docx` 格式；若为旧版 `.doc` 格式，脚本会输出错误并提示用户另存为 `.docx` 后重试。

### 2g. Excel 文件（`.xls` / `.xlsx`）

运行 Excel 表格提取脚本：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/extract_excel.py "[文件路径]"
```

脚本输出 JSON，包含 `success`、`text`、`sheets`、`total_rows` 字段。注意：仅支持 `.xlsx` 格式；旧版 `.xls` 格式脚本会提示用户转存为 `.xlsx` 后重试。

---

## Batch Archive Mode — 批量归档模式

**并行配置**：

- `MAX_PARALLEL = 4`（默认值，用户可在触发时口头覆盖，如"最多3个并行"）

> **⚠ 严格禁止 — 违反此规则将导致分类结果不可靠**
>
> 1. **不得编写任何批处理脚本**：不得创建 `.py` 或 `.sh` 文件来循环处理文件列表。每个文件由一个独立的 subagent 处理。
> 2. **不得用代码逻辑分类**：`classify_by_content()`、`if "CT" in text` 等关键词匹配都是错误做法。分类必须由你（Agent/subagent）阅读文档全文后，凭理解判断。
> 3. **不得用正则提取摘要**：`re.search(r"诊断[:：](.+)")` 等正则提取是错误做法。摘要必须由你阅读后概括。
> 4. **`document-taxonomy.md` 是给你学习用的参考手册**，不是给代码用的映射表。
>
> **正确做法示例**（单个文件的处理流程）：
> ```
> Agent 调用: $PYTHON extract_pdf.py "file.pdf"   ← 脚本提取文本
> Agent 阅读: JSON 输出中的 text 字段              ← 你读内容
> Agent 判断: "这是一份腹部增强 CT 报告"            ← 你凭理解分类
> Agent 提取: date=2024-03-15, summary=肝脏多发...  ← 你提取字段
> Agent 执行: cp file.pdf $PATIENT_DIR/04_.../      ← 你执行复制
> ```
>
> **错误做法示例**（绝对禁止）：
> ```python
> # ❌ 以下代码片段全部违规
> def classify_by_content(text):
>     if "CT" in text: return "CT报告"      # 关键词匹配
>     if "CEA" in text: return "肿瘤标志物"  # 硬编码规则
>
> for file in files:                         # 批处理循环
>     process_one(file)                      # 脚本化流程
> ```

当输入为压缩包时：

1. **解压缩**：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/unpack_archive.py "[压缩包路径]"
```

脚本返回 JSON，包含 `tmp_dir`（临时目录）和 `files`（文件列表）。

2. **分批并行处理**：将 `files` 列表按 `MAX_PARALLEL` 分批，每批同时处理：

   ```
   batch_count = ceil(文件总数 / MAX_PARALLEL)
   ```

   对每一批（第1批 … 第 batch_count 批）：
   - 同时为该批内的**每个文件各启动一个 subagent**，每个 subagent 独立执行：
     - Step 2（检测类型并提取文本）
     - Step 3（分类 — **必须通过读取文档内容判断，禁止基于文件名或关键词**）
     - Step 4（图片隐私遮挡，仅图片输入时执行）
     - Step 5（提取关键字段）
     - Step 6（复制并重命名原始文件）
   - 等待该批**所有** subagent 完成后，向用户报告进度：
     > `[第N批/共M批] 已完成：文件1 (CT报告)、文件2 (血常规)、文件3 (肿瘤标志物)、...`
   - 主 Agent 将该批文件的条目行写入 INDEX.md 对应分类小节，并追加 timeline.md 行（Phase A）
   - 再开始下一批

   **示例**（MAX_PARALLEL=4，共9个文件）：

   ```
   第1批：文件1、2、3、4 → 并行处理 → 完成后报告进度
   第2批：文件5、6、7、8 → 并行处理 → 完成后报告进度
   第3批：文件9           → 单独处理 → 完成后报告进度
   ```

3. **最终聚合更新**：所有批次完成后，执行一次聚合操作：
   - 更新 INDEX.md 的聚合模块：关键指标（最新值）表格、最近更新日期
   - 如有肿瘤标志物文档，更新 `肿标趋势.md`
   - Step 9（更新 profile.json）
   - Step 10（更新当前状态快照，需用户确认）

4. **清理临时文件**：

```bash
rm -rf [tmp_dir]
```

5. **输出汇总报告**：

> "共处理 X 份文档：Y 份影像报告、Z 份检验报告、W 份其他文档"

---

## Step 3 — 分类文档

阅读文档内容，理解文档的性质和用途，对照分类法判断类别。**不要依赖关键词匹配**，通过理解文档整体内容来判断。

**执行主体**：分类判断必须由你（Agent）完成，不能委托给任何脚本或函数。你应该：
1. 阅读文档的完整文本（或用视觉能力查看图片）
2. 理解文档的整体性质——是检验报告、影像报告、病理报告还是出院记录
3. 对照 `document-taxonomy.md` 中的分类描述，选择最匹配的类别
4. 如果不确定，归入 `10_原始文件/未分类/`

分类参考文件（包含完整对照表和优先级规则）：

```
~/.openclaw/skills/medical-record-organizer/assets/document-taxonomy.md
```

如果无法确定文档类别，归入 `10_原始文件/未分类/`，并提示用户确认。

---

## Step 4 — 图片/扫描件隐私遮挡（OCR 自动方案）

**触发条件**：仅在输入为图片（`.jpg`/`.png`）时执行。其他文件类型跳过此步。

**时序约束**：必须在 Step 3（分类）之后、Step 5（提取关键字段）之前执行。Step 6 应复制 `_redacted` 版本而非原始文件。

**执行步骤**：

1. **OCR 自动遮挡**：运行 OCR 脚本一键完成 PII 检测与遮挡：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/redact_ocr.py "[原始文件路径]" --output "[输出路径_redacted.ext]"
```

脚本自动完成：PaddleOCR 文字检测 → PII 分类（PaddleNLP UIE NER）→ 标签-值分离（只遮值不遮标签）→ 输出遮挡图。

**输出**：
脚本输出的遮挡图不需要再进行任何额外脱敏处理。
`_redacted` 文件路径，作为 Step 6 的复制源。

---

## Step 5 — 提取关键字段

**执行主体**：以下字段由你（Agent）阅读文档内容后提取和填写，不得用正则表达式或模板脚本自动生成。

从文档内容中提取以下字段：

| 字段             | 说明               | 格式                            |
| ---------------- | ------------------ | ------------------------------- |
| `date`           | 文档日期           | YYYY-MM-DD（部分日期可估算）    |
| `hospital`       | 医院/机构名称      | 字符串                          |
| `department`     | 科室               | 字符串                          |
| `doc_type`       | 分类后的文档类型   | 中文，如"CT报告"                |
| `summary`        | 关键发现一句话摘要 | 中文，不超过80字                |
| `key_values`     | 重要数值           | 字典，如 `{"CEA": "5.2 ng/mL"}` |
| `abnormal_items` | 异常项列表         | 字符串数组                      |
| `conclusion`     | 医生结论/印象      | 字符串                          |

**注意事项**：

- 日期格式统一为 `YYYY-MM-DD`。如果文档只有"2024年3月"，记为 `2024-03-01`。
- 如果某个字段无法提取，留空或标记为"未提供"。
- 对于检验报告，`key_values` 应包含所有数值结果及参考范围。
- 对于影像报告，`summary` 应包含最关键的影像学发现。

---

## Step 6 — 复制并重命名原始文件

将原始文件复制到 Step 3 确定的目标目录，并按标准格式重命名：

### 文件命名规则

```
YYYY-MM-DD_[doc_type]_[brief_desc].[原始扩展名]
```

- `YYYY-MM-DD`：来自 Step 5 的 `date` 字段
- `[doc_type]`：来自 Step 5 的 `doc_type` 字段（如 `CT报告`、`肿瘤标志物`）
- `[brief_desc]`：来自 Step 5 的 `summary` 字段中最关键的2–4个中文词（如 `腹部增强`、`CEA升高`），且禁止包含任何PII
- 扩展名保留原始文件扩展名（`.pdf`、`.jpg`、`.png` 等）

示例：`2024-03-15_CT报告_腹部增强.pdf`、`2024-03-15_肿瘤标志物_CEA升高.jpg`

### 操作命令

**备份原始文件**：无论文件类型，先将原始未遮挡文件按序号复制到备份目录：

```bash
cp "[原始文件路径]" "$PATIENT_DIR/10_原始文件/原始未遮挡/[序号].[原始扩展名]"
```

- 序号格式为 `0001`、`0002`（与解压时一致）；单文件输入时序号为 `0001`
- 此操作保留未经任何处理的原始文件，确保可追溯

根据文件类型选择不同的源文件复制到分类目录：

**图片/扫描件（经过 Step 4 遮挡）：**

```bash
cp "[_redacted文件路径]" "$PATIENT_DIR/[目标目录]/YYYY-MM-DD_[doc_type]_[brief_desc].[ext]"
```

**其他文件类型（未经遮挡）：**

```bash
cp "[原始文件路径]" "$PATIENT_DIR/[目标目录]/YYYY-MM-DD_[doc_type]_[brief_desc].[ext]"
```

### 注意事项

- 如果目标文件名已存在（同名文件），在 `brief_desc` 后附加 `_2`、`_3` 以此类推
- 如果原文件名已符合 `YYYY-MM-DD_` 开头的标准格式，可直接复制不重命名
- 批量模式下：每个 subagent 完成 Step 5 后立即执行此步，无需等待其他文件

---

## Step 7 — 更新 INDEX.md

**执行主体**：INDEX.md 的更新由你（Agent）直接编辑文件完成。不得编写脚本来修改 INDEX.md。

> **批量模式下（两阶段）**：
> - **Phase A（逐批）**：每批 subagent 完成后，主 Agent 立即将该批文件的条目行插入对应分类小节（`<!-- 新文档条目插入此处 -->` 之后）。此阶段只写条目行，不改其他区域。
> - **Phase B（最终）**：所有批次完成后，执行一次聚合更新——刷新"关键指标（最新值）"表格、"最近更新"日期等非条目区域。

1. 读取 `$PATIENT_DIR/INDEX.md`。
2. 找到对应分类的小节标题（如 `### 04_影像学/CT/`）。
3. 在该小节的 `<!-- 新文档条目插入此处 -->` 注释**之后**插入新条目，直接链接原始文件：

```markdown
- [2024-03-15*CT报告*腹部增强.pdf](04_影像学/CT/2024-03-15_CT报告_腹部增强.pdf) — 肝脏多发转移灶，最大2.1cm，较前增大 ↑
```

条目格式说明：

- 链接文本和链接目标均为 Step 6 生成的原始文件名（非 `.md`）
- 破折号后为一句话摘要（Step 5 的 `summary` 字段 + 关键数值），直接内联，无需打开另一个文件

4. 如果文档包含被追踪的检验指标（CEA、CA-199、血红蛋白、肌酐等），同时更新 INDEX.md 中"关键指标（最新值）"表格对应行。

5. 更新"最近更新"日期。

6. 如果 `INDEX.md` 不存在，从模板创建：

```bash
cp ~/.openclaw/skills/medical-record-organizer/assets/templates/INDEX-template.md $PATIENT_DIR/INDEX.md
```

并将 `{{PATIENT_ID}}` 替换为匿名患者ID，`{{UPDATE_DATE}}` 替换为当前日期。

---

## Step 8 — 更新 timeline.md

**执行主体**：timeline.md 的更新由你（Agent）直接编辑文件完成。不得编写脚本来修改 timeline.md。

> **批量模式下（逐批写入）**：每批 subagent 完成后，主 Agent 立即将该批文件的行追加到 timeline.md 表格中（保持时间倒序）。无需等到所有批次完成。

在 `$PATIENT_DIR/timeline.md` 的表格中追加新行（按时间倒序，最新的在最前），文件路径指向原始文件：

```markdown
| 2024-03-15 | CT报告 | 肝脏多发转移灶，最大2.1cm | 04*影像学/CT/2024-03-15_CT报告*腹部增强.pdf |
```

---

## Step 9 — 更新 profile.json

**执行主体**：profile.json 的更新由你（Agent）直接读写文件完成。不得编写脚本来修改 profile.json。

> **批量模式下**：所有文件处理完毕后只执行**一次** profile.json 更新。

根据本次归档文档中提取的信息，自动回填 `$PATIENT_DIR/profile.json` 中仍为 `null` 的字段。

### 规则

1. **只填 `null` 字段**：如果字段已有非 `null` 值，绝对不覆盖。
2. **可回填的字段**（仅限以下 5 个）：

| 字段 | 数据来源示例 |
|------|-------------|
| `diagnosis` | 出院小结中的"出院诊断"、病理报告中的"病理诊断" |
| `diagnosis_date` | 首次确诊的日期（格式 `YYYY-MM-DD`） |
| `hospital` | 报告抬头中的医院名称（取最常出现的） |
| `doctor` | 主治/主管医生姓名（取最常出现的） |
| `age` | 报告中出现的年龄信息（取最新文档中的值） |

3. **隐私红线**：`name` 字段**永远不得填写**，即使文档中包含患者姓名。
4. **不确定时不填**：如果信息模糊或矛盾，保留 `null`，不要猜测。

### 执行步骤

1. 读取 `$PATIENT_DIR/profile.json`。
2. 检查上述 5 个字段是否为 `null`。
3. 从本次处理的文档提取信息中，匹配可填入的值。
4. 将更新后的 JSON 写回文件（保持格式化，UTF-8 编码）。

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

## Step 10 — 更新当前状态快照

**执行主体**：当前状态快照的更新由你（Agent）直接读写文件完成。不得编写脚本来修改当前状态。

> **批量模式下**：所有文件处理完毕后只执行**一次**当前状态更新（需用户确认）。

当新录入的文档是以下类型时：

- 影像报告（CT / MRI / PET-CT / 超声）
- 肿瘤标志物检验报告

处理完毕后，提示用户：

> "本次录入了[影像报告/肿瘤标志物]，是否要更新当前状态快照？(y/n)"

如果用户确认（y），则更新 `$PATIENT_DIR/01_当前状态/当前状态.md`，将最新的影像学发现或标志物数值写入对应小节。同时将旧版本的当前状态复制到 `01_当前状态/历史快照/` 目录保存。

---

## GPU 加速（可选）

默认使用 CPU 运行 OCR。如有 NVIDIA GPU，GPU 版本可提速 5–10x。

**自动检测**：Step 0 的 GPU 检测已自动诊断并提示安装。如果跳过了提示或需要手动安装，参考以下命令：

```bash
# CUDA 11.x
pip install --upgrade paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.x
pip install --upgrade paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
```

> **注意**：标准 PyPI 上 `paddlepaddle-gpu` 最高只有 2.x。PaddleX 3.x 需要 PaddlePaddle ≥ 3.0，必须从 PaddlePaddle 官方源安装。

安装后可运行诊断脚本验证：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/check_gpu.py
```

无需修改任何脚本，PaddlePaddle 自动检测 GPU。

---

## 隐私保护（默认开启，强制执行）

详细规则见参考文件：

```
~/.openclaw/skills/medical-record-organizer/assets/privacy-rules.md
```

核心原则：除非用户明确说”关闭隐私模式”，否则始终启用。目录必须使用匿名ID，文件名和索引内容禁止出现 PII。图片/扫描件的 PII 遮挡由 Step 4 的 `redact_ocr.py` 自动完成。

## 临时文件管理

| 来源                         | 路径                                 | 清理时机                              |
| ---------------------------- | ------------------------------------ | ------------------------------------- |
| `unpack_archive.py` 解压目录 | `$TEMP/openclaw_unpack_[timestamp]/` | 批量归档完成后立即 `rm -rf [tmp_dir]` |

**容错**：如果批量流程中途失败或被中断，在下次运行任何归档任务前，先检查并清理残留临时目录：

```bash
rm -rf "$($PYTHON -c "import tempfile; print(tempfile.gettempdir())")/openclaw_unpack_"*
```

其余脚本不产生临时文件。`_redacted` 和 `_debug` 文件是最终产物，不属于临时文件。

## 错误处理

- 如果 PDF 提取失败（加密、损坏），告知用户并建议拍照后用图片模式重试。
- 如果无法判断文档分类，归入 `10_原始文件/未分类/` 并提示用户手动确认。
- 如果关键字段无法提取，标注"未提供"并继续流程。
- 所有文件操作使用 UTF-8 编码。
