#!/usr/bin/env python3
"""Render manifest-driven README overview and catalog blocks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from skill_catalog import repo_root


BADGES_MARKER = "README_BADGES"
OVERVIEW_MARKER = "README_OVERVIEW"
CATALOG_MARKER = "README_CATALOG"

ZH_SCOPE = {
    "health-core": "健康核心",
    "out-of-scope": "本次迭代范围外",
}
ZH_TIER = {
    "core": "core",
    "labs": "labs",
    "restricted": "restricted",
}
ZH_CATEGORY = {
    "health": "health",
    "health-scenario": "health-scenario",
    "health-analyzer": "health-analyzer",
    "health-data": "health-data",
    "health-records": "health-records",
    "health-infrastructure": "health-infrastructure",
    "medical-research": "medical-research",
    "medical-imaging": "medical-imaging",
    "medical-nlp": "medical-nlp",
    "uncategorized": "uncategorized",
}


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def marker_block(name: str, content: str) -> str:
    return f"<!-- BEGIN GENERATED:{name} -->\n{content.rstrip()}\n<!-- END GENERATED:{name} -->"


def replace_marker(text: str, name: str, content: str) -> str:
    start = f"<!-- BEGIN GENERATED:{name} -->"
    end = f"<!-- END GENERATED:{name} -->"
    if start not in text or end not in text:
        raise ValueError(f"missing marker block {name}")
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    return before.rstrip() + "\n\n" + marker_block(name, content) + "\n" + after.lstrip("\n")


def badge_block(summary: dict, zh: bool) -> str:
    skills = summary["skill_count"]
    health_core = summary["health_skill_count"]
    license_label = "per-skill%20audit"
    return " ".join(
        [
            f"![Skills](https://img.shields.io/badge/skills-{skills}-blue)",
            f"![Health Core](https://img.shields.io/badge/health__core-{health_core}-teal)",
            "![Iteration](https://img.shields.io/badge/iteration-1-orange)",
            f"![License](https://img.shields.io/badge/license-{license_label}-lightgrey)",
        ]
    )


def build_overview(summary: dict, records: list[dict], zh: bool) -> str:
    health_records = [record for record in records if record["governance_scope"] == "health-core"]
    out_of_scope = [record for record in records if record["governance_scope"] == "out-of-scope"]

    category_lines = []
    category_counts: dict[str, list[dict]] = {}
    for record in health_records:
        category_counts.setdefault(record.get("category") or "uncategorized", []).append(record)

    sorted_categories = sorted(category_counts.items(), key=lambda item: (-len(item[1]), item[0]))
    for category, items in sorted_categories:
        highlights = ", ".join(f"`{row['slug']}`" for row in items[:3])
        if zh:
            label = ZH_CATEGORY.get(category, category)
            category_lines.append(f"| `{label}` | {len(items)} | {highlights} |")
        else:
            category_lines.append(f"| `{category}` | {len(items)} | {highlights} |")

    if zh:
        lines = [
            "_以下内容由 `skills-manifest.json` 自动生成。_",
            "",
            "### 仓库统计",
            "",
            "| 指标 | 数量 |",
            "| --- | ---: |",
            f"| 总 skill 数（不含 `_shared`） | {summary['skill_count']} |",
            f"| 健康核心 skill | {summary['health_skill_count']} |",
            f"| 健康核心 frontmatter 校验通过 | {summary['health_skill_count']} |",
            f"| 健康核心审计通过 | {summary['health_core_audit_pass']} |",
            f"| 带代码 skill | {summary['with_code']} |",
            f"| 带 CLI 入口 skill | {summary['with_cli_entrypoints']} |",
            f"| 带测试 skill | {summary['with_tests']} |",
            "",
            "### 治理快照",
            "",
            "| 范围 / 分层 | 数量 | 说明 |",
            "| --- | ---: | --- |",
            f"| 健康核心 | {len(health_records)} | Iteration 1 直接治理对象 |",
            f"| `core` | {summary['health_core_core']} | 默认开箱即用的健康工作区能力 |",
            f"| `labs` | {summary['health_core_labs']} | 高级分析 / 研究型健康能力 |",
            f"| `restricted` | {summary['health_core_restricted']} | 专有版权、特殊许可或需人工复核 |",
            f"| 范围外 | {len(out_of_scope)} | 本轮只做审计，不做批量整改 |",
            "",
            "### 健康核心分类统计",
            "",
            "| 分类 | 数量 | 示例 |",
            "| --- | ---: | --- |",
            *category_lines,
        ]
        return "\n".join(lines)

    lines = [
        "_The block below is generated from `skills-manifest.json`._",
        "",
        "### Repository Stats",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Total skills (excluding `_shared`) | {summary['skill_count']} |",
        f"| Health-core skills | {summary['health_skill_count']} |",
        f"| Health-core frontmatter valid | {summary['health_skill_count']} |",
        f"| Health-core audit pass | {summary['health_core_audit_pass']} |",
        f"| Skills with code | {summary['with_code']} |",
        f"| Skills with CLI entrypoints | {summary['with_cli_entrypoints']} |",
        f"| Skills with tests | {summary['with_tests']} |",
        "",
        "### Governance Snapshot",
        "",
        "| Scope / Tier | Count | Notes |",
        "| --- | ---: | --- |",
        f"| Health core | {len(health_records)} | Directly governed in Iteration 1 |",
        f"| `core` | {summary['health_core_core']} | Workspace-ready self-service health skills |",
        f"| `labs` | {summary['health_core_labs']} | Advanced analysis or research-heavy health skills |",
        f"| `restricted` | {summary['health_core_restricted']} | Proprietary or manual-license-review skills |",
        f"| Out of scope | {len(out_of_scope)} | Audited only in Iteration 1 |",
        "",
        "### Health-Core Category Snapshot",
        "",
        "| Category | Count | Highlights |",
        "| --- | ---: | --- |",
        *category_lines,
    ]
    return "\n".join(lines)


def _format_bool(value: bool | None) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "pending"


def build_catalog(records: list[dict], zh: bool) -> str:
    header = (
        "| Skill | Scope | Tier | User-invocable | Category | Description |\n"
        "| --- | --- | --- | --- | --- | --- |"
        if not zh
        else "| Skill | 范围 | 分层 | user-invocable | 分类 | 描述 |\n| --- | --- | --- | --- | --- | --- |"
    )
    lines = [header]
    for record in sorted(
        records,
        key=lambda item: (
            item["governance_scope"] != "health-core",
            item.get("distribution_tier") == "restricted",
            item.get("distribution_tier") == "labs",
            item["slug"],
        ),
    ):
        scope = record["governance_scope"]
        tier = record.get("distribution_tier") or "-"
        user_invocable = _format_bool(record.get("user_invocable"))
        category = record.get("category") or "uncategorized"
        if zh:
            scope = ZH_SCOPE.get(scope, scope)
            tier = ZH_TIER.get(tier, tier)
            category = ZH_CATEGORY.get(category, category)
        description = (record.get("description") or "").replace("\n", " ").strip()
        description = description or "pending description"
        lines.append(
            "| [{slug}]({path}/) | `{scope}` | `{tier}` | `{user}` | `{category}` | {description} |".format(
                slug=record["slug"],
                path=record["path"],
                scope=scope,
                tier=tier,
                user=user_invocable,
                category=category,
                description=description,
            )
        )
    return "\n".join(lines)


def render_readme(path: Path, manifest: dict, zh: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    rendered = replace_marker(text, BADGES_MARKER, badge_block(manifest["summary"], zh=zh))
    rendered = replace_marker(rendered, OVERVIEW_MARKER, build_overview(manifest["summary"], manifest["skills"], zh=zh))
    rendered = replace_marker(rendered, CATALOG_MARKER, build_catalog(manifest["skills"], zh=zh))
    changed = rendered != text
    if changed:
        path.write_text(rendered, encoding="utf-8")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Render manifest-driven README blocks")
    parser.add_argument(
        "--manifest",
        default="skills-manifest.json",
        help="Manifest path relative to the repo root",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 if README files are not up to date",
    )
    args = parser.parse_args()

    root = repo_root()
    manifest = load_manifest(root / args.manifest)
    changed = False
    changed |= render_readme(root / "README.md", manifest, zh=False)
    changed |= render_readme(root / "README.zh.md", manifest, zh=True)

    if args.check and changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
