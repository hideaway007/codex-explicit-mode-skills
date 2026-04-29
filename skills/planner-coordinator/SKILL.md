---
name: planner-coordinator
description: Use when the user explicitly asks for Planner mode,主控 Planner, task coordination, multi-agent planning, or a complex project plan with subagent delegation and independent review. Do not use for ordinary small edits or single-step fixes.
---

# Planner Coordinator

## Overview

Use this as an explicit orchestration mode for complex, multi-step work. The agent acts as the planner and integrator: understand the project, compare approaches, make a concrete plan, delegate independent work when useful, review outputs, and keep the final decision grounded in verification.

This skill complements Superpowers and ECC. Superpowers remains the default workflow; ECC remains a support layer. Use this skill only when the user asks for a planner/coordinator mode or the task is clearly large enough to benefit from explicit coordination.

## When to Use

Use this skill when:
- The user asks for "Planner", "主控", "任务协调", "subagent 分工", or similar.
- The task spans multiple modules, artifacts, roles, or phases.
- Several independent research, implementation, or review tasks can run in parallel.
- The user wants a plan before execution and clear ownership of each task.

Do not use it when:
- A direct answer, small code edit, or narrow bug fix is enough.
- The next step is blocked on a single local investigation.
- Subagent overhead would slow down a simple task.
- The user explicitly asks you to implement directly without planning.

## Workflow

1. Understand context first.
   - Read project instructions, structure, key files, docs, tests, and current implementation.
   - Do not edit files during the initial scan unless the user explicitly asked for immediate changes.
   - Ask only for blocking missing information; otherwise proceed with reasonable assumptions.

2. Define goal and success criteria.
   - Restate the user goal in concrete terms.
   - Identify non-goals, constraints, risk boundaries, and verification commands.

3. Compare approaches.
   - Propose 2-4 viable options for non-trivial decisions.
   - For each option, state core idea, benefits, costs, risks, and when it fits.
   - Select one approach and explain why it is the best fit for the current context.

4. Build the execution plan.
   - Split the selected approach into ordered tasks.
   - For each task include objective, files or modules, implementation steps, acceptance criteria, verification, and risks.
   - Keep tasks small enough to review independently.

5. Delegate only when useful.
   - Use subagents only for independent, bounded side tasks.
   - Assign clear ownership and acceptance criteria.
   - Keep urgent blocking work local if your next step depends on it.
   - Do not silently make project-specific agents or roles into global defaults.

6. Integrate and adjudicate.
   - Review subagent output before accepting it.
   - Resolve conflicts by citing project evidence, user goals, and verification results.
   - Drop low-value suggestions and avoid broad refactors outside the task.

7. Verify before completion.
   - Use the project's own gates first: tests, lint, build, typecheck, or domain validation.
   - For meaningful changes, use `verification-loop`.
   - For non-trivial final answers or plans, use `reflection-review-loop`.

## Subagent Role Templates

Use only the roles needed for the task:

- Implementation subagent: modifies a bounded file set and reports changed paths, tests run, and blockers.
- Research subagent: reads docs, source, issues, or external references and reports evidence with links or file paths.
- Review subagent: checks diff, behavior, tests, complexity, and missed edge cases.
- Red Team subagent: challenges assumptions and proposes lower-cost alternatives or verification methods.

## Output Shape

For planning-only tasks, return:
- Selected approach.
- Ordered task list.
- Suggested subagent split.
- Verification plan.
- Open risks or blockers.

For execution tasks, return:
- What changed.
- What passed or failed.
- What remains blocked.
- Key files and commands.
- Next action.

## Guardrails

- Do not force subagents for every task.
- Do not force commits unless the user asked for commit-driven execution.
- Do not generate planning documents unless they will be used in the current project.
- Do not let debate replace verification.
- Keep the workflow proportional to task size.
