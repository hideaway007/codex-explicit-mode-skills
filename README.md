# Codex Explicit Mode Skills

Three explicit-mode Codex skills for heavier planning, optimization, and long-running project execution workflows.

These skills are intentionally opt-in. They do not replace Superpowers, ECC, or a project's own `AGENTS.md`; they provide named modes you can invoke when a task needs more structure than the default workflow.

## Skills

### `planner-coordinator`

Use when you explicitly want a main Planner to coordinate a complex task, compare approaches, split work, delegate bounded subagent tasks, integrate results, and verify before completion.

Best for:

- Multi-module implementation plans.
- Tasks that need research, implementation, and review split apart.
- Work where ownership, acceptance criteria, and verification need to be explicit.

Not for:

- Small edits.
- Single-step fixes.
- Tasks where direct implementation is faster and safer.

### `optimization-council`

Use when you explicitly want a council-style optimization process with real subagents. The council must run 3-6 debate rounds and include perspectives for architecture, efficiency, user value, and Red Team risk review.

Best for:

- Product, workflow, prompt, paper, or system optimization.
- Decisions with competing goals such as maintainability, cost, quality, and user value.
- High-impact changes that need structured challenge before execution.

Not for:

- Routine bug fixes.
- Simple performance suggestions.
- Situations where subagents are unavailable and you do not want a simulated fallback.

### `project-task-executor`

Use when you explicitly want a long-running project controller that creates `AGENT_*` ledgers, splits executable tasks, dispatches bounded subagents, separates implementation and review, runs structural gates, and commits only after integrated verification.

Best for:

- Project-level goals that need plan/work/review continuity across context compaction or session resume.
- Multi-task implementation where task state must be durable in repo files.
- Work that needs implementer/reviewer separation and batch verification before commit.

Not for:

- Small edits.
- Read-only planning.
- Ordinary Q&A or quick debugging.

## Install

Copy the skill folders into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/planner-coordinator ~/.codex/skills/
cp -R skills/optimization-council ~/.codex/skills/
cp -R skills/project-task-executor ~/.codex/skills/
```

Restart Codex so the new skill metadata is loaded.

## Invocation Examples

```text
Use planner-coordinator mode to plan this multi-module refactor before implementation.
```

```text
Use optimization-council mode to evaluate this product workflow. Run the minimum 3 council rounds.
```

```text
启动优化议会，针对这个论文工作流做多角色优化，必须启动 subagents。
```

```text
Use project-task-executor to plan, dispatch subagents, review, verify, and commit this project goal: ...
```

## Design Rules

- Explicit mode only: these skills should trigger when requested by name or by a clearly matching user request.
- Proportional process: do not use the Planner for tiny tasks.
- Real council: `optimization-council` requires subagents unless the user explicitly accepts a simulated fallback.
- Ledger discipline: `project-task-executor` keeps recoverable project state in `AGENT_PRD.md`, `AGENT_TASKS.md`, `AGENT_DECISIONS.md`, and `AGENT_REVIEW.md`.
- Verification matters: debate and planning do not replace project tests, lint, build, review, or domain-specific gates.

## License

MIT
