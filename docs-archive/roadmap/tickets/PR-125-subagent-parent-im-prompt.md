# PR-125: Child subagent reports through parent IM

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


## 背景

子 Agent 需要知道父 Agent 的 subagent id，才能用 `subagent_send(parent_subagent_id, message)` 汇报结果。旧提示词仍引导 child 使用 `subagent_report`，这和统一 IM 方案冲突。

## Scope

- Business prompt builder 为 child subagent 注入 parent communication context。
- Prompt guide 改为：完成任务后向 parent 发送 `subagent_send`。
- 不改工具 schema，保证本票可独立 merge。

## 非目标

- 不删除 `subagent_report` tool；后续票删除。
- 不改变 main agent prompt 行为。

## 实施计划

- 查询当前 subagent 的 `parent_subagent_id`。
- child prompt 中显式写入 `你的 parent_subagent_id = ...`。
- 子 Agent 行为说明从 `subagent_report(...)` 改成 `subagent_send(target_subagent_id="<parent>", message="...")`。

## 单元测试

- Business prompt 单测：child prompt 包含 parent_subagent_id。
- Business prompt 单测：child prompt 不再要求使用 `subagent_report`。
- main agent prompt 不包含 child-only parent report 指令。

## 冒烟测试

- 创建 child，检查 LLM 调用里的 system prompt 是否含 parent id。
- child 完成任务时，用 `subagent_send` 回 parent。

## 部署 Checklist

- Business 测试通过。
- Business 服务部署。
- 线上抓一条 child LLM 调用，确认 parent IM 指令存在。

## GitHub / Merge

- 依赖 PR-124 preferred，可在 PR-124 前后独立 merge。
- Commit message: `fix(prompt): guide child subagents to report via parent im`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: `novaic-business/tests/test_pr111_system_prompt_builder.py` passed and confirms child prompt uses parent IM instead of `subagent_report`.
- Current architecture: child-to-parent substantive reporting is through `subagent_send`.
