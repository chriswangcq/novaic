# P507 Finalize/Watchdog/Recovery Ownership Map

## Raw Evidence

- `.complex-problems/L20260516-222011/tmp/p507/finalize-recovery-raw-guard.txt`
- `.complex-problems/L20260516-222011/tmp/p507/key-source-slices.md`
- `.complex-problems/L20260516-222011/tmp/p507/artifact-line-counts.txt`

## Ownership Matrix

| Path | File Evidence | Owner | Notes |
| --- | --- | --- | --- |
| Normal wake finalize payload construction | `task_queue/sagas/wake_finalize.py:97-113` in `key-source-slices.md` | Wake finalize saga definition | `_remaining_stack_snapshot` requires a dict; `_build_session_ended_payload` carries `finalize_reason`, `generation`, and `remaining_stack` into `SESSION_ENDED`. |
| Session-ended task validation | `task_queue/handlers/session_handlers.py:31-82` | Task handler boundary | Validates required `scope_id`, positive `generation`, non-empty `finalize_reason`, and dict `remaining_stack`; delegates to `saga_client.session_ended`. |
| Queue session finalize mutation | `queue_service/session_repo.py:502-650` | SessionRepository + session ledger/FSM | Closes the active generation via ledger transition, records finalize metadata, and either closes or restarts from pending inbox through outbox effect. |
| Wake start/restart after pending inbox | `queue_service/session_repo.py:650-674` and `session_recovery.py:99-132` | SessionRepository + recovery shaping helper | Recovery marker becomes explicit dispatch metadata; new wake creation remains outbox-mediated. |
| Saga failure compensation | `queue_service/saga_repo.py:1180-1326` | SagaRepository compensation writer + saga outbox | Failed wake/think/actions saga queues `create_wake_finalize_saga` effect with explicit or unknown `remaining_stack`; publishing is delegated to saga outbox processing. |
| Wake-finalize failure detection | `queue_service/saga_repo.py:1345-1375` | SagaRepository suspected-dead event writer | Failed `wake_finalize` records `SESSION_SUSPECTED_DEAD` with `reason`, generation, recovery id, and remaining stack diagnostics. |
| Suspected-dead marker shaping | `queue_service/session_recovery.py:59-96` | Pure recovery helper | Converts explicit suspected-dead event into recovery marker; no DB or queue side effects. |
| Recovery archive effect construction | `queue_service/session_recovery.py:143-187` | Pure recovery helper + session outbox effect | Builds `RECOVERY_ARCHIVE_SCOPE`; missing stack becomes explicit unknown, invalid stack is rejected. |
| Recovery archive publish | `queue_service/session_outbox.py:198-228` | SessionOutboxDispatcher | Required side-effect outlet that publishes `CORTEX_SCOPE_END` only after validating scope, generation, and `remaining_stack`. |
| Wake-created observation | `queue_service/session_observed_events.py:31-130` | Observed-event handler + session ledger | Applies outbox-created saga observation idempotently and records active session via `session_state` projection. |
| Cortex archive bridge | `task_queue/handlers/cortex_handlers.py` and `task_queue/utils/cortex_bridge.py:121-152` from raw guard | Cortex scope-end handler + bridge client | Queue handler requires generation/remaining stack before bridge call. Bridge method remains generic enough to omit optional fields, but active session-finalize route is strict. |

## Ownership Conclusion

The checked paths are event/FSM/outbox-oriented:

- Normal finalize goes `wake_finalize saga -> SESSION_ENDED task -> SessionRepository.session_ended -> session ledger transition`.
- Recovery archive goes `suspected-dead event -> pure recovery helper -> session outbox effect -> SessionOutboxDispatcher -> CORTEX_SCOPE_END`.
- Recovery wake creation goes through `SessionRepository` dispatch/restart logic and session outbox, not direct saga creation in the session repo.
- Saga failure compensation writes durable saga outbox effects or explicit suspected-dead events; it does not directly archive Cortex or mutate session state as a hidden side effect.

## P508 Candidate Gaps

No active ownership bypass was found. Two watch items do not require source changes unless future policy narrows them further:

1. `CortexBridge.scope_end` keeps optional fields because it is a generic bridge client; the active `CORTEX_SCOPE_END` handler is strict.
2. Saga failure compensation may use explicit unknown stack when the failed saga context lacks stack diagnostics; this is intentional and covered by recovery tests.
