#!/usr/bin/env python3
"""Update one ledger task status and checkbox."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from validate_ledgers import ALLOWED_STATUSES, parse_tasks


CHECKBOX_CHOICES = {"auto", "checked", "unchecked"}


def desired_mark(status: str, checkbox: str) -> str:
    if checkbox == "checked":
        return "x"
    if checkbox == "unchecked":
        return " "
    return "x" if status == "verified" else " "


def replace_task_line(line: str, mark: str) -> str:
    return re.sub(r"^- \[[ xX]\]", f"- [{mark}]", line, count=1)


def replace_status_line(line: str, status: str) -> str:
    return re.sub(r"^(\s+- Status:\s*).*", rf"\g<1>{status}", line, count=1)


def update_task(root: Path, task_id: str, status: str, checkbox: str) -> None:
    tasks_path = root / "AGENT_TASKS.md"
    if not tasks_path.exists():
        raise RuntimeError("AGENT_TASKS.md does not exist")

    tasks, _ = parse_tasks(tasks_path)
    target = next((task for task in tasks if task.task_id == task_id), None)
    if target is None:
        raise RuntimeError(f"task {task_id} not found")

    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    mark = desired_mark(status, checkbox)
    lines[target.line - 1] = replace_task_line(lines[target.line - 1], mark)

    status_field = target.fields.get("Status")
    if status_field is None:
        lines.insert(target.line, f"  - Status: {status}")
    else:
        lines[status_field.line - 1] = replace_status_line(lines[status_field.line - 1], status)

    tasks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update one project-task-executor task.")
    parser.add_argument("--root", default=".", help="Project root containing AGENT_TASKS.md.")
    parser.add_argument("--task", required=True, help="Task id, for example T001.")
    parser.add_argument("--status", required=True, choices=sorted(ALLOWED_STATUSES))
    parser.add_argument("--checkbox", default="auto", choices=sorted(CHECKBOX_CHOICES))
    args = parser.parse_args()

    try:
        update_task(Path(args.root).resolve(), args.task, args.status, args.checkbox)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"updated {args.task}: Status={args.status}, checkbox={args.checkbox}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
