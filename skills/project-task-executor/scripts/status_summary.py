#!/usr/bin/env python3
"""Summarize project-task-executor ledger, next wave, and git status."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from event_log import EVENTS_FILE
from next_wave import find_next_wave
from validate_ledgers import Issue, parse_review_verdict, parse_tasks, validate


def format_issue(issue: Issue, root: Path) -> str:
    return issue.format(root)


def summarize_tasks(root: Path) -> dict[str, object]:
    tasks_path = root / "AGENT_TASKS.md"
    if not tasks_path.exists():
        return {
            "counts_by_status": {},
            "blocked": [],
            "parse_issues": ["AGENT_TASKS.md does not exist"],
        }

    tasks, issues = parse_tasks(tasks_path)
    counts: dict[str, int] = {}
    blocked: list[dict[str, str]] = []
    claimed: list[dict[str, str]] = []
    worktrees: list[dict[str, str]] = []
    for task in tasks:
        status = task.status or "empty"
        counts[status] = counts.get(status, 0) + 1
        if task.status == "blocked":
            blocked.append({"id": task.task_id, "name": task.name})
        owner = task.field_value("Owner")
        if owner:
            claimed.append({"id": task.task_id, "name": task.name, "owner": owner})
        worktree = task.field_value("Worktree")
        if worktree:
            worktrees.append({"id": task.task_id, "name": task.name, "worktree": worktree})

    return {
        "counts_by_status": counts,
        "blocked": blocked,
        "claimed": claimed,
        "worktrees": worktrees,
        "parse_issues": [format_issue(issue, root) for issue in issues],
    }


def summarize_next_wave(root: Path) -> dict[str, object]:
    try:
        ready, waiting = find_next_wave(root)
    except RuntimeError as exc:
        return {"ready": [], "waiting": [], "error": str(exc)}
    return {"ready": ready, "waiting": waiting, "error": None}


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def summarize_git(root: Path) -> dict[str, object]:
    inside = run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "is_repo": False,
            "branch": None,
            "status_short": [],
            "diff_scope": [],
            "error": (inside.stderr or inside.stdout).strip() or "not a git repository",
        }

    branch = run_git(root, "branch", "--show-current")
    branch_name = branch.stdout.strip()
    if not branch_name:
        head = run_git(root, "rev-parse", "--short", "HEAD")
        branch_name = f"detached:{head.stdout.strip()}" if head.returncode == 0 else "unknown"

    status = run_git(root, "status", "--short")
    status_lines = [line for line in status.stdout.splitlines() if line.strip()]
    diff_scope = [line[3:] if len(line) > 3 else line for line in status_lines]

    return {
        "is_repo": True,
        "branch": branch_name,
        "status_short": status_lines,
        "diff_scope": diff_scope,
        "error": None,
    }


def summarize_review(root: Path) -> dict[str, object]:
    review_path = root / "AGENT_REVIEW.md"
    verdict, issues = parse_review_verdict(review_path)
    return {
        "verdict": verdict,
        "issues": [format_issue(issue, root) for issue in issues],
    }


def summarize_events(root: Path, limit: int = 5) -> dict[str, object]:
    events_path = root / EVENTS_FILE
    if not events_path.exists():
        return {"path": EVENTS_FILE, "recent": [], "issues": [f"{EVENTS_FILE} does not exist"]}

    recent: list[dict[str, object]] = []
    issues: list[str] = []
    for lineno, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(f"{EVENTS_FILE}:{lineno}: invalid JSON: {exc.msg}")
            continue
        if isinstance(event, dict):
            recent.append(event)
        else:
            issues.append(f"{EVENTS_FILE}:{lineno}: event must be an object")

    return {"path": EVENTS_FILE, "recent": recent[-limit:], "issues": issues}


def build_summary(root: Path) -> dict[str, object]:
    root = root.resolve()
    validation_issues = validate(root)
    return {
        "root": str(root),
        "ledger": {
            "valid": not validation_issues,
            "issues": [format_issue(issue, root) for issue in validation_issues],
        },
        "review": summarize_review(root),
        "tasks": summarize_tasks(root),
        "next_wave": summarize_next_wave(root),
        "git": summarize_git(root),
        "events": summarize_events(root),
    }


def render_text(summary: dict[str, object]) -> str:
    ledger = summary["ledger"]
    review = summary["review"]
    tasks = summary["tasks"]
    next_wave = summary["next_wave"]
    git = summary["git"]
    events = summary["events"]
    assert isinstance(ledger, dict)
    assert isinstance(review, dict)
    assert isinstance(tasks, dict)
    assert isinstance(next_wave, dict)
    assert isinstance(git, dict)
    assert isinstance(events, dict)

    ready = next_wave.get("ready") or []
    waiting = next_wave.get("waiting") or []
    blocked = tasks.get("blocked") or []
    claimed = tasks.get("claimed") or []
    worktrees = tasks.get("worktrees") or []
    counts = tasks.get("counts_by_status") or {}
    diff_scope = git.get("diff_scope") or []

    lines = [
        "Project Task Executor Status",
        f"Root: {summary['root']}",
        f"Ledger validation: {'PASS' if ledger.get('valid') else 'FAIL'}",
        f"Review verdict: {review.get('verdict') or 'missing'}",
        "Tasks: " + (", ".join(f"{key}={value}" for key, value in sorted(counts.items())) if counts else "none"),
        "Next wave: " + (" ".join(str(item) for item in ready) if ready else "none"),
    ]

    if next_wave.get("error"):
        lines.append(f"Next wave error: {next_wave['error']}")
    if waiting:
        lines.append("Waiting:")
        lines.extend(f"- {item}" for item in waiting)

    lines.append("Blocked tasks: " + (", ".join(f"{item['id']} {item['name']}" for item in blocked) if blocked else "none"))
    lines.append("Claimed tasks: " + (", ".join(f"{item['id']} owner={item['owner']}" for item in claimed) if claimed else "none"))
    lines.append("Worktrees: " + (", ".join(f"{item['id']} -> {item['worktree']}" for item in worktrees) if worktrees else "none"))

    if git.get("is_repo"):
        lines.append(f"Git: branch {git.get('branch')}")
    else:
        lines.append("Git: not a git repository")
    lines.append("Diff scope: " + (", ".join(str(item) for item in diff_scope) if diff_scope else "none"))
    recent_events = events.get("recent") or []
    lines.append(
        "Recent events: "
        + (
            ", ".join(str(event.get("event", "unknown")) for event in recent_events if isinstance(event, dict))
            if recent_events
            else "none"
        )
    )

    if not ledger.get("valid"):
        lines.append("Ledger issues:")
        lines.extend(f"- {item}" for item in ledger.get("issues", []))

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize project-task-executor state for resume.")
    parser.add_argument("--root", default=".", help="Project root containing AGENT_*.md files.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    summary = build_summary(Path(args.root))
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
