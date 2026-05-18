# PR-159A — Business Product Context Boundary Guardrail

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-159 |
| Repos | novaic-business, novaic-agent-runtime, novaic-cortex, docs |

## Goal

把 Business 产品上下文与 Cortex 连续性边界固化成测试：Business 可以提供显式产品上下文，Runtime 可以请求 Business 组装系统提示词，但不得重新出现“Agent 自主记忆”、旧 notebook/task/profile 推断通路，Cortex active code 也不得代理这些业务上下文。

## Current-State Analysis

- Business prompt 已使用 `## 显式产品上下文`，并在系统提示词中说明 Business context 不是 Cortex 记忆。
- Runtime `BusinessClient` 仍保留必要的 `build_system_prompt`、entity CRUD、message transition、broadcast、recover 等服务调用；旧 drive/skill/task wrapper 已有部分 guard。
- Cortex 已有 PR-75/PR-76 guard，禁止 memory/notebook/task/search proxy、wake summary 和自动总结等概念回流，但还缺少对 Business 产品上下文字段的明确边界回归测试。

## Implementation Plan

- [x] Business：增加 prompt boundary 测试，确认显式产品上下文不会被命名为用户画像/记忆/笔记本/wake summary。
- [x] Runtime：扩展 BusinessClient boundary 测试，确认旧产品上下文 wrapper 不会重新出现。
- [x] Cortex：扩展 boundary guard，禁止 active Cortex code 引入 Business 产品上下文字段或 agent binding/schema ownership。
- [x] 运行 Business/Runtime/Cortex 目标测试。
- [x] 部署/状态检查。
- [x] Git 提交。

## Done Criteria

- [x] Prompt wording boundary is tested.
- [x] Runtime BusinessClient product-context wrappers are blocked.
- [x] Cortex active code cannot reintroduce Business context/schema ownership.
- [x] Tests pass.
- [x] Deployment/status check complete.
- [x] Git commits recorded.

## Verification

- `novaic-business`: `python3 -m pytest tests/test_pr159_product_context_boundary.py tests/test_pr144_prompt_memory_boundary.py tests/test_pr111_system_prompt_builder.py` — 12 passed.
- `novaic-agent-runtime`: `python3 -m pytest tests/test_pr112_business_client_boundary.py tests/test_pr85_llm_context_smoke_guardrails.py` — 6 passed.
- `novaic-cortex`: `python3 -m pytest tests/test_pr76_boundary_guard.py tests/test_pr75_proxy_boundary.py` — 10 passed.
- Deploy: `./deploy business`, `./deploy runtime`, `./deploy cortex`, then `./deploy status` — all backend services healthy; relay active.
- Git: `novaic-business` 120b6df, `novaic-agent-runtime` d7e25a4, `novaic-cortex` 6c77450.
