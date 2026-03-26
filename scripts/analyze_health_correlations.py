#!/usr/bin/env python3
"""CLI entry point for health metric correlation analysis.

Analyzes cross-metric correlations using the CorrelationEngine and outputs
results in markdown or JSON format.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "_shared"))

from correlation_engine import CorrelationEngine  # noqa: E402


def _parse_pairs(pairs_str: str) -> list[tuple[str, str, str, str]]:
    """Parse comma-separated concept pairs like 'sleep:total_min,blood-sugar:value'.

    Each pair is two concept:field specs separated by comma, grouped in pairs.
    Example: "sleep:total_min,blood-sugar:value;blood-pressure:systolic,weight:kg"
    """
    parsed: list[tuple[str, str, str, str]] = []
    for group in pairs_str.split(";"):
        parts = group.strip().split(",")
        if len(parts) != 2:
            print(f"[WARN] Invalid pair format: '{group}'. Expected 'concept:field,concept:field'.", file=sys.stderr)
            continue
        try:
            concept_a, field_a = parts[0].strip().split(":")
            concept_b, field_b = parts[1].strip().split(":")
            parsed.append((concept_a.strip(), field_a.strip(), concept_b.strip(), field_b.strip()))
        except ValueError:
            print(f"[WARN] Invalid pair format: '{group}'. Use concept:field,concept:field.", file=sys.stderr)
    return parsed


def _format_markdown(results: list, all_results: list | None = None) -> str:
    """Format correlation results as markdown."""
    lines = ["# 健康指标相关性分析", ""]

    significant = [r for r in results if r.is_significant()]
    non_significant = [r for r in (all_results or results) if not r.is_significant()]

    if significant:
        lines.append("## 显著相关性")
        lines.append("")
        for r in significant:
            lines.append(f"### {r.concept_a} 与 {r.concept_b}")
            lines.append(f"- 相关系数：r = {r.correlation:.3f}")
            lines.append(f"- 统计显著性：p = {r.p_value:.4f}")
            lines.append(f"- 样本量：n = {r.sample_count}")
            lines.append(f"- 方法：{r.method}")
            lines.append(f"- 解读：{r.to_natural_language()}")
            lines.append("")
    else:
        lines.append("## 未发现显著相关性")
        lines.append("")
        lines.append("在分析的指标对中，未发现统计显著的相关性。")
        lines.append("")

    if non_significant:
        lines.append("## 未发现显著相关性")
        lines.append("")
        for r in non_significant:
            if r.method == "insufficient_data":
                lines.append(f"- {r.concept_a} 与 {r.concept_b}：数据不足（n={r.sample_count}，需要至少14天数据）")
            else:
                lines.append(f"- {r.concept_a} 与 {r.concept_b}：未发现显著相关性（p={r.p_value:.3f}, n={r.sample_count}）")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="分析健康指标之间的相关性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s                                    # 分析所有预设指标对\n"
            "  %(prog)s --days 90                           # 分析最近90天\n"
            '  %(prog)s --pairs "sleep:total_min,blood-sugar:value"  # 自定义分析对\n'
            "  %(prog)s --format json                       # JSON格式输出\n"
            '  %(prog)s --person-id dad                     # 分析指定家庭成员\n'
        ),
    )
    parser.add_argument(
        "--pairs",
        default=None,
        help='自定义分析对，格式: "concept:field,concept:field" 多对用分号分隔',
    )
    parser.add_argument("--days", type=int, default=90, help="分析时间窗口（天），默认90天")
    parser.add_argument("--person-id", default=None, help="指定家庭成员ID")
    parser.add_argument("--data-dir", default=None, help="数据目录路径")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json"], help="输出格式")
    parser.add_argument(
        "--min-strength",
        default="weak",
        choices=["weak", "moderate", "strong"],
        help="最小相关强度过滤",
    )

    args = parser.parse_args()

    engine = CorrelationEngine(data_dir=args.data_dir)

    if args.pairs:
        custom_pairs = _parse_pairs(args.pairs)
        if not custom_pairs:
            print("[WARN] 未能解析自定义分析对，使用预设分析对。", file=sys.stderr)
            custom_pairs = None
    else:
        custom_pairs = None

    # Get all results for reporting, then filter significant ones
    all_pairs = custom_pairs or CorrelationEngine.DEFAULT_PAIRS
    all_results = []
    for concept_a, field_a, concept_b, field_b in all_pairs:
        result = engine.correlate(concept_a, field_a, concept_b, field_b, args.days, person_id=args.person_id)
        all_results.append(result)

    significant_results = engine.discover_correlations(
        window_days=args.days,
        min_strength=args.min_strength,
        pairs=custom_pairs,
        person_id=args.person_id,
    )

    if not all_results:
        print("[WARN] 未找到可分析的数据。请确认数据目录中有足够的健康记录。", file=sys.stderr)

    if args.format == "json":
        output = json.dumps([r.to_dict() for r in all_results], ensure_ascii=False, indent=2)
        print(output)
    else:
        print(_format_markdown(significant_results, all_results))


if __name__ == "__main__":
    main()
