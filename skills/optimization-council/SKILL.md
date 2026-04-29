---
name: optimization-council
description: Use when the user explicitly asks for an optimization council,多角色优化, Socratic debate, Red Team review, or structured optimization of a project, module, paper, product, prompt, workflow, or system. Must start real subagents to form the council and run 3-6 debate rounds. Do not use for routine bug fixes or simple optimization suggestions.
---

# Optimization Council

## Overview

Use this as an explicit multi-perspective optimization mode. The lead agent hosts a structured discussion, but the council must be made of real subagents rather than purely simulated perspectives. The council stress-tests assumptions, then converges on an executable plan. It is for high-value optimization decisions where architecture, efficiency, user value, and risk need to be weighed together.

This skill complements `harness-optimization-loop`, `reflection-review-loop`, Superpowers, and ECC. Use those for default planning, verification, and implementation. Use this skill only when the user wants a council-style optimization process or the decision is complex enough to justify it.

## When to Use

Use this skill when:
- The user asks for "优化议会", "Socratic Debate", "Red Team", "多角色评审", or similar.
- A project, module, paper, product, prompt, workflow, or system needs structured optimization.
- Several optimization goals conflict, such as maintainability, speed, cost, quality, and user value.
- The output should be a final optimization plan rather than immediate code changes.

Do not use it when:
- There is a single obvious bug or performance fix.
- No evidence or verification surface exists.
- A normal `harness-optimization-loop` comparison is enough.
- The user wants fast implementation rather than structured debate.

## Roles

Start subagents for these council roles before the debate begins. If the environment cannot start subagents, state that this skill is blocked and ask the user whether to continue with a simulated fallback.

- Optimizer A: structure and architecture.
  - Focus: module boundaries, maintainability, extensibility, long-term shape.

- Optimizer B: performance and efficiency.
  - Focus: speed, resource use, automation, cost, operational effort.

- Optimizer C: user value and result quality.
  - Focus: user experience, product value, paper quality, readability, completion quality.

- Opposition / Red Team: risk and assumption review.
  - Focus: failed assumptions, hidden costs, over-design, unverifiable claims, lower-cost alternatives.
  - Must provide alternatives or verification methods, not just objections.

## Debate Loop

Run at least 3 rounds and at most 6 rounds. Default to 3 rounds for normal council work. Use 4-6 rounds only when the user requests more depth, the decision is high stakes, or earlier rounds expose unresolved conflicts.

Each round includes:

1. Moderator frames the question.
   - State the exact issue this round should resolve.

2. Optimizers respond.
   - Each optimizer gives recommendation, reasoning, expected benefit, cost, risk, and verification method.

3. Red Team challenges.
   - Test assumptions, cheaper options, new problems, evidence quality, and whether the change is worth doing now.

4. Moderator asks 3-5 Socratic questions.
   - Force clarity on evidence, boundaries, tradeoffs, priority, and measurable outcomes.

5. Moderator adjudicates.
   - Keep high-value ideas.
   - Drop low-value or overbuilt ideas.
   - Mark unresolved disputes.
   - Update the current best plan.

## Round Focus

If running 6 rounds:

1. Divergence: surface the strongest candidate improvements.
2. Feasibility: check implementation cost and available evidence.
3. Risk and counterexamples: identify failure modes and rollback paths.
4. Priority and resources: choose what is worth doing now.
5. Validation design: define metrics, checks, rollback signals, and evidence thresholds.
6. Convergence: produce the execution route.

If running 4-5 rounds:

- Combine adjacent phases from the 6-round structure while preserving risk review and final convergence.

If running 3 rounds:

1. Candidate improvements and goals.
2. Feasibility, risks, and evidence.
3. Priority, final plan, and verification.

## Final Output

Return:
- Final optimization plan.
- Priority order.
- Rejected options and reasons.
- Risk list.
- Verification metrics.
- Executable task list.
- Suggested subagent split, if useful.
- Next execution order.

## Guardrails

- Do not turn every optimization request into a long council.
- Do not run this skill without real subagents unless the user explicitly accepts a simulated fallback after being told subagents are unavailable.
- Do not run fewer than 3 rounds or more than 6 rounds.
- Do not repeat the same arguments across rounds.
- Do not accept claims without a verification method.
- Do not let architectural cleanliness outrank user value unless the project evidence supports it.
- Do not write files or modify code unless the user explicitly asks to execute the final plan.
