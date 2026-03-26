#!/usr/bin/env python3
"""Detect stale SKILL.md files where description has drifted from Python implementation.

Uses keyword extraction and overlap analysis to flag skills where the SKILL.md
description no longer matches the actual Python code. Produces actionable fix
suggestions for each flagged skill.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from skill_catalog import iter_skill_dirs, read_text, repo_root, split_frontmatter


# ---------------------------------------------------------------------------
# Stop words (common English + Chinese function words)
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset({
    # English
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "were",
    "been", "being", "have", "has", "had", "does", "did", "will", "would",
    "shall", "should", "may", "might", "can", "could", "not", "but", "its",
    "all", "any", "each", "few", "more", "most", "other", "some", "such",
    "than", "too", "very", "also", "just", "about", "into", "over", "after",
    "before", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "what", "which", "who", "whom",
    "their", "them", "they", "your", "you", "our", "out", "own", "same",
    "only", "both", "through", "during", "above", "below",
    # Common code words
    "self", "none", "true", "false", "return", "import", "class", "def",
    "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "print", "open", "file", "path", "name", "type", "value", "data",
    "use", "used", "using", "based", "support", "supports", "provide",
    "provides", "include", "includes", "allow", "allows",
    # Chinese stop words
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这",
})

_WORD_SPLIT_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful terms from text for keyword matching.

    Uses simple word splitting and stop word filtering. Keeps terms >= 3 chars
    that look like identifiers (tool names, data types, format names).
    """
    words = _WORD_SPLIT_RE.findall(text.lower())
    return {
        word for word in words
        if len(word) >= 3 and word not in STOP_WORDS
    }


def check_staleness(skill_dir: Path) -> dict | None:
    """Check if a skill's SKILL.md description has drifted from its Python implementation.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        A staleness report dict, or None if skill is prompt-only (no Python).
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    text = read_text(skill_md)
    frontmatter, _, _ = split_frontmatter(text)
    if not frontmatter:
        return None

    description = frontmatter.get("description", "")
    if not description or not isinstance(description, str):
        return None

    # Gather all Python code in skill directory
    py_contents: list[str] = []
    for py_file in skill_dir.rglob("*.py"):
        if not py_file.is_file():
            continue
        # Skip test files
        if py_file.name.startswith("test_"):
            continue
        try:
            py_contents.append(read_text(py_file))
        except OSError:
            continue

    if not py_contents:
        return None  # Prompt-only skill, not applicable

    code_text = "\n".join(py_contents)

    # Extract keywords
    desc_keywords = extract_keywords(description)
    code_keywords = extract_keywords(code_text)

    if not desc_keywords:
        return None  # Description too short to analyze

    matched = desc_keywords & code_keywords
    unmatched = desc_keywords - code_keywords
    match_ratio = len(matched) / len(desc_keywords)

    # Determine suggestion
    if match_ratio < 0.3:
        suggestion = "Update SKILL.md description to match implementation"
    elif match_ratio < 0.5:
        suggestion = "Review Python implementation -- may be incomplete"
    else:
        suggestion = "Description mostly matches implementation"

    return {
        "slug": skill_dir.name,
        "match_ratio": round(match_ratio, 3),
        "description_keywords": sorted(desc_keywords),
        "matched": sorted(matched),
        "unmatched": sorted(unmatched),
        "suggestion": suggestion,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_staleness_report_markdown(results: list[dict], threshold: float) -> str:
    """Generate a markdown report of stale SKILL.md files."""
    flagged = [r for r in results if r["match_ratio"] < threshold]
    flagged.sort(key=lambda r: r["match_ratio"])

    lines: list[str] = []
    lines.append("# Skill Staleness Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"**Total skills scanned:** {len(results)}")
    lines.append(f"**Flagged as potentially stale (< {threshold:.0%} match):** {len(flagged)}")
    lines.append("")

    if not flagged:
        lines.append("No stale skills detected.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Flagged Skills")
    lines.append("")
    lines.append("| Skill | Match% | Unmatched Keywords | Suggestion |")
    lines.append("|-------|--------|-------------------|------------|")

    for result in flagged:
        unmatched_str = ", ".join(result["unmatched"][:5])
        if len(result["unmatched"]) > 5:
            unmatched_str += f" (+{len(result['unmatched']) - 5} more)"
        lines.append(
            f"| {result['slug']} "
            f"| {result['match_ratio']:.0%} "
            f"| {unmatched_str} "
            f"| {result['suggestion']} |"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect stale SKILL.md files where description drifts from implementation"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        dest="output_format",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Match ratio threshold for flagging staleness (default: 0.5)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: stdout for markdown, reports/skill-staleness-report.json for json)",
    )
    args = parser.parse_args()

    skill_dirs = iter_skill_dirs(include_shared=False)
    results: list[dict] = []
    for skill_dir in skill_dirs:
        result = check_staleness(skill_dir)
        if result is not None:
            results.append(result)

    if args.output_format == "markdown":
        report = generate_staleness_report_markdown(results, args.threshold)
        if args.output:
            out_path = repo_root() / args.output
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report, encoding="utf-8")
            print(f"Staleness report written to {out_path}", file=sys.stderr)
        else:
            print(report)
    else:
        flagged = [r for r in results if r["match_ratio"] < args.threshold]
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "threshold": args.threshold,
            "total_scanned": len(results),
            "flagged_count": len(flagged),
            "flagged_skills": sorted(flagged, key=lambda r: r["match_ratio"]),
        }
        output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            out_path = repo_root() / args.output
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output, encoding="utf-8")
            print(f"Staleness report written to {out_path}", file=sys.stderr)
        else:
            print(output)


if __name__ == "__main__":
    main()
