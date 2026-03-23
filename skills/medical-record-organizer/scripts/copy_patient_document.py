#!/usr/bin/env python3
"""Fail-closed copy helper for medical-record-organizer.

This script is the mandatory gate between a raw intake file and the classified
patient archive. When privacy mode is ON and the source is an image, the script
will run OCR redaction first and refuse to copy the original image into the
classified archive unless a redacted file is successfully produced.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def _normalize_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "on", "yes", "y"}:
        return True
    if text in {"0", "false", "off", "no", "n"}:
        return False
    return default


def _default_redact_cmd() -> list[str]:
    script_path = Path(__file__).with_name("redact_ocr.py")
    return [sys.executable, str(script_path)]


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _backup_original(source: Path, patient_dir: Path, sequence: str) -> Path:
    suffix = source.suffix or ""
    backup_path = patient_dir / "10_原始文件" / "原始未遮挡" / f"{sequence}{suffix}"
    _ensure_parent(backup_path)
    shutil.copy2(source, backup_path)
    return backup_path


def _run_redaction(
    source: Path,
    output: Path,
    redact_cmd: list[str] | None = None,
) -> dict:
    command = list(redact_cmd or _default_redact_cmd())
    command.extend([str(source), "--output", str(output)])
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout = completed.stdout.strip()
    payload = None
    if stdout:
        try:
            payload = json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError:
            payload = None

    success = completed.returncode == 0 and bool(payload and payload.get("success"))
    return {
        "success": success,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": completed.stderr.strip(),
        "payload": payload or {},
        "command": command,
    }


def copy_patient_document(
    *,
    source_path: str,
    patient_dir: str,
    target_rel_path: str,
    sequence: str,
    privacy_mode: bool = True,
    redacted_source: str | None = None,
    redact_cmd: list[str] | None = None,
) -> dict:
    source = Path(source_path).expanduser().resolve()
    archive_root = Path(patient_dir).expanduser().resolve()
    target = archive_root / target_rel_path

    if not source.exists():
        return {
            "success": False,
            "blocked": True,
            "stage": "input-validation",
            "error": f"Source file not found: {source}",
        }

    backup_path = _backup_original(source, archive_root, sequence)
    is_image = source.suffix.lower() in IMAGE_SUFFIXES
    requires_redaction = privacy_mode and is_image
    redaction_info = None
    source_used = source

    if requires_redaction:
        if redacted_source:
            source_used = Path(redacted_source).expanduser().resolve()
            if source_used == source:
                return {
                    "success": False,
                    "blocked": True,
                    "stage": "privacy-gate",
                    "error": "Privacy mode is ON, but the provided redacted source points to the original image.",
                    "backup_path": str(backup_path),
                    "target_path": str(target),
                }
            if not source_used.exists():
                return {
                    "success": False,
                    "blocked": True,
                    "stage": "privacy-gate",
                    "error": f"Redacted source not found: {source_used}",
                    "backup_path": str(backup_path),
                    "target_path": str(target),
                }
        else:
            source_used = source.parent / f"{source.stem}_redacted{source.suffix}"
            redaction_info = _run_redaction(
                source=source,
                output=source_used,
                redact_cmd=redact_cmd,
            )
            if not redaction_info["success"] or not source_used.exists():
                return {
                    "success": False,
                    "blocked": True,
                    "stage": "privacy-gate",
                    "error": (
                        "Privacy mode is ON and image redaction did not complete successfully. "
                        "The original file was backed up, but the classified archive copy was blocked."
                    ),
                    "backup_path": str(backup_path),
                    "target_path": str(target),
                    "redaction": redaction_info,
                }

    _ensure_parent(target)
    shutil.copy2(source_used, target)
    return {
        "success": True,
        "blocked": False,
        "privacy_mode": "ON" if privacy_mode else "OFF",
        "requires_redaction": requires_redaction,
        "backup_path": str(backup_path),
        "target_path": str(target),
        "source_used": str(source_used),
        "redaction": redaction_info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy a patient document into the archive with mandatory privacy gating."
    )
    parser.add_argument("source", help="Raw intake file path")
    parser.add_argument("--patient-dir", required=True, help="Patient archive root directory")
    parser.add_argument(
        "--target-rel",
        required=True,
        help="Target path relative to patient archive root",
    )
    parser.add_argument(
        "--sequence",
        default="0001",
        help="Sequence number for 10_原始文件/原始未遮挡 backup (default: 0001)",
    )
    parser.add_argument(
        "--privacy-mode",
        default="on",
        help="on/off (default: on)",
    )
    parser.add_argument(
        "--redacted-source",
        help="Optional pre-generated redacted file path. If omitted, image redaction is attempted automatically.",
    )
    parser.add_argument(
        "--redact-cmd",
        nargs="+",
        help="Override redact command for testing or custom runtimes.",
    )
    args = parser.parse_args()

    result = copy_patient_document(
        source_path=args.source,
        patient_dir=args.patient_dir,
        target_rel_path=args.target_rel,
        sequence=args.sequence,
        privacy_mode=_normalize_bool(args.privacy_mode, default=True),
        redacted_source=args.redacted_source,
        redact_cmd=args.redact_cmd,
    )
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 2)


if __name__ == "__main__":
    main()
