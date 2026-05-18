# PR-126: Remove `subagent_report` LLM tool path

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


## 背景

统一 IM 后，child 向 parent 汇报只走 `subagent_send`。`subagent_report` 是旧的并行汇报通路，会造成模型行为分叉和维护熵增。

## Scope

- 从 canonical LLM tool schema 删除 `subagent_report`。
- 从 Runtime tool executor 删除 `_exec_subagent_report` 与 mapping。
- 从 Business 删除只服务该工具的 report endpoint。
- 删除 active prompt / docs / tests 中对 `subagent_report` 的行为指令。

## 非目标

- 不删除 `subagent_query` / `subagent_cancel`。
- 不删除 `SUBAGENT_COMPLETED` 生命周期路径。

## 实施计划

- Common tool schema 物理删除 `subagent_report`。
- Runtime executor 物理删除 report handler。
- Business internal endpoint 物理删除 report route。
- 更新 contract tests，新增 guardrail：LLM tools 不包含 `subagent_report`。

## 单元测试

- Common tool schema 测试。
- Runtime tool dispatch contract 测试。
- Business prompt/tool contract 测试。

## 冒烟测试

- 生成 main 与 child LLM call，确认 tools 数组都没有 `subagent_report`。
- child 汇报通过 `subagent_send` 正常进入 parent IM。

## 部署 Checklist

- Common/Runtime/Business 测试通过。
- Business + Runtime 部署。
- 线上 LLM call 抽样确认无 `subagent_report`。

## GitHub / Merge

- 依赖 PR-125。
- Commit message: `refactor(agent): remove subagent report tool path`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: Common, Cortex, Business, and Runtime contract tests passed; active LLM tool schemas do not expose `subagent_report`.
- Current architecture: `subagent_report` is not an LLM tool path.
