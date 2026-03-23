#!/usr/bin/env python3
"""Shared helpers for cataloging VitaClaw skills."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FRONTMATTER_KEYS = [
    "name",
    "description",
    "version",
    "user-invocable",
    "allowed-tools",
    "metadata",
]

CODE_SUFFIXES = {".py", ".sh", ".js", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".rb"}
TEST_SUFFIXES = (
    "_test.py",
    ".test.ts",
    ".test.js",
    ".spec.ts",
    ".spec.js",
    "_test.go",
)
LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".sh": "shell",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
}
DEPENDENCY_FILE_NAMES = {
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Pipfile",
    "Pipfile.lock",
    "environment.yml",
    "environment.yaml",
    "Cargo.toml",
    "go.mod",
}
REPO_LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "NOTICE")
PROPRIETARY_MARKERS = (
    "all rights reserved",
    "proprietary",
    "confidential",
    "unauthorized copying",
)
HEALTH_CORE_LABS = {
    "bio-clinical-databases-tumor-mutational-burden",
    "bio-tumor-fraction-estimation",
    "clinical-trial-search",
    "medical-entity-extractor",
    "medical-imaging-review",
    "medical-research-toolkit",
    "pubmed-abstract-reader",
}
HEALTH_CORE_RESTRICTED = {
    "cancer-metabolism-agent",
    "microbiome-cancer-agent",
    "multimodal-medical-imaging",
    "tumor-clonal-evolution-agent",
    "tumor-heterogeneity-agent",
    "tumor-mutational-burden-agent",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def skills_root() -> Path:
    return repo_root() / "skills"


def iter_skill_dirs(include_shared: bool = False) -> list[Path]:
    dirs = []
    for path in sorted(skills_root().iterdir()):
        if not path.is_dir():
            continue
        if not include_shared and path.name == "_shared":
            continue
        dirs.append(path)
    return dirs


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    if not text.startswith("---\n"):
        return None, text, ["missing-frontmatter"]

    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text, ["unclosed-frontmatter"]

    raw_frontmatter = text[4:end]
    body = text[end + 5 :]
    try:
        parsed = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError as exc:
        return None, body, [f"yaml-error:{exc.__class__.__name__}"]

    if not isinstance(parsed, dict):
        return None, body, ["frontmatter-not-mapping"]

    return parsed, body, []


def normalize_allowed_tools(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value).strip()]


def detect_root_python_files(skill_dir: Path) -> list[str]:
    return sorted(path.name for path in skill_dir.glob("*.py") if path.is_file())


def detect_cli_entrypoints(skill_dir: Path) -> list[str]:
    candidates = []
    for path in skill_dir.glob("*.py"):
        if not path.is_file():
            continue
        if path.name.startswith("test_") or any(path.name.endswith(suffix) for suffix in TEST_SUFFIXES):
            continue
        text = read_text(path)
        if "argparse.ArgumentParser" in text or "__main__" in text:
            candidates.append(path.name)
    return sorted(candidates)


def detect_code_files(skill_dir: Path) -> list[str]:
    files: list[str] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(skill_dir).parts):
            continue
        if path.suffix.lower() in CODE_SUFFIXES:
            files.append(str(path.relative_to(skill_dir)))
    return sorted(files)


def detect_tests(skill_dir: Path) -> list[str]:
    files: list[str] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(skill_dir))
        name = path.name
        if name.startswith("test_") or any(name.endswith(suffix) for suffix in TEST_SUFFIXES):
            files.append(rel)
    return sorted(files)


def detect_dependency_files(skill_dir: Path) -> list[str]:
    files = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in DEPENDENCY_FILE_NAMES:
            files.append(str(path.relative_to(skill_dir)))
    return sorted(files)


def detect_license_files(skill_dir: Path) -> list[str]:
    candidates = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        upper = path.name.upper()
        if upper.startswith(("LICENSE", "COPYING", "NOTICE")):
            candidates.append(str(path.relative_to(skill_dir)))
    return sorted(candidates)


def detect_repo_license_files() -> list[str]:
    candidates = []
    for name in REPO_LICENSE_FILES:
        path = repo_root() / name
        if path.exists():
            candidates.append(name)
    return candidates


def infer_languages(code_files: list[str]) -> list[str]:
    languages = []
    for rel in code_files:
        suffix = Path(rel).suffix.lower()
        language = LANGUAGE_BY_SUFFIX.get(suffix)
        if language and language not in languages:
            languages.append(language)
    return languages


def infer_category(frontmatter: dict[str, Any] | None) -> str | None:
    if not frontmatter:
        return None
    metadata = frontmatter.get("metadata")
    if isinstance(metadata, dict):
        openclaw = metadata.get("openclaw")
        if isinstance(openclaw, dict) and openclaw.get("category") is not None:
            return str(openclaw["category"])
        if metadata.get("category") is not None:
            return str(metadata["category"])
    return None


def infer_health_category(skill_name: str, frontmatter: dict[str, Any] | None) -> str | None:
    category = infer_category(frontmatter)
    if category:
        return category

    slug = skill_name.replace("_", "-")
    if slug in {"health-memory", "medical-record-organizer", "health-timeline", "apple-health-digest"}:
        return "health-infrastructure"
    if slug.endswith(("-hub", "-copilot", "-companion", "-advisor", "-manager")):
        return "health-scenario"
    if any(token in slug for token in ("tracker", "digest", "monitor", "analyzer", "reminder")):
        return "health"
    if any(token in slug for token in ("tumor", "cancer", "oncology", "trial", "imaging", "pubmed")):
        return "medical-research"
    return None


def is_health_skill(skill_name: str, frontmatter: dict[str, Any] | None) -> bool:
    category = (infer_category(frontmatter) or "").lower()
    if "health" in category or "medical" in category or "oncology" in category:
        return True

    tokens = skill_name.replace("_", "-").split("-")
    health_markers = {
        "health",
        "medical",
        "cancer",
        "tumor",
        "sleep",
        "blood",
        "kidney",
        "diabetes",
        "hypertension",
        "supplement",
        "medication",
        "wellness",
        "nutrition",
        "checkup",
        "mental",
    }
    return any(token in health_markers for token in tokens)


def _frontmatter_license(frontmatter: dict[str, Any] | None) -> str | None:
    if not isinstance(frontmatter, dict):
        return None
    value = frontmatter.get("license")
    if value is None:
        return None
    return str(value).strip()


def _has_proprietary_notice(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PROPRIETARY_MARKERS)


def infer_governance_scope(skill_name: str, frontmatter: dict[str, Any] | None) -> str:
    return "health-core" if is_health_skill(skill_name, frontmatter) else "out-of-scope"


def infer_distribution_tier(
    skill_name: str,
    frontmatter: dict[str, Any] | None,
    skill_md_text: str,
    governance_scope: str,
) -> str | None:
    if governance_scope != "health-core":
        return None

    slug = skill_name.replace("_", "-")
    license_name = (_frontmatter_license(frontmatter) or "").lower()
    if (
        slug in HEALTH_CORE_RESTRICTED
        or "proprietary" in license_name
        or "non-commercial" in license_name
        or _has_proprietary_notice(skill_md_text)
    ):
        return "restricted"
    if slug in HEALTH_CORE_LABS:
        return "labs"
    return "core"


def infer_license_evidence(
    frontmatter: dict[str, Any] | None,
    license_files: list[str],
    repo_license_files: list[str],
    skill_md_text: str,
    distribution_tier: str | None,
) -> str | None:
    if license_files:
        joined = ", ".join(license_files)
        return f"skill-local license file: {joined}"

    license_name = _frontmatter_license(frontmatter)
    if license_name:
        return f"frontmatter license: {license_name}"

    if _has_proprietary_notice(skill_md_text):
        return "embedded proprietary notice in SKILL.md"

    if distribution_tier in {"core", "labs"} and repo_license_files:
        return f"repository license inheritance: {', '.join(repo_license_files)}"

    return None


def infer_audit_status(
    governance_scope: str,
    frontmatter_valid: bool,
    distribution_tier: str | None,
    license_evidence: str | None,
    allowed_tools: list[str],
) -> str:
    if governance_scope != "health-core":
        return "needs-review"
    if not frontmatter_valid or not allowed_tools or not license_evidence:
        return "needs-review"
    if distribution_tier == "restricted":
        return "needs-review"
    return "pass"


def validate_frontmatter(frontmatter: dict[str, Any] | None) -> list[str]:
    if frontmatter is None:
        return ["missing-frontmatter"]

    errors = []
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in frontmatter:
            errors.append(f"missing:{key}")

    metadata = frontmatter.get("metadata")
    if metadata is None:
        return errors
    if not isinstance(metadata, dict):
        errors.append("invalid:metadata:not-object")
        return errors

    openclaw_meta = metadata.get("openclaw")
    if openclaw_meta is None:
        errors.append("missing:metadata.openclaw")
        return errors
    if not isinstance(openclaw_meta, dict):
        errors.append("invalid:metadata.openclaw:not-object")
        return errors
    if "category" not in openclaw_meta:
        errors.append("missing:metadata.openclaw.category")

    return errors


def build_skill_record(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    frontmatter = None
    frontmatter_errors: list[str] = []
    skill_md_text = ""
    if skill_md.exists():
        skill_md_text = read_text(skill_md)
        frontmatter, _, frontmatter_errors = split_frontmatter(skill_md_text)
    else:
        frontmatter_errors = ["missing:SKILL.md"]

    validation_errors = validate_frontmatter(frontmatter)
    root_python_files = detect_root_python_files(skill_dir)
    cli_entrypoints = detect_cli_entrypoints(skill_dir)
    code_files = detect_code_files(skill_dir)
    test_files = detect_tests(skill_dir)
    dependency_files = detect_dependency_files(skill_dir)
    license_files = detect_license_files(skill_dir)
    frontmatter_name = frontmatter.get("name") if isinstance(frontmatter, dict) else None
    languages = infer_languages(code_files)
    governance_scope = infer_governance_scope(skill_dir.name, frontmatter)
    category = infer_category(frontmatter) or infer_health_category(skill_dir.name, frontmatter)
    distribution_tier = infer_distribution_tier(
        skill_dir.name,
        frontmatter,
        skill_md_text,
        governance_scope,
    )
    repo_license_files = detect_repo_license_files()
    allowed_tools = normalize_allowed_tools(frontmatter.get("allowed-tools") if isinstance(frontmatter, dict) else None)
    license_evidence = infer_license_evidence(
        frontmatter=frontmatter,
        license_files=license_files,
        repo_license_files=repo_license_files,
        skill_md_text=skill_md_text,
        distribution_tier=distribution_tier,
    )
    audit_status = infer_audit_status(
        governance_scope=governance_scope,
        frontmatter_valid=len(validation_errors) == 0,
        distribution_tier=distribution_tier,
        license_evidence=license_evidence,
        allowed_tools=allowed_tools,
    )

    record = {
        "slug": skill_dir.name,
        "path": str(skill_dir.relative_to(repo_root())),
        "has_skill_md": skill_md.exists(),
        "has_readme": (skill_dir / "README.md").exists(),
        "has_frontmatter": frontmatter is not None,
        "frontmatter_parse_errors": frontmatter_errors,
        "frontmatter_valid": len(validation_errors) == 0,
        "frontmatter_validation_errors": validation_errors,
        "name": str(frontmatter_name or skill_dir.name),
        "description": frontmatter.get("description") if isinstance(frontmatter, dict) else None,
        "version": frontmatter.get("version") if isinstance(frontmatter, dict) else None,
        "user_invocable": frontmatter.get("user-invocable") if isinstance(frontmatter, dict) else None,
        "allowed_tools": allowed_tools,
        "category": category,
        "metadata": frontmatter.get("metadata") if isinstance(frontmatter, dict) else None,
        "has_code": len(code_files) > 0,
        "code_file_count": len(code_files),
        "code_files": code_files,
        "languages": languages,
        "primary_language": languages[0] if languages else None,
        "has_dependencies": len(dependency_files) > 0,
        "dependency_files": dependency_files,
        "root_python_files": root_python_files,
        "cli_entrypoints": cli_entrypoints,
        "primary_cli_entrypoint": cli_entrypoints[0] if cli_entrypoints else None,
        "has_tests": len(test_files) > 0,
        "test_files": test_files,
        "license_files": license_files,
        "license_status": "present" if license_files or license_evidence else "unknown",
        "license_evidence": license_evidence,
        "governance_scope": governance_scope,
        "distribution_tier": distribution_tier,
        "audit_status": audit_status,
        "is_health_skill": governance_scope == "health-core",
    }
    return record


def build_manifest_records() -> list[dict[str, Any]]:
    return [build_skill_record(skill_dir) for skill_dir in iter_skill_dirs(include_shared=False)]


def manifest_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    def count(predicate) -> int:
        return sum(1 for record in records if predicate(record))

    return {
        "skill_count": len(records),
        "health_skill_count": count(lambda record: record["is_health_skill"]),
        "with_frontmatter": count(lambda record: record["has_frontmatter"]),
        "frontmatter_valid": count(lambda record: record["frontmatter_valid"]),
        "with_code": count(lambda record: record["has_code"]),
        "with_tests": count(lambda record: record["has_tests"]),
        "with_cli_entrypoints": count(lambda record: bool(record["cli_entrypoints"])),
        "user_invocable_true": count(lambda record: record["user_invocable"] is True),
        "user_invocable_missing": count(lambda record: record["user_invocable"] is None),
        "health_core_core": count(
            lambda record: record["governance_scope"] == "health-core"
            and record["distribution_tier"] == "core"
        ),
        "health_core_labs": count(
            lambda record: record["governance_scope"] == "health-core"
            and record["distribution_tier"] == "labs"
        ),
        "health_core_restricted": count(
            lambda record: record["governance_scope"] == "health-core"
            and record["distribution_tier"] == "restricted"
        ),
        "health_core_audit_pass": count(
            lambda record: record["governance_scope"] == "health-core"
            and record["audit_status"] == "pass"
        ),
        "out_of_scope_count": count(lambda record: record["governance_scope"] == "out-of-scope"),
    }


def group_records_by(records: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        group_name = str(record.get(key) or "uncategorized")
        grouped.setdefault(group_name, []).append(record)
    return grouped


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
