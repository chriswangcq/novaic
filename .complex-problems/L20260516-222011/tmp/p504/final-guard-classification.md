# P504 Final Imperative Dispatch Guard Classification

## Raw Artifacts

- `.complex-problems/L20260516-222011/tmp/p504/guard-commands-and-scope.md`
- `.complex-problems/L20260516-222011/tmp/p504/hit-counts.tsv`
- `.complex-problems/L20260516-222011/tmp/p504/production-hit-counts.tsv`
- `.complex-problems/L20260516-222011/tmp/p504/*-production.txt`
- `.complex-problems/L20260516-222011/tmp/p504/runtime-diff-before-classification.txt`

## Production Hit Classification

| Bucket | Production Evidence | Classification |
| --- | --- | --- |
| Direct saga creation | `queue_service/session_outbox.py:148-196` | Required session outbox dispatcher boundary. P486 explicitly retained this as the only session-owned wake saga creation outlet. |
| Create-wake effect builder | `queue_service/session_effects.py:13`, `queue_service/session_wake_plan.py:76`, `queue_service/session_wake_plan.py:113` | Intended FSM/outbox effect construction, not a direct side effect. |
| Observed wake strings | `queue_service/session_observed_events.py:77`, `:93`, `:130` | Observation/race handling labels for already-dispatched outbox effects. |
| Generic task publish route | `queue_service/routes.py:217-219` | Required generic queue adapter boundary. P485 retained and guarded it as non-session-owned infrastructure. |
| Session queue publish | `queue_service/session_outbox.py:212`, `:255` | Required session outbox dispatcher boundary. P486 guard requires exactly these session-owned publish outlets. |
| Generic worker task publish | `task_queue/workers/saga_effects.py:35`, `task_queue/workers/task_effects.py:84` | Required worker effect execution boundary; not session dispatch decision logic. |
| Client/queue examples | `task_queue/client.py:36`, `queue_service/queue_db.py:75` | Documentation/example snippets inside production modules; not active dispatch branches. |
| Active-session naming | `queue_service/session_repo.py:697-831`, `queue_service/routes.py:599`, `queue_service/session_ledger.py:431` | Current projection API over `session_state` SSOT. No `tq_active_sessions` table path remains in production hits. |
| Attach generation | `queue_service/session_outbox.py:242-263`, `task_queue/handlers/runtime_handlers.py:253-322`, `task_queue/contracts/session_generation.py` | Strict positive-generation validation path. No no-generation attach production path found. |
| Cortex bridge generation | `task_queue/utils/cortex_bridge.py:121-152` | Bridge method accepts optional fields, but the active queue handler caller requires `session_generation`, `remaining_stack`, and finalize metadata before calling it. This is not an active bypass, but it is a hardening candidate if the bridge becomes session-finalize-only. |
| Finalize/session-ended | `task_queue/sagas/wake_finalize.py:97-113`, `task_queue/handlers/session_handlers.py:51-77`, `queue_service/session_repo.py:502-528`, `queue_service/saga_repo.py:1140-1374`, `queue_service/session_recovery.py:160-180` | Current strict finalize/recovery/session-ended path. Remaining stack is required or explicitly unknown in recovery. |
| Tool-surface migration labels | `task_queue/tool_surface_policy.py:1-60` | Intentional final policy vocabulary: migrated interface tools are a denylist/classification set for shell capability routing. |
| Schema migration text | `queue_service/db/schema.py:433-436` | Fresh-schema guard error message for unsupported old DBs; not runtime compatibility behavior. |
| Deprecated startup text | `queue_service/main.py:61` | Comment explaining FastAPI lifecycle replacement. Not dispatch logic. |

## Test/Docs Guard Hits

The full raw files include intentional guard tests such as:

- `tests/test_pr255_legacy_compat_cleanup.py`
- `tests/test_pr257_remove_active_sessions_table.py`
- `tests/test_pr267_session_outbox_effect_boundary.py`
- `tests/test_pr273_session_harness_final_residue_guard.py`
- `tests/test_saga_creation_policy_boundary.py`
- `tests/test_runtime_tool_path_contract.py`

These are regression guards or fixture terms, not production paths.

## P505 Cleanup Candidates

The final guard sweep found a small amount of high-confidence stale residue that should be handled in P505:

1. `novaic-agent-runtime/task_queue/constants.py` is an unused deprecated phase constants module. Repository-wide search only finds its own definitions.
2. `novaic-agent-runtime/task_queue/client.py:678` contains a stale “Deprecated Message polling removed” separator comment with no live code below it.
3. `novaic-agent-runtime/queue_service/session_repo.py:502-528` types `remaining_stack` as optional even though it is required immediately. This is not a runtime bypass, but tightening the signature would reduce misleading compatibility shape.

## Conclusion

No dangerous unclassified production dispatch bypass was found in P504. The remaining production direct side-effect hits are classified as required adapter/dispatcher/worker boundaries or strict FSM/outbox validation paths. P505 should remove the small stale residue candidates above before P506 performs final tests.
