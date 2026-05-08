# Generic FSM Runner 接入 Session/Task/Saga

## Problem Definition

当前已有 `FsmSqliteStore`，但各 domain ledger/repo 仍手写重复的 append event、upsert state、append outbox 组合流程。需要引入更上层但仍很薄的 Generic FSM Runner，让状态转移的持久化机制统一，并把它接入活路径，避免只添加未使用基础设施。

## Proposed Solution

实现一个小型 `queue_service.fsm.runner`：

- `FsmTransitionRecord` 描述 machine_id、event、state、outbox effects。
- `FsmTransitionRunner.record(...)` 统一完成 event append、state upsert、outbox append。
- runner 不读取 clock/id/env/db 外部状态；所有 id/time/payload 由调用方显式传入。
- 将 `TaskLedgerRepository` 和 `SagaLedgerRepository` 接入 runner，用于通用 event/state/outbox mechanics。
- Session 的 `record_transition` 仍保留 session-specific input consumption，但内部可复用 runner 做 event/state/outbox 主体。

## Acceptance Criteria

- 新 runner 被 Session/Task/Saga 活路径至少两条使用，最好三条都使用。
- Task/Saga `_record_*_transition` 不再直接调用 append_event + upsert_state + append_outbox 三件套。
- Runner 单元测试证明 event/state/outbox 统一持久化和无 hidden input。
- 现有 FSM cutover tests 通过。

## Verification Plan

- 新增/更新 runner tests。
- 运行 FSM targeted tests。
- 搜索 runner 使用点，确认不是 dead code。

## Risks

- 抽象过度会掩盖 domain projection 差异；runner 只承接通用持久化，不承接业务 projection merge。
- Session input-consumed 逻辑是 session-specific，不能硬塞进 generic runner。

## Assumptions

- 不改数据库 schema。
- 不做历史数据兼容分支。
