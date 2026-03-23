# VitaClaw Release Packages

Iteration 3 把 VitaClaw 的发行物收口成 4 层：

## `vitaclaw-core`

- 默认 chief-led 团队
- 包含 `health-chief-of-staff`、`health-main`、`health-records`、`health-metrics`、`health-lifestyle`、`health-safety`、`health-research`、`health-mental`
- 适合普通个人健康分身

## `vitaclaw-family-care`

- 家人照护扩展包
- 增加 `health-family`
- 适合父母慢病、术后恢复、陪诊和家庭协作

## `vitaclaw-oncology`

- 受限分发专科包
- 增加 `health-oncology`
- 适合肿瘤标志物、病历时间线、密集复查和专科 follow-up

## `vitaclaw-labs`

- 实验性能力集合
- 不默认进入普通用户模板

## 构建方式

```bash
python3 scripts/build_vitaclaw_release.py --package all --clean
```

生成目录：

- `dist/vitaclaw-core`
- `dist/vitaclaw-family-care`
- `dist/vitaclaw-oncology`
- `dist/vitaclaw-labs`

## 版本控制边界

建议纳入版本控制：

- 模板、配置、脚本、docs、tests、脱敏 fixtures、package manifests

不建议纳入版本控制：

- 真实用户 workspace
- `memory/health/daily/*.md`
- 原始患者档案与 Apple Health 导出
- `memory/health/team/audit/dispatch-log.jsonl`
- 生成后的 digest、timeline、随访文件

如需备份个人数据，建议使用私有 git 仓库或私有同步盘，不要把真实健康数据提交到公开仓库。
