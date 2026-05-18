# PR-158 — Runtime Tool Product Semantics Matrix

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | novaic-common, novaic-agent-runtime, novaic-app, novaic-business, novaic-cortex, docs |
| Depends on | PR-155, PR-157 |

## Goal

把 Runtime tool 从“schema/executor 存在”推进到“产品语义一致”：

- 每个 LLM-facing tool 有明确用户价值。
- 每个 tool 的失败语义清楚且可测试。
- Agent Monitor 的用户可见表达与真实执行一致。
- LLM tool description 不夸大能力、不暗示旧路径或 fallback。
- Chat UI / Agent Monitor / Runtime execution log 对同一个 tool 的体验一致。

## Why This Matters

PR-155 已经证明 Common schema、Runtime executor 和 Agent Monitor display kind 的工具名集合一致。但这还不够：工具名存在不代表产品语义正确。下一步要确认的是“模型看到的能力、Runtime 执行的行为、用户看到的监视器语言、失败时的体验”是同一件事。

## Required Process

1. 分析现状：逐个工具复核 schema description、executor、失败路径、execution log、Agent Monitor 展示和用户体验。
2. 创建小工单：每个具体不一致点单独成票，可独立测试和 merge。
3. 对照小工单实施：每个小票必须包含单元测试、冒烟测试、部署、git 提交。
4. 确认是否收口：若仍有不一致，继续回到第 2 步；否则关闭本大票。

## Boundary Invariant

- Common owns LLM tool schema.
- Runtime owns execution and failure result shape.
- Common display contract owns monitor event kind and user-facing wording keys.
- App renders semantic monitor events; it must not infer product semantics from raw debug payload.
- Business/Cortex only own their respective tool side effects, not the global product matrix.

## Initial Candidate Tools

- `shell`
- `skill_begin`
- `skill_end`
- `chat_reply`
- `display`
- `audio_qa`
- `chat_history`
- `subagent_spawn`
- `subagent_send`
- `sleep`

## Small Tickets

- [x] [PR-158A — Tool Product Semantics Contract](PR-158A-tool-product-semantics-contract.md)

## Current-State Analysis

2026-05-02 scan found:

1. Common `AGENT_BUILTIN_TOOL_SCHEMAS` exposes ten active LLM-facing tools: `shell`, `skill_begin`, `skill_end`, `chat_reply`, `display`, `audio_qa`, `chat_history`, `subagent_spawn`, `subagent_send`, `sleep`.
2. Runtime `_EXECUTORS` implements exactly those names.
3. Common `execution_log_display.json` maps exactly those tool names to Agent Monitor display kinds.
4. App `executionLogUtils.test.ts` verifies App display titles cover every backend display kind.
5. Missing piece: no checked-in acceptance matrix describes product value, failure semantics, user-facing monitor behavior, and LLM description commitments per tool.

First concrete small ticket is PR-158A: add that product semantics contract and bind Common/Runtime/App tests to it.

## Closure

2026-05-02 PR-158A added a machine-readable `tool_product_semantics.json` contract in Common. The contract now pins each active LLM-facing tool to product value, success/failure semantics, monitor display kind, user experience, and LLM description commitments. Common, Runtime, and App tests consume the same contract so a new tool cannot be added by schema/executor/display-kind only.

## Done Criteria

- [x] A checked-in tool semantics matrix exists and is treated as the acceptance reference.
- [x] Tests fail if a tool is added without product semantics / failure semantics / monitor mapping.
- [x] Each tool has an intentional failure story and user-facing monitor expression.
- [x] LLM tool descriptions match actual executor behavior.
- [x] A representative smoke run confirms monitor and chat behavior for at least one success and one failure case.
- [x] Affected services are deployed and git commits are recorded.
