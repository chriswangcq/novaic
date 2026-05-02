# PR-158A — Tool Product Semantics Contract

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | [PR-158](PR-158-runtime-tool-product-semantics-matrix.md) |
| Repos | novaic-common, novaic-agent-runtime, novaic-app, docs |

## Goal

新增机器可读的 Runtime tool 产品语义矩阵，让工具验收不再只停留在“schema/executor/display kind 名字集合一致”。

## Current Finding

- Common 已有 canonical LLM schemas。
- Runtime 已有 `_EXECUTORS`。
- Common 已有 `execution_log_display.json`，App 也按该文件校验 monitor display kinds。
- 缺口：没有一个 contract 同时描述每个工具的产品价值、失败语义、Agent Monitor 表达和 LLM description 必须承诺的重点。

## Implementation Checklist

- [x] 在 `novaic-common/common/contracts` 添加 tool product semantics contract。
- [x] Common 测试：矩阵覆盖所有 LLM-facing builtin tools，并与 display contract 对齐。
- [x] Runtime 测试：矩阵覆盖所有 `_EXECUTORS`，且每个 tool 的 monitor kind 与 Runtime log data 一致。
- [x] App 测试：Agent Monitor display titles 覆盖矩阵声明的 monitor kind。
- [x] 更新 PR-158 父票 current-state / small-ticket 状态。

## Test / Smoke / Deploy Checklist

- [x] `novaic-common`: targeted contract tests pass。
- [x] `novaic-agent-runtime`: targeted runtime contract tests pass。
- [x] `novaic-app`: targeted Agent Monitor tests pass。
- [x] Deploy affected service(s) if runtime/common contract behavior is packaged.
- [x] Commit subrepos and root submodule/docs bump.

## Done Criteria

- [x] 新增工具时，如果没有产品语义矩阵条目会失败。
- [x] 工具 monitor kind 与矩阵不一致会失败。
- [x] LLM description 缺少矩阵声明的关键承诺会失败。
- [x] 本票可独立 merge.

## Verification Notes

- Common: `python3 -m pytest tests/test_tool_product_semantics_contract.py tests/test_execution_log_display_contract.py tests/test_tool_definitions_contract.py` → 11 passed.
- Runtime: `python3 -m pytest tests/test_runtime_tool_path_contract.py tests/test_pr86_execution_log_metadata.py tests/unit/task_queue/test_tool_handlers_display_chat_history.py tests/unit/task_queue/test_tool_handlers_failure_event.py` → 23 passed.
- App: `npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx` → 12 passed.
- Deploy: `./deploy runtime` restarted all backend services; `./deploy status` confirmed Entangled, Gateway, Business, Device, Queue Service, Storage-A, Cortex, workers, and Relay running.
- Git: `novaic-common` `4256a8c`, `novaic-agent-runtime` `c2efcd8`, `novaic-app` `950f718`, plus root submodule/docs bump.
