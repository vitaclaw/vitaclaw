---
name: health-visit-summary
description: "生成就诊摘要：包含近期生命体征、趋势图表、用药、检验结果和关注问题，支持 Markdown/HTML/PDF 多格式输出"
version: 1.0.0
user-invocable: true
allowed-tools: [Edit, Read, Write, Bash]
metadata: {"openclaw":{"emoji":"","category":"health"}}
---

# 就诊摘要生成

为用户生成医生可读的就诊摘要，汇总近期健康数据，包括生命体征趋势图表、当前用药、检验结果和需关注的健康问题。

## 使用场景

- 用户即将去看医生，需要准备就诊资料
- 用户希望打印或在手机上展示健康数据给医生
- 家庭成员（如妈妈）需要带健康摘要就诊

## 输出内容

就诊摘要包含以下部分：

1. **患者信息** -- 姓名、年龄/出生日期、主要健康问题
2. **近期生命体征** -- 血压、血糖、体重的近期数据和趋势图表
3. **当前用药** -- 从 medications.md 解析的用药列表
4. **近期检验结果** -- 近期化验/检查结果
5. **关注问题** -- 由 Heartbeat 巡检发现的健康风险
6. **就诊问题（可编辑）** -- 预留空白供用户填写想问医生的问题

## 输出格式

| 格式 | 说明 | 适用场景 |
|------|------|----------|
| Markdown | 可编辑的纯文本格式 | 在对话中查看/编辑 |
| HTML | 自包含网页，内嵌 CSS 和图表 | 手机展示、浏览器打印 |
| PDF | 打印就绪文档 | 直接打印（需安装 weasyprint） |

## CLI 用法

```bash
# 生成 Markdown 格式摘要（默认）
python scripts/generate_visit_summary.py

# 生成 HTML 格式，指定时间范围
python scripts/generate_visit_summary.py --format html --days 60

# 为家庭成员生成摘要
python scripts/generate_visit_summary.py --person-id mom --format html

# 指定输出路径
python scripts/generate_visit_summary.py --format html --output ~/Desktop/visit-summary.html
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--format` | markdown | 输出格式：markdown, html, pdf |
| `--person-id` | 无 | 指定家庭成员 ID |
| `--days` | 30 | 包含多少天的数据 |
| `--data-dir` | 自动 | 数据目录 |
| `--workspace-root` | 自动 | 工作区根目录 |
| `--memory-dir` | 自动 | 记忆目录 |
| `--output` | 自动 | 指定输出文件路径 |
| `--no-write` | 否 | 不写入文件，仅输出到终端 |

## 数据来源

- `memory/health/_health-profile.md` -- 患者基本信息
- `memory/health/items/medications.md` -- 当前用药
- `data/blood-pressure-tracker/` -- 血压记录（via CrossSkillReader）
- `data/chronic-condition-monitor/` -- 血糖、体重记录
- HealthHeartbeat 巡检结果 -- 健康风险

## 注意事项

- 如果没有足够数据，摘要会显示"近期无记录"等提示，不会出错
- PDF 需要安装 `weasyprint`，未安装时自动回退为 HTML 格式
- HTML 格式已优化为手机和打印友好，图表以 base64 内嵌
- 使用 `--person-id` 可为不同家庭成员生成独立摘要
