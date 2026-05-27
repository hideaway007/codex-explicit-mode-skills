---
name: project-task-executor
description: 用于用户明确要求长时间项目主控、受控多任务执行、AGENT_* 账本、实现者/审查者分离、并行 subagent、plan-work-review 闭环或项目级执行恢复的场景；不要用于小修复、单步任务、只读规划或普通问答。
---

# Project Task Executor

## 定位

这是显式触发的长时间项目主控工作流 skill。它把一个较大的项目目标推进成完整闭环：

```text
Understand -> Brainstorm -> Optional Council -> Plan -> Parallel Work -> Integrated Review -> Verify -> Record -> Commit
```

它不是单纯执行层，而是 Planner + Coordinator + Reviewer：负责理解项目、头脑风暴、方案选择、任务拆分、subagent 调度、结果整合、整体审查、验证、记录和最终提交。

它可以和 `goals` 配合：如果用户明确给出项目目标，且 goal 工具可用，可以把 session goal 作为顶层目标锚点；但项目状态、任务账本、审查记录和决策记录仍必须落在 repo 文件里。

## 触发条件

仅在用户明确要求以下任一情况时使用：

- “启动项目 Planner”“自动化执行 Planner”“任务调度者”“项目主控”“长时间任务”
- “plan + work + review”“实现者和审查者分离”“用 subagent 并行执行/审查”
- 需要 `AGENT_PRD.md`、`AGENT_TASKS.md`、`AGENT_DECISIONS.md`、`AGENT_REVIEW.md`
- 多任务项目优化，且需要计划、分工、整体审查、验证和提交

不要用于：

- 单文件修复、快速 bug 修复、配置小改、小 UI 调整、直接问答
- 只要求规划、不要求进入执行的请求
- 用户明确说不要编辑文件、不要 commit、只读审查的 repo

## 总原则

- 先明确项目目标、成功标准、非目标和验证方式。
- 项目理解阶段不改代码。
- 显式 forward-test、小型示例项目或用户要求快速验证 skill 时，压缩 Brainstorm/Council；先创建最小 `AGENT_*` 账本，再做一个 bounded implementation。
- 优先使用真实 subagent 并行完成独立、边界清晰的任务。
- 不再默认“一次只完成一个任务”；默认按依赖关系组织并行 task waves。
- 实现者和审查者必须分离；审查者不能批准自己写的 diff。
- 只有显式 forward-test 或极小压缩任务可以跳过真实角色分离；必须在 `AGENT_REVIEW.md` 记录原因，且不能把这种豁免用于正式项目执行。
- 每个 subagent 必须有明确 owner、文件范围、交付物、验收标准和交接点。
- subagent 完成单项任务后只记录状态和交付摘要；主控不做逐项最终验收。
- 等所有任务或当前 wave 完成后，再做整体 diff review、整体验证、账本更新和 commit。
- 不要卡在纯规划：完成项目理解后，必须先落 `AGENT_*` 账本或明确报告 blocker，再启动长时间并行执行。
- 不 `git push`，除非用户明确要求。

## Runtime Hardening / Script Gates

这个 skill 不是 Codex 内置 harness state machine；它仍由主 agent 执行。但关键状态必须尽量交给脚本 gate 结构化，不能只靠 prompt 自觉。

脚本失败视为 workflow blocker，不是普通 warning。修复账本或记录 blocker 后再继续。

公开安装默认脚本路径：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
```

- `scripts/init_ledgers.py --root . --goal "..."`：从项目目标初始化或规范化 `AGENT_PRD.md`、`AGENT_TASKS.md`、`AGENT_DECISIONS.md`、`AGENT_REVIEW.md`；保留项目已有有效内容；生成一个真实可解析的 planned bootstrap task，供后续替换或细化为项目任务列表。
- `scripts/next_wave.py --root .`：读取 `AGENT_TASKS.md`，根据 status 和 dependencies 输出下一批可执行任务；用于分派前、wave 间切换和 resume；如果只剩 bootstrap task，必须失败并阻断分派。
- `scripts/update_task.py --root . --task T001 --status ...`：更新单个任务状态；状态变更优先走它，不手改状态字段，除非脚本不可用且已记录原因。
- `scripts/validate_ledgers.py --root .`：检查四个 `AGENT_*` 账本结构、任务字段、状态、实现者/审查者分离和可恢复性；创建账本后、resume 后、commit 前必须跑。
- `scripts/validate_ledgers.py --root . --require-executable-plan`：进入分派前使用；如果 `AGENT_TASKS.md` 仍包含 bootstrap task，必须失败。
- `scripts/validate_ledgers.py --root . --require-complete`：最终提交和完成前使用；如果任一任务未 verified 或 bootstrap task 仍存在，必须失败。
- `scripts/eval_project_task_executor.py --json`：SkillOpt-lite 评测入口；用固定 train/heldout fixtures 检查 bootstrap、依赖、完成态、review 覆盖和角色分离 gate。修改这个 skill 或脚本 gate 后必须跑；分数退化时拒绝该改动或记录 blocker。

如果脚本路径存在，以脚本输出为准；如果脚本尚未实现或不可执行，必须在 `AGENT_REVIEW.md` 记录 gate 缺失、临时替代动作和风险。

## State Discipline

- 不允许靠聊天口头宣布任务完成；任务状态必须写回 `AGENT_TASKS.md`。
- `implemented-unverified` 不是完成；只有通过整体 review 和验证后的任务才能标为 `verified`。
- review 结论、发现、返工和验证结果必须写回 `AGENT_REVIEW.md`。
- 关键取舍、范围变化、依赖变化和风险接受必须写回 `AGENT_DECISIONS.md`。
- 聊天回复只是摘要；repo 内 `AGENT_*` 文件才是恢复、审查和提交依据。

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

如果目录不是 git repo，或者验证/commit 无法成立，先报告 blocker，不进入执行循环。

## Phase 2: Brainstorm

对实质性项目任务先做头脑风暴：

- 默认提出 3-5 个优化方向；复杂项目至少 5 个。
- 每个方向说明：思路、收益、成本、风险、验证方式。
- 只保留能服务当前项目目标的方向，避免无关平台化扩张。
- 对非平凡决策比较 2-4 个可行方案，并选择当前最适合方案。

只有阻塞性决策才问用户；低风险不确定点做明确假设并继续。

## Phase 3: Optional Council

遇到复杂决策时，启动真实 read-only subagent debate，或先切到 `planner-coordinator` 产出方案再回到执行循环：

- 架构/可维护性、性能/效率、用户价值/结果质量之间存在明显冲突。
- 方案会影响长期架构、数据模型、发布质量、成本或安全边界。
- 用户明确要求“辩论议会”“优化议会”“多角色优化”。
- 涉及论文、学术内容、引用、实验、结论时，需要独立证据审查。

默认 3-5 轮；用户明确要求时按指定轮数执行。每轮由主 agent 整合当前最佳方案，第末轮输出最终方案、取舍理由和验证策略。

学术边界：不得编造引用、实验、数据或结论。证据不足时标记 `unknown`、`needs verification` 或 `blocked by missing evidence`。

## Phase 4: Ledger Files

在项目根目录创建或更新以下文件；如果项目规则指定了别的位置，服从项目规则。

优先用脚本初始化账本：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/init_ledgers.py" --root . --goal "..."
```

初始化后的 `AGENT_TASKS.md` 会包含 `T001: Define executable task plan`。这是 `planned` 状态的 bootstrap task，只代表账本结构已创建，不代表任何项目实现任务已完成；进入执行前应把它替换或细化为真实 task list。

### `AGENT_PRD.md`

包含：

- 项目目标
- 背景
- 当前问题
- 头脑风暴方向摘要
- 选定方案
- 非目标
- 验收标准
- 风险和约束

### `AGENT_TASKS.md`

使用以下格式：

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
  - Status:
```

任务必须边界清晰。可并行任务应分配给不同 subagent；存在依赖的任务按 wave 排列。

### `AGENT_DECISIONS.md`

记录关键决策：

- Date
- Decision
- Reason
- Alternatives
- Risk

### `AGENT_REVIEW.md`

记录整体审查和必要的任务级发现：

- Scope
- Reviewer
- Conclusion
- Findings
- Verification
- Passed
- Follow-up

账本创建或更新后必须立即运行：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/validate_ledgers.py" --root .
```

validate 未通过时，先修复账本或记录 blocker；不要进入任务分派。

把 bootstrap task 替换或细化成真实项目任务后，分派前必须再运行：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/validate_ledgers.py" --root . --require-executable-plan
```

如果 validate 通过但 `--require-executable-plan` 失败，不要直接分派实现工作；先把 bootstrap task 替换或细化成真实项目任务。

## Phase 5: Parallel Work Loop

执行默认按 task waves 推进：

1. 分派任务前先运行：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/validate_ledgers.py" --root . --require-executable-plan
python3 "$PTE_SKILL_DIR/scripts/next_wave.py" --root .
```

2. 按脚本输出选择可并行 tasks；不要凭聊天记忆或肉眼猜下一批。
3. 分派前把任务标为 `in_progress`；状态变更优先使用：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/update_task.py" --root . --task T001 --status in_progress
```

4. 优先分配给真实 implementation subagents；强耦合或阻塞性工作才留在主 agent。
5. 每个 subagent 限定文件范围，并说明不得覆盖他人改动。
6. subagent 完成后汇报 changed paths、实现摘要、本地自检、blockers。
7. 主 agent 只做冲突整合和状态记录，不做逐项最终验收。
8. 实现完成但未整体验证时标为 `implemented-unverified`；blocked 时标为 `blocked` 并记录原因。
9. 如果发现任务冲突、依赖遗漏或范围扩大，更新 `AGENT_TASKS.md` 或 `AGENT_DECISIONS.md` 后继续。
10. 当前 wave 完成后再次运行 `next_wave.py`，直到所有任务完成或遇到真实 blocker。

如果没有足够独立任务值得并行，记录原因并由主 agent 本地完成最小 bounded change；不要为了形式上的 subagent 而停滞。

任务状态建议：

- `planned`
- `in_progress`
- `implemented-unverified`
- `blocked`
- `verified`

## Phase 6: Integrated Review And Verification

所有任务或当前执行批次完成后，再统一检查：

1. 运行 `git status` 并确认 changed file scope。
2. 做整体 diff review，检查：
   - 是否满足 `AGENT_PRD.md` 和 `AGENT_TASKS.md`
   - 是否有 subagent 冲突、重复实现或遗漏集成
   - existing behavior 是否被破坏
   - edge cases、over-design、missing tests/docs
   - 安全、数据、学术证据等特殊边界
3. 运行项目自带 tests、lint、build、typecheck、domain gate，或最窄可信替代。
4. 审查或验证失败时，批量记录到 `AGENT_REVIEW.md`，再分配返工任务。
5. 同一批次最多返工 3 轮；仍失败则标记 blocked 并说明原因。
6. 全部通过后，统一更新：
   - `AGENT_TASKS.md`
   - `AGENT_REVIEW.md`
   - `AGENT_DECISIONS.md`（如有重要决策）
7. 提交前必须运行 ledger gate：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/validate_ledgers.py" --root . --require-complete
```

8. commit 前必须同时通过：
   - `validate_ledgers.py --root . --require-complete`
   - 项目自己的 tests、lint、build、typecheck、domain gate，或最窄可信替代
   - 人工整体 diff review

`validate_ledgers.py` 只做结构性账本检查；项目真实质量仍以 tests、lint、build、typecheck、domain gate 和人工 diff review 为准。

### SkillOpt-lite Eval

维护这个 skill 时，不要凭感觉接受规则改动。先跑固定评测，再做 bounded edit：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/eval_project_task_executor.py" --json
```

接受改动的最低条件：

- `score` 不低于改动前。
- `heldout` split 不退化。
- 新增规则优先对应一个新增 fixture 或一个已观测失败模式。
- 每轮只改 1-4 个规则或一个脚本 gate；不要整篇重写。
- 被拒绝的方向记录到 `AGENT_REVIEW.md` 或当前维护记录中，避免重复尝试。

## Phase 7: Commit And Completion

默认在整体审查和整体验证通过后再 commit。不要在每个任务刚完成时提交。

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

最终汇报：

- 完成了什么
- 每个任务的结果
- subagent 分工和交付摘要
- commit 摘要
- 测试结果
- 剩余风险
- 后续建议

如果创建了 session goal，只有在项目目标真的完成且没有剩余必要工作时，才标记 goal complete。

## Resume Protocol

长时间任务、context compaction 或新会话恢复时，先读：

- `AGENT_PRD.md`
- `AGENT_TASKS.md`
- `AGENT_DECISIONS.md`
- `AGENT_REVIEW.md`
- `git status`

然后先跑：

```bash
PTE_SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/project-task-executor"
python3 "$PTE_SKILL_DIR/scripts/validate_ledgers.py" --root .
python3 "$PTE_SKILL_DIR/scripts/next_wave.py" --root .
```

validate 失败时先修复账本或记录 blocker；通过后按 `next_wave.py` 输出从第一个未完成、未验证或 blocked 的任务/wave 继续。不要仅凭聊天记忆继续执行。

## 常见错误

- 把这个 skill 用在小修小补上。
- 只创建账本，但执行时不维护。
- 没有优先考虑 subagent 并行。
- 让同一个角色实现并批准自己的 diff。
- 每个任务刚实现就急着 commit，导致集成后难以统一审查。
- 所有任务完成后没有做整体 diff review 和项目 gate。
- 测试通过了，但漏记 `AGENT_*` 账本或 review 记录。
