# P537 Queue Service Production Classification

## Summary

Queue service production hits: 105 across 13 files.

Classification result: no follow-up-worthy risky residue found in this file group.

## File Classifications

| File | Hits | Category | Rationale |
|---|---:|---|---|
| `queue_service/main.py` | 1 | documentation/comment | `deprecated` appears in a startup/shutdown hook docstring explaining replacement of deprecated FastAPI `@app.on_event`; not a compatibility branch. |
| `queue_service/queue_audit.py` | 7 | live expected | `_optional_*` helpers normalize nullable audit values for read-only audit/replay output. No queue/session side effect. |
| `queue_service/queue_db.py` | 4 | live expected | `publish()` is the queue service's core public enqueue API; examples/docstrings and lease-active guard are expected in the queue substrate. |
| `queue_service/routes.py` | 6 | live expected | HTTP API endpoints expose queue publish, saga create, active session list, and finalize/restart payload fields. These are boundary APIs, not hidden bypasses. |
| `queue_service/saga_repo.py` | 15 | live expected | `remaining_stack` and `session_suspected_dead` are saga/session recovery effects. The effect pathway is explicit and covered by focused tests. |
| `queue_service/session_events.py` | 3 | live expected | `SESSION_SUSPECTED_DEAD` vocabulary constants are canonical event names. |
| `queue_service/session_fsm.py` | 4 | live expected | `suspected_dead`, `recovering`, and active-scope checks are the explicit FSM/state transition vocabulary. |
| `queue_service/session_ledger.py` | 6 | live expected | `record_active_session`, active generation, and `suspected_dead`/`recovering` are state projection/ledger adapter vocabulary. |
| `queue_service/session_observed_events.py` | 3 | live expected | Observed-event handling updates active session projection through ledger APIs; no legacy table ownership is visible in the hit context. |
| `queue_service/session_outbox.py` | 8 | live expected | `_publish`, `queue.publish`, and `remaining_stack` are the durable outbox dispatcher and recovery archive payload boundary. |
| `queue_service/session_rebuild.py` | 1 | live expected | `record_active_session` belongs to rebuild/projector synchronization. |
| `queue_service/session_recovery.py` | 10 | live expected | `remaining_stack` handling and suspected-dead recovery marker construction are current recovery semantics. |
| `queue_service/session_repo.py` | 37 | live expected | Active session, suspected-dead, generation, remaining-stack, and no-active vocabulary are the session coordinator/repository boundary. Focused tests cover finalize, attach, recovery, and active-state behavior. |

## Count Reconciliation

- Queue service production hits from P531: 105
- Classified hits in this artifact: 105
- Follow-up-worthy hits: 0

## Notes

The scan intentionally uses broad terms, so legitimate state vocabulary such as `active_session`, `suspected_dead`, `recovering`, and `remaining_stack` appears in active production code. These hits are expected when they sit at explicit FSM/repository/outbox boundaries.
