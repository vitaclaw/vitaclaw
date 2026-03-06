---
name: medical-record-organizer
description: "Archive and organize patient medical records for any condition — optimized for oncology and chronic disease management. Auto-classifies PDFs and scanned photos into a structured per-patient directory: imaging (CT/MRI/PET-CT/ultrasound), lab results (CBC, tumor markers CEA/CA-199/AFP/CA-125), pathology, gene panel (NGS/KRAS/EGFR/BRCA/TMB/MSI), immunohistochemistry (IHC/PD-L1/HER2/Ki-67), and discharge summaries. Supports bulk import via zip/rar/7z archives. Builds a navigable INDEX.md for each patient — ideal for patients and family caregivers managing multi-year records. Supports both Chinese and English medical documents. Trigger phrases: 整理这份报告, 归档这个检查单, 帮我存这份CT, 存这份化验单, 添加出院小结, organize this report, file this lab result, save this CT scan, archive discharge summary, store medical record."
version: 1.0.0
metadata: {"openclaw":{"emoji":"🏥","requires":{"bins":["python3"],"anyBins":["unrar","unar"]},"install":[{"kind":"uv","package":"pdfplumber"},{"kind":"uv","package":"rarfile"},{"kind":"uv","package":"pillow"},{"kind":"uv","package":"python-docx"},{"kind":"uv","package":"openpyxl"},{"kind":"uv","package":"paddlepaddle"},{"kind":"uv","package":"paddleocr"}]}}
---

# Medical Record Organizer — 病历整理与归档

本技能将医疗文档（PDF 报告、纸质扫描件照片、化验单等）自动分类、提取关键信息，并归档到结构化的患者病历目录中。

## 整体流程

```
输入文件 → 检测类型 → 提取文本 → 分类文档 → [图片?] 隐私遮挡 → 提取关键字段 → 复制并重命名 → 更新索引
```

---

## Step 0 — 检测 Python 命令

在执行任何脚本之前，先确定当前系统可用的 Python 3 命令。按以下优先级依次尝试：

1. `python3 --version`
2. `python --version`（需确认输出为 Python 3.x）
3. `py -3 --version`（Windows py launcher）

将第一个成功返回 Python 3.x 版本号的命令记为 `$PYTHON`，后续所有脚本调用均使用 `$PYTHON` 代替 `python3`。

如果三个命令均不可用，告知用户需要安装 Python 3。

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
     - Step 3（分类）
     - Step 4（图片隐私遮挡，仅图片输入时执行）
     - Step 5（提取关键字段）
     - Step 6（复制并重命名原始文件）
   - 等待该批**所有** subagent 完成后，向用户报告进度：
     > `[第N批/共M批] 已完成：文件1 (CT报告)、文件2 (血常规)、文件3 (肿瘤标志物)、...`
   - 再开始下一批

   **示例**（MAX_PARALLEL=4，共9个文件）：

   ```
   第1批：文件1、2、3、4 → 并行处理 → 完成后报告进度
   第2批：文件5、6、7、8 → 并行处理 → 完成后报告进度
   第3批：文件9           → 单独处理 → 完成后报告进度
   ```

3. **批量更新索引**：所有批次完成后，**仅执行一次** Step 7（更新 INDEX.md）和 Step 8（更新 timeline.md）。

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

| 文档类型      | 目标目录                  | 关键词                                                          |
| ------------- | ------------------------- | --------------------------------------------------------------- |
| 出院小结      | `08_出院小结/`            | 出院小结、入院诊断、出院诊断、住院号 等                         |
| 入院小结      | `08_出院小结/入院小结/`   | 入院小结、入院记录、入院病历、主诉、现病史 等（不含"出院小结"） |
| CT 报告       | `04_影像学/CT/`           | CT、计算机断层、增强CT、平扫 等                                 |
| MRI 报告      | `04_影像学/MRI/`          | MRI、磁共振、核磁 等                                            |
| PET-CT 报告   | `04_影像学/PET-CT/`       | PET、PET-CT、PET/CT、代谢 等                                    |
| 超声报告      | `04_影像学/超声/`         | 超声、B超、彩超、腹部超声 等                                    |
| 血常规        | `05_检验检查/血常规/`     | 血常规、CBC、白细胞、红细胞、血红蛋白、血小板 等                |
| 生化/肝肾功能 | `05_检验检查/生化肝肾功/` | 生化、肝功能、肾功能、ALT、AST、肌酐、尿素氮 等                 |
| 肿瘤标志物    | `05_检验检查/肿瘤标志物/` | 肿瘤标志物、CEA、CA-199、CA199、AFP、CA-125、CA125 等           |
| 基因检测/NGS  | `03_分子病理/基因检测/`   | 基因检测、NGS、二代测序、KRAS、EGFR、BRCA、MSI、TMB 等          |
| 免疫组化      | `03_分子病理/免疫组化/`   | 免疫组化、IHC、PD-L1、HER2、Ki-67、MLH1、MSH2 等                |
| 病理报告      | `02_诊断与分期/病理报告/` | 病理、活检、组织学、腺癌、鳞癌、分化 等                         |
| 处方/门诊记录 | `10_原始文件/门诊记录/`   | 处方、门诊、Rx、用法用量 等                                     |
| 无法判断      | `10_原始文件/未分类/`     | —                                                               |

### 分类优先级规则

1. 如果文档同时包含"基因检测"和"免疫组化"关键词，以文档主体内容为准——如果主要是基因突变位点列表，归入基因检测；如果主要是蛋白表达结果，归入免疫组化。
2. 出院小结优先级最高：如果文档包含"出院小结"字样，直接归类为出院小结，即使内容中提到了检验或影像结果。
3. 入院小结识别：如果文档包含"入院小结"或"入院记录"字样，但**不含**"出院小结"，归类为入院小结。
4. 如果病理报告中包含免疫组化结果，仍归类为病理报告（完整病理报告 > 单独免疫组化）。
5. 对于无法确定的文档，归入 `10_原始文件/未分类/`，并提示用户确认。

---

## Step 4 — 图片/扫描件隐私遮挡（OCR 自动方案）

**触发条件**：仅在输入为图片（`.jpg`/`.png`）时执行。其他文件类型跳过此步。

**时序约束**：必须在 Step 3（分类）之后、Step 5（提取关键字段）之前执行。Step 6 应复制 `_redacted` 版本而非原始文件。

**执行步骤**：

1. **OCR 自动遮挡**：运行 OCR 脚本一键完成 PII 检测与遮挡：

```bash
$PYTHON ~/.openclaw/skills/medical-record-organizer/scripts/redact_ocr.py "[原始文件路径]" --output "[输出路径_redacted.ext]"
```

脚本自动完成：PaddleOCR 文字检测 → PII 分类（正则+医疗白名单）→ 标签-值分离（只遮值不遮标签）→ 输出遮挡图。

**输出**：
脚本输出的遮挡图不需要再进行任何额外脱敏处理。
`_redacted` 文件路径，作为 Step 6 的复制源。

---

## Step 5 — 提取关键字段

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

根据文件类型选择不同的源文件：

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

> **批量模式下**：所有文件处理完毕后只执行**一次**索引更新。

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

> **批量模式下**：所有文件处理完毕后只执行**一次**时间线更新。

在 `$PATIENT_DIR/timeline.md` 的表格中追加新行（按时间倒序，最新的在最前），文件路径指向原始文件：

```markdown
| 2024-03-15 | CT报告 | 肝脏多发转移灶，最大2.1cm | 04*影像学/CT/2024-03-15_CT报告*腹部增强.pdf |
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

## 隐私保护（默认开启，强制执行）

> 不再需要触发短语。除非用户明确说“关闭隐私模式”，否则始终启用。

### 强制规则（适用于所有步骤）

1. **目录匿名化**：患者目录必须使用匿名ID（如 `PT-XXXXXXXXXX`），禁止使用真实姓名。
2. **文件名去隐私**：`brief_desc` 中禁止出现姓名、身份证号、手机号、具体地址、住院号、床号等PII。
3. **文本去隐私**：写入 `INDEX.md`、`timeline.md`、`当前状态.md`、`profile.json` 时，所有可识别个人信息必须先遮蔽。
4. **最小化暴露**：医疗必要信息可保留（诊断、指标、疗效）；身份识别信息必须脱敏或删除。

### 文本隐私遮蔽规则（默认执行）

在 Step 7/Step 8 以及任何摘要写入前，先对文本应用下列遮蔽：

| 信息类型           | 识别特征                            | 遮蔽格式                         |
| ------------------ | ----------------------------------- | -------------------------------- |
| 身份证号           | 15/18 位数字（末位可为 X）          | 保留前3位+后2位：`330***XXXXX82` |
| 手机号             | `1[3-9]` 开头11位数字               | 保留前3位+后4位：`138****5678`   |
| 详细地址           | 路/街/弄/号/室前后数字              | 保留至区县级：`XX区 ****`        |
| 患者/联系人姓名    | 「姓名：」「患者：」标签后2–4字中文 | 保留姓，遮蔽名：`张**`           |
| 住院号/床号/申请号 | 医院单据编号字段                    | 仅保留后2–4位，其余 `*`          |

### 图片/扫描件隐私遮挡

> 详见 Step 4。图片和扫描件 PDF 的 PII 遮挡由 `redact_ocr.py` 自动完成。

### 关闭隐私模式（显式指令才允许）

仅当用户明确说出“关闭隐私模式/disable privacy mode”时，才允许不遮蔽处理；执行前需再次确认风险。

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
