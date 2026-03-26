#!/usr/bin/env python3
"""Validate SKILL.md frontmatter against VitaClaw's standard contract.

Extended with import direction validation: skills/_shared/ must NOT import
from individual skill directories, while individual skills MAY import from
_shared/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from skill_catalog import (
    REQUIRED_FRONTMATTER_KEYS,
    build_manifest_records,
    iter_skill_dirs,
    manifest_summary,
    repo_root,
    validate_frontmatter,
    write_json,
)


# ---------------------------------------------------------------------------
# Import direction validation
# ---------------------------------------------------------------------------

# Patterns that indicate importing from a specific skill directory
_IMPORT_FROM_SKILL_RE = re.compile(
    r"""
    (?:
        from\s+skills\.(?!_shared\b)([a-z0-9_]+)  # from skills.<name> (not _shared)
      | import\s+skills\.(?!_shared\b)([a-z0-9_]+) # import skills.<name>
    )
    """,
    re.VERBOSE,
)

_SYS_PATH_SKILL_RE = re.compile(
    r"""sys\.path\.\w+\(.*skills[/\\](?!_shared)([a-zA-Z0-9_-]+)""",
)


def check_import_directions(skill_dir: Path | None = None) -> list[dict]:
    """Scan skills/_shared/ for imports that reference individual skill directories.

    The rule: skills/_shared/ must NOT import from any specific skill directory.
    Individual skills MAY import from _shared/.

    Args:
        skill_dir: Unused (kept for API symmetry). Always scans _shared/.

    Returns:
        List of violation dicts with keys: file, line, import_text, violation, remediation.
    """
    shared_dir = repo_root() / "skills" / "_shared"
    if not shared_dir.is_dir():
        return []

    violations: list[dict] = []
    for py_file in sorted(shared_dir.rglob("*.py")):
        if not py_file.is_file():
            continue
        try:
            lines = py_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        rel_path = str(py_file.relative_to(repo_root()))
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#"):
                continue

            match = _IMPORT_FROM_SKILL_RE.search(stripped)
            if match:
                skill_name = match.group(1) or match.group(2)
                violations.append({
                    "file": rel_path,
                    "line": line_no,
                    "import_text": stripped,
                    "violation": (
                        f"_shared/ imports from individual skill '{skill_name}'. "
                        f"This creates a reverse dependency that breaks modularity."
                    ),
                    "remediation": (
                        f"Move the shared logic into skills/_shared/ or pass it as "
                        f"a parameter. Remove the import from '{skill_name}'. "
                        f"The dependency direction must be: skill -> _shared, never _shared -> skill."
                    ),
                })

            sys_match = _SYS_PATH_SKILL_RE.search(stripped)
            if sys_match:
                skill_name = sys_match.group(1)
                violations.append({
                    "file": rel_path,
                    "line": line_no,
                    "import_text": stripped,
                    "violation": (
                        f"_shared/ modifies sys.path to include individual skill '{skill_name}'. "
                        f"This creates a hidden reverse dependency."
                    ),
                    "remediation": (
                        f"Remove the sys.path manipulation targeting '{skill_name}'. "
                        f"If _shared/ needs functionality from a skill, refactor that "
                        f"functionality into _shared/ itself."
                    ),
                })

    return violations


def check_skill_imports(skill_dir: Path) -> list[dict]:
    """Scan a specific skill directory and verify imports from _shared are valid.

    Individual skills are allowed to import from _shared/. This function verifies
    that the imported _shared modules actually exist.

    Args:
        skill_dir: Path to the individual skill directory to scan.

    Returns:
        List of issue dicts for invalid _shared imports (missing files).
    """
    if not skill_dir.is_dir():
        return []

    shared_dir = repo_root() / "skills" / "_shared"
    issues: list[dict] = []

    _shared_import_re = re.compile(
        r"from\s+skills\._shared\.(\w+)\s+import"
        r"|from\s+skills\._shared\s+import\s+(\w+)"
    )

    for py_file in sorted(skill_dir.rglob("*.py")):
        if not py_file.is_file():
            continue
        try:
            lines = py_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        rel_path = str(py_file.relative_to(repo_root()))
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            match = _shared_import_re.search(stripped)
            if match:
                module_name = match.group(1) or match.group(2)
                expected_file = shared_dir / f"{module_name}.py"
                if not expected_file.exists():
                    issues.append({
                        "file": rel_path,
                        "line": line_no,
                        "import_text": stripped,
                        "violation": (
                            f"Imports '{module_name}' from _shared/ but "
                            f"'{module_name}.py' does not exist in skills/_shared/."
                        ),
                        "remediation": (
                            f"Check the module name for typos. If '{module_name}' was "
                            f"renamed or removed, update the import to use the current name."
                        ),
                    })

    return issues


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _format_violations_markdown(violations: list[dict], title: str) -> str:
    """Format violations as a human-readable Markdown report."""
    lines: list[str] = []
    lines.append(f"## {title}")
    lines.append("")

    if not violations:
        lines.append("No violations found.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"**{len(violations)} violation(s) found:**")
    lines.append("")

    for i, v in enumerate(violations, start=1):
        lines.append(f"### {i}. {v['file']}:{v['line']}")
        lines.append("")
        lines.append(f"**Import:** `{v['import_text']}`")
        lines.append("")
        lines.append(f"**Issue:** {v['violation']}")
        lines.append("")
        lines.append(f"**Fix:** {v['remediation']}")
        lines.append("")

    return "\n".join(lines)


def _format_frontmatter_markdown(invalid: list[dict]) -> str:
    """Format frontmatter validation results as Markdown."""
    lines: list[str] = []
    lines.append("## Frontmatter Validation")
    lines.append("")

    if not invalid:
        lines.append("All skills have valid frontmatter.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"**{len(invalid)} skill(s) with invalid frontmatter:**")
    lines.append("")

    for entry in invalid:
        problems = entry["parse_errors"] + entry["validation_errors"]
        lines.append(f"### {entry['slug']}")
        lines.append("")
        lines.append(f"**Path:** `{entry['path']}`")
        lines.append("")
        for problem in problems:
            # Add remediation instructions for each type of error
            remediation = _frontmatter_error_remediation(problem)
            lines.append(f"- **Error:** `{problem}`")
            if remediation:
                lines.append(f"  - **Fix:** {remediation}")
        lines.append("")

    return "\n".join(lines)


def _frontmatter_error_remediation(error: str) -> str:
    """Return remediation instruction for a frontmatter validation error."""
    remediations = {
        "missing-frontmatter": (
            "Add YAML frontmatter block at the top of SKILL.md: "
            "start with `---`, add required fields, close with `---`."
        ),
        "unclosed-frontmatter": (
            "Add closing `---` after the YAML frontmatter block."
        ),
        "frontmatter-not-mapping": (
            "Ensure the YAML frontmatter is a key-value mapping (dict), "
            "not a list or scalar."
        ),
    }

    # Check exact match first
    if error in remediations:
        return remediations[error]

    # Pattern-based remediation
    if error == "missing:SKILL.md":
        return "Create a SKILL.md file in this skill directory with proper YAML frontmatter."

    if error.startswith("missing:"):
        field = error.split(":", 1)[1]
        return f"Add the required field `{field}` to your SKILL.md frontmatter."

    if error.startswith("invalid:"):
        field = error.split(":")[1]
        return f"Fix the `{field}` field -- it must be a valid object/mapping."

    if error.startswith("yaml-error:"):
        return "Fix the YAML syntax error in the frontmatter block."

    return ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate VitaClaw SKILL.md frontmatter")
    parser.add_argument(
        "--scope",
        choices=["all", "health-core", "out-of-scope"],
        default="all",
        help="Restrict validation to a governance scope",
    )
    parser.add_argument(
        "--output",
        default="reports/skill-frontmatter-report.json",
        help="Report path relative to the repo root",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with status 1 when any skill fails validation",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Enable import direction validation (checks _shared/ does not import from individual skills)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        dest="output_format",
        help="Output format: json (default) or markdown (human-readable with remediation)",
    )
    args = parser.parse_args()

    has_errors = False

    # --- Frontmatter validation (always runs) ---
    records = build_manifest_records()
    if args.scope != "all":
        records = [record for record in records if record["governance_scope"] == args.scope]

    invalid = [
        {
            "slug": record["slug"],
            "path": record["path"],
            "governance_scope": record["governance_scope"],
            "distribution_tier": record.get("distribution_tier"),
            "parse_errors": record["frontmatter_parse_errors"],
            "validation_errors": record["frontmatter_validation_errors"],
        }
        for record in records
        if not record["frontmatter_valid"]
    ]

    if invalid:
        has_errors = True

    # --- Import direction validation (optional) ---
    import_violations: list[dict] = []
    if args.check_imports:
        import_violations = check_import_directions()
        if import_violations:
            has_errors = True

    # --- Output ---
    if args.output_format == "markdown":
        report = _format_frontmatter_markdown(invalid)
        if args.check_imports:
            report += "\n" + _format_violations_markdown(
                import_violations, "Import Direction Violations"
            )
        print(report)
    else:
        payload = {
            "scope": args.scope,
            "required_keys": REQUIRED_FRONTMATTER_KEYS,
            "summary": manifest_summary(records),
            "invalid_count": len(invalid),
            "invalid_skills": invalid,
        }
        if args.check_imports:
            payload["import_violations"] = import_violations
            payload["import_violation_count"] = len(import_violations)

        output_path = repo_root() / args.output
        write_json(output_path, payload)

        print(f"frontmatter report written to {output_path}")
        print(f"  invalid skills: {len(invalid)} / {len(records)}")
        if invalid:
            for entry in invalid[:20]:
                problems = entry["parse_errors"] + entry["validation_errors"]
                print(f"  - {entry['slug']}: {', '.join(problems)}")
            if len(invalid) > 20:
                print(f"  ... and {len(invalid) - 20} more")

        if args.check_imports:
            print(f"  import violations: {len(import_violations)}")
            for v in import_violations[:10]:
                print(f"  - {v['file']}:{v['line']}: {v['violation']}")

    if args.fail_on_error and has_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
