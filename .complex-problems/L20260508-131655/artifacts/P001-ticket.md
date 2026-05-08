# 审计 FSM substrate 与状态机接入

## Problem Definition

需要确认当前 Runtime 是否已经把 generic FSM substrate、Session/Task/Saga 状态机、ledger/outbox 接到真实活路径，而不是保留新旧双路或 shadow-only 状态。

## Proposed Solution

阅读 Queue/FSM 相关源码、测试和 guard，搜索旧 SSOT 与直接分支残留，运行关键 FSM/session/task/saga 测试，并输出达成项与 gap。

## Acceptance Criteria

- 确认 generic FSM substrate 是否存在并被 Task/Saga/Session/worker lease 使用。
- 确认 session dispatch/finalize/recovery 是否走 session ledger/outbox/FSM。
- 确认 task/saga repository 是否走 FSM store/ledger/outbox。
- 列出仍未达到“完美 FSM”的代码结构 gap。

## Verification Plan

- `rg` 搜索 FSM/store/outbox 入口与旧路径。
- 阅读关键文件。
- 跑 session/task/saga FSM 关键测试。

## Risks

- 命名中的 `active_sessions` 可能是投影接口而非旧表，需要区分语义。

## Assumptions

- 审计基于当前工作树。
