# Subagent finalize status identity guard parent result

## Summary

Closed the P354 split ticket by completing and checking all four children: payload identity, handler validation, wake-finalize gating order, and aggregate verification.

## Done

- P357/R334/C355: terminal subagent status payload builders now emit `scope_id` and positive `session_generation`, reject missing/non-positive generation, preserve existing fields, and do not emit `last_scope_id`.
- P358/R335/C356: terminal subagent status handlers require `scope_id` and positive `session_generation` before Business mutation; malformed payloads do not call `entity_update()`.
- P359/R336/C357: wake-finalize now runs `session_ended` before terminal subagent status mutation; both status tasks explicitly depend on `session_ended`; `finalize_rejected` now fails the task gate with `BusinessError`.
- P360/R337/C358: aggregate verification passed 109 tests and source guards, confirming no live last-scope or generation-defaulting residue in the touched runtime files.

## Verification

- Child success checks:
  - P357 -> C355 success.
  - P358 -> C356 success.
  - P359 -> C357 success.
  - P360 -> C358 success.
- Strongest aggregate run from P360: 109 tests passed across payload, handler, finalize ownership, scope-end, runtime contract, and DAG integration suites.
- Source guards found no live `last_scope_id`, `last_scope_archived_at`, or session-generation defaulting in the touched runtime files.

## Known Gaps

- Recovery/compensation finalize identity remains owned by P351 and is outside P354's terminal subagent status path.

## Artifacts

- Child results: R334, R335, R336, R337.
- Child checks: C355, C356, C357, C358.
- Primary runtime files: `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`, `novaic-agent-runtime/task_queue/handlers/subagent_handlers.py`, `novaic-agent-runtime/task_queue/handlers/session_handlers.py`, `novaic-agent-runtime/task_queue/saga.py`.
