#!/usr/bin/env python3
"""Build layered VitaClaw release directories from package manifests."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def manifests_dir() -> Path:
    return repo_root() / "packages"


def available_packages() -> list[str]:
    return sorted(path.stem for path in manifests_dir().glob("*.json"))


def load_manifest(name: str) -> dict:
    path = manifests_dir() / f"{name}.json"
    if not path.exists():
        available = ", ".join(available_packages())
        raise ValueError(f"Unknown package '{name}'. Available: {available}")
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_matches(pattern: str) -> list[Path]:
    root = repo_root()
    matches = sorted(root.glob(pattern))
    result: list[Path] = []
    for path in matches:
        if "__pycache__" in path.parts:
            continue
        if path.is_dir():
            for nested in sorted(path.rglob("*")):
                if nested.is_file() and "__pycache__" not in nested.parts:
                    result.append(nested)
        elif path.is_file():
            result.append(path)
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in result:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return deduped


def build_package(name: str, dist_dir: Path, clean: bool = False) -> Path:
    root = repo_root()
    manifest = load_manifest(name)
    package_dir = dist_dir / manifest["name"]
    if clean and package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    included: list[str] = []
    for pattern in manifest.get("include", []):
        for source in _iter_matches(pattern):
            relative = source.relative_to(root)
            target = package_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            included.append(relative.as_posix())

    manifest_out = {
        "name": manifest["name"],
        "tier": manifest.get("tier", "stable"),
        "description": manifest.get("description", ""),
        "file_count": len(included),
        "files": included,
    }
    (package_dir / "package-manifest.json").write_text(
        json.dumps(manifest_out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    readme_lines = [
        f"# {manifest['name']}",
        "",
        f"- Tier: {manifest.get('tier', 'stable')}",
        f"- Description: {manifest.get('description', '')}",
        f"- Files: {len(included)}",
        "",
        "## Usage",
        "",
        "- Use `scripts/init_health_workspace.py` to initialize the matching workspace template.",
        "- Use `scripts/run_health_chief_of_staff.py` as the single-entry team workflow runner.",
    ]
    (package_dir / "README.md").write_text("\n".join(readme_lines).rstrip() + "\n", encoding="utf-8")
    return package_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VitaClaw layered release directories")
    parser.add_argument(
        "--package",
        choices=["all", *available_packages()],
        default="all",
        help="Package to build",
    )
    parser.add_argument("--dist-dir", default="dist", help="Output dist directory")
    parser.add_argument("--clean", action="store_true", help="Remove package directory before building")
    args = parser.parse_args()

    dist_dir = (repo_root() / args.dist_dir).resolve()
    dist_dir.mkdir(parents=True, exist_ok=True)

    package_names = available_packages() if args.package == "all" else [args.package]
    for name in package_names:
        built = build_package(name, dist_dir=dist_dir, clean=args.clean)
        print(f"built {name}: {built}")


if __name__ == "__main__":
    main()
