# P001 Success Check - Generic FSM Runner 接入 Session/Task/Saga

## Summary
P001 is successful. Active Session/Task/Saga transition write paths now route through the generic `FsmTransitionRunner`, keeping business reducers/handlers away from repeated event/state/outbox persistence mechanics.

## Evidence
- `queue_service/fsm/runner.py` provides the generic transition write substrate.
- `SessionLedgerRepository.record_transition()` calls `FsmTransitionRunner.record()`.
- `TaskQueue._record_task_transition()` calls `TaskLedgerRepository.record_transition()`.
- `SagaRepository._record_saga_transition()` calls `SagaLedgerRepository.record_transition()`.
- Source guard confirms no active direct `_task_ledger.append_event/upsert_state` and no active direct `_saga_ledger.append_event/upsert_state/append_outbox`.

## Criteria Map
- Runner used by active paths: met for Session/Task/Saga transition paths.
- Repeated mechanics centralized: met for event + materialized state + outbox effects.
- Explicit dependency boundary: met; runner takes IDs/timestamps/payloads as arguments and imports no clock/env/random/uuid modules.
- Tests: met by `test_pr342_generic_fsm_transition_runner.py` and existing FSM regression group.

## Execution Map
- Added runner.
- Wired ledger adapters.
- Replaced direct active-path persistence calls.
- Added tests.
- Ran targeted regression suite.

## Stress Test
The targeted suite exercises generic core purity, SQLite store contract, session generic store cutover, task FSM cutover, saga FSM cutover, final residue guards, and the new transition runner guard. All passed.

## Residual Risk
Lease lifecycle still uses its separate existing ledger mechanics. That is outside this ticket's Session/Task/Saga scope and can be handled by a later runner-expansion ticket if desired.
