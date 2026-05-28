# Resume And Status

PTE 的恢复目标是让新会话或 context compaction 后可以不靠聊天记忆继续推进。

## Resume Order

长时间任务、context compaction 或新会话恢复时，先读：

1. `AGENT_PRD.md`
2. `AGENT_TASKS.md`
3. `AGENT_DECISIONS.md`
4. `AGENT_REVIEW.md`
5. `git status`

然后跑：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/status_summary.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root .
python3 ~/.codex/skills/project-task-executor/scripts/next_wave.py --root .
```

`status_summary.py --json` 可给机器消费：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/status_summary.py --root . --json
```

## Status Bar Content

状态栏摘要至少包含：

- current wave
- blocked tasks
- verified tasks
- claimed tasks
- Worktree bindings
- next gate
- review verdict
- diff scope
- 最近 `AGENT_EVENTS.jsonl` events
- 下一步验证命令

不要只汇报“我做了什么”；要汇报还缺什么、如何验证、下一步 gate 是什么。

## Handling Failed Gates

脚本失败时：

1. 不继续分派新实现工作。
2. 先判断是账本格式问题、任务依赖问题、review/Evidence Pack 缺失，还是项目验证失败。
3. 能修账本就修账本。
4. 不能修时在 `AGENT_REVIEW.md` 记录 `Verdict: BLOCKED`、原因、已尝试动作、下一步。
5. 再向用户汇报 blocker。

常见失败：

- `AGENT_TASKS.md` 仍只有 bootstrap task。
- task 缺 required field。
- `implemented-unverified` 被当成完成。
- dependency 未 verified 就启动下游 task。
- `Implementer` 和 `Reviewer` 重叠。
- `AGENT_REVIEW.md` 缺 `Verdict` 或 Evidence Pack。
- `AGENT_EVENTS.jsonl` 缺失或不是 JSONL。

## Updating Status

状态变更优先使用脚本：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --status implemented-unverified
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --status blocked
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --status verified
```

并行任务必须先 claim：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --claim worker-a
```

释放任务：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/update_task.py --root . --task T001 --release worker-a
```

## Completion Report

最终汇报应包含：

- 完成了什么
- 状态层摘要：current wave、verified、blocked、next gate
- 每个任务结果
- subagent 分工和交付摘要
- commit 摘要
- 测试结果
- Evidence Pack 摘要
- 剩余风险

如果创建了 session goal，只有在项目目标真的完成且没有剩余必要工作时，才标记 goal complete。
