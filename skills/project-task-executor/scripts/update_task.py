#!/usr/bin/env python3
"""Update one ledger task status and checkbox."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from event_log import append_event
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


def field_line(key: str, value: str) -> str:
    return f"  - {key}: {value}"


def replace_field_line(line: str, key: str, value: str) -> str:
    prefix_match = re.match(r"^(\s*)-", line)
    prefix = prefix_match.group(1) if prefix_match else "  "
    return f"{prefix}- {key}: {value}"


def task_block_end(lines: list[str], start_index: int) -> int:
    for index in range(start_index + 1, len(lines)):
        if re.match(r"^- \[[ xX]\] T\d{3,}:", lines[index]):
            return index
    return len(lines)


def upsert_field(lines: list[str], start_index: int, key: str, value: str) -> None:
    end_index = task_block_end(lines, start_index)
    for index in range(start_index + 1, end_index):
        if re.match(rf"^\s+- {re.escape(key)}:\s*", lines[index]):
            lines[index] = replace_field_line(lines[index], key, value)
            return

    insert_at = end_index
    for index in range(end_index - 1, start_index, -1):
        if re.match(r"^\s+- [A-Za-z ]+:\s*", lines[index]):
            insert_at = index + 1
            break
    lines.insert(insert_at, field_line(key, value))


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def update_task(
    root: Path,
    task_id: str,
    status: str | None,
    checkbox: str,
    *,
    claim: str | None = None,
    release: str | None = None,
    worktree: str | None = None,
) -> list[str]:
    tasks_path = root / "AGENT_TASKS.md"
    if not tasks_path.exists():
        raise RuntimeError("AGENT_TASKS.md does not exist")

    tasks, _ = parse_tasks(tasks_path)
    target = next((task for task in tasks if task.task_id == task_id), None)
    if target is None:
        raise RuntimeError(f"task {task_id} not found")

    if claim and release:
        raise RuntimeError("--claim and --release cannot be used together")

    messages: list[str] = []
    owner = target.field_value("Owner")
    original_status = target.status
    start_index = target.line - 1
    lines = tasks_path.read_text(encoding="utf-8").splitlines()

    if claim:
        if owner and owner != claim:
            raise RuntimeError(f"task {task_id} already claimed by {owner}")
        upsert_field(lines, start_index, "Owner", claim)
        upsert_field(lines, start_index, "Claimed at", utc_now())
        status = status or "in_progress"
        append_event(root, "task.claimed", task=task_id, owner=claim)
        messages.append(f"claimed by {claim}")

    if release:
        if owner and owner != release:
            raise RuntimeError(f"task {task_id} is owned by {owner}, not {release}")
        upsert_field(lines, start_index, "Owner", "")
        upsert_field(lines, start_index, "Claimed at", "")
        if status is None and original_status == "in_progress":
            status = "planned"
        append_event(root, "task.released", task=task_id, owner=release)
        messages.append(f"released by {release}")

    if worktree is not None:
        upsert_field(lines, start_index, "Worktree", worktree)
        append_event(root, "task.worktree_bound", task=task_id, worktree=worktree)
        messages.append(f"Worktree={worktree}")

    if status is not None:
        mark = desired_mark(status, checkbox)
        lines[start_index] = replace_task_line(lines[start_index], mark)

        status_field = target.fields.get("Status")
        if status_field is None:
            upsert_field(lines, start_index, "Status", status)
        else:
            lines[status_field.line - 1] = replace_status_line(lines[status_field.line - 1], status)
        if status != original_status:
            append_event(root, "task.status_changed", task=task_id, from_status=original_status, to_status=status)
        messages.append(f"Status={status}")

    tasks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Update one project-task-executor task.")
    parser.add_argument("--root", default=".", help="Project root containing AGENT_TASKS.md.")
    parser.add_argument("--task", required=True, help="Task id, for example T001.")
    parser.add_argument("--status", choices=sorted(ALLOWED_STATUSES))
    parser.add_argument("--checkbox", default="auto", choices=sorted(CHECKBOX_CHOICES))
    parser.add_argument("--claim", help="Claim the task for this owner and mark it in_progress unless --status is set.")
    parser.add_argument("--release", help="Release a task owned by this owner; in_progress tasks return to planned unless --status is set.")
    parser.add_argument("--worktree", help="Bind or update the optional Worktree field for this task.")
    args = parser.parse_args()

    if not any((args.status, args.claim, args.release, args.worktree is not None)):
        parser.error("one of --status, --claim, --release, or --worktree is required")

    try:
        messages = update_task(
            Path(args.root).resolve(),
            args.task,
            args.status,
            args.checkbox,
            claim=args.claim,
            release=args.release,
            worktree=args.worktree,
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    detail = ", ".join(messages) if messages else "updated"
    print(f"updated {args.task}: {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
