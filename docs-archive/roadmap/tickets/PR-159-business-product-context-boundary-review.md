# PR-159 — Business Product Context Boundary Review

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | novaic-business, novaic-agent-runtime, novaic-common, novaic-cortex, docs |
| Depends on | PR-158 |

## Goal

收口 Business 内部产品上下文边界：`profile`、`chat_history`、`subagent`、`device binding` 等仍然可以是产品价值路径，但不能被包装成“Agent 自主记忆”，也不能绕过 Cortex 的 scope/context 连续性模型。

## Why This Matters

Business 可以拥有产品数据和用户上下文，但如果这些路径在 prompt、Runtime 或 tool contract 里被描述成 Agent 自己的长期记忆，就会重新制造多套连续性系统。当前原则是：Cortex 负责 scope/context；Business 负责产品上下文；两者不能互相冒充。

## Required Process

1. 分析现状：扫描 Business prompt、profile/chat_history/subagent/device binding、Runtime business client、Cortex context assembly 的边界。
2. 创建小工单：每个边界泄漏或误导措辞单独成票。
3. 对照小工单实施：每个小票必须包含单元测试、冒烟测试、部署、git 提交。
4. 确认是否收口：若仍有产品上下文绕过 Cortex 或伪装成自主记忆，继续拆票；否则关闭本大票。

## Boundary Invariant

- Cortex owns durable Agent continuity through scopes and summaries.
- Business owns product context and product APIs.
- `chat_history` 是只读上下文工具，不是长期记忆系统。
- `profile` 如存在，只能作为产品画像/偏好数据，不得在 prompt 中暗示 Agent 自己维护隐藏记忆。
- `subagent` communication should use IM semantics.
- `device binding` is device capability context, not Agent memory.

## Small Tickets

- [x] PR-159A — Business Product Context Boundary Guardrail

## Done Criteria

- [x] Prompt and tool descriptions do not imply Business product data is Cortex memory.
- [x] No active Runtime/Cortex path pulls Business profile/chat_history/subagent/device binding as a hidden continuity substitute.
- [x] Business tests or guardrails pin the product-context wording and ownership boundary.
- [x] Representative LLM prompt/context smoke confirms the boundary.
- [x] Affected services are deployed and git commits are recorded.

## Current-State Closure Notes

PR-159A covered the only active gap found in this review: the boundary existed in code, but was not pinned as one cross-repo product-context invariant. Business prompt wording now has direct tests, Runtime BusinessClient has explicit retired-wrapper guards, and Cortex active code guard now blocks Business product-context/schema ownership markers.
