# OpenClaw Medical Skills 与 VitaClaw 整合建议

这份文档回答一个非常实际的问题：

是否应该把 [OpenClaw-Medical-Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills/tree/main) 整合进 VitaClaw？

结论先说：

- **应该整合，但只能选择性吸收**
- **绝不能把 869 个 skills 整仓并入 `vitaclaw-core`**
- **优先吸收对象是 `health-research`、`health-oncology` 和 `vitaclaw-labs`**
- **默认普通用户路径仍以 VitaClaw 自己的 chief-led 健康团队为主**

## 1. 为什么不能整仓并入

OpenClaw-Medical-Skills 的定位是“医学和生物医药研究技能大仓”，不是“个人健康分身产品模板”。

从上游 README 可以看到，它当前宣称：

- 共 `869` 个 skills
- 覆盖临床、药物发现、基因组学、生信、医疗器械、科研基础设施
- 聚合自 `12+` 个开源 skill 仓库

这和 VitaClaw 当前的产品方向并不一样：

- VitaClaw 现在的健康核心是 `79` 个 health-core skills
- 已经收口成 chief-led、多角色后台协作、长期记忆和主动服务系统
- 发行物已经分为 `vitaclaw-core / vitaclaw-family-care / vitaclaw-oncology / vitaclaw-labs`

如果整仓并入，最容易出现的 5 个问题：

1. 普通用户体验被科研型 skill 淹没
2. `health-main` 的长期记忆和研究型能力串线
3. 依赖、数据文件和 API key 复杂度暴涨
4. license 和来源链条失控
5. VitaClaw 从“健康操作系统”退化成“技能大仓”

## 2. 当前最重要的法律与治理风险

不要因为上游 README 用了 “MIT” badge 就直接认为整仓都能安全 vendoring。

实际抽样中已经看到两类风险：

### 2.1 仓库级 license 信息不稳定

通过 GitHub API 查看仓库元信息时，`license` 字段为空，不能直接把整个仓库视为已完成 license 归档。

### 2.2 单个 skill 存在明显的版权冲突信号

至少部分精准肿瘤学和试验匹配类 skill 的文件头已经出现了 “All Rights Reserved / Proprietary / Confidential” 之类的版权声明，例如 `trialgpt-matching`。

这意味着：

- 即使 frontmatter 里写了 `license: MIT`
- 也**不能**直接假定该 skill 可安全并入 VitaClaw

因此，VitaClaw 对这个上游仓库的接入必须默认采用：

- **白名单准入**
- **逐 skill 审核**
- **按包隔离**

而不是 repo 级 blanket import。

## 3. 推荐整合策略

### 3.1 接入方式

推荐顺序：

1. **外部挂载 / adapter 接入**
   - 先通过 `health-research` 或 `health-oncology` 调用外部 skill
   - 不先复制进 VitaClaw 主树
2. **白名单稳定后再 vendor**
   - 只有通过法律、依赖、安全和产品审查的 skill 才考虑纳入 `vitaclaw-labs`
3. **最后再决定是否进入正式发行包**
   - 只有长期稳定、低复杂度、与 chief-led 产品模型兼容的 skill 才能进入 `vitaclaw-core` 或 `vitaclaw-oncology`

### 3.2 默认接入边界

这些外部 skills 默认只能给以下 agent 使用：

- `health-research`
- `health-oncology`
- 少量可进入 `health-safety`

默认**不要**直接给：

- `health-main`
- `health-chief-of-staff`
- `health-family`

除非 VitaClaw 自己加了一层 adapter，把输出收口成：

- evidence brief
- source list
- risk note
- follow-up suggestion

而不是把上游 skill 的原始输出直接暴露给普通用户。

## 4. 第一批最值得接入的候选 skill

下面是当前最值得进入 VitaClaw 白名单的第一批方向。

### A. 优先进入 `health-research`

#### `drug-labels-search`

- 用途：FDA 官方药品标签检索
- 适合：`health-research`
- 价值：可补齐药品标签、适应证、警示语和相互作用来源
- 风险：中等，依赖外部 API key，不适合默认 core

#### `clinicaltrials-database`

- 用途：ClinicalTrials.gov API v2 查询
- 适合：`health-research`、部分 `health-oncology`
- 价值：很适合做试验匹配前的证据后援
- 风险：中等，需注意不是直接做患者入组结论

#### `tooluniverse-clinical-guidelines`

- 用途：多源临床指南检索
- 适合：`health-research`
- 价值：非常适合 VitaClaw 的“证据优先”后援层
- 风险：中等，依赖 ToolUniverse 生态，需要单独环境审计

#### `fda-database`

- 用途：OpenFDA 多领域检索
- 适合：`health-research`、`health-safety`
- 价值：适合大众健康场景里的用药安全和消费级健康查询
- 风险：中等，需要对输出口径做二次约束

### B. 优先进入 `vitaclaw-labs`

#### `tooluniverse-pharmacovigilance`

- 用途：药物安全信号、FAERS、标签、PGx 综合分析
- 适合：`health-research`、`health-safety`
- 价值：对复杂用药、长期用药和风险说明很有价值
- 风险：较高，输出容易越界，需要 VitaClaw adapter 做风险层级收口

#### `tooluniverse-drug-drug-interaction`

- 用途：DDI 风险分析
- 适合：`health-research`、`health-safety`
- 价值：可做药物相互作用的 evidence brief
- 风险：较高，不应让其直接给普通用户处方级建议

### C. 可保留为远端观察对象，但不进入大众健康主线

#### `clinical-trials-search`

- 用途：临床试验搜索
- 适合：`health-research`
- 价值：可作为 `clinicaltrials-database` 的备选或轻量入口
- 风险：中等

## 5. 当前不建议直接吸收的 skill

### A. 法律风险高

以下高风险方向当前**不建议**直接 vendor 或进入发行包：

- 带 proprietary 声明的精准肿瘤学类 skill
- `trialgpt-matching`

原因：

- 文件头已有 proprietary / all rights reserved 声明
- 与仓库 README 的开放授权信号不一致
- 必须在单 skill 层面补齐许可证明后，才可能进入 `restricted`

### B. 产品方向不匹配

以下类型不建议直接进 VitaClaw：

- 大型 bioinformatics pipeline
- RNA-seq / scRNA-seq / GWAS / variant calling 主流程
- 医疗器械合规开发类 skill
- 实验自动化 / 大模型科研基础设施 skill

这些能力很强，但它们属于“科研平台”，不属于“普通人健康分身”。

### C. 心理健康类不建议直接照搬

`mental-health-analyzer` 这类 skill 方向上相关，但不要直接并进 `health-mental`。

原因：

- VitaClaw 当前心理线是“支持型 + 危机分流”
- 不能直接把外部心理分析 skill 的假设、命令和风险评估逻辑原样带进来

更合适的做法是：

- 借鉴思路
- 抽取可用 schema
- 用 VitaClaw 自己的安全边界重写 adapter

## 6. 推荐的白名单准入顺序

### Phase 1：只做 research adapter

候选：

- `clinicaltrials-database`
- `tooluniverse-clinical-guidelines`
- `drug-labels-search`
- `fda-database`

目标：

- 全部只通过 `health-research` 输出 evidence brief
- 不接触 `MEMORY.md`
- 不直接写长期画像

### Phase 2：进入 labs

候选：

- `tooluniverse-pharmacovigilance`
- `tooluniverse-drug-drug-interaction`
- `biomedical-search`

目标：

- 进入 `vitaclaw-labs`
- 允许 chief 调 research 请求，但不能直出临床处置结论

### Phase 3：保留在远端观察

候选：

- 其他经法律和依赖审计后通过的肿瘤 / trials skills

目标：

- 不进入大众健康默认模板
- 仅在单独的研究或专病工作区中评估

## 7. 最终建议

一句话总结：

**要整合，但方式必须是“research / oncology 定向吸收 + white-list + adapter + license audit”，而不是“把 OpenClaw-Medical-Skills 全拷进 VitaClaw”。**

如果后续要正式推进，建议下一步就做两件事：

1. 为第一批白名单 skill 建立 `external-skill-adapters/` 准入层
2. 对候选 skill 做逐项 license / dependency / privacy / product-fit 审计
