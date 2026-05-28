# Codex Explicit Mode Skills

Explicit-mode Codex skills for heavier planning, optimization, and long-running project state workflows.

These skills are intentionally opt-in. They do not replace Superpowers, ECC, or a project's own `AGENTS.md`; they provide named modes you can invoke when a task needs more structure than the default workflow.

## Skills

### `project-task-executor`

Use when you explicitly need a long-running project status layer with `AGENT_*` ledgers, resumability, ledger gates, plan-work-review coordination, controlled parallel execution, integrated review, and completion evidence.

Best for:

- Long-running project execution that must survive compaction or a new session.
- Work that needs `AGENT_PRD.md`, `AGENT_TASKS.md`, `AGENT_DECISIONS.md`, `AGENT_REVIEW.md`, and `AGENT_EVENTS.jsonl`.
- Multi-task batches where implementers, reviewers, worktrees, verification commands, and commit evidence need to be recorded.

Not for:

- Ordinary feature work already covered by Superpowers.
- Small edits or single-step fixes.
- Read-only planning when no durable project ledger is needed.

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

## Install

Copy the skill folders into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/project-task-executor ~/.codex/skills/
cp -R skills/planner-coordinator ~/.codex/skills/
cp -R skills/optimization-council ~/.codex/skills/
```

Restart Codex so the new skill metadata is loaded.

## Invocation Examples

```text
Use project-task-executor for this long-running project. Build the AGENT_* ledgers, coordinate the current task wave, and require Evidence Pack before completion.
```

```text
Use planner-coordinator mode to plan this multi-module refactor before implementation.
```

```text
Use optimization-council mode to evaluate this product workflow. Run the minimum 3 council rounds.
```

```text
启动优化议会，针对这个论文工作流做多角色优化，必须启动 subagents。
```

## Design Rules

- Explicit mode only: these skills should trigger when requested by name or by a clearly matching user request.
- Proportional process: do not use the Planner for tiny tasks.
- Durable state: `project-task-executor` uses repo-local ledgers as the recovery source of truth, not chat memory.
- Real council: `optimization-council` requires subagents unless the user explicitly accepts a simulated fallback.
- Verification matters: debate and planning do not replace project tests, lint, build, review, or domain-specific gates.

## License

MIT
