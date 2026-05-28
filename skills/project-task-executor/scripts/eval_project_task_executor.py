#!/usr/bin/env python3
"""Run SkillOpt-lite fixture checks for project-task-executor gates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
COMPLETE_REVIEW = """Verdict: APPROVE

## Integrated Review
- T001 passed with pytest.

## Evidence Pack
- Verification commands: pytest
- Diff scope: src/app.py
- Review conclusion: APPROVE - T001 passed.
- Commit hash: abc1234
- Failed/skipped reasons: none
"""


@dataclass(frozen=True)
class Case:
    name: str
    split: str
    setup: Callable[[Path], None]
    command: Callable[[Path], list[str]]
    expected_exit: int
    stdout_contains: tuple[str, ...] = ()
    stderr_contains: tuple[str, ...] = ()


def script_command(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPT_DIR / script_name), *args]


def run_script(script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        script_command(script_name, *args),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_ledgers(root: Path, tasks: str, review: str = "Verdict: BLOCKED\n\n## Review\n- None.\n") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "AGENT_PRD.md").write_text("# AGENT_PRD\n\nGoal.\n", encoding="utf-8")
    (root / "AGENT_TASKS.md").write_text(textwrap.dedent(tasks).strip() + "\n", encoding="utf-8")
    (root / "AGENT_DECISIONS.md").write_text("# AGENT_DECISIONS\n\n- None.\n", encoding="utf-8")
    (root / "AGENT_REVIEW.md").write_text("# AGENT_REVIEW\n\n" + review, encoding="utf-8")
    (root / "AGENT_EVENTS.jsonl").write_text(
        json.dumps({"ts": "2026-01-01T00:00:00Z", "event": "test.fixture"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def setup_noop(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)


def skill_contract_command(root: Path) -> list[str]:
    code = r"""
from pathlib import Path
import sys

skill_root = Path(sys.argv[1])
skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
openai = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
reference_contracts = {
    "references/ledger-contract.md": [
        "AGENT_EVENTS.jsonl",
        "Evidence Pack",
        "Verdict: APPROVE",
        "Worktree:",
    ],
    "references/execution-loop.md": [
        "Understand -> Brainstorm -> Optional Council -> Plan -> Parallel Work -> Integrated Review -> Verify -> Record -> Commit",
        "validate_ledgers.py --root . --require-complete",
    ],
    "references/superpowers-interop.md": [
        "using-git-worktrees",
        "docs/superpowers/plans",
        "Codex Native Features",
    ],
    "references/resume-and-status.md": [
        "status_summary.py --root .",
        "AGENT_EVENTS.jsonl",
        "Resume Order",
    ],
}

required_skill = [
    "Superpowers",
    "ECC",
    "状态层",
    "AGENT_EVENTS.jsonl",
    "--claim",
    "Worktree:",
    "Evidence Pack",
    "Verdict: APPROVE | REQUEST_CHANGES | BLOCKED",
    "status_summary.py",
    "docs/superpowers/plans",
    "不要用 `project-task-executor` 替代 Superpowers",
    "`AGENT_TASKS.md`",
]
required_openai = [
    "长期项目状态层",
    "AGENT_*",
    "allow_implicit_invocation: false",
    "Superpowers/ECC",
]

missing = [f"SKILL.md:{text}" for text in required_skill if text not in skill]
missing.extend(f"agents/openai.yaml:{text}" for text in required_openai if text not in openai)
for rel_path, fragments in reference_contracts.items():
    if rel_path not in skill:
        missing.append(f"SKILL.md:{rel_path}")
    path = skill_root / rel_path
    if not path.exists():
        missing.append(f"{rel_path}:missing")
        continue
    text = path.read_text(encoding="utf-8")
    missing.extend(f"{rel_path}:{fragment}" for fragment in fragments if fragment not in text)
if missing:
    print("Missing content contract fragments:")
    for item in missing:
        print(f"- {item}")
    sys.exit(1)

print("Skill contract passed")
"""
    return [sys.executable, "-c", code, str(SKILL_ROOT)]


def setup_init(root: Path) -> None:
    result = run_script("init_ledgers.py", "--root", str(root), "--goal", "Evaluate project task executor")
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def setup_dependency_block(root: Path) -> None:
    write_ledgers(
        root,
        """
        # AGENT_TASKS

        - [ ] T001: Prepare foundation
          - Goal: Prepare foundation.
          - Files: README.md
          - Dependencies: none
          - Steps: Prepare.
          - Acceptance: Foundation is ready.
          - Test commands: pytest
          - Implementer: Worker A
          - Reviewer: Reviewer B
          - Status: planned

        - [ ] T002: Use foundation
          - Goal: Use foundation.
          - Files: src/app.py
          - Dependencies: T001
          - Steps: Implement dependent work.
          - Acceptance: Dependent work is ready.
          - Test commands: pytest
          - Implementer: Worker C
          - Reviewer: Reviewer D
          - Status: in_progress
        """,
    )


def setup_next_wave_dependencies(root: Path) -> None:
    write_ledgers(
        root,
        """
        # AGENT_TASKS

        - [ ] T001: Prepare foundation
          - Goal: Prepare foundation.
          - Files: README.md
          - Dependencies: none
          - Steps: Prepare.
          - Acceptance: Foundation is ready.
          - Test commands: pytest
          - Implementer: Worker A
          - Reviewer: Reviewer B
          - Status: planned

        - [ ] T002: Use foundation
          - Goal: Use foundation.
          - Files: src/app.py
          - Dependencies: T001
          - Steps: Implement dependent work.
          - Acceptance: Dependent work is ready.
          - Test commands: pytest
          - Implementer: Worker C
          - Reviewer: Reviewer D
          - Status: planned
        """,
    )


def setup_completion_unverified(root: Path) -> None:
    write_ledgers(
        root,
        """
        # AGENT_TASKS

        - [ ] T001: Implement feature
          - Goal: Build feature.
          - Files: src/app.py
          - Dependencies: none
          - Steps: Implement.
          - Acceptance: Feature works.
          - Test commands: pytest
          - Implementer: Worker A
          - Reviewer: Reviewer B
          - Status: implemented-unverified
        """,
    )


def setup_completion_verified(root: Path) -> None:
    write_ledgers(
        root,
        """
        # AGENT_TASKS

        - [x] T001: Implement feature
          - Goal: Build feature.
          - Files: src/app.py
          - Dependencies: none
          - Steps: Implement.
          - Acceptance: Feature works.
          - Test commands: pytest
          - Implementer: Worker A
          - Reviewer: Reviewer B
          - Status: verified
        """,
        review=COMPLETE_REVIEW,
    )


def setup_actor_overlap(root: Path) -> None:
    write_ledgers(
        root,
        """
        # AGENT_TASKS

        - [ ] T001: Implement feature
          - Goal: Build feature.
          - Files: src/app.py
          - Dependencies: none
          - Steps: Implement.
          - Acceptance: Feature works.
          - Test commands: pytest
          - Implementer: root agent
          - Reviewer: root agent integrated review
          - Status: planned
        """,
    )


def setup_review_missing_verified_task(root: Path) -> None:
    write_ledgers(
        root,
        """
        # AGENT_TASKS

        - [x] T001: Implement feature
          - Goal: Build feature.
          - Files: src/app.py
          - Dependencies: none
          - Steps: Implement.
          - Acceptance: Feature works.
          - Test commands: pytest
          - Implementer: Worker A
          - Reviewer: Reviewer B
          - Status: verified
        """,
        review=COMPLETE_REVIEW.replace("- T001 passed with pytest.", "- pytest passed.").replace(
            "T001 passed.", "pytest passed."
        ),
    )


def cases() -> list[Case]:
    return [
        Case(
            name="skill_contract_mentions_superpowers_ecc_status_layer",
            split="heldout",
            setup=setup_noop,
            command=skill_contract_command,
            expected_exit=0,
            stdout_contains=("Skill contract passed",),
        ),
        Case(
            name="baseline_init_validates",
            split="train",
            setup=setup_init,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root)),
            expected_exit=0,
            stdout_contains=("Ledger validation passed",),
        ),
        Case(
            name="bootstrap_requires_executable_plan",
            split="train",
            setup=setup_init,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root), "--require-executable-plan"),
            expected_exit=1,
            stdout_contains=("bootstrap task",),
        ),
        Case(
            name="dependency_gate_blocks_in_progress",
            split="train",
            setup=setup_dependency_block,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root)),
            expected_exit=1,
            stdout_contains=("dependency T001 is not verified",),
        ),
        Case(
            name="next_wave_respects_dependencies",
            split="train",
            setup=setup_next_wave_dependencies,
            command=lambda root: script_command("next_wave.py", "--root", str(root)),
            expected_exit=0,
            stdout_contains=("T001",),
        ),
        Case(
            name="actor_separation_blocks_overlap",
            split="train",
            setup=setup_actor_overlap,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root)),
            expected_exit=1,
            stdout_contains=("clearly separate",),
        ),
        Case(
            name="bootstrap_not_executable_wave",
            split="heldout",
            setup=setup_init,
            command=lambda root: script_command("next_wave.py", "--root", str(root)),
            expected_exit=1,
            stderr_contains=("bootstrap task",),
        ),
        Case(
            name="completion_rejects_unverified",
            split="heldout",
            setup=setup_completion_unverified,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root), "--require-complete"),
            expected_exit=1,
            stdout_contains=("must be verified before completion",),
        ),
        Case(
            name="completion_accepts_verified_reviewed",
            split="heldout",
            setup=setup_completion_verified,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root), "--require-complete"),
            expected_exit=0,
            stdout_contains=("Ledger validation passed",),
        ),
        Case(
            name="review_must_cover_verified_task",
            split="heldout",
            setup=setup_review_missing_verified_task,
            command=lambda root: script_command("validate_ledgers.py", "--root", str(root)),
            expected_exit=1,
            stdout_contains=("should cover verified task T001",),
        ),
    ]


def evaluate_case(case: Case) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"pte-{case.name}-") as tmp:
        root = Path(tmp)
        case.setup(root)
        result = subprocess.run(
            case.command(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    missing_stdout = [text for text in case.stdout_contains if text not in result.stdout]
    missing_stderr = [text for text in case.stderr_contains if text not in result.stderr]
    passed = (
        result.returncode == case.expected_exit
        and not missing_stdout
        and not missing_stderr
    )
    failure = ""
    if not passed:
        failure = (
            f"expected exit {case.expected_exit}, got {result.returncode}; "
            f"missing stdout={missing_stdout}; missing stderr={missing_stderr}"
        )

    return {
        "name": case.name,
        "split": case.split,
        "passed": passed,
        "expected_exit": case.expected_exit,
        "actual_exit": result.returncode,
        "failure": failure,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def summarize(results: list[dict[str, object]]) -> dict[str, object]:
    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    splits: dict[str, dict[str, float | int]] = {}
    for split in sorted({str(result["split"]) for result in results}):
        split_results = [result for result in results if result["split"] == split]
        split_total = len(split_results)
        split_passed = sum(1 for result in split_results if result["passed"])
        splits[split] = {
            "total": split_total,
            "passed": split_passed,
            "failed": split_total - split_passed,
            "score": round(split_passed / split_total, 4) if split_total else 0.0,
        }

    return {
        "suite": "project-task-executor",
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(passed / total, 4) if total else 0.0,
        "splits": splits,
        "cases": results,
    }


def render_text(report: dict[str, object]) -> str:
    lines = [
        f"project-task-executor eval: {report['passed']}/{report['total']} passed, score={report['score']}",
    ]
    for case in report["cases"]:
        assert isinstance(case, dict)
        mark = "PASS" if case["passed"] else "FAIL"
        lines.append(f"- {mark} [{case['split']}] {case['name']}")
        if not case["passed"]:
            lines.append(f"  {case['failure']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate project-task-executor script gates on fixed fixtures.")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    parser.add_argument("--history", help="Optional path to write the JSON report.")
    args = parser.parse_args()

    report = summarize([evaluate_case(case) for case in cases()])

    if args.history:
        history_path = Path(args.history)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
