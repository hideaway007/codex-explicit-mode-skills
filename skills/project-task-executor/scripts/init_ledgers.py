#!/usr/bin/env python3
"""Initialize project-task-executor ledger files without overwriting existing files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def render_prd(goal: str) -> str:
    return f"""# AGENT_PRD

## 目标
{goal}

## 成功标准
- 明确任务拆分，任务之间的依赖可检查。
- 每个完成任务都能追溯实现者、审查者、验收标准和验证命令。
- 最终交付前完成整体验证，并把结论记录到 `AGENT_REVIEW.md`。

## 范围
- In scope: 待补充。
- Out of scope: 待补充。

## 约束
- Markdown 文档中文优先；代码、命令、路径和错误文本保留英文。
- 不把未验证任务标记为完成。
"""


def render_tasks(goal: str) -> str:
    return f"""# AGENT_TASKS

## 使用方式
- 真实任务使用 `- [ ] T001: 任务名` 开头。
- `Status` 可用：`planned`、`in_progress`、`implemented-unverified`、`blocked`、`verified`。
- `Dependencies` 可为空，或填写 `none`、`-`、`n/a`，也可填写 `T001, T002`。
- 只有 `Status: verified` 的任务使用 `[x]`。
- `verified` 任务必须填写 `Acceptance`、`Test commands`、`Implementer`、`Reviewer`，且实现者和审查者要分离。

## 当前目标
{goal}

## Bootstrap task

- [ ] T001: Define executable task plan
  - Goal: Replace or refine this bootstrap task into a concrete executable task list for the project goal.
  - Files: AGENT_PRD.md, AGENT_TASKS.md, AGENT_DECISIONS.md, AGENT_REVIEW.md
  - Dependencies: none
  - Steps: Read project context; define real implementation tasks; assign implementer/reviewer roles; record dependencies and verification commands.
  - Acceptance: AGENT_TASKS.md contains concrete tasks ready for execution or this bootstrap task is explicitly refined into that task list.
  - Test commands: python3 "${{CODEX_HOME:-$HOME/.codex}}/skills/project-task-executor/scripts/validate_ledgers.py" --root .
  - Implementer: Planning worker
  - Reviewer: Independent reviewer
  - Status: planned
"""


def render_decisions() -> str:
    return """# AGENT_DECISIONS

## 决策记录
- 待记录。
"""


def render_review() -> str:
    return """# AGENT_REVIEW

## 审查记录
- 待记录。
"""


TEMPLATES = {
    "AGENT_PRD.md": render_prd,
    "AGENT_TASKS.md": render_tasks,
    "AGENT_DECISIONS.md": lambda goal: render_decisions(),
    "AGENT_REVIEW.md": lambda goal: render_review(),
}


def init_ledgers(root: Path, goal: str) -> list[str]:
    root.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []
    for filename, renderer in TEMPLATES.items():
        path = root / filename
        if path.exists():
            messages.append(f"skip existing {filename}")
            continue
        path.write_text(renderer(goal).rstrip() + "\n", encoding="utf-8")
        messages.append(f"created {filename}")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize project-task-executor ledger files.")
    parser.add_argument("--root", default=".", help="Project root for AGENT_*.md files.")
    parser.add_argument("--goal", required=True, help="Project goal to place in the templates.")
    args = parser.parse_args()

    messages = init_ledgers(Path(args.root).resolve(), args.goal.strip())
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
