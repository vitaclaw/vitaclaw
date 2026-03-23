#!/usr/bin/env python3
"""Manage stateful heartbeat tasks for a VitaClaw health workspace."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SHARED_DIR = os.path.join(ROOT, "skills", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from health_reminder_center import HealthReminderCenter  # noqa: E402


def _build_center(args) -> HealthReminderCenter:
    return HealthReminderCenter(
        memory_dir=args.memory_dir,
        workspace_root=args.workspace_root,
    )


def _print_tasks(tasks: list[dict]) -> None:
    if not tasks:
        print("当前没有匹配的 heartbeat 任务。")
        return

    print(f"# Health Heartbeat Tasks ({len(tasks)})\n")
    for task in tasks:
        print(f"- {task['id']} | {task.get('priority', 'low')} | {task.get('status', 'open')} | {task.get('title', 'Untitled')}")
        print(f"  原因：{task.get('reason', 'pending')}")
        if task.get("next_step"):
            print(f"  下一步：{task['next_step']}")
        if task.get("next_follow_up_at"):
            print(f"  下次跟进：{task['next_follow_up_at']}")
        if task.get("execution_mode"):
            print(f"  执行模式：{task['execution_mode']}")
        if task.get("delivery_note"):
            print(f"  备注：{task['delivery_note']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage VitaClaw health heartbeat tasks")
    parser.add_argument("--workspace-root", default=None, help="OpenClaw workspace root")
    parser.add_argument("--memory-dir", default=None, help="memory/health directory")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_list = subparsers.add_parser("list", help="List heartbeat tasks")
    p_list.add_argument("--status", default=None, help="Filter by task status")

    p_complete = subparsers.add_parser("complete", help="Mark task as completed")
    p_complete.add_argument("task_id", help="Task id")
    p_complete.add_argument("--note", default="", help="Optional completion note")

    p_snooze = subparsers.add_parser("snooze", help="Temporarily silence a task")
    p_snooze.add_argument("task_id", help="Task id")
    p_snooze.add_argument("--hours", type=int, default=24, help="Snooze duration in hours")
    p_snooze.add_argument("--until", default=None, help="Absolute ISO datetime")
    p_snooze.add_argument("--note", default="", help="Optional snooze note")

    p_reopen = subparsers.add_parser("reopen", help="Reopen a completed or resolved task")
    p_reopen.add_argument("task_id", help="Task id")
    p_reopen.add_argument("--note", default="", help="Optional reopen note")

    args = parser.parse_args()
    center = _build_center(args)

    if args.command == "list":
        tasks = center.list_tasks(status=args.status)
        if args.format == "json":
            print(json.dumps(tasks, ensure_ascii=False, indent=2))
            return
        _print_tasks(tasks)
        return

    if args.command == "complete":
        result = center.complete_task(args.task_id, note=args.note)
    elif args.command == "snooze":
        result = center.snooze_task(args.task_id, hours=args.hours, until=args.until, note=args.note)
    else:
        result = center.reopen_task(args.task_id, note=args.note)

    if args.format == "json":
        print(json.dumps(result or {}, ensure_ascii=False, indent=2))
        return

    if not result:
        print("未找到对应任务。")
        return
    print(f"已更新任务：{result['id']} -> {result.get('status')}")
    if result.get("delivery_note"):
        print(result["delivery_note"])


if __name__ == "__main__":
    main()
