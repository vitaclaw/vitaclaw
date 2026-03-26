---
name: health-correlation-analyzer
description: "跨指标相关性分析：发现健康数据之间的统计关联"
version: 1.0.0
user-invocable: true
allowed-tools:
  - Read
metadata:
  openclaw:
    category: health-analyzer
    iteration: 2
---

# 健康指标相关性分析

分析用户多种健康指标之间的统计关联，帮助发现潜在的健康模式和因果线索。

## 功能

### 预设分析对

以下是经过临床验证的、具有生物学合理性的指标组合：

| 组合 | 含义 |
|------|------|
| 睡眠时长 <-> 血糖 | 睡眠不足可能影响血糖调节 |
| 血压 <-> 睡眠时长 | 睡眠与血压控制的关系 |
| 血压 <-> 体重 | 体重变化对血压的影响 |
| 咖啡因 <-> 睡眠时长 | 咖啡因摄入对睡眠的影响 |
| 血糖 <-> 体重 | 体重管理与血糖控制 |
| 血压 <-> 咖啡因 | 咖啡因对血压的影响 |

### 自定义分析对

用户可以请求任意两个健康指标的相关性分析，不限于预设组合。

### 输出内容

每个分析结果包含：

- **相关系数 (r)**：-1 到 1 之间，表示关联强度和方向
- **p 值**：统计显著性，p < 0.05 视为显著
- **样本量 (n)**：参与分析的数据点数量，最少需要 14 天数据
- **方向**：正相关（同升同降）或负相关（此升彼降）
- **强度**：强 (|r| >= 0.7)、中等 (|r| >= 0.4)、弱 (|r| >= 0.2)
- **自然语言解读**：用中文描述发现的关联及其统计证据

### 显著性标准

- p < 0.05 且 n >= 14：报告为"存在显著相关性"
- p >= 0.05：报告为"未发现显著相关性"
- n < 14：报告为"数据不足，无法进行可靠的相关性分析"

## 使用方式

用户可以用自然语言发起请求，例如：

- "分析我的睡眠和血糖有没有关联"
- "看看咖啡因对睡眠质量的影响"
- "我的血压和体重有相关性吗"
- "帮我做一次全面的健康指标关联分析"
- "看看爸爸的血压和睡眠有没有关系"（指定家庭成员）

## 实现

使用 `skills/_shared/correlation_engine.py` 中的 `CorrelationEngine` 类：

```python
from skills._shared.correlation_engine import CorrelationEngine

engine = CorrelationEngine(data_dir=data_dir)

# 全面分析（使用预设对）
results = engine.discover_correlations(window_days=90, person_id=person_id)

# 自定义分析对
result = engine.correlate("sleep", "total_min", "blood-sugar", "value", window_days=90, person_id=person_id)

# 获取自然语言解读
insight = result.to_natural_language()
```

## 输出格式

### Markdown 格式

```markdown
# 健康指标相关性分析

## 显著相关性

### 睡眠时长 与 血糖
- 相关系数：r = -0.452
- 统计显著性：p = 0.012
- 样本量：n = 28
- 解读：过去分析期间，sleep 与 blood-sugar 存在中等负相关（r=-0.452, p=0.012, n=28）

## 未发现显著相关性

- 血压 与 体重（p=0.230, n=25）
```

### JSON 格式

调用 `result.to_dict()` 获取结构化数据，包含所有分析字段。

## 注意事项

- 相关性不等于因果关系，分析结果仅供参考
- 建议至少收集 30 天以上的数据以获得更可靠的结果
- 同时使用 Pearson（线性）和 Spearman（秩）相关方法，自动选择更显著的结果
