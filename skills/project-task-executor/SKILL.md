---
name: project-task-executor
description: Use when 用户明确要求长期项目状态层/status layer、独立状态栏、AGENT_* 账本、项目级恢复、ledger gate、plan-work-review 长跑主控或受控并行执行；不要用于 Superpowers 可覆盖的普通开发、小修复、单步任务、只读规划或普通问答。
---

# Project Task Executor

## 定位

这是显式触发的长期项目状态层和长跑主控 skill。默认开发、bugfix、feature、TDD、debugging、短中程计划、普通 subagent 执行和验证优先走 Superpowers。

第一职责是维护可恢复的项目状态栏：长期目标、任务、决策、审查、验证和生命周期事件必须落到 repo 内 `AGENT_*` 与 `AGENT_EVENTS.jsonl`。需要执行时，它按这个闭环推进：

```text
Understand -> Brainstorm -> Optional Council -> Plan -> Parallel Work -> Integrated Review -> Verify -> Record -> Commit
```

不要用 `project-task-executor` 替代 Superpowers。PTE 只在用户明确需要长期状态、强恢复、ledger gate、统一整体验证或 plan-work-review 长跑主控时启用。

## 何时使用

使用：

- 用户明确要“长期状态层”“项目状态栏”“独立状态栏”“跨会话恢复”“账本 gate”。
- 用户要求 `AGENT_PRD.md`、`AGENT_TASKS.md`、`AGENT_DECISIONS.md`、`AGENT_REVIEW.md`。
- 用户要求 plan + work + review、实现者和审查者分离、subagent 并行执行或统一整体验收。
- 多任务项目需要任务依赖、wave、owner、review、Evidence Pack 和 batch commit。

不要使用：

- 单文件修复、快速 bugfix、配置小改、直接问答。
- 只读规划，且用户没有要求进入执行。
- Superpowers 足够覆盖的普通开发任务。
- 用户明确禁止编辑、验证或 commit 的 repo。

## Reference Map

只加载当前阶段需要的 reference，避免把整个长流程塞进上下文：

- `references/ledger-contract.md`：需要创建或修复 `AGENT_*`、`AGENT_EVENTS.jsonl`、`Verdict: APPROVE | REQUEST_CHANGES | BLOCKED`、Evidence Pack 或 task schema 时读取。
- `references/execution-loop.md`：需要进入完整 plan-work-review 执行、subagent wave、整体 review、验证或 commit 时读取。
- `references/superpowers-interop.md`：需要和 Superpowers/ECC/Codex 原生能力配合时读取，特别是 `docs/superpowers/plans`、`using-git-worktrees`、TDD、review、verification。
- `references/resume-and-status.md`：恢复长任务、生成状态栏、处理 blocked/failed gate 或跨会话继续时读取。

## 必守规则

- 项目理解阶段不改代码。
- 如果目录不是 git repo，或验证和 commit 无法成立，先报告 blocker；显式 forward-test 除外。
- 长期项目状态以 `AGENT_TASKS.md` 为准，不以 TodoWrite、聊天摘要、subagent 汇报或 Superpowers plan checkbox 为准。
- `implemented-unverified` 不是完成；只有通过整体 review 和验证后的任务才能标为 `verified`。
- 实现者和审查者必须分离；审查者不能批准自己写的 diff。
- 默认按依赖关系组织 task waves，不再默认“一次只完成一个任务”。
- 当前 wave 完成后再做整体 diff review、整体验证、账本更新和 commit。
- 不 `git push`，除非用户明确要求。

## 脚本 Gate

脚本失败视为 workflow blocker，不是普通 warning。以脚本输出为准；缺脚本时在 `AGENT_REVIEW.md` 记录替代动作和风险。

```bash
python3 ~/.codex/skills/project-task-executor/scripts/init_ledgers.py --root . --goal "..."
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root . --require-executable-plan
python3 ~/.codex/skills/project-task-executor/scripts/next_wave.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --claim worker-a --worktree wt/feature
python3 ~/.codex/skills/project-task-executor/scripts/status_summary.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root . --require-complete
```

`update_task.py --claim` 用于抢占任务；`Worktree:` 只是记录隔离目录绑定。创建和验证 git worktree 时优先调用 Superpowers `using-git-worktrees`，成功后再把路径写回 PTE 账本。

## 最小执行协议

1. 读项目 `AGENTS.md`、README/docs、build/test 配置、关键源码、现有测试和 `git status`。
2. 初始化或恢复账本：优先跑 `init_ledgers.py` 或 `status_summary.py`。
3. 把 bootstrap task 替换或细化为真实 task list；每个 task 写明 files、dependencies、acceptance、test commands、implementer、reviewer。
4. 分派前跑 `validate_ledgers.py --require-executable-plan` 和 `next_wave.py`。
5. 对每个并行 task 用 `update_task.py --claim <owner>`；使用隔离目录时加 `--worktree <path>`。
6. subagent 完成后只记录交付摘要和状态；最终验收留到 integrated review。
7. 所有任务或当前 wave 完成后，统一 diff review、项目 tests/lint/build/typecheck/domain gate、账本更新。
8. 完工前必须让 `AGENT_REVIEW.md` 的 `Verdict` 为 `APPROVE`，写完整 Evidence Pack，并通过 `validate_ledgers.py --require-complete`。

## Superpowers / ECC 边界

- Superpowers 是默认 workflow layer；PTE 是显式重型状态层。
- 如果已有 `docs/superpowers/plans/...`，把它作为输入引用到 `AGENT_PRD.md` 或 `AGENT_TASKS.md`，不要重复写聊天计划。
- 当 PTE 已激活时，Superpowers plan 里的 per-task commit step 只作为 checkpoint 建议；最终 commit 节奏由 `AGENT_TASKS.md`、integrated review、Evidence Pack 和 `validate_ledgers.py --require-complete` 决定。
- ECC 是支持层，不是替代 workflow；可用它的 MCP、documentation lookup、security review、verification-loop、项目本地 `.codex/agents` 和 scripts 增强证据与验证。

## 完成条件

不得只在聊天里宣布完成。完成前必须同时满足：

- 所有目标 task 为 `verified`，或 blocker 已明确记录。
- `AGENT_REVIEW.md` 含固定 verdict：`Verdict: APPROVE | REQUEST_CHANGES | BLOCKED`，正式完成时必须是 `APPROVE`。
- `AGENT_REVIEW.md` 含 `## Evidence Pack`，字段包括 `Verification commands`、`Diff scope`、`Review conclusion`、`Commit hash`、`Failed/skipped reasons`。
- `validate_ledgers.py --root . --require-complete` 通过。
- 项目自己的 tests/lint/build/typecheck/domain gate 或最窄可信替代已运行并记录。
- commit 已完成，或 `Commit hash: none - <原因>` 已记录。

## 恢复协议

长任务、context compaction 或新会话恢复时先读：

- `AGENT_PRD.md`
- `AGENT_TASKS.md`
- `AGENT_DECISIONS.md`
- `AGENT_REVIEW.md`
- `git status`

然后跑：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/status_summary.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/next_wave.py --root .
```

validate 失败时先修复账本或记录 blocker。不要仅凭聊天记忆继续执行。

## 维护这个 Skill

修改 PTE 或脚本 gate 后必须跑：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/eval_project_task_executor.py --json
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/project-task-executor
```

评测分数、heldout split 或 quick validate 退化时，不接受改动，除非把原因和风险记录为 blocker。

## 常见错误

- 把这个 skill 用在小修小补上。
- 只创建账本，但执行时不维护。
- 让 TodoWrite、聊天摘要或 `docs/superpowers/plans` checkbox 替代 `AGENT_TASKS.md`。
- 创建 worktree 但没有把 `Worktree:` 回写到 task。
- 让同一个角色实现并批准自己的 diff。
- 每个任务刚实现就急着 commit，导致集成后难以统一审查。
- 测试通过了，但漏记 Evidence Pack 或 review verdict。
