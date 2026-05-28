# Superpowers / ECC / Codex Interop

PTE 不复制 Superpowers、ECC 或 Codex 原生能力。它只维护长期项目状态和完成 gate。

## Routing

- 普通开发、bugfix、feature、TDD、debugging、短中程计划、普通 subagent 执行和 verification：优先 Superpowers。
- 长期项目状态层、`AGENT_*` 账本、强恢复、ledger gate、统一整体验证、plan-work-review 长跑主控：使用 PTE。
- ECC 是支持层，不是替代 workflow；用它增强 evidence、docs lookup、security review、verification-loop、项目本地 agents 和 scripts。

## Superpowers Plan

如果项目已有 `docs/superpowers/plans/...`：

- 在 `AGENT_PRD.md` 或 `AGENT_TASKS.md` 引用它。
- 不重复写一份聊天计划。
- 把 Superpowers plan 当 bounded implementation slice 的输入。
- 长期 source of truth 仍是 `AGENT_TASKS.md`。

当 PTE 已激活时，Superpowers plan 的 per-task commit step 只作为 checkpoint 建议。最终 commit 节奏由 `AGENT_TASKS.md`、integrated review、Evidence Pack 和 `validate_ledgers.py --require-complete` 决定。

## Git Worktrees

PTE 的 `Worktree:` 字段只记录 task 和隔离目录的绑定，不负责创建 worktree。

需要隔离开发时：

1. 调用 Superpowers `using-git-worktrees`。
2. 让它检测是否已经在 linked worktree。
3. 优先使用 native worktree 工具；没有时 fallback 到 `git worktree add`。
4. 确认 `.worktrees/` 或 `worktrees/` 被忽略。
5. 运行项目 setup 和 baseline tests。
6. 成功后用 PTE 写回绑定：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --claim worker-a --worktree .worktrees/feature-a
```

如果 baseline tests 失败，先记录 blocker 或询问是否继续；不要把失败 baseline 当成 task 已完成。

## TDD / Debugging / Review

PTE 可以把单个 bounded task 交给 Superpowers 的专门 skill：

- 新 feature 或 bugfix：`test-driven-development`
- 异常、失败、回归：`systematic-debugging`
- 独立任务实现：`subagent-driven-development`
- 完工前审查：`requesting-code-review`
- 完成声明前验证：`verification-before-completion`

但这些 skill 的输出必须回写到 PTE：

- task 状态写回 `AGENT_TASKS.md`
- review 结论写回 `AGENT_REVIEW.md`
- 关键取舍写回 `AGENT_DECISIONS.md`
- 生命周期事件写入 `AGENT_EVENTS.jsonl`
- 最终证据写入 Evidence Pack

## Codex Native Features

Codex 原生能力可以配合 PTE，但不替代 PTE 账本：

- `resume` / `fork`：恢复或分叉会话，不是 repo 级任务账本。
- `goals`：session 目标锚点，不是 task graph 或 ledger gate。
- `multi_agent`：执行并行 agent，不提供 `Owner`、`Claimed at`、`Worktree`、Evidence Pack。
- `codex review`：可做审查，但 verdict 和证据要落到 `AGENT_REVIEW.md`。
- `hooks` / `plugin_hooks`：可以增强自动化，但 PTE 当前 gate 是显式脚本，不依赖 hook 强制执行。

## Conflict Rules

- 如果 Superpowers 和 PTE 都能完成当前任务，优先 Superpowers。
- 如果 PTE 已激活，长期状态和最终完成判断以 PTE 账本和脚本 gate 为准。
- 如果项目已有自己的 release、commit 或 verification 规则，项目规则优先；PTE 只补状态和证据结构。
- 不要把项目专用 ECC harness 静默提升为全局默认。
