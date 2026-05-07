# PR-311 — Saga Compensation Outbox Cutover

Status: Closed

## Goal

Move saga compensation side effects out of repository/orchestrator decisions and
into durable outbox effects.

## Scope

- Convert wake-finalize creation into a durable effect.
- Convert session suspected-dead recording into a durable effect or session
  observed event publisher.
- Add effect publisher tests for idempotency and failure retry.

## Explicit Dependency Boundary Review

Saga reducer may choose compensation effect intent from explicit failure
context. It must not create sagas, write session events, or call external
services directly.

## Branch / Old Code Cleanup Ledger

Removed in this PR:

- `SagaOrchestrator.mark_failed` no longer calls `self.create(...)` to spawn
  wake-finalize compensation.
- `SagaOrchestrator.mark_failed` no longer writes session suspected-dead events.
- Saga compensation is represented as durable `tq_saga_outbox` rows.
- Added visible `saga-outbox-worker` process entrypoint and production start
  script wiring so committed saga compensation effects have an explicit
  publisher.

## Verification

- `python -m py_compile queue_service/saga_repo.py queue_service/saga_outbox_worker.py main_novaic.py`
- `pytest tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr247_recovery_outbox_cutover.py tests/test_pr233_active_inbox_dispatch.py tests/test_runtime_tool_path_contract.py`
- `pytest tests/test_pr312_saga_old_sql_residue_cleanup.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_pr310_saga_repository_fsm_cutover.py`

## Closure Notes

Closed. Saga failure paths now commit compensation intent before publishing it.
The publisher is explicit and retryable: failed effect publication increments
attempts and dead-letters after the configured maximum. Existing recovery tests
now drain saga outbox effects explicitly, matching the worker-owned publication
model.
