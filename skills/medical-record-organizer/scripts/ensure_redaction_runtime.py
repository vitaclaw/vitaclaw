#!/usr/bin/env python3
"""Prepare PaddleOCR/PaddleNLP runtime for mandatory image redaction."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _load_redact_module():
    script_path = Path(__file__).with_name("redact_ocr.py")
    namespace: dict = {}
    exec(script_path.read_text(encoding="utf-8"), namespace)
    return namespace


def _runtime_check() -> dict:
    module = _load_redact_module()
    return module["runtime_check"]()


def _candidate_install_commands() -> list[list[str]]:
    commands: list[list[str]] = []
    packages = ["pillow", "paddlepaddle", "paddleocr", "paddlenlp", "opencv-python", "PyMuPDF"]
    if shutil.which("uv"):
        commands.append(["uv", "pip", "install", *packages])
    commands.append([sys.executable, "-m", "pip", "install", *packages])
    return commands


def _select_install_command(preferred: str | None = None) -> list[str]:
    packages = ["pillow", "paddlepaddle", "paddleocr", "paddlenlp", "opencv-python", "PyMuPDF"]
    if preferred == "uv" and shutil.which("uv"):
        return ["uv", "pip", "install", *packages]
    if preferred == "pip":
        return [sys.executable, "-m", "pip", "install", *packages]
    for command in _candidate_install_commands():
        if command[0] == "uv" and not shutil.which("uv"):
            continue
        return command
    return [sys.executable, "-m", "pip", "install", *packages]


def ensure_runtime(auto_install: bool = False, installer: str | None = None) -> dict:
    check = _runtime_check()
    result = {
        "success": check.get("success", False),
        "ready": check.get("success", False),
        "auto_install_attempted": False,
        "check": check,
        "install_required": not check.get("success", False),
        "recommended_commands": _candidate_install_commands(),
    }
    if check.get("success", False) or not auto_install:
        return result

    command = _select_install_command(installer)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    post_check = _runtime_check()
    result.update(
        {
            "success": post_check.get("success", False),
            "ready": post_check.get("success", False),
            "auto_install_attempted": True,
            "install_command": command,
            "install_returncode": completed.returncode,
            "install_stdout": completed.stdout.strip(),
            "install_stderr": completed.stderr.strip(),
            "check": post_check,
            "install_required": not post_check.get("success", False),
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ensure PaddleOCR/PaddleNLP runtime for medical image redaction."
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Check runtime readiness and exit non-zero if redaction runtime is not ready.",
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Attempt to install missing dependencies before re-checking readiness.",
    )
    parser.add_argument(
        "--installer",
        choices=("auto", "uv", "pip"),
        default="auto",
        help="Preferred installer when --auto-install is used.",
    )
    args = parser.parse_args()

    preferred = None if args.installer == "auto" else args.installer
    result = ensure_runtime(auto_install=args.auto_install, installer=preferred)
    print(json.dumps(result, ensure_ascii=False))

    if result.get("success"):
        raise SystemExit(0)
    if args.require_ready or args.auto_install:
        raise SystemExit(2)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
