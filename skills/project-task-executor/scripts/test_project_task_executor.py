#!/usr/bin/env python3
"""Regression tests for project-task-executor script gates."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def run_script(script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_ledgers(root: Path, tasks: str, review: str = "## Review\n") -> None:
    (root / "AGENT_PRD.md").write_text("# AGENT_PRD\n\nGoal.\n", encoding="utf-8")
    (root / "AGENT_TASKS.md").write_text(textwrap.dedent(tasks).strip() + "\n", encoding="utf-8")
    (root / "AGENT_DECISIONS.md").write_text("# AGENT_DECISIONS\n\n- None.\n", encoding="utf-8")
    (root / "AGENT_REVIEW.md").write_text("# AGENT_REVIEW\n\n" + review, encoding="utf-8")


class ProjectTaskExecutorScriptTests(unittest.TestCase):
    def test_next_wave_rejects_bootstrap_only_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init = run_script("init_ledgers.py", "--root", str(root), "--goal", "Ship a feature")
            self.assertEqual(init.returncode, 0, init.stderr)

            result = run_script("next_wave.py", "--root", str(root))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("bootstrap task", result.stderr)

    def test_require_executable_plan_rejects_bootstrap_only_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init = run_script("init_ledgers.py", "--root", str(root), "--goal", "Ship a feature")
            self.assertEqual(init.returncode, 0, init.stderr)

            result = run_script("validate_ledgers.py", "--root", str(root), "--require-executable-plan")

            self.assertEqual(result.returncode, 1)
            self.assertIn("bootstrap task", result.stdout)

    def test_require_complete_rejects_unverified_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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

            result = run_script("validate_ledgers.py", "--root", str(root), "--require-complete")

            self.assertEqual(result.returncode, 1)
            self.assertIn("must be verified before completion", result.stdout)

    def test_require_complete_accepts_reviewed_verified_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
                review="## Integrated Review\n- T001 passed with pytest.\n",
            )

            result = run_script("validate_ledgers.py", "--root", str(root), "--require-complete")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Ledger validation passed", result.stdout)

    def test_eval_harness_outputs_json_score_with_train_and_heldout_splits(self) -> None:
        result = run_script("eval_project_task_executor.py", "--json")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["score"], 1.0)
        self.assertEqual(report["failed"], 0)
        self.assertGreaterEqual(report["total"], 8)
        self.assertGreaterEqual(report["splits"]["train"]["total"], 1)
        self.assertGreaterEqual(report["splits"]["heldout"]["total"], 1)
        self.assertTrue(all(case["passed"] for case in report["cases"]))

    def test_eval_harness_can_write_history_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_path = Path(tmp) / "history.json"

            result = run_script("eval_project_task_executor.py", "--json", "--history", str(history_path))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(history_path.exists())
            history = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(history["score"], 1.0)
            self.assertIn("cases", history)


if __name__ == "__main__":
    unittest.main()
