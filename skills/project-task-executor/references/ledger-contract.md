# Ledger Contract

PTE 的长期状态必须落在 repo 内文件里。聊天、TodoWrite、Superpowers plan checkbox 和 subagent 汇报都只能作为辅助，不是恢复依据。

## Required Files

创建或恢复 PTE 时，项目根目录应包含：

- `AGENT_PRD.md`
- `AGENT_TASKS.md`
- `AGENT_DECISIONS.md`
- `AGENT_REVIEW.md`
- `AGENT_EVENTS.jsonl`

优先初始化：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/init_ledgers.py --root . --goal "..."
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root .
```

`init_ledgers.py` 生成的 `T001: Define executable task plan` 是 bootstrap task，只说明账本结构存在。进入执行前必须替换或细化为真实 task list。

## AGENT_PRD.md

包含：

- 项目目标
- 上游计划来源，例如 `docs/superpowers/plans/...`
- 背景和当前问题
- 头脑风暴方向摘要
- 选定方案
- 非目标
- 验收标准
- 风险和约束

## AGENT_TASKS.md

任务格式：

```markdown
- [ ] T001: Task name
  - Goal:
  - Files:
  - Dependencies:
  - Steps:
  - Acceptance:
  - Test commands:
  - Implementer:
  - Reviewer:
  - Owner:
  - Claimed at:
  - Worktree:
  - Status:
```

状态只能使用：

- `planned`
- `in_progress`
- `implemented-unverified`
- `blocked`
- `verified`

规则：

- `Dependencies` 可为空，或填写 `none`、`-`、`n/a`，也可填写 `T001, T002`。
- 只有 `Status: verified` 的任务使用 `[x]`。
- `verified` 任务必须有非空 `Acceptance`、`Test commands`、`Implementer`、`Reviewer`。
- `Implementer` 和 `Reviewer` 必须明显分离。
- `Owner`、`Claimed at`、`Worktree` 是运行期字段，由 `update_task.py` 更新。
- `Worktree:` 只记录已经创建或等价隔离的工作目录；不要把它当成 worktree 创建器。

抢占和释放任务：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --claim worker-a
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --claim worker-a --worktree .worktrees/feature-a
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --release worker-a
```

如果任务已被其他 owner claim，脚本必须失败。

## AGENT_DECISIONS.md

记录影响范围、架构、依赖、验证或风险接受的决定：

```markdown
## YYYY-MM-DD
- Decision:
- Reason:
- Alternatives:
- Risk:
```

低风险局部实现不需要事后补流水账；影响长期恢复和审查的选择必须写。

## AGENT_REVIEW.md

顶部必须包含固定 verdict：

```markdown
Verdict: APPROVE
```

可用值只有：

- `APPROVE`
- `REQUEST_CHANGES`
- `BLOCKED`

正式完成前必须是 `APPROVE`。否则：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root . --require-complete
```

必须失败。

## Evidence Pack

每次完工或准备宣布完成前，`AGENT_REVIEW.md` 必须包含：

```markdown
## Evidence Pack
- Verification commands: <实际运行的 test/lint/build/typecheck/domain gate；没有运行则写 skipped 和原因>
- Diff scope: <git status / git diff --name-only 的范围；不是 git repo 则写 none 和原因>
- Review conclusion: <APPROVE | REQUEST_CHANGES | BLOCKED，加一句结论>
- Commit hash: <hash；没有 commit 则写 none 和原因>
- Failed/skipped reasons: <失败、跳过、不可验证或未提交的原因；没有则写 none>
```

不要把 Evidence Pack 只写在聊天里。最终 gate 以 `AGENT_REVIEW.md` 为准。

## AGENT_EVENTS.jsonl

每行一个 JSON object：

```json
{"ts":"2026-01-01T00:00:00Z","event":"task.claimed","task":"T001","details":{"owner":"worker-a"}}
```

必须记录的事件类型包括：

- `ledger.init`
- `task.claimed`
- `task.released`
- `task.status_changed`
- `task.worktree_bound`

`AGENT_EVENTS.jsonl` 是机器可读审计流，不替代 `AGENT_TASKS.md`。
