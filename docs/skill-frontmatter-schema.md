# VitaClaw Skill Frontmatter Schema

本文件定义 VitaClaw 对 `skills/<skill>/SKILL.md` frontmatter 的标准化约束。

对应 JSON Schema 文件：

- [schemas/skill-frontmatter.schema.json](/Users/baozhiwei/Library/CloudStorage/坚果云-452858265@qq.com/我的坚果云/其他项目/vitaclaw-main/schemas/skill-frontmatter.schema.json)

## 目标

- 让 skill 元数据可自动收集到 `skills-manifest.json`
- 让 README、安装器、测试器、分发包都能使用同一数据源
- 为后续清理遗留风格、生成不合规报告和 CI 校验打基础

## 必填字段

```yaml
---
name: blood-pressure-tracker
description: "Tracks blood pressure readings and writes to shared health memory."
version: 1.0.0
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Edit
metadata:
  openclaw:
    emoji: "🩺"
    category: health-metric
---
```

### 字段说明

- `name`
  要求：kebab-case，且与 skill 目录名一致
- `description`
  要求：一句完整描述，说明做什么、何时使用
- `version`
  要求：SemVer 风格，如 `1.0.0`
- `user-invocable`
  要求：布尔值
- `allowed-tools`
  要求：逗号分隔字符串或字符串数组
- `metadata.openclaw`
  要求：至少提供 `category`

## 兼容策略

当前仓库包含大量历史 skill，frontmatter 风格并不统一。现阶段采用“两段式”策略：

1. 先定义严格标准
2. 再用校验器输出不合规报告，逐步迁移

也就是说，校验脚本会指出问题，但不会假设历史 skill 已全部达标。

## 校验脚本

生成不合规报告：

```bash
python3 scripts/validate_skill_frontmatter.py
```

默认输出：

- `reports/skill-frontmatter-report.json`

若要在 CI 或发布流程中失败退出：

```bash
python3 scripts/validate_skill_frontmatter.py --fail-on-error
```

## 相关脚本

- [scripts/build_skills_manifest.py](/Users/baozhiwei/Library/CloudStorage/坚果云-452858265@qq.com/我的坚果云/其他项目/vitaclaw-main/scripts/build_skills_manifest.py)
- [scripts/validate_skill_frontmatter.py](/Users/baozhiwei/Library/CloudStorage/坚果云-452858265@qq.com/我的坚果云/其他项目/vitaclaw-main/scripts/validate_skill_frontmatter.py)
- [scripts/smoke_test_skills.py](/Users/baozhiwei/Library/CloudStorage/坚果云-452858265@qq.com/我的坚果云/其他项目/vitaclaw-main/scripts/smoke_test_skills.py)
