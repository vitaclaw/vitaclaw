#!/usr/bin/env python3
"""Repository-level smoke tests for VitaClaw skills."""

from __future__ import annotations

import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path
from shutil import which

from skill_catalog import build_manifest_records, repo_root, write_json


CORE_HELP_COMMANDS = {
    "blood-pressure-tracker": [
        "python3",
        "skills/blood-pressure-tracker/blood_pressure_tracker.py",
        "--help",
    ],
    "chronic-condition-monitor": [
        "python3",
        "skills/chronic-condition-monitor/chronic_condition_monitor.py",
        "--help",
    ],
    "weekly-health-digest": [
        "python3",
        "skills/weekly-health-digest/weekly_health_digest.py",
        "--help",
    ],
    "sleep-analyzer": [
        "python3",
        "skills/sleep-analyzer/sleep_analyzer.py",
        "--help",
    ],
    "sleep-optimizer": [
        "python3",
        "skills/sleep-optimizer/sleep_optimizer.py",
        "--help",
    ],
    "caffeine-tracker": [
        "python3",
        "skills/caffeine-tracker/caffeine_tracker.py",
        "--help",
    ],
    "supplement-manager": [
        "python3",
        "skills/supplement-manager/supplement_manager.py",
        "--help",
    ],
}


def run_command(cmd: list[str], cwd: Path) -> dict:
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "duration_ms": duration_ms,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
    }


def detected_cli_commands() -> dict[str, list[str]]:
    commands = {}
    for record in build_manifest_records():
        entrypoint = record.get("primary_cli_entrypoint")
        if not entrypoint:
            continue
        commands[record["slug"]] = ["python3", f"{record['path']}/{entrypoint}", "--help"]
    return commands


def health_core_compile_commands(records: list[dict]) -> dict[str, list[str]]:
    commands: dict[str, list[str]] = {}
    for record in records:
        if record["governance_scope"] != "health-core" or not record["has_code"]:
            continue
        if record["primary_language"] == "python":
            targets = [
                f"{record['path']}/{relative_path}"
                for relative_path in record["code_files"]
                if relative_path.endswith(".py")
            ]
            if targets:
                commands[f"{record['slug']}::py_compile"] = ["python3", "-m", "py_compile", *targets]
        elif record["primary_language"] == "javascript" and which("node"):
            targets = [
                f"{record['path']}/{relative_path}"
                for relative_path in record["code_files"]
                if relative_path.endswith((".js", ".mjs", ".cjs"))
            ]
            for target in targets:
                commands[f"{record['slug']}::node_check::{Path(target).name}"] = ["node", "--check", target]
    return commands


def health_core_cli_commands(records: list[dict]) -> dict[str, list[str]]:
    commands: dict[str, list[str]] = {}
    for record in records:
        if record["governance_scope"] != "health-core":
            continue
        entrypoint = record.get("primary_cli_entrypoint")
        if not entrypoint:
            continue
        commands[f"{record['slug']}::help"] = ["python3", f"{record['path']}/{entrypoint}", "--help"]
    return commands


def health_core_smoke_commands() -> dict[str, list[str]]:
    records = build_manifest_records()
    command_map = {}
    command_map.update(health_core_compile_commands(records))
    command_map.update(health_core_cli_commands(records))
    return command_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repository-level skill smoke tests")
    parser.add_argument(
        "--mode",
        choices=["core", "all-cli", "health-core"],
        default="core",
        help="Test the curated core set, all detected CLI entrypoints, or the Iteration 1 health-core scope",
    )
    parser.add_argument(
        "--scope",
        choices=["all", "health-core"],
        default="all",
        help="Alias filter that can force the health-core pipeline regardless of mode",
    )
    parser.add_argument(
        "--output",
        default="reports/skill-smoke-report.json",
        help="Report path relative to the repo root",
    )
    parser.add_argument(
        "--include-unit-tests",
        action="store_true",
        help="Run python3 -m unittest discover -s tests before CLI smoke tests",
    )
    parser.add_argument(
        "--include-health-e2e",
        action="store_true",
        help="Run the current hypertension/diabetes/annual-checkup end-to-end test subset before smoke tests",
    )
    args = parser.parse_args()

    cwd = repo_root()
    effective_mode = "health-core" if args.scope == "health-core" else args.mode
    if effective_mode == "core":
        command_map = CORE_HELP_COMMANDS
    elif effective_mode == "all-cli":
        command_map = detected_cli_commands()
    else:
        command_map = health_core_smoke_commands()
    results = []

    if args.include_unit_tests:
        results.append(
            {
                "slug": "repo-unit-tests",
                **run_command(["python3", "-m", "unittest", "discover", "-s", "tests"], cwd),
            }
        )

    if args.include_health_e2e:
        e2e_modules = [
            "tests.test_hypertension_workflow",
            "tests.test_diabetes_workflow",
            "tests.test_annual_checkup_memory",
        ]
        results.append(
            {
                "slug": "health-core-e2e",
                **run_command(["python3", "-m", "unittest", *e2e_modules], cwd),
            }
        )

    for slug, cmd in sorted(command_map.items()):
        result = run_command(cmd, cwd)
        result["slug"] = slug
        results.append(result)
        print(f"[{'OK' if result['ok'] else 'FAIL'}] {slug} ({result['duration_ms']} ms)")

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": effective_mode,
        "scope": args.scope,
        "result_count": len(results),
        "passed": sum(1 for result in results if result["ok"]),
        "failed": sum(1 for result in results if not result["ok"]),
        "results": results,
    }
    output_path = cwd / args.output
    write_json(output_path, payload)
    print(f"smoke report written to {output_path}")

    if payload["failed"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
