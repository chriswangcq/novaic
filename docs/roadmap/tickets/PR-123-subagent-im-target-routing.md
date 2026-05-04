# PR-123: SubAgent IM target routing

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


## 背景

`SUBAGENT_SEND` / `SPAWN_SUBAGENT` 的 outbox payload 已经携带目标 `subagent_id`，但 subscriber dispatch 时没有把它传给 Runtime assembler，导致目标子 Agent 可能被发到 main agent session，破坏 IM 通信语义。

## Scope

- Business `dispatch_subscriber` 只负责从 outbox payload 取目标 `subagent_id` 并传给 queue dispatch assembler。
- 不改变工具 schema。
- 不改变 spawn 的消息类型，保持本票可独立 merge。

## 非目标

- 不删除 `subagent_report` / `subagent_query` / `subagent_cancel`。
- 不删除 `SPAWN_SUBAGENT`。

## 实施计划

- 单条 outbox 投递：把 payload top-level `subagent_id` 透传到 `assemble_sync(..., subagent_id=...)`。
- 聚合投递：保留 user-message 聚合语义；如果未来 payload 有目标 subagent，则同样透传。
- 确保 metadata 仍原样透传，不靠 metadata 覆盖 Runtime session context。

## 单元测试

- Business subscriber 单测：`SUBAGENT_SEND` payload 带 `subagent_id` 时，assembler 收到同一 `subagent_id`。
- Business subscriber 单测：`SPAWN_SUBAGENT` payload 带 `subagent_id` 时，assembler 收到同一 `subagent_id`。
- 保持既有 user-message 聚合测试通过。

## 冒烟测试

- 本地跑 Business subscriber 相关测试。
- 如有可用环境，发送一条 parent → child 的 `subagent_send`，确认 dispatch request 的 session key 指向 child。

## 部署 Checklist

- Business 测试通过。
- Business 服务部署。
- 线上日志 grep：`dispatch_subscriber` 对 `subagent_send` / `spawn_subagent` 的 dispatch 记录包含目标 subagent。

## GitHub / Merge

- 单独 PR，可独立 merge。
- Commit message: `fix(business): route subagent im dispatch to target subagent`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: Business prompt/spawn tests, Runtime tool path tests, Common tool contract tests, and Cortex tool-schema tests passed in the current `main` workspace.
- Current architecture: SubAgent communication is aligned around `subagent_spawn` + `subagent_send`; no additional work remains in this ticket.
