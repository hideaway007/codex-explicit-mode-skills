# Execution Loop

PTE 执行的是长跑闭环，不是单项修复：

```text
Understand -> Brainstorm -> Optional Council -> Plan -> Parallel Work -> Integrated Review -> Verify -> Record -> Commit
```

## Phase 1: Understand

窄读但读够：

- 项目 `AGENTS.md` 和本地规则
- README、产品说明、关键 docs
- package/build/test 配置
- 关键源码模块
- 现有测试和 scripts
- 当前 `git status`

进入计划前先总结：

1. 项目概况
2. 当前问题
3. 可优化方向初判
4. 风险和保护文件
5. 可用 test/lint/build/typecheck/gate 命令
6. 当前 git 状态是否允许受控执行和最终 commit

如果目录不是 git repo，或者验证/commit 无法成立，先报告 blocker，不进入执行循环。显式 forward-test 可以压缩这个要求，但必须记录原因。

## Phase 2: Brainstorm

对实质性项目任务先做头脑风暴：

- 默认提出 3-5 个优化方向；复杂项目至少 5 个。
- 每个方向说明思路、收益、成本、风险、验证方式。
- 只保留服务当前项目目标的方向，避免无关平台化扩张。
- 对非平凡决策比较 2-4 个方案并选择当前最适合方案。
- 如果已有 `docs/superpowers/plans/...`，先检查它是否仍符合当前项目目标、风险和验证方式；符合则引用，不重复设计。

只有阻塞性决策才问用户；低风险不确定点做明确假设并继续。

## Phase 3: Optional Council

遇到复杂决策时，启动真实 read-only subagent debate，或先切到 `planner-coordinator` 产出方案再回到执行循环：

- 架构/可维护性、性能/效率、用户价值/结果质量存在明显冲突。
- 方案影响长期架构、数据模型、发布质量、成本或安全边界。
- 用户明确要求“辩论议会”“优化议会”“多角色优化”。
- 涉及论文、学术内容、引用、实验、结论，需要独立证据审查。

学术边界：不得编造引用、实验、数据或结论。证据不足时标记 `unknown`、`needs verification` 或 `blocked by missing evidence`。

## Phase 4: Plan

用 `init_ledgers.py` 初始化或规范化账本。把 bootstrap task 替换为真实 task list 后，分派前必须跑：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root . --require-executable-plan
python3 ~/.codex/skills/project-task-executor/scripts/next_wave.py --root .
```

每个 task 必须边界清晰，包含 files、dependencies、acceptance、test commands、implementer、reviewer。可并行任务应分配给不同 worker；有依赖的任务按 wave 排列。

## Phase 5: Parallel Work

执行默认按 task waves 推进：

1. 按 `next_wave.py` 输出选择可并行 tasks，不凭聊天记忆或肉眼猜下一批。
2. 分派前用 `update_task.py --claim <owner>` 抢占任务。
3. 需要隔离开发时先用 Superpowers `using-git-worktrees` 创建并验证 worktree，再用 `--worktree <path>` 写回任务。
4. 每个 subagent 限定文件范围、交付物和不得覆盖他人改动。
5. subagent 完成后汇报 changed paths、实现摘要、本地自检、blockers。
6. 主 agent 做冲突整合和状态记录，不做逐项最终验收。
7. 实现完成但未整体验证时标为 `implemented-unverified`；blocked 时标为 `blocked` 并记录原因。
8. 当前 wave 完成后再次运行 `next_wave.py`，直到所有任务完成或遇到真实 blocker。

如果没有足够独立任务值得并行，记录原因并由主 agent 本地完成最小 bounded change；不要为了形式上的 subagent 而停滞。

## Phase 6: Integrated Review And Verification

所有任务或当前执行批次完成后，再统一检查：

1. 运行 `git status` 并确认 changed file scope。
2. 做整体 diff review，检查是否满足 `AGENT_PRD.md` 和 `AGENT_TASKS.md`，是否有 subagent 冲突、重复实现、遗漏集成、行为回归、edge cases、over-design、missing tests/docs。
3. 运行项目自带 tests、lint、build、typecheck、domain gate，或最窄可信替代。
4. 审查或验证失败时，批量记录到 `AGENT_REVIEW.md`，再分配返工任务。
5. 同一批次最多返工 3 轮；仍失败则标记 blocked 并说明原因。
6. 全部通过后，统一更新 `AGENT_TASKS.md`、`AGENT_REVIEW.md`、`AGENT_DECISIONS.md`。

提交前必须同时通过：

```bash
python3 ~/.codex/skills/project-task-executor/scripts/validate_ledgers.py --root . --require-complete
```

以及项目自己的验证命令和人工整体 diff review。

## Phase 7: Commit And Completion

默认在整体审查和整体验证通过后再 commit，不在每个任务刚实现时提交。

默认单次集成提交：

```text
agent: complete project task batch - short summary
```

如果用户明确要求按任务拆 commit，也必须先完成整体审查和验证，再根据最终 diff 安全拆分提交。

停止条件：

- 所有任务完成并整体通过验证
- 真实 blocker 阻止继续
- 验证不可用且没有可靠替代
- 同一批次返工 3 轮仍失败
- 用户要求停止
