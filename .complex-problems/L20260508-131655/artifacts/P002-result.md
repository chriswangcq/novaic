# P002 Result - 审计业务 DSL 与 worker assembly 厚度

## Scope

审计 `novaic-agent-runtime/task_queue/workers` 的 worker assembly、business handler、action engine/effect adapter 是否满足“组件层通用员工，业务层尽量只写状态机/计算逻辑”的目标。

## Evidence Read

- `task_queue/workers/assembly_helpers.py`
  - 232 行。
  - 唯一集中构造 `GenericWorker`、`ConcurrentGenericWorker`、`WorkerRuntimeConfig`、`ShutdownController`、`SyntheticJobSource`。
  - 测试 `test_pr340_assembly_helpers.py` 明确禁止它依赖业务模块。
- `task_queue/workers/registry.py`
  - worker command registry 是 declarative `WorkerSpec` 列表。
  - `build_process` 指向 component assembly function，registry 不直接构造 worker/handler。
- `task_queue/workers/worker_assemblies.py`
  - 557 行。
  - 负责将 service config、clients、effect adapters、engines、handlers、sources 组装成 `WorkerProcessSpec`。
  - 没有 raw `GenericWorker`/`ConcurrentGenericWorker` 构造，全部经 `assembly_helpers`。
- `task_queue/workers/task_worker.py`
  - Handler 已是 typed boundary，仅 decode job 并委托 `TaskExecutionEngine`。
  - 测试守卫禁止 worker lifecycle、protocol clients、runtime dependencies 泄漏回 handler。
- `task_queue/workers/saga_worker.py`
  - Handler 已是 typed boundary，仅 decode claimed saga 并委托 `SagaLaunchEngine`。
- `task_queue/workers/task_execution.py`
  - 432 行。
  - 这是最厚的业务/协议 engine，包含 heartbeat、idempotency guard、retry/fail/complete、handler dispatch、saga step payload adaptation。
- `task_queue/workers/saga_launch.py`
  - 121 行。
  - 包含 heartbeat、DAG publish、mark launched/failed。
- `task_queue/workers/health_recovery.py`
  - 103 行。
  - 已通过 effect executor 执行 recovery action。
- `task_queue/workers/scheduled_wake.py`
  - 218 行。
  - 已通过 effect executor 执行 scheduled wake action，但仍含较多 result classification/metric/logging 分支。
- `task_queue/workers/*_effects.py`
  - task/saga/health/scheduler effect adapters 合计 267 行左右。

## Searches

Raw worker constructor 搜索：

- `GenericWorker(`、`ConcurrentGenericWorker(`、`WorkerRuntimeConfig(`、`ShutdownController(`、`SyntheticJobSource(` 只出现在 `assembly_helpers.py`。
- 在业务 handler、registry、engine 中没有 raw worker lifecycle constructor。

## Verification

在 `novaic-agent-runtime` 执行：

```bash
pytest -q \
  tests/test_pr340_action_engine_effect_boundaries.py \
  tests/test_pr340_assembly_helpers.py \
  tests/test_pr331_task_worker_handler_cutover.py \
  tests/test_pr333_saga_worker_handler_cutover.py \
  tests/test_pr328_health_generic_worker.py \
  tests/test_pr329_scheduler_generic_worker.py \
  tests/test_pr340_worker_effect_plan.py \
  tests/test_pr337_worker_command_registry.py \
  tests/test_pr335_worker_residue_guards.py \
  tests/test_pr338_business_handlers_lifecycle_free.py \
  tests/test_pr323_generic_worker_contracts.py \
  tests/test_pr324_generic_worker_loop.py \
  tests/test_pr326_session_outbox_generic_worker.py \
  tests/test_pr327_saga_outbox_generic_worker.py
```

结果：`66 passed in 0.26s`。

## Conclusion

当前已经达到“worker lifecycle/component substrate 统一”的形态：业务 worker modules 不再拥有 loop、shutdown、runtime config、source construction、client construction。通用 worker/并发 worker/synthetic worker 的构造集中在 `assembly_helpers.py`，worker registry 也已经声明式。

## Remaining Gaps

- 还没有达到“业务只剩几行 DSL”的极致形态。`worker_assemblies.py` 仍有 557 行组件组装代码，业务 role 的 wiring 仍以 Python 函数表达，而不是更小的 declarative spec。
- `task_execution.py` 仍是 432 行 protocol engine，包含 idempotency/retry/heartbeat/saga-step 适配。它比旧 worker loop 清晰，但不是纯 DSL。
- `scheduled_wake.py` 仍有较多分类分支和 logging/metrics 逻辑。它已是 action engine，不是 lifecycle loop，但还可以继续用小型 decision/plan DSL 收薄。
- effect adapter 已隔离 side effects，但 action kind 到 adapter method 的映射仍是手写 dict/method，不是统一的 declarative effect binding。
