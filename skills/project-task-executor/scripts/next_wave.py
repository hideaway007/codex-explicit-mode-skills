#!/usr/bin/env python3
"""Print executable project-task-executor task ids."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validate_ledgers import is_bootstrap_task, parse_dependencies, parse_tasks


READY_STATUSES = {"", "planned"}


def find_next_wave(root: Path) -> tuple[list[str], list[str]]:
    tasks_path = root / "AGENT_TASKS.md"
    if not tasks_path.exists():
        raise RuntimeError("AGENT_TASKS.md does not exist")

    tasks, _ = parse_tasks(tasks_path)
    if not tasks:
        return [], ["no tasks found in AGENT_TASKS.md"]

    if len(tasks) == 1 and is_bootstrap_task(tasks[0]):
        raise RuntimeError(
            "AGENT_TASKS.md contains only the bootstrap task; replace or refine it into concrete tasks before dispatch"
        )

    tasks_by_id = {task.task_id: task for task in tasks}
    ready: list[str] = []
    waiting: list[str] = []

    for task in tasks:
        status = task.status
        if status not in READY_STATUSES:
            waiting.append(f"{task.task_id}: status is {status or 'empty'}")
            continue

        dependencies, invalid_tokens = parse_dependencies(task.field_value("Dependencies"))
        if invalid_tokens:
            waiting.append(f"{task.task_id}: invalid dependencies {', '.join(invalid_tokens)}")
            continue

        unmet: list[str] = []
        missing: list[str] = []
        for dependency in dependencies:
            dependency_task = tasks_by_id.get(dependency)
            if dependency_task is None:
                missing.append(dependency)
            elif dependency_task.status != "verified":
                unmet.append(dependency)

        if missing:
            waiting.append(f"{task.task_id}: missing dependencies {', '.join(missing)}")
        elif unmet:
            waiting.append(f"{task.task_id}: waiting for {', '.join(unmet)}")
        else:
            ready.append(task.task_id)

    return ready, waiting


def main() -> int:
    parser = argparse.ArgumentParser(description="Print executable project-task-executor task ids.")
    parser.add_argument("--root", default=".", help="Project root containing AGENT_TASKS.md.")
    args = parser.parse_args()

    try:
        ready, waiting = find_next_wave(Path(args.root).resolve())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if ready:
        print(" ".join(ready))
        return 0

    print("No executable tasks.")
    for reason in waiting:
        print(f"- {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
