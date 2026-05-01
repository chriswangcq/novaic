# PR-127: Remove `subagent_query` and `subagent_cancel` LLM tools

## 背景

子 Agent 通信保留 `spawn` + `send` 两个 LLM 能力。`query` / `cancel` 属于旧控制面工具，不应暴露给模型作为聊天主路径能力。

## Scope

- 从 canonical LLM tool schema 删除 `subagent_query` / `subagent_cancel`。
- 从 Runtime tool executor 删除 query/cancel handler 与 mapping。
- 删除只服务 LLM 工具的 Business internal routes。
- 更新 prompt 工具速查和测试。

## 非目标

- 不影响内部后台或 UI 如果仍需直接读 subagent 状态的非 LLM API；若发现只服务旧工具，则物理删除。
- 不改 spawn/send。

## 实施计划

- 搜索 active code 中 query/cancel 调用点并分类：LLM 工具路径 vs 非 LLM 控制面。
- 删除 LLM 工具路径。
- 增加 guardrail：tools 数组仅包含 `subagent_spawn` / `subagent_send` 两个 subagent 通信工具。

## 单元测试

- Common tool schema 测试。
- Runtime tool dispatch contract 测试。
- Business prompt contract 测试。
- API 删除后相关旧测试移除或改为新不变量测试。

## 冒烟测试

- 生成 LLM call，确认无 `subagent_query` / `subagent_cancel`。
- spawn/send 仍可用。

## 部署 Checklist

- Common/Runtime/Business 测试通过。
- Business + Runtime 部署。
- 线上 LLM call 抽样确认无 query/cancel tools。

## GitHub / Merge

- 依赖 PR-126 preferred。
- Commit message: `refactor(agent): remove subagent query and cancel tools`

## Closure — 2026-05-01

- Status: verified closed and deployed.
- Verification: Common and Cortex tool-schema tests passed; active LLM tool schemas do not expose `subagent_query` or `subagent_cancel`.
- Current architecture: SubAgent LLM-facing control surface is `subagent_spawn` + `subagent_send`.
