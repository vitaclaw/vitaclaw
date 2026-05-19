#!/usr/bin/env python3
"""Bulk-fix SKILL.md frontmatter to satisfy schemas/skill-frontmatter.schema.json.

Adds the four governance fields VitaClaw requires (version, user-invocable,
allowed-tools, metadata.openclaw.category) wherever they are missing — without
disturbing fields that are already set. Skills with no frontmatter block at all
get a fresh one synthesized from their slug + first H1 in the body.

Defaults applied:
  version: 0.1.0
  user-invocable: false
  allowed-tools: [Read, Grep, Glob, Bash, Write, Edit, WebFetch, WebSearch]
  metadata.openclaw.category: <inferred from slug prefix>

Run with --dry-run to preview changes without writing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT = REPO_ROOT / "reports" / "skill-frontmatter-report.json"

DEFAULT_VERSION = "0.1.0"
DEFAULT_ALLOWED_TOOLS = ["Read", "Grep", "Glob", "Bash", "Write", "Edit", "WebFetch", "WebSearch"]


def infer_category(slug: str) -> str:
    if slug.startswith("bio-"):
        return "bioinformatics"
    if slug.startswith(("biomedical-", "biorxiv", "medrxiv", "pubmed", "europe-pmc")):
        return "biomedical-research"
    if slug.startswith(("clinical-", "clinicaltrials", "trial")):
        return "clinical-research"
    if slug.startswith(("genomic", "variant", "gene", "ngs", "cnv", "rna-")):
        return "genomics"
    if slug.startswith(("fda-", "ema-", "regulatory")):
        return "regulatory"
    if slug.startswith(("clinical-decision", "diagnosis", "icd")):
        return "clinical-decision-support"
    return "research"


def find_h1_in_body(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def parse_frontmatter(text: str) -> tuple[list[str] | None, list[str]]:
    """Return (frontmatter_lines, body_lines). frontmatter_lines is None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines

    closing = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing = i
            break
    if closing is None:
        return None, lines

    return lines[1:closing], lines[closing + 1 :]


def has_top_level_key(fm_lines: list[str], key: str) -> bool:
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    return any(pattern.match(line) for line in fm_lines)


def has_metadata_openclaw(fm_lines: list[str]) -> bool:
    in_metadata = False
    for line in fm_lines:
        if re.match(r"^metadata\s*:", line):
            stripped = line.split(":", 1)[1].strip()
            if stripped.startswith("{") and "openclaw" in stripped:
                return True
            in_metadata = True
            continue
        if in_metadata:
            if re.match(r"^[^\s#]", line):
                in_metadata = False
                continue
            if re.match(r"^\s+openclaw\s*:", line):
                return True
    return False


def build_minimal_frontmatter(slug: str, description: str) -> list[str]:
    category = infer_category(slug)
    return [
        f"name: {slug}",
        f"description: {description}",
        f"version: {DEFAULT_VERSION}",
        "user-invocable: false",
        f"allowed-tools: [{', '.join(DEFAULT_ALLOWED_TOOLS)}]",
        "metadata:",
        "  openclaw:",
        f"    category: {category}",
    ]


def patch_frontmatter(slug: str, fm_lines: list[str]) -> list[str]:
    result = list(fm_lines)
    if not has_top_level_key(result, "version"):
        result.append(f"version: {DEFAULT_VERSION}")
    if not has_top_level_key(result, "user-invocable"):
        result.append("user-invocable: false")
    if not has_top_level_key(result, "allowed-tools"):
        result.append(f"allowed-tools: [{', '.join(DEFAULT_ALLOWED_TOOLS)}]")
    if not has_metadata_openclaw(result):
        category = infer_category(slug)
        if has_top_level_key(result, "metadata"):
            # Nest openclaw under existing metadata key by appending an indented block.
            # Walk to the end of the metadata block.
            insert_at = None
            in_metadata = False
            for i, line in enumerate(result):
                if re.match(r"^metadata\s*:", line):
                    in_metadata = True
                    insert_at = i + 1
                    continue
                if in_metadata:
                    if re.match(r"^[^\s#]", line):
                        break
                    insert_at = i + 1
            metadata_block = [
                "  openclaw:",
                f"    category: {category}",
            ]
            if insert_at is None:
                result.extend(metadata_block)
            else:
                result[insert_at:insert_at] = metadata_block
        else:
            result.extend([
                "metadata:",
                "  openclaw:",
                f"    category: {category}",
            ])
    return result


def fix_skill(path: Path, slug: str, dry_run: bool = False) -> tuple[bool, str]:
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md missing"

    text = skill_md.read_text(encoding="utf-8")
    fm_lines, body_lines = parse_frontmatter(text)

    if fm_lines is None:
        h1 = find_h1_in_body(text) or slug.replace("-", " ").title()
        description = f"{h1} — auto-onboarded skill. Refine description before promoting to health_core."
        new_fm = build_minimal_frontmatter(slug, description)
        new_text = "---\n" + "\n".join(new_fm) + "\n---\n\n" + text.lstrip()
    else:
        patched = patch_frontmatter(slug, fm_lines)
        if patched == fm_lines:
            return False, "no change"
        new_text = "---\n" + "\n".join(patched) + "\n---\n" + "\n".join(body_lines)
        if not new_text.endswith("\n"):
            new_text += "\n"

    if dry_run:
        return True, "would update"

    skill_md.write_text(new_text, encoding="utf-8")
    return True, "updated"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", help="Comma-separated slugs to limit to")
    args = parser.parse_args()

    if not REPORT.exists():
        print("Report not found; run scripts/validate_skill_frontmatter.py first", file=sys.stderr)
        return 1
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    only = set(args.only.split(",")) if args.only else None

    updated = []
    skipped = []
    for entry in report["invalid_skills"]:
        slug = entry["slug"]
        if only and slug not in only:
            continue
        path = REPO_ROOT / entry["path"]
        changed, reason = fix_skill(path, slug, dry_run=args.dry_run)
        if changed:
            updated.append((slug, reason))
        else:
            skipped.append((slug, reason))

    print(f"updated: {len(updated)}")
    print(f"skipped: {len(skipped)}")
    if skipped:
        for slug, reason in skipped[:20]:
            print(f"  - {slug}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
