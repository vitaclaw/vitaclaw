#!/usr/bin/env python3
"""Retroactively redact already-archived patient images in-place."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SKIP_PARTS = {"10_原始文件", "原始未遮挡"}


def _default_redact_cmd() -> list[str]:
    script_path = Path(__file__).with_name("redact_ocr.py")
    return [sys.executable, str(script_path)]


def _should_skip(path: Path, patient_dir: Path) -> bool:
    try:
        rel_parts = path.relative_to(patient_dir).parts
    except ValueError:
        return True
    if any(part in SKIP_PARTS for part in rel_parts):
        return True
    if path.name.endswith("_redacted" + path.suffix):
        return True
    if path.name.endswith("_debug" + path.suffix):
        return True
    return False


def _run_redaction(source: Path, output: Path, redact_cmd: list[str] | None = None) -> dict:
    command = list(redact_cmd or _default_redact_cmd())
    command.extend([str(source), "--output", str(output)])
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    payload = {}
    if stdout:
        try:
            payload = json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError:
            payload = {}
    return {
        "success": completed.returncode == 0 and bool(payload.get("success")),
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": completed.stderr.strip(),
        "payload": payload,
        "command": command,
    }


def repair_patient_images(patient_dir: str, redact_cmd: list[str] | None = None) -> dict:
    root = Path(patient_dir).expanduser().resolve()
    if not root.exists():
        return {"success": False, "error": f"Patient directory not found: {root}"}

    repaired: list[dict] = []
    failed: list[dict] = []
    skipped: list[str] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if _should_skip(path, root):
            skipped.append(str(path))
            continue

        temp_output = path.with_name(f"{path.stem}_redacted{path.suffix}")
        result = _run_redaction(path, temp_output, redact_cmd=redact_cmd)
        if not result["success"] or not temp_output.exists():
            failed.append(
                {
                    "path": str(path),
                    "redaction": result,
                }
            )
            continue

        os.replace(temp_output, path)
        repaired.append(
            {
                "path": str(path),
                "pii_detected": result["payload"].get("pii_detected"),
            }
        )

    return {
        "success": not failed,
        "patient_dir": str(root),
        "repaired": repaired,
        "failed": failed,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repair already-archived patient images by redacting them in-place."
    )
    parser.add_argument("--patient-dir", required=True, help="Patient archive root directory")
    parser.add_argument(
        "--redact-cmd",
        nargs="+",
        help="Override redact command for testing or custom runtimes.",
    )
    args = parser.parse_args()

    result = repair_patient_images(
        patient_dir=args.patient_dir,
        redact_cmd=args.redact_cmd,
    )
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 2)


if __name__ == "__main__":
    main()
