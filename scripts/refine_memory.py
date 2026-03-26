#!/usr/bin/env python3
"""Sleep-time memory refinement — the Digital Twin's offline learning.

Runs periodically (e.g. nightly cron) to:
  1. Check expired facts and archive them
  2. Detect contradictions between items
  3. Merge trend updates
  4. Update confidence scores based on source count

v1: Health data refinement only.
v2: Extends to cognitive/behavioral twin state updates.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from memory_lifecycle import HealthFact, MemoryLifecycle  # noqa: E402


def refine_memory(
    workspace_root: str | None = None,
    memory_dir: str | None = None,
    dry_run: bool = False,
    now_fn=None,
) -> dict:
    """Run memory refinement cycle.

    Returns summary of actions taken.
    """
    lifecycle = MemoryLifecycle(
        memory_dir=memory_dir,
        workspace_root=workspace_root,
        now_fn=now_fn,
    )

    if memory_dir:
        items_dir = Path(memory_dir) / "items"
    elif workspace_root:
        items_dir = Path(workspace_root) / "memory" / "health" / "items"
    else:
        items_dir = ROOT / "memory" / "health" / "items"

    summary = {
        "items_processed": 0,
        "facts_processed": 0,
        "consolidated": 0,
        "archived": 0,
        "actions": [],
    }

    if not items_dir.exists():
        summary["actions"].append("items directory not found — nothing to refine")
        return summary

    for item_file in sorted(items_dir.glob("*.md")):
        if dry_run:
            summary["actions"].append(f"[dry-run] would process {item_file.name}")
            summary["items_processed"] += 1
            continue

        result = lifecycle.process_item_facts(item_file)
        summary["items_processed"] += 1
        summary["facts_processed"] += result["processed"]
        summary["consolidated"] += result["consolidated"]
        summary["archived"] += result["archived"]

        if result["consolidated"] > 0:
            summary["actions"].append(
                f"{item_file.name}: consolidated {result['consolidated']} facts"
            )
        if result["archived"] > 0:
            summary["actions"].append(
                f"{item_file.name}: archived {result['archived']} expired facts"
            )

    if not summary["actions"]:
        summary["actions"].append("no refinement actions needed")

    return summary


def main():
    parser = argparse.ArgumentParser(description="VitaClaw sleep-time memory refinement")
    parser.add_argument("--workspace", default=None, help="Workspace root directory")
    parser.add_argument("--memory-dir", default=None, help="Memory directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    result = refine_memory(
        workspace_root=args.workspace,
        memory_dir=args.memory_dir,
        dry_run=args.dry_run,
    )

    print(f"Items processed: {result['items_processed']}")
    print(f"Facts processed: {result['facts_processed']}")
    print(f"Consolidated: {result['consolidated']}")
    print(f"Archived: {result['archived']}")
    for action in result["actions"]:
        print(f"  - {action}")


if __name__ == "__main__":
    main()
