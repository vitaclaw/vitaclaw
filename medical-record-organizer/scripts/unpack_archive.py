#!/usr/bin/env python3
"""Unpack archive files (.zip, .rar, .7z) and list medical document files."""

import sys
import os
import json
import time
import tempfile
import zipfile
import subprocess
from pathlib import Path

MEDICAL_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}


def make_tmp_dir() -> str:
    timestamp = int(time.time() * 1000)
    tmp_dir = os.path.join(tempfile.gettempdir(), f"openclaw_unpack_{timestamp}")
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


def list_files(directory: str) -> list:
    """Recursively list files with medical extensions."""
    results = []
    for root, _dirs, files in os.walk(directory):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in MEDICAL_EXTENSIONS:
                full_path = os.path.join(root, fname)
                results.append({
                    "path": full_path,
                    "name": fname,
                    "ext": ext,
                })
    return results


def unpack_zip(archive_path: str, output_dir: str) -> None:
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(output_dir)


def unpack_rar(archive_path: str, output_dir: str) -> None:
    # Try unrar command first
    try:
        result = subprocess.run(
            ["unrar", "x", "-o+", archive_path, output_dir + "/"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
    except FileNotFoundError:
        pass

    # Try unar command
    try:
        result = subprocess.run(
            ["unar", "-o", output_dir, archive_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
    except FileNotFoundError:
        pass

    # Fallback to rarfile library
    try:
        import rarfile
        with rarfile.RarFile(archive_path) as rf:
            rf.extractall(output_dir)
        return
    except ImportError:
        pass

    raise RuntimeError(
        "Cannot extract RAR file: none of unrar, unar, or rarfile library is available"
    )


def unpack_7z(archive_path: str, output_dir: str) -> None:
    result = subprocess.run(
        ["7z", "x", f"-o{output_dir}", archive_path, "-y"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"7z extraction failed: {result.stderr}")


def main() -> None:
    if len(sys.argv) < 2:
        print(
            json.dumps({"success": False, "error": "Usage: python3 unpack_archive.py [archive_path] [optional_output_dir]"}),
            flush=True,
        )
        sys.exit(1)

    archive_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.isfile(archive_path):
        print(
            json.dumps({"success": False, "error": f"File not found: {archive_path}"}),
            flush=True,
        )
        sys.exit(1)

    ext = os.path.splitext(archive_path)[1].lower()
    tmp_dir = output_dir or make_tmp_dir()

    try:
        if ext == ".zip":
            unpack_zip(archive_path, tmp_dir)
        elif ext == ".rar":
            unpack_rar(archive_path, tmp_dir)
        elif ext == ".7z":
            unpack_7z(archive_path, tmp_dir)
        else:
            print(
                json.dumps({"success": False, "error": f"Unsupported archive format: {ext}"}),
                flush=True,
            )
            sys.exit(1)

        files = list_files(tmp_dir)
        result = {
            "success": True,
            "tmp_dir": tmp_dir,
            "files": files,
            "total": len(files),
        }
        print(json.dumps(result, ensure_ascii=False), flush=True)

    except Exception as e:
        print(
            json.dumps({"success": False, "error": str(e)}),
            flush=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
