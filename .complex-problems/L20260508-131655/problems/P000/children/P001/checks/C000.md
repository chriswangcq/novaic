# P001 Check - FSM substrate 与状态机接入

## Status

success

## Summary

P001 的目标是审计 FSM substrate 与状态机接入是否真实落地。证据显示 generic FSM substrate 已存在，Session/Task/Saga 主生命周期均已通过 pure decision + generic store + ledger/outbox 接入，关键旧路径如 `tq_active_sessions` 和 dispatch direct wake creation 不再是活路径。

## Criteria Map

- 覆盖 FSM substrate：已覆盖 `queue_service/fsm/core.py` 与 `queue_service/fsm/sqlite_store.py`。
- 覆盖 Session 接入：已覆盖 `session_fsm.py`、`session_ledger.py`、`session_repo.py`、`session_outbox.py`、schema 和切换测试。
- 覆盖 Task 接入：已覆盖 `task_fsm.py`、`task_ledger.py`、`queue_db.py` 和切换测试。
- 覆盖 Saga 接入：已覆盖 `saga_fsm.py`、`saga_ledger.py`、`saga_repo.py` 和切换测试。
- 旧路径判断：`tq_active_sessions` 运行时代码无活 SQL 引用；wake creation direct create 仅在 outbox side-effect adapter。

## Execution Map

- 搜索运行时代码和测试中的 `tq_active_sessions`、`active_sessions`、wake creation/outbox 相关引用。
- 读取 Session/Task/Saga FSM、ledger、repo、schema、outbox adapter。
- 运行 13 个相关测试文件，共 57 个测试。

## Stress Test

这次没有只看命名或摘要，而是同时确认：

- 数据表权威性：`tq_session_state` / `tq_task_state` / `tq_saga_state`
- side effect 边界：session outbox dispatcher
- durable wake cutover：dispatch 返回 `WAKE_START_QUEUED`，outbox worker 创建 saga
- guard tests：旧表/旧 shadow/helper residue 检查

## Residual Risk

- FSM 基建是活路径，但还不是“业务只剩 DSL”的终态；repos/coordinators 仍较厚。
- legacy vocabulary 还存在于函数名和诊断接口名，不是活旧表路径，但会影响代码阅读。
- 尚未在本问题内审计 worker assembly、显式依赖边界、旧兼容分支和 CI 守卫，这些由 P002-P005 覆盖。
