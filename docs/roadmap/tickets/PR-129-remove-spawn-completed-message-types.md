# PR-129: Remove `SPAWN_SUBAGENT` and `SUBAGENT_COMPLETED` message residues

## 背景

PR-124 后 spawn 初始任务走 `SUBAGENT_SEND`；PR-128 后 completed 不再是通信通路。此时 `SPAWN_SUBAGENT` / `SUBAGENT_COMPLETED` 留在 message lifecycle/context renderer 中只会误导后续维护。

## Scope

- 从 message lifecycle contract 删除 `SPAWN_SUBAGENT` / `SUBAGENT_COMPLETED`。
- 从 TriggerType 删除 `SPAWN_SUBAGENT`（若已无生产者）。
- 从 Runtime context renderer 删除 `SUBAGENT_COMPLETED` sender/render/filter 分支。
- 从 tests/docs/guardrails 删除旧类型引用。

## 非目标

- 不删除 `SUBAGENT_SEND`。
- 不改变 `subagent_spawn` 工具本身，只改变 spawn 后的消息通路。

## 实施计划

- 全仓搜索旧类型。
- 删除 active code 中旧 enum、renderer、outbox、prompt references。
- 增加 guardrail：message lifecycle allowed/hidden/outbox 都不包含旧类型。

## 单元测试

- Common message lifecycle contract 测试。
- Runtime context read/render 测试。
- Business subscriber/spawn 测试。

## 冒烟测试

- spawn child：只看到 `SUBAGENT_SEND` outbox。
- child report parent：只看到 `SUBAGENT_SEND` outbox。
- LLM context 中不出现 `SPAWN_SUBAGENT` / `SUBAGENT_COMPLETED` 特例。

## 部署 Checklist

- Common/Business/Runtime 测试通过。
- Business + Runtime 部署。
- 线上 SQL 检查新消息无旧类型；旧历史如需保留，只作为历史数据不再被 active code 特判。

## GitHub / Merge

- 依赖 PR-124 + PR-128。
- Commit message: `refactor(im): remove spawn and completed message residues`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: Common message lifecycle and Business spawn tests passed; old spawn/completed message paths are not active LLM communication paths.
- Current architecture: SubAgent traffic uses `SUBAGENT_SEND` semantics.
