[English](README.md) | **中文**

<div align="center">

# 🩺 VitaClaw

### 204 个 AI 健康技能，适用于 OpenClaw

![Skills](https://img.shields.io/badge/skills-204-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-orange)

从血压追踪到肿瘤委员会分析——即插即用的健康智能，为你的 AI 助手赋能。

</div>

---

## 什么是 VitaClaw？

VitaClaw 是一个开源的模块化健康 AI 技能库，包含 204 个技能，专为在 [OpenClaw](https://openclaw.ai) 中运行而设计。每个技能都是一个独立的 `SKILL.md` 文件，赋予你的 AI 助手深度、领域特定的健康能力——从日常体征记录到临床基因组学解读。

VitaClaw 建立在三大支柱之上：

1. **健康记忆系统** —— 在 `memory/health/` 下进行每日健康追踪，在 `~/.openclaw/patients/` 下维护结构化的临床病历档案。你的数据以纯 Markdown 文件形式存储在本地，由 git 版本控制，完全由你掌控。
2. **模块化技能** —— 204 个独立的 `SKILL.md` 文件，每个文件定义自己的提示词、工具和数据格式。按需引入，自由编辑，无限扩展。
3. **场景编排** —— 7 个场景应用（如 `diabetes-control-hub`、`hypertension-daily-copilot`）将多个技能串联成端到端的临床工作流，从数据采集到纵向分析再到健康建议。

### 为什么选择 VitaClaw？


| 特性     | 通用健康应用         | VitaClaw                                |
| -------- | -------------------- | --------------------------------------- |
| 数据归属 | 云端 / 厂商锁定     | 本地文件——数据完全属于你              |
| 可定制性 | 固定功能             | 可编辑任何 `SKILL.md`                   |
| 临床深度 | 消费级               | 研究级（PubMed、ClinVar、GWAS）         |
| 集成能力 | 各自孤立             | 技能通过 health-memory 互联互通         |
| AI 模型  | 单一供应商           | 通过 OpenClaw 支持任意模型（Claude、GPT、Gemini、Llama……） |

---

## 安装

### 方式 A —— Git Clone（推荐）

```bash
# 克隆到 OpenClaw 共享技能目录
git clone https://github.com/vitaclaw/vitaclaw.git ~/.openclaw/skills/vitaclaw

# 或克隆到工作区
git clone https://github.com/vitaclaw/vitaclaw.git ./skills/vitaclaw
```

### 方式 B —— 按需挑选

```bash
# 只复制你需要的技能
cp -r vitaclaw/skills/blood-pressure-tracker ~/.openclaw/skills/
cp -r vitaclaw/skills/diabetes-control-hub   ~/.openclaw/skills/
```

无需构建步骤，无需依赖，无需配置向导。OpenClaw 会自动发现技能目录中的 `SKILL.md` 文件。

---

## 技能概览


| #  | 分类                                                                     | 数量 | 亮点                                                                                          |
| -- | ------------------------------------------------------------------------ | ---- | --------------------------------------------------------------------------------------------- |
| 1  | [健康记忆与基础设施](#1-健康记忆与基础设施)                              | 2    | `health-memory`、`medical-record-organizer`——所有技能的统一数据层                            |
| 2  | [场景应用](#2-场景应用)                                                  | 7    | `diabetes-control-hub`、`hypertension-daily-copilot`、`mental-wellness-companion`             |
| 3  | [每日健康追踪](#3-每日健康追踪)                                          | 13   | `blood-pressure-tracker`、`sleep-analyzer`、`wearable-analysis-agent`、`weekly-health-digest` |
| 4  | [心理健康与危机干预](#4-心理健康与危机干预)                              | 12   | `crisis-detection-intervention-ai`、`adhd-daily-planner`、`grief-companion`                   |
| 5  | [慢性病与治疗管理](#5-慢性病与治疗管理)                                  | 10   | `chemo-side-effect-tracker`、`medication-reminder`、`post-surgery-recovery`                   |
| 6  | [生物医学数据库](#6-生物医学数据库)                                      | 23   | `pubmed-database`、`clinvar-database`、`kegg-database`、`uniprot-database`                    |
| 7  | [药理学与药物安全](#7-药理学与药物安全)                                  | 9    | `drug-interaction-checker`、`drug-label-lookup`、`drugbank-database`                          |
| 8  | [临床研究与试验](#8-临床研究与试验)                                      | 7    | `trial-eligibility-agent`、`clinical-trial-protocol-skill`、`clinical-diagnostic-reasoning`   |
| 9  | [基因组学与变异解读](#9-基因组学与变异解读)                              | 14   | `variant-interpretation-acmg`、`gwas-lookup`、`gwas-prs`                                      |
| 10 | [药物基因组学](#10-药物基因组学)                                         | 4    | `pharmgx-reporter`、`nutrigx_advisor`、`pharmacogenomics-agent`                               |
| 11 | [肿瘤学与精准医疗](#11-肿瘤学与精准医疗)                                | 13   | `tumor-heterogeneity-agent`、`digital-twin-clinical-agent`、`hrd-analysis-agent`              |
| 12 | [血液学与血液疾病](#12-血液学与血液疾病)                                 | 8    | `chip-clonal-hematopoiesis-agent`、`mpn-progression-monitor-agent`、`myeloma-mrd-agent`       |
| 13 | [免疫信息学](#13-免疫信息学)                                             | 4    | `bio-immunoinformatics-neoantigen-prediction`、`bio-immunoinformatics-mhc-binding-prediction` |
| 14 | [液体活检与 ctDNA](#14-液体活检与-ctdna)                                 | 8    | `bio-ctdna-mutation-detection`、`mrd-edge-detection-agent`、`liquid-biopsy-analytics-agent`   |
| 15 | [ToolUniverse 套件](#15-tooluniverse-套件)                               | 27   | 涵盖数据库、分析和报告的综合多工具研究工作流                                                  |
| 16 | [医学 NLP 与报告](#16-医学-nlp-与报告)                                   | 13   | `clinical-note-summarization`、`radgpt-radiology-reporter`、`checkup-report-interpreter`      |
| 17 | [科研与文献](#17-科研与文献)                                             | 11   | `literature-review`、`deep-research`、`pubmed-search`、`knowledge-synthesis`                  |
| 18 | [数据科学与可视化](#18-数据科学与可视化)                                 | 4    | `statistical-analysis`、`data-visualization-biomedical`、`exploratory-data-analysis`          |
| 19 | [综合健康与生活方式](#19-综合健康与生活方式)                             | 11   | `tcm-constitution-analyzer`、`travel-health-analyzer`、`food-database-query`                  |
| 20 | [工具与文档处理](#20-工具与文档处理)                                     | 5    | `markitdown`、`pdf-processing-pro`、`medical-research-toolkit`                                |

**共计：204 个技能**

---

## 完整技能目录

## 1. 健康记忆与基础设施


| 技能                          | 描述                                                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------- |
| [health-memory](skills/health-memory/) | 集中式健康记忆中枢——管理 memory/health/ 下的每日日志和按项目的纵向追踪文件。 |
| [medical-record-organizer](skills/medical-record-organizer/) | 结构化病历档案——自动将 PDF、扫描件和化验报告分类存储到按患者组织的目录中（影像、化验、病理、基因组、出院小结），并生成可导航的 INDEX.md 汇总。 |

## 2. 场景应用


| 技能                                                              | 描述                                                                                                                                                                           |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [annual-checkup-advisor](skills/annual-checkup-advisor/)                 | 编排年度体检解读：协调报告解析、化验解读、家族史分析、遗传风险评分、中医体质评估和指南查询。 |
| [caffeine-sleep-advisor](skills/caffeine-sleep-advisor/)                 | 分析咖啡因摄入与睡眠质量的关系：协调咖啡因追踪、睡眠分析和趋势关联。                     |
| [calorie-fitness-manager](skills/calorie-fitness-manager/)               | 管理每日热量平衡与运动追踪：协调 BMR/TDEE 计算、营养分析、食物查询、运动统计、趋势分析和 SMART 目标追踪。 |
| [diabetes-control-hub](skills/diabetes-control-hub/)                     | 全面管理糖尿病控制：协调血糖追踪、营养分析、运动关联、肾功能监测和并发症风险评估。         |
| [hypertension-daily-copilot](skills/hypertension-daily-copilot/)         | 提供全面的每日高血压管理：协调血压追踪、用药依从性、DASH 饮食评分、运动监测和趋势分析。   |
| [mental-wellness-companion](skills/mental-wellness-companion/)           | 提供每日心理健康支持：协调 PHQ-9/GAD-7 评估、危机检测、睡眠-情绪关联、运动处方和行为激活。 |
| [nutrition-supplement-optimizer](skills/nutrition-supplement-optimizer/) | 评估膳食营养缺口与补充剂安全性：协调营养分析、食物替代、补充剂相互作用检查、不良事件筛查和效果追踪。 |

## 3. 每日健康追踪


| 技能                                                    | 描述                                                                                                                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [blood-pressure-tracker](skills/blood-pressure-tracker/)       | 按 ACC/AHA 2017 指南记录和分级血压，检测晨峰现象，分析昼夜变异，生成月度统计。                                                                                                 |
| [caffeine-tracker](skills/caffeine-tracker/)                   | 追踪每日咖啡因摄入，利用半衰期衰减模型（t½=5h）计算残留咖啡因。                                                                                                               |
| [chronic-condition-monitor](skills/chronic-condition-monitor/) | 按中国临床指南监测多种慢性病指标（血压、血糖、糖化血红蛋白、血脂、尿酸、肌酐、eGFR、肝功能）。                                                                                 |
| [fitness-analyzer](skills/fitness-analyzer/)                   | 分析运动数据，识别锻炼模式，评估体能进展，提供个性化训练建议。支持与慢性病数据关联。                                                                                             |
| [health-trend-analyzer](skills/health-trend-analyzer/)         | 分析健康数据趋势与模式。关联药物、症状、体征、化验和其他健康指标。识别异常趋势和改善情况，提供数据驱动的洞察。支持交互式 HTML 可视化报告（ECharts）。 |
| [kidney-function-tracker](skills/kidney-function-tracker/)     | 使用 CKD-EPI 2021（无种族校正）公式追踪肾功能，CKD G1-G5 分期，白蛋白尿 A1-A3 分类，计算 eGFR 下降速率。                                                                       |
| [nutrition-analyzer](skills/nutrition-analyzer/)               | 分析营养数据，识别饮食模式，评估营养状态，提供个性化营养建议。支持与运动、睡眠和慢性病数据关联。                                                                                 |
| [sleep-analyzer](skills/sleep-analyzer/)                       | 分析睡眠数据，计算睡眠效率、质量评分（0-100）和睡眠阶段分布。                                                                                                                   |
| [tumor-marker-trend](skills/tumor-marker-trend/)               | 肿瘤标志物趋势追踪——记录 CEA/CA199/AFP 等标志物，支持趋势分析、突增检测和多标志物对比。                                                                                       |
| [tumor-journey-summary](skills/tumor-journey-summary/)         | 肿瘤诊疗历程时间线汇总（基于患者目录结构 + LLM 提取）。                                                                                                                         |
| [wearable-analysis-agent](skills/wearable-analysis-agent/)     | 分析可穿戴设备纵向传感器数据（心率、活动、睡眠），检测异常并提供个性化健康洞察。                                                                                                 |
| [weekly-health-digest](skills/weekly-health-digest/)           | 汇总过去 7 天的 health-memory 数据，生成叙述性周报，包含综合健康评分（0-100）、各领域摘要、跨领域关联和下周可行建议。                                                             |
| [weightloss-analyzer](skills/weightloss-analyzer/)             | 分析减重数据，计算代谢率，追踪能量赤字，管理减重阶段。                                                                                                                           |

## 4. 心理健康与危机干预


| 技能                                                                  | 描述                                                                                                                                                                           |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [adhd-daily-planner](skills/adhd-daily-planner/)                             | 时间感知友好的日程规划、执行功能支持和 ADHD 人群的日常结构。擅长现实时间估计、多巴胺导向任务设计和系统构建。 |
| [crisis-detection-intervention-ai](skills/crisis-detection-intervention-ai/) | 使用 NLP 和心理健康情感分析检测用户内容中的危机信号，实施安全干预协议。包含自杀意念检测、自动升级和危机资源路由。 |
| [crisis-response-protocol](skills/crisis-response-protocol/)                 | 在 AI 辅导中安全处理心理健康危机情境。实施危机检测、安全协议、紧急升级和自杀预防功能。 |
| [grief-companion](skills/grief-companion/)                                   | 富有同理心的丧亲支持、纪念创建、哀伤教育和康复旅程引导。擅长理解悲伤阶段、创建有意义的纪念和支持疗愈。 |
| [hrv-alexithymia-expert](skills/hrv-alexithymia-expert/)                     | 心率变异性生物指标与情绪觉察训练。 |
| [jungian-psychologist](skills/jungian-psychologist/)                         | 荣格分析心理学专家：深度心理学、阴影工作、原型分析、梦的解析、积极想象、成瘾/康复的荣格视角以及个体化过程。 |
| [mental-health-analyzer](skills/mental-health-analyzer/)                     | 分析心理健康数据，识别心理模式，评估心理健康状态，提供个性化心理健康建议。支持与睡眠、运动和营养数据关联。 |
| [modern-drug-rehab-computer](skills/modern-drug-rehab-computer/)             | 成瘾康复环境的综合知识系统，支持住院和门诊（IOP/PHP）患者。精通循证治疗方法（CBT、DBT、MI）。 |
| [psychologist-analyst](skills/psychologist-analyst/)                         | 心理分析与咨询支持。 |
| [recovery-community-moderator](skills/recovery-community-moderator/)         | 创伤知情的 AI 管理员，用于成瘾康复社区。应用减害原则，尊重十二步传统，区分健康冲突与滥用，检测危机帖子。 |
| [speech-pathology-ai](skills/speech-pathology-ai/)                           | 专业语言病理学家：AI 辅助言语治疗、音素分析、构音可视化、嗓音障碍、流畅性干预和辅助沟通。 |
| [occupational-health-analyzer](skills/occupational-health-analyzer/)         | 分析职业健康数据，识别工作相关健康风险，评估职业健康状态，提供个性化职业健康建议。 |

## 5. 慢性病与治疗管理


| 技能                                                    | 描述                                                                                                                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [cancer-nutrition-coach](skills/cancer-nutrition-coach/)       | 癌症患者营养评估与饮食方案生成（NRS-2002 评分 + LLM 营养建议）。 |
| [chemo-side-effect-tracker](skills/chemo-side-effect-tracker/) | 化疗副作用追踪——按 CTCAE v5.0 分级记录副作用，支持周期对比、毒性趋势分析和综合毒性报告。 |
| [emergency-card](skills/emergency-card/)                       | 生成紧急医疗信息摘要卡。提取关键信息（过敏、用药、急症、植入物），支持多格式输出（JSON、文本、二维码）。 |
| [family-health-analyzer](skills/family-health-analyzer/)       | 分析家族病史，评估遗传风险，识别家族健康模式，提供个性化预防建议。 |
| [follow-up-reminder](skills/follow-up-reminder/)               | 复诊提醒管理工具——支持疾病特定的随访项目、定期提醒和完成追踪。 |
| [goal-analyzer](skills/goal-analyzer/)                         | 分析健康目标数据，识别目标模式，评估目标进度，提供个性化目标管理建议。 |
| [medication-reminder](skills/medication-reminder/)             | 管理用药计划，追踪用药依从性（实际服药次数 vs. 处方剂量）。 |
| [post-surgery-recovery](skills/post-surgery-recovery/)         | 术后康复追踪——记录引流量、伤口状态、疼痛、活动和饮食恢复；支持里程碑检查和复诊提醒。 |
| [rehabilitation-analyzer](skills/rehabilitation-analyzer/)     | 分析康复训练数据，识别恢复模式，评估康复进度，提供个性化恢复建议。 |
| [supplement-manager](skills/supplement-manager/)               | 补充剂管理——管理每日补充剂方案，追踪摄入记录和依从性，RxNorm 相互作用检查，智能服用时间建议。 |

## 6. 生物医学数据库


| 技能                                                | 描述                                                                                                                                                       |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [biorxiv-database](skills/biorxiv-database/)               | bioRxiv 预印本服务器的高效数据库检索工具。 |
| [cbioportal-database](skills/cbioportal-database/)         | 查询 cBioPortal 癌症基因组学数据，包括体细胞突变、拷贝数变异、基因表达和数百个癌症研究的生存数据。 |
| [clinicaltrials-database](skills/clinicaltrials-database/) | 通过 API v2 查询 ClinicalTrials.gov。按疾病、药物、地点、状态或分期搜索试验，通过 NCT ID 获取试验详情。 |
| [clinpgx-database](skills/clinpgx-database/)               | 访问 ClinPGx 药物基因组学数据（PharmGKB 的后续项目）。查询基因-药物相互作用、CPIC 指南、等位基因功能，用于精准医疗和基因型指导用药。 |
| [clinvar-database](skills/clinvar-database/)               | 查询 NCBI ClinVar 变异临床意义。按基因/位置搜索，解读致病性分类，通过 E-utilities API 或 FTP 访问，注释 VCF。 |
| [cosmic-database](skills/cosmic-database/)                 | 访问 COSMIC 癌症突变数据库。查询体细胞突变、癌症基因普查、突变特征、基因融合。需要认证。 |
| [ensembl-database](skills/ensembl-database/)               | 查询 Ensembl 基因组数据库 REST API，支持 250+ 物种。基因查找、序列检索、变异分析、比较基因组学、直系同源物、VEP 预测。 |
| [fda-database](skills/fda-database/)                       | 查询 openFDA API，获取药品、器械、不良事件、召回、监管审批（510k、PMA）、物质标识（UNII）。 |
| [gene-database](skills/gene-database/)                     | 通过 E-utilities/Datasets API 查询 NCBI Gene。按符号/ID 搜索，检索基因信息（RefSeqs、GO、位置、表型），批量查找。 |
| [geo-database](skills/geo-database/)                       | 访问 NCBI GEO 基因表达/基因组学数据。搜索和下载微阵列和 RNA-seq 数据集（GSE、GSM、GPL），检索 SOFT/Matrix 文件。 |
| [gnomad-database](skills/gnomad-database/)                 | 查询 gnomAD 群体等位基因频率、变异约束评分（pLI、LOEUF）和功能缺失不耐受性。 |
| [gwas-database](skills/gwas-database/)                     | 查询 NHGRI-EBI GWAS Catalog 的 SNP-性状关联。按 rs ID、疾病/性状、基因搜索变异，获取 p 值和汇总统计。 |
| [hmdb-database](skills/hmdb-database/)                     | 访问人类代谢组数据库（220K+ 代谢物）。按名称/ID/结构搜索，获取化学性质、生物标志物数据、NMR/MS 谱图、通路。 |
| [interpro-database](skills/interpro-database/)             | 查询 InterPro 蛋白质家族、结构域和功能位点注释。 |
| [kegg-database](skills/kegg-database/)                     | 直接 REST API 访问 KEGG（仅限学术用途）。 |
| [monarch-database](skills/monarch-database/)               | 查询 Monarch Initiative 知识图谱，获取跨物种的疾病-基因-表型关联。 |
| [openalex-database](skills/openalex-database/)             | 使用 OpenAlex 数据库查询和分析学术文献。 |
| [opentargets-database](skills/opentargets-database/)       | 查询 Open Targets 平台的靶点-疾病关联、药物靶点发现、成药性/安全性数据、遗传学/组学证据、已知药物。 |
| [pubchem-database](skills/pubchem-database/)               | 通过 PUG-REST API/PubChemPy 查询 PubChem（110M+ 化合物）。按名称/CID/SMILES 搜索，获取性质，相似性/子结构搜索，生物活性。 |
| [pubmed-database](skills/pubmed-database/)                 | 直接 REST API 访问 PubMed。高级布尔/MeSH 查询，E-utilities API，批量处理，引用管理。 |
| [reactome-database](skills/reactome-database/)             | 查询 Reactome REST API 进行通路分析、富集分析、基因-通路映射、疾病通路、分子相互作用、表达分析。 |
| [string-database](skills/string-database/)                 | 查询 STRING API 获取蛋白质-蛋白质相互作用（59M 蛋白质，20B 相互作用）。网络分析，GO/KEGG 富集，相互作用发现，5000+ 物种。 |
| [uniprot-database](skills/uniprot-database/)               | 直接 REST API 访问 UniProt。蛋白质搜索、FASTA 检索、ID 映射、Swiss-Prot/TrEMBL。 |

## 7. 药理学与药物安全


| 技能                                                  | 描述                                                                                                                                                       |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [drug-adverse-event-query](skills/drug-adverse-event-query/) | 通过 openFDA FAERS API 查询药物不良反应报告（频率、严重程度、结局）。 |
| [drug-discovery-search](skills/drug-discovery-search/)       | 端到端药物发现平台，整合 ChEMBL 化合物、DrugBank、靶点和 FDA 标签。Valyu 自然语言驱动。 |
| [drug-interaction-checker](skills/drug-interaction-checker/) | 检查药物-药物相互作用（基于 RxNorm API + FDA 标签补充）。 |
| [drug-label-lookup](skills/drug-label-lookup/)               | 通过 openFDA API 查询药品说明书（适应症、用法用量、警告、禁忌、不良反应、药物相互作用）。 |
| [drug-labels-search](skills/drug-labels-search/)             | 以自然语言搜索 FDA 药品说明书。Valyu 驱动的官方药物信息、适应症和安全数据。 |
| [drug-name-resolver](skills/drug-name-resolver/)             | 将药物名称（通用名/商品名/研发代号）标准化为 RxNorm RxCUI，并获取药物分类信息。 |
| [drug-photo](skills/drug-photo/)                             | 药物照片转个性化 PGx 剂量卡——通过 Claude 视觉识别药片，获取基因型指导建议。 |
| [drugbank-database](skills/drugbank-database/)               | 访问和分析 DrugBank 综合药物信息，包括药物性质、相互作用、靶点、通路、化学结构和药理学数据。 |
| [drugbank-search](skills/drugbank-search/)                   | 以自然语言搜索 DrugBank 综合药物数据库。Valyu 驱动的药物机制、相互作用和安全数据。 |

## 8. 临床研究与试验


| 技能                                                            | 描述                                                                                                                                                       |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [clinical-decision-support](skills/clinical-decision-support/)         | 为制药和临床研究环境生成专业临床决策支持（CDS）文件，包括患者队列分析和治疗建议报告。支持 GRADE 证据分级、统计分析、生物标志物整合。 |
| [clinical-diagnostic-reasoning](skills/clinical-diagnostic-reasoning/) | 通过系统性错误分析和上下文算法应用，识别和纠正医学决策中的认知偏差。 |
| [clinical-trial-protocol-skill](skills/clinical-trial-protocol-skill/) | 生成医疗器械或药物的临床试验方案。 |
| [clinical-trial-search](skills/clinical-trial-search/)                 | 搜索 ClinicalTrials.gov 临床试验，支持按疾病、干预、地区、试验状态多维度筛选。 |
| [clinical-trials-search](skills/clinical-trials-search/)               | 以自然语言搜索 ClinicalTrials.gov。Valyu 语义搜索驱动的临床试验、入组和结果查找。 |
| [trial-eligibility-agent](skills/trial-eligibility-agent/)             | 解析试验方案和患者数据，按标准逐项生成 MET/NOT/UNKNOWN 判定，附带证据和缺口分析，用于临床试验筛选。 |
| [trialgpt-matching](skills/trialgpt-matching/)                         | 试验短名单——AI 驱动的患者-试验匹配。 |

## 9. 基因组学与变异解读


| 技能                                                                                              | 描述                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bio-clinical-databases-clinvar-lookup](skills/bio-clinical-databases-clinvar-lookup/)                   | 通过 REST API 或本地 VCF 查询 ClinVar 变异致病性分类、审查状态和疾病关联。 |
| [bio-clinical-databases-dbsnp-queries](skills/bio-clinical-databases-dbsnp-queries/)                     | 查询 dbSNP 进行 rsID 查找、变异注释和与其他数据库的交叉引用。 |
| [bio-clinical-databases-gnomad-frequencies](skills/bio-clinical-databases-gnomad-frequencies/)           | 查询 gnomAD 群体等位基因频率以评估变异稀有性。 |
| [bio-clinical-databases-hla-typing](skills/bio-clinical-databases-hla-typing/)                           | 使用 OptiType、HLA-HD 或 arcasHLA 从 NGS 数据推断 HLA 分型，用于免疫基因组学应用。 |
| [bio-clinical-databases-myvariant-queries](skills/bio-clinical-databases-myvariant-queries/)             | 查询 myvariant.info API 获取来自多个数据库（ClinVar、gnomAD、dbSNP、COSMIC 等）的聚合变异注释。 |
| [bio-clinical-databases-polygenic-risk](skills/bio-clinical-databases-polygenic-risk/)                   | 使用 PRSice-2、LDpred2 或 PRS-CS 从 GWAS 汇总统计计算多基因风险评分。 |
| [bio-clinical-databases-somatic-signatures](skills/bio-clinical-databases-somatic-signatures/)           | 使用 SigProfiler 或 MutationalPatterns 从体细胞变异中提取和分析突变特征。 |
| [bio-clinical-databases-tumor-mutational-burden](skills/bio-clinical-databases-tumor-mutational-burden/) | 从 panel 或 WES 数据计算肿瘤突变负荷，进行适当的标准化处理并应用临床阈值。 |
| [bio-clinical-databases-variant-prioritization](skills/bio-clinical-databases-variant-prioritization/)   | 按致病性、群体频率和临床证据对变异进行过滤和优先排序，用于罕见病分析。 |
| [gwas-lookup](skills/gwas-lookup/)                                                                       | 跨 9 个基因组数据库的联合变异查找——GWAS Catalog、Open Targets、PheWeb（UKB、FinnGen、BBJ）、GTEx、eQTL Catalogue。 |
| [gwas-prs](skills/gwas-prs/)                                                                             | 使用 PGS Catalog 从消费级基因检测数据计算多基因风险评分。 |
| [multi-ancestry-prs-agent](skills/multi-ancestry-prs-agent/)                                             | AI 驱动的多祖源多基因风险评分计算与优化，实现跨全球多样化人群的公平疾病风险预测。 |
| [variant-interpretation-acmg](skills/variant-interpretation-acmg/)                                       | 按 ACMG（美国医学遗传学与基因组学学会）指南对遗传变异进行分类。 |
| [varcadd-pathogenicity](skills/varcadd-pathogenicity/)                                                   | 使用 CADD 和其他计算预测器进行变异致病性评分。 |

## 10. 药物基因组学


| 技能                                                                                | 描述                                                                                                                                                       |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bio-clinical-databases-pharmacogenomics](skills/bio-clinical-databases-pharmacogenomics/) | 查询 PharmGKB 和 CPIC 获取药物-基因相互作用、药物基因组学注释和用药指南。 |
| [nutrigx_advisor](skills/nutrigx_advisor/)                                                 | 从消费级基因检测数据（23andMe、AncestryDNA）生成个性化营养报告。将营养相关 SNP 转化为膳食和补充剂指导。 |
| [pharmacogenomics-agent](skills/pharmacogenomics-agent/)                                   | AI 驱动的药物基因组学分析，利用多组学数据实现精准用药和不良事件预测。 |
| [pharmgx-reporter](skills/pharmgx-reporter/)                                               | 从消费级基因检测数据（23andMe/AncestryDNA）生成药物基因组学报告——12 个基因、31 个 SNP、51 种药物。 |

## 11. 肿瘤学与精准医疗


| 技能                                                                        | 描述                                                                                                                                                       |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [autonomous-oncology-agent](skills/autonomous-oncology-agent/)                     | 精准肿瘤学研究与治疗推荐。 |
| [cancer-metabolism-agent](skills/cancer-metabolism-agent/)                         | AI 驱动的癌症代谢重编程分析，包括 Warburg 效应、谷氨酰胺成瘾、脂质代谢和代谢脆弱性治疗靶向。 |
| [cellular-senescence-agent](skills/cellular-senescence-agent/)                     | AI 驱动的细胞衰老分析，用于衰老研究、癌症治疗响应和衰老细胞清除药物开发。 |
| [chromosomal-instability-agent](skills/chromosomal-instability-agent/)             | AI 驱动的染色体不稳定性（CIN）特征分析，用于癌症预后、免疫治疗响应预测和治疗脆弱性识别。 |
| [digital-twin-clinical-agent](skills/digital-twin-clinical-agent/)                 | AI 驱动的患者数字孪生创建，用于临床试验模拟、治疗结果预测和个性化医疗，整合真实世界数据和多组学数据。 |
| [hrd-analysis-agent](skills/hrd-analysis-agent/)                                   | AI 驱动的同源重组缺陷（HRD）分析，使用基因组瘢痕特征和 BRCA 通路评估预测 PARP 抑制剂响应。 |
| [immune-checkpoint-combination-agent](skills/immune-checkpoint-combination-agent/) | AI 驱动的免疫检查点抑制剂最优组合预测分析，基于肿瘤微环境、生物标志物和分子谱分析。 |
| [microbiome-cancer-agent](skills/microbiome-cancer-agent/)                         | AI 驱动的微生物组-癌症相互作用分析，包括肿瘤微生物组图谱、免疫治疗响应预测和微生物组靶向治疗机会。 |
| [nk-cell-therapy-agent](skills/nk-cell-therapy-agent/)                             | AI 驱动的 NK 细胞癌症免疫治疗设计，包括 CAR-NK 工程、记忆样 NK 生成和 KIR/HLA 匹配优化。 |
| [precision-oncology-agent](skills/precision-oncology-agent/)                       | 融合基因组变异、病理发现和临床背景，为肿瘤委员会审查草拟有证据支持的治疗方案。 |
| [tumor-clonal-evolution-agent](skills/tumor-clonal-evolution-agent/)               | AI 驱动的肿瘤克隆架构、亚克隆动态和进化轨迹分析，基于多区域测序和纵向液体活检数据。 |
| [tumor-heterogeneity-agent](skills/tumor-heterogeneity-agent/)                     | AI 驱动的肿瘤内异质性分析，用于克隆架构重建、亚克隆进化追踪和治疗耐药预测。 |
| [tumor-mutational-burden-agent](skills/tumor-mutational-burden-agent/)             | 跨平台计算和标准化肿瘤突变负荷（TMB），预测免疫治疗响应。 |

## 12. 血液学与血液疾病


| 技能                                                                | 描述                                                                                                                                                       |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bone-marrow-ai-agent](skills/bone-marrow-ai-agent/)                       | AI 驱动的骨髓形态分析、细胞分类和血液学疾病诊断，使用深度学习处理骨髓穿刺和活检图像。 |
| [chip-clonal-hematopoiesis-agent](skills/chip-clonal-hematopoiesis-agent/) | AI 驱动的不确定潜能克隆性造血（CHIP）检测、风险分层和心血管/恶性肿瘤风险预测。 |
| [coagulation-thrombosis-agent](skills/coagulation-thrombosis-agent/)       | AI 驱动的凝血障碍分析、血栓风险预测、抗凝管理和血小板功能评估。 |
| [cytokine-storm-analysis-agent](skills/cytokine-storm-analysis-agent/)     | AI 驱动的细胞因子释放综合征（CRS）和细胞因子风暴分析，用于免疫治疗和感染性疾病的预测、监测和管理。 |
| [hemoglobinopathy-analysis-agent](skills/hemoglobinopathy-analysis-agent/) | AI 驱动的血红蛋白病分析，包括镰状细胞病、地中海贫血和变异血红蛋白，使用 HPLC、电泳和分子数据。 |
| [mpn-progression-monitor-agent](skills/mpn-progression-monitor-agent/)     | AI 驱动的骨髓增殖性肿瘤监测，用于 PV、ET 和骨髓纤维化的疾病进展预测、治疗响应追踪和转化风险评估。 |
| [mpn-research-assistant](skills/mpn-research-assistant/)                   | 骨髓增殖性肿瘤（MPN）研究专家，涵盖 JAK2/CALR/MPL 突变、骨髓纤维化、真性红细胞增多症、原发性血小板增多症。 |
| [myeloma-mrd-agent](skills/myeloma-mrd-agent/)                             | AI 驱动的多发性骨髓瘤微小残留病（MRD）分析，使用新一代流式细胞术、NGS 和质谱方法。 |

## 13. 免疫信息学


| 技能                                                                                          | 描述                                                                                                                                                       |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bio-immunoinformatics-epitope-prediction](skills/bio-immunoinformatics-epitope-prediction/)         | 使用 BepiPred、IEDB 工具和基于结构的方法预测 B 细胞和 T 细胞表位，用于疫苗和抗体设计。 |
| [bio-immunoinformatics-immunogenicity-scoring](skills/bio-immunoinformatics-immunogenicity-scoring/) | 使用多因子模型（结合 MHC 结合、加工、表达和序列特征）对新抗原和表位进行免疫原性评分和优先排序。 |
| [bio-immunoinformatics-mhc-binding-prediction](skills/bio-immunoinformatics-mhc-binding-prediction/) | 使用 MHCflurry 和 NetMHCpan 神经网络模型预测肽段-MHC I 类和 II 类结合亲和力。 |
| [bio-immunoinformatics-neoantigen-prediction](skills/bio-immunoinformatics-neoantigen-prediction/)   | 使用 pVACtools 从体细胞突变中识别肿瘤新抗原，用于个性化癌症免疫治疗。 |

## 14. 液体活检与 ctDNA


| 技能                                                                | 描述                                                                                                                                                       |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bio-ctdna-mutation-detection](skills/bio-ctdna-mutation-detection/)       | 使用针对低等位基因频率优化的变异调用器和基于 UMI 的错误抑制，在循环肿瘤 DNA 中检测体细胞突变。 |
| [bio-liquid-biopsy-pipeline](skills/bio-liquid-biopsy-pipeline/)           | 从血浆测序到肿瘤监测的游离 DNA 分析流水线。 |
| [bio-longitudinal-monitoring](skills/bio-longitudinal-monitoring/)         | 使用连续液体活检样本追踪 ctDNA 动态变化，用于治疗响应监测。 |
| [bio-methylation-based-detection](skills/bio-methylation-based-detection/) | 使用 cfMeDIP-seq 或亚硫酸氢盐测序（MethylDackel）分析 cfDNA 甲基化模式用于癌症检测。 |
| [bio-tumor-fraction-estimation](skills/bio-tumor-fraction-estimation/)     | 使用 ichorCNA 从浅全基因组测序估算循环肿瘤 DNA 比例。 |
| [ctdna-dynamics-mrd-agent](skills/ctdna-dynamics-mrd-agent/)               | AI 驱动的循环肿瘤 DNA 动态分析，用于分子残留病检测、治疗响应监测和早期复发预测。 |
| [liquid-biopsy-analytics-agent](skills/liquid-biopsy-analytics-agent/)     | 液体活检数据（ctDNA、CTC）综合分析，用于癌症检测、MRD 监测和响应追踪。 |
| [mrd-edge-detection-agent](skills/mrd-edge-detection-agent/)               | 使用 MRD-EDGE 深度学习实现超灵敏 AI 分子残留病检测，达到亚 0.001% VAF ctDNA 检测水平，用于早期复发预测。 |

## 15. ToolUniverse 套件


| 技能                                                                                              | 描述                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [tooluniverse-adverse-event-detection](skills/tooluniverse-adverse-event-detection/)                     | 使用 FDA FAERS 数据、药品说明书、不均衡分析（PRR、ROR、IC）和生物医学证据检测和分析药物不良事件信号。 |
| [tooluniverse-cancer-variant-interpretation](skills/tooluniverse-cancer-variant-interpretation/)         | 对癌症中的体细胞突变提供全面的临床解读。 |
| [tooluniverse-clinical-guidelines](skills/tooluniverse-clinical-guidelines/)                             | 搜索和检索来自 12+ 权威来源的临床实践指南，包括 NICE、WHO、ADA、AHA/ACC、NCCN、SIGN、CPIC。 |
| [tooluniverse-clinical-trial-design](skills/tooluniverse-clinical-trial-design/)                         | 使用 ToolUniverse 进行策略性临床试验设计可行性评估。 |
| [tooluniverse-clinical-trial-matching](skills/tooluniverse-clinical-trial-matching/)                     | AI 驱动的精准医疗和肿瘤学患者-试验匹配。 |
| [tooluniverse-disease-research](skills/tooluniverse-disease-research/)                                   | 使用 100+ ToolUniverse 工具生成全面的疾病研究报告。 |
| [tooluniverse-drug-drug-interaction](skills/tooluniverse-drug-drug-interaction/)                         | 全面的药物-药物相互作用（DDI）预测和风险评估。 |
| [tooluniverse-drug-repurposing](skills/tooluniverse-drug-repurposing/)                                   | 使用 ToolUniverse 识别药物再利用候选物，支持基于靶点、基于化合物和基于疾病的策略。 |
| [tooluniverse-drug-research](skills/tooluniverse-drug-research/)                                         | 生成全面的药物研究报告，包含化合物消歧、证据分级和强制完整性检查。 |
| [tooluniverse-drug-target-validation](skills/tooluniverse-drug-target-validation/)                       | 早期药物发现阶段的全面计算靶点验证。 |
| [tooluniverse-gwas-drug-discovery](skills/tooluniverse-gwas-drug-discovery/)                             | 将 GWAS 信号转化为可操作的药物靶点和再利用机会。 |
| [tooluniverse-gwas-finemapping](skills/tooluniverse-gwas-finemapping/)                                   | 使用统计精细定位和位点-基因预测识别和优先排序 GWAS 位点的因果变异。 |
| [tooluniverse-gwas-snp-interpretation](skills/tooluniverse-gwas-snp-interpretation/)                     | 通过聚合多个数据库的证据解读来自 GWAS 研究的遗传变异（SNP）。 |
| [tooluniverse-gwas-study-explorer](skills/tooluniverse-gwas-study-explorer/)                             | 比较 GWAS 研究，执行荟萃分析，评估跨队列的重复性。 |
| [tooluniverse-gwas-trait-to-gene](skills/tooluniverse-gwas-trait-to-gene/)                               | 使用 GWAS Catalog（500,000+ 关联）和 Open Targets Genetics 的 GWAS 数据发现与疾病和性状相关的基因。 |
| [tooluniverse-immune-repertoire-analysis](skills/tooluniverse-immune-repertoire-analysis/)               | T 细胞和 B 细胞受体测序数据的全面免疫组库分析。 |
| [tooluniverse-immunotherapy-response-prediction](skills/tooluniverse-immunotherapy-response-prediction/) | 使用多生物标志物整合预测患者对免疫检查点抑制剂（ICI）的响应。 |
| [tooluniverse-infectious-disease](skills/tooluniverse-infectious-disease/)                               | 传染病爆发的快速病原体鉴定和药物再利用分析。 |
| [tooluniverse-literature-deep-research](skills/tooluniverse-literature-deep-research/)                   | 进行全面的文献研究，包含靶点消歧、证据分级和结构化主题提取。 |
| [tooluniverse-network-pharmacology](skills/tooluniverse-network-pharmacology/)                           | 构建和分析化合物-靶点-疾病网络，用于药物再利用、多药理学发现和系统药理学。 |
| [tooluniverse-pharmacovigilance](skills/tooluniverse-pharmacovigilance/)                                 | 从 FDA 不良事件报告、标签警告和药物基因组学数据中分析药物安全信号。 |
| [tooluniverse-polygenic-risk-score](skills/tooluniverse-polygenic-risk-score/)                           | 使用 GWAS 汇总统计为复杂疾病构建和解读多基因风险评分（PRS）。 |
| [tooluniverse-precision-medicine-stratification](skills/tooluniverse-precision-medicine-stratification/) | 通过整合基因组、临床和治疗数据实现精准医疗的全面患者分层。 |
| [tooluniverse-precision-oncology](skills/tooluniverse-precision-oncology/)                               | 基于分子谱分析为癌症患者提供可操作的治疗建议。 |
| [tooluniverse-rare-disease-diagnosis](skills/tooluniverse-rare-disease-diagnosis/)                       | 基于表型和遗传数据为疑似罕见病患者提供鉴别诊断。 |
| [tooluniverse-variant-analysis](skills/tooluniverse-variant-analysis/)                                   | 生产级 VCF 处理、变异注释、突变分析和结构变异（SV/CNV）解读。 |
| [tooluniverse-variant-interpretation](skills/tooluniverse-variant-interpretation/)                       | 从原始变异调用到 ACMG 分类建议的系统性临床变异解读，包含结构影响分析。 |

## 16. 医学 NLP 与报告


| 技能                                                        | 描述                                                                                                                                                       |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [chatehr-clinician-assistant](skills/chatehr-clinician-assistant/) | EHR 对话助手，用于临床工作流。 |
| [checkup-report-interpreter](skills/checkup-report-interpreter/)   | 体检报告智能解读（PDF 解析 + LLM 异常识别和健康建议）。 |
| [clinical-nlp-extractor](skills/clinical-nlp-extractor/)           | 使用正则、规则或 LLM 封装从非结构化临床文本中提取医学实体（疾病、药物、手术）。 |
| [clinical-note-summarization](skills/clinical-note-summarization/) | 将原始临床记录结构化为 SOAP 格式摘要，明确标注矛盾、缺失数据和 ICD 关联评估。 |
| [clinical-reports](skills/clinical-reports/)                       | 撰写全面的临床报告，包括病例报告（CARE 指南）、诊断报告、临床试验报告（ICH-E3）和患者文档（SOAP、H&P、出院小结）。 |
| [lab-results](skills/lab-results/)                                 | 化验结果解读与追踪，用于医疗工作流。 |
| [medical-entity-extractor](skills/medical-entity-extractor/)       | 从患者消息中提取医学实体（症状、药物、化验值、诊断）。 |
| [medical-imaging-review](skills/medical-imaging-review/)           | 医学影像审阅与分析。 |
| [multimodal-medical-imaging](skills/multimodal-medical-imaging/)   | 使用多模态 LLM 分析医学影像（X 光、MRI、CT），识别异常并生成报告。 |
| [patiently-ai](skills/patiently-ai/)                               | 为患者简化医学文档。 |
| [prior-auth-review-skill](skills/prior-auth-review-skill/)         | 自动化支付方对预授权（PA）申请的审核。 |
| [radgpt-radiology-reporter](skills/radgpt-radiology-reporter/)     | 放射学报告生成与解读。 |
| [treatment-plans](skills/treatment-plans/)                         | 为所有临床专科生成简洁、聚焦的 LaTeX/PDF 格式医学治疗计划。 |

## 17. 科研与文献


| 技能                                                | 描述                                                                                                                                                       |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [biomedical-search](skills/biomedical-search/)             | 综合生物医学信息搜索，结合 PubMed、预印本、临床试验和 FDA 药品说明书。Valyu 语义搜索驱动。 |
| [citation-management](skills/citation-management/)         | 学术研究的全面引用管理。 |
| [deep-research](skills/deep-research/)                     | 对任何主题执行自主多步骤深度研究。 |
| [knowledge-synthesis](skills/knowledge-synthesis/)         | 将来自多个来源的搜索结果合成为连贯、去重的答案，并附带来源归属。 |
| [leads-literature-mining](skills/leads-literature-mining/) | 自动化文献综述与挖掘。 |
| [literature-review](skills/literature-review/)             | 使用多个学术数据库（PubMed、arXiv、bioRxiv、Semantic Scholar 等）进行全面系统的文献综述。 |
| [literature-search](skills/literature-search/)             | 跨 PubMed、arXiv、bioRxiv、medRxiv 的全面科学文献搜索。Valyu 语义搜索驱动的自然语言查询。 |
| [medrxiv-search](skills/medrxiv-search/)                   | 以自然语言搜索 medRxiv 医学预印本。Valyu 语义搜索驱动。 |
| [pubmed-abstract-reader](skills/pubmed-abstract-reader/)   | 通过 PMID 批量获取 PubMed 文章摘要、作者和期刊信息。 |
| [pubmed-search](skills/pubmed-search/)                     | 智能 PubMed 文献检索：3 层 LLM 渐进式查询 + 证据桶分类 + 分层抽样，获取高质量临床文献。 |
| [research-lookup](skills/research-lookup/)                 | 通过 OpenRouter 使用 Perplexity 的 Sonar Pro Search 或 Sonar Reasoning Pro 模型查找最新研究信息。 |

## 18. 数据科学与可视化


| 技能                                                            | 描述                                                                                                                                                       |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [data-stats-analysis](skills/data-stats-analysis/)                     | 使用 scipy 和 statsmodels 执行统计检验、假设检验、相关性分析和多重检验校正。适用于任何 LLM 提供商。 |
| [data-visualization-biomedical](skills/data-visualization-biomedical/) | 用于生物医学和基因组学数据的出版级可视化。 |
| [exploratory-data-analysis](skills/exploratory-data-analysis/)         | 对科学数据文件执行全面的探索性数据分析，支持 200+ 种文件格式。 |
| [statistical-analysis](skills/statistical-analysis/)                   | 统计分析工具包。假设检验（t 检验、ANOVA、卡方检验）、回归、相关性、贝叶斯统计、功效分析、假设检查、APA 报告。 |

## 19. 综合健康与生活方式


| 技能                                                    | 描述                                                                                                                                                       |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [care-coordination](skills/care-coordination/)                 | 医疗工作流中的护理协调代理。 |
| [claims-appeals](skills/claims-appeals/)                       | 医疗工作流中的理赔申诉代理。 |
| [ehr-fhir-integration](skills/ehr-fhir-integration/)           | 使用 HL7 FHIR 标准处理电子健康记录（EHR）的综合工具。 |
| [fhir-developer-skill](skills/fhir-developer-skill/)           | 医疗互操作性 FHIR 开发工具包。 |
| [food-database-query](skills/food-database-query/)             | 综合食物营养数据库，支持搜索、对比、推荐和自动热量计算。 |
| [oral-health-analyzer](skills/oral-health-analyzer/)           | 分析口腔健康数据，识别牙科问题，评估口腔健康状态，提供个性化口腔健康建议。 |
| [sexual-health-analyzer](skills/sexual-health-analyzer/)       | 全面的性健康数据分析，包括 IIEF-5 评分、性病筛查管理、避孕评估和跨领域关联分析。 |
| [skin-health-analyzer](skills/skin-health-analyzer/)           | 分析皮肤健康数据，识别皮肤问题，评估皮肤健康状态，提供个性化皮肤健康建议。 |
| [sleep-optimizer](skills/sleep-optimizer/)                     | 基于睡眠指标、咖啡因数据、屏幕时间和运动时间，生成优先排序的个性化睡眠改善建议。 |
| [tcm-constitution-analyzer](skills/tcm-constitution-analyzer/) | 分析中医体质数据，识别体质类型，评估体质特征，提供个性化养生建议。 |
| [travel-health-analyzer](skills/travel-health-analyzer/)       | 分析旅行健康数据，评估目的地健康风险，提供疫苗建议，生成多语言紧急医疗信息卡。整合 WHO/CDC 数据。 |

## 20. 工具与文档处理


| 技能                                                  | 描述                                                                                                                                                       |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [markitdown](skills/markitdown/)                             | 将文件和办公文档转换为 Markdown。支持 PDF、DOCX、PPTX、XLSX、图片（OCR）、音频（转录）、HTML、CSV、JSON、XML、ZIP、YouTube URL、EPub 等。 |
| [medical-research-toolkit](skills/medical-research-toolkit/) | 查询 14+ 个生物医学数据库，用于药物再利用、靶点发现、临床试验和文献研究。 |
| [pdf](skills/pdf/)                                           | 处理 PDF 文件的通用技能。 |
| [pdf-processing](skills/pdf-processing/)                     | 从 PDF 文件提取文本和表格，填写表单，合并文档。 |
| [pdf-processing-pro](skills/pdf-processing-pro/)             | 生产级 PDF 处理：表单、表格、OCR、验证和批量操作。 |

---

## 场景应用

7 个场景技能将多个子技能编排成完整的临床工作流，将用户的单一提示转化为协调的多代理健康会话。

`diabetes-control-hub` 场景展示了子技能如何端到端串联：

```mermaid
graph LR
    A[用户输入] --> B[chronic-condition-monitor]
    B --> C[nutrition-analyzer]
    C --> D[food-database-query]
    D --> E[fitness-analyzer]
    E --> F[health-trend-analyzer]
    F --> G[health-memory]
    G --> H[每日简报]
```


| 场景                                                              | 编排内容                                                                                                       |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| [annual-checkup-advisor](skills/annual-checkup-advisor/)                 | 体检报告解析、化验解读、纵向趋势分析和个性化筛查提醒。                                                         |
| [caffeine-sleep-advisor](skills/caffeine-sleep-advisor/)                 | 咖啡因摄入追踪、睡眠质量分析、昼夜节律优化和行为提醒生成。                                                     |
| [calorie-fitness-manager](skills/calorie-fitness-manager/)               | 热量记录、食物数据库查询、运动追踪、体重趋势分析和目标调整膳食规划。                                           |
| [diabetes-control-hub](skills/diabetes-control-hub/)                     | 血糖监测、营养分析、食物数据库查询、运动追踪、趋势分析和每日简报合成。                                         |
| [hypertension-daily-copilot](skills/hypertension-daily-copilot/)         | 血压记录、用药依从性追踪、钠/饮食评估、压力关联和预警升级。                                                     |
| [mental-wellness-companion](skills/mental-wellness-companion/)           | 情绪日记、睡眠质量关联、压力模式检测、CBT 导向建议和每周健康摘要。                                             |
| [nutrition-supplement-optimizer](skills/nutrition-supplement-optimizer/) | 膳食摄入分析、微量营养素缺口检测、补充剂相互作用检查和个性化补充剂方案推荐。                                   |

---

## 健康记忆系统

所有 VitaClaw 健康技能共享 `memory/health/` 下的统一记忆布局：

```
memory/health/
├── _health-profile.md              # 长期健康基线
├── daily/                           # 每日日志（每天一个文件）
│   └── YYYY-MM-DD.md
├── items/                           # 按项目的纵向追踪
│   ├── blood-pressure.md
│   ├── blood-sugar.md
│   └── ...
└── files/                           # 健康文档（PDF、图片）
```

- **每日日志**将多个技能的数据汇总到每天一个文件中。每个技能写入自己的 `## Section [skill-name · HH:MM]` 区块。
- **项目文件**维护 90 天滚动历史记录，用于纵向指标（血压、体重、血糖等），并附有趋势摘要。
- **格式规约** —— 所有技能遵循相同的 Markdown 模式（含 YAML frontmatter），因此任何技能都可以直接消费其他技能产生的数据，无需转换。

### 病历档案

对于临床文档——影像报告、化验结果、病理、基因组和出院小结——[medical-record-organizer](skills/medical-record-organizer/) 技能在 `~/.openclaw/patients/` 下提供结构化的按患者归档：

```
~/.openclaw/patients/[patient-id]/
├── INDEX.md                  # 导航入口
├── profile.json              # 结构化患者信息
├── timeline.md               # 时间线事件表
├── 01_Current Status/
├── 02_Diagnosis & Staging/
├── 03_Molecular Pathology/   # 基因 panel + IHC
├── 04_Imaging/               # CT / MRI / PET-CT
├── 05_Lab Results/           # 血常规、肿瘤标志物
├── 06_Treatment History/
├── 07_Comorbidities & Meds/
├── 08_Discharge Summaries/
├── 09_Apple_Health/
└── 10_Raw Files/
```

`health-memory` 追踪**每日健康指标**（体征、睡眠、营养），`medical-record-organizer` 管理**临床文档**（医院报告、扫描件、化验单）。两者共同构成完整的个人健康数据层——每日自我追踪加上纵向病历记录。

详见 [health-memory/SKILL.md](skills/health-memory/) 的完整规范。

---

## 医疗免责声明

> **VitaClaw 仅供健康管理参考，不构成医疗诊断或治疗建议。**
> 医疗决策请务必咨询专业医疗人员。
> 紧急情况请立即拨打当地急救电话（120/911/999）。

---

## 许可证

MIT 许可证。详见 [LICENSE](../LICENSE)。

---
