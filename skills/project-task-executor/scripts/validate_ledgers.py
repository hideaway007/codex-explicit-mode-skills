#!/usr/bin/env python3
"""Validate project-task-executor ledger files."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_FILES = (
    "AGENT_PRD.md",
    "AGENT_TASKS.md",
    "AGENT_DECISIONS.md",
    "AGENT_REVIEW.md",
)

TASK_RE = re.compile(r"^- \[(?P<mark>[ xX])\] (?P<id>T\d{3,}): (?P<name>.+)$")
FIELD_RE = re.compile(r"^(?P<prefix>\s+- )(?P<key>[A-Za-z ]+):\s*(?P<value>.*)$")
TASK_ID_RE = re.compile(r"\bT\d{3,}\b")
NONE_DEPENDENCIES = {"", "none", "-", "n/a"}
REQUIRED_TASK_FIELDS = (
    "Goal",
    "Files",
    "Dependencies",
    "Steps",
    "Acceptance",
    "Test commands",
    "Implementer",
    "Reviewer",
    "Status",
)
ALLOWED_STATUSES = {
    "planned",
    "in_progress",
    "implemented-unverified",
    "blocked",
    "verified",
}
DEPENDENCIES_MUST_BE_VERIFIED_STATUSES = {
    "in_progress",
    "implemented-unverified",
    "verified",
}
BOOTSTRAP_TASK_ID = "T001"
BOOTSTRAP_TASK_NAME = "Define executable task plan"


@dataclass
class Issue:
    path: Path
    line: int
    message: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line}: {self.message}"


@dataclass
class Field:
    key: str
    value: str
    line: int
    prefix: str


@dataclass
class Task:
    task_id: str
    name: str
    line: int
    checkbox: str
    fields: dict[str, Field]

    def field_value(self, key: str) -> str:
        field = self.fields.get(key)
        if field is None:
            return ""
        return field.value.strip()

    @property
    def status(self) -> str:
        return self.field_value("Status")

    @property
    def checked(self) -> bool:
        return self.checkbox.lower() == "x"


def is_bootstrap_task(task: Task) -> bool:
    return task.task_id == BOOTSTRAP_TASK_ID and task.name.strip().lower() == BOOTSTRAP_TASK_NAME.lower()


def nonempty_markdown(path: Path, root: Path) -> list[Issue]:
    if not path.exists():
        return [Issue(path, 1, "missing required ledger file")]
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return [Issue(path, 1, "ledger file is empty")]
    if not re.search(r"^#\s+\S+", text, re.MULTILINE):
        return [Issue(path, 1, "ledger file should contain a top-level markdown heading")]
    return []


def _append_continuation(field: Field, line: str) -> None:
    stripped = line.strip()
    if not stripped:
        return
    if field.value:
        field.value = f"{field.value}\n{stripped}"
    else:
        field.value = stripped


def parse_tasks(path: Path) -> tuple[list[Task], list[Issue]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tasks: list[Task] = []
    issues: list[Issue] = []
    current: Task | None = None
    current_field: Field | None = None
    in_fence = False

    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        task_match = TASK_RE.match(line)
        if task_match:
            current = Task(
                task_id=task_match.group("id"),
                name=task_match.group("name").strip(),
                line=lineno,
                checkbox=task_match.group("mark"),
                fields={},
            )
            current_field = None
            tasks.append(current)
            continue

        field_match = FIELD_RE.match(line)
        if field_match and current is not None:
            key = field_match.group("key").strip()
            current_field = Field(
                key=key,
                value=field_match.group("value").strip(),
                line=lineno,
                prefix=field_match.group("prefix"),
            )
            current.fields[key] = current_field
            continue

        if current_field is not None and line.startswith(("    ", "\t")):
            _append_continuation(current_field, line)

    if not tasks:
        issues.append(Issue(path, 1, "no tasks found; expected '- [ ] T001: Task name' entries"))

    return tasks, issues


def parse_dependencies(value: str) -> tuple[list[str], list[str]]:
    normalized = value.strip()
    if normalized.lower() in NONE_DEPENDENCIES:
        return [], []

    tokens = [token for token in re.split(r"[\s,，]+", normalized) if token]
    dependencies: list[str] = []
    invalid: list[str] = []
    for token in tokens:
        cleaned = token.strip("[](){}.;:")
        if TASK_ID_RE.fullmatch(cleaned):
            dependencies.append(cleaned)
        elif cleaned.lower() not in NONE_DEPENDENCIES:
            invalid.append(token)
    return dependencies, invalid


def actors_overlap(implementer: str, reviewer: str) -> bool:
    implementer = implementer.strip()
    reviewer = reviewer.strip()
    if not implementer or not reviewer:
        return False
    if implementer == reviewer:
        return True

    normalized_implementer = re.sub(r"[\W_]+", "", implementer.lower())
    normalized_reviewer = re.sub(r"[\W_]+", "", reviewer.lower())
    return bool(
        normalized_implementer
        and normalized_reviewer
        and (
            normalized_implementer in normalized_reviewer
            or normalized_reviewer in normalized_implementer
        )
    )


def validate_tasks(
    tasks_path: Path,
    review_path: Path,
    *,
    require_executable_plan: bool = False,
    require_complete: bool = False,
) -> list[Issue]:
    tasks, issues = parse_tasks(tasks_path)
    if not tasks:
        return issues

    tasks_by_id: dict[str, Task] = {}
    for task in tasks:
        if task.task_id in tasks_by_id:
            issues.append(Issue(tasks_path, task.line, f"duplicate task id {task.task_id}"))
        else:
            tasks_by_id[task.task_id] = task

    verified_ids: list[str] = []
    for task in tasks:
        task_id = task.task_id

        if require_executable_plan and is_bootstrap_task(task):
            issues.append(
                Issue(
                    tasks_path,
                    task.line,
                    f"{task_id} is still the bootstrap task; replace or refine it into concrete executable tasks before dispatch",
                )
            )

        if require_complete:
            if is_bootstrap_task(task):
                issues.append(
                    Issue(
                        tasks_path,
                        task.line,
                        f"{task_id} bootstrap task cannot count as project completion",
                    )
                )
            if task.status != "verified":
                issues.append(
                    Issue(
                        tasks_path,
                        task.line,
                        f"{task_id} Status '{task.status or 'empty'}' must be verified before completion",
                    )
                )

        for required in REQUIRED_TASK_FIELDS:
            if required not in task.fields:
                issues.append(Issue(tasks_path, task.line, f"{task_id} missing field '{required}:'"))

        status_field = task.fields.get("Status")
        status = task.status
        if status_field and status and status not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))
            issues.append(
                Issue(
                    tasks_path,
                    status_field.line,
                    f"{task_id} has unknown Status '{status}' (allowed: {allowed})",
                )
            )

        if status == "verified" and not task.checked:
            issues.append(Issue(tasks_path, task.line, f"{task_id} Status verified should use checked checkbox '[x]'"))
        if status != "verified" and task.checked:
            issues.append(Issue(tasks_path, task.line, f"{task_id} checkbox should be unchecked unless Status is verified"))

        dependencies_field = task.fields.get("Dependencies")
        dependencies: list[str] = []
        if dependencies_field:
            dependencies, invalid_tokens = parse_dependencies(dependencies_field.value)
            for token in invalid_tokens:
                issues.append(Issue(tasks_path, dependencies_field.line, f"{task_id} has invalid dependency token '{token}'"))
            for dependency in dependencies:
                if dependency not in tasks_by_id:
                    issues.append(Issue(tasks_path, dependencies_field.line, f"{task_id} references missing dependency {dependency}"))

        if status in DEPENDENCIES_MUST_BE_VERIFIED_STATUSES:
            for dependency in dependencies:
                dependency_task = tasks_by_id.get(dependency)
                if dependency_task is not None and dependency_task.status != "verified":
                    issues.append(
                        Issue(
                            tasks_path,
                            task.line,
                            f"{task_id} is {status} but dependency {dependency} is not verified",
                        )
                    )

        implementer = task.field_value("Implementer")
        reviewer = task.field_value("Reviewer")
        if actors_overlap(implementer, reviewer):
            line = task.fields.get("Implementer", Field("Implementer", "", task.line, "")).line
            issues.append(Issue(tasks_path, line, f"{task_id} Implementer and Reviewer must be clearly separate"))

        if status == "verified":
            verified_ids.append(task_id)
            for field_name in ("Acceptance", "Test commands", "Implementer", "Reviewer"):
                if not task.field_value(field_name):
                    field = task.fields.get(field_name)
                    line = field.line if field else task.line
                    issues.append(Issue(tasks_path, line, f"{task_id} verified task requires non-empty {field_name}"))

    if verified_ids and review_path.exists():
        review_text = review_path.read_text(encoding="utf-8")
        for task_id in verified_ids:
            if not re.search(rf"\b{re.escape(task_id)}\b", review_text):
                issues.append(Issue(review_path, 1, f"AGENT_REVIEW.md should cover verified task {task_id}"))

    return issues


def validate(root: Path, *, require_executable_plan: bool = False, require_complete: bool = False) -> list[Issue]:
    root = root.resolve()
    issues: list[Issue] = []

    for filename in REQUIRED_FILES:
        issues.extend(nonempty_markdown(root / filename, root))

    tasks_path = root / "AGENT_TASKS.md"
    if tasks_path.exists() and tasks_path.read_text(encoding="utf-8").strip():
        issues.extend(
            validate_tasks(
                tasks_path,
                root / "AGENT_REVIEW.md",
                require_executable_plan=require_executable_plan,
                require_complete=require_complete,
            )
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate project-task-executor ledger files.")
    parser.add_argument("--root", default=".", help="Project root containing AGENT_*.md files.")
    parser.add_argument(
        "--require-executable-plan",
        action="store_true",
        help="Fail if AGENT_TASKS.md still contains the bootstrap planning task.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail unless every task is verified and no bootstrap task remains.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues = validate(
        root,
        require_executable_plan=args.require_executable_plan,
        require_complete=args.require_complete,
    )
    if issues:
        print("Ledger validation failed:")
        for issue in issues:
            print(f"- {issue.format(root)}")
        return 1

    print("Ledger validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
