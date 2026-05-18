# Normalize remaining runtime generation default boundaries result

## Summary

The split children closed the scoped session-generation default work across runtime state adapters, finalize FSM boundaries, audit/projection readers, Cortex operational store writes, and selected round/stack-depth archive boundaries. The narrow live-session generation guard is now clean across `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and `novaic-cortex/novaic_cortex`, and the focused runtime/Cortex suites pass.

This result is deliberately not claiming the broader residue surface is solved. The widened guard still finds classified counters/defaults and at least two suspicious live-adjacent hits that should be judged by the parent check.

## Done

- Closed child result R373 for `P390`: session finalize generation now validates explicit non-bool/non-negative generation through `session_fsm.py`, with malformed finalize and state generation tests.
- Closed child result R376 for `P391`: session repository and session ledger generation adapters now require explicit generation boundaries instead of inline raw `int(... or 0)` coercions.
- Closed child result R379 for `P392`: audit and generic FSM generation surfaces were classified and bounded; audit replay now rejects malformed generation inputs where relevant.
- Closed child result R380 for `P393`: selected round and stack-depth archive defaults in finalize/recovery paths now use named helpers and tests.
- Added/updated focused tests around session repo state taxonomy, session ledger reconstruction, finalize ownership, recovery boundary, audit tooling, queue control-plane replay, Cortex operational store generation validation, and active-stack/operational store boundaries.

## Verification

- `rg -n "int\\((generation|session_generation|current_generation|expected_generation|finalize_generation)\\)|generation\\s*=\\s*None|session_generation\\s*=\\s*None|expected_session_generation\\s*=\\s*None|finalize_generation\\s*=\\s*int" novaic-agent-runtime/queue_service novaic-agent-runtime/task_queue novaic-cortex/novaic_cortex` returned no matches.
- Focused runtime verification passed: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr235_session_ledger.py tests/test_pr283_session_state_taxonomy.py tests/test_pr264_session_finalize_fsm_boundary.py tests/test_pr295_session_audit_tooling.py tests/test_pr314_queue_control_plane_audit_replay.py tests/test_pr254_finalize_ownership.py tests/test_pr266_session_recovery_boundary.py` -> `43 passed in 0.32s`.
- Earlier focused runtime suite covering finalize/recovery/outbox/FSM paths passed: `81 passed`.
- Focused Cortex suite covering operational store, active stack projection, and context event lifecycle passed: `104 passed`.

## Known Gaps

- Widened guard still reports broader non-session defaults/counters, many likely classified as metrics, retry counters, or round numbers rather than session-generation authority.
- Two hits still look too close to live session-generation semantics to call solved without another skeptical pass:
  - `novaic-agent-runtime/queue_service/session_fsm.py` still has `event_generation=int(decision.payload.get("event_generation") or 0)`.
  - `novaic-agent-runtime/task_queue/sagas/subagent_wake.py` still coerces `session_generation` from saga context with `int(ctx["session_generation"])`.
- `session_outbox.py`, `task_queue/handlers/cortex_handlers.py`, and `novaic-cortex/novaic_cortex/api.py` still contain round/counter default conversions that may be acceptable only if explicitly classified and tested.

## Artifacts

- Child results: R373, R376, R379, R380.
- Changed implementation files include runtime session repo/FSM/ledger/audit/recovery/finalize boundaries and Cortex operational store/active stack generation boundaries.
- Changed tests include `test_pr235_session_ledger.py`, `test_pr283_session_state_taxonomy.py`, `test_pr264_session_finalize_fsm_boundary.py`, `test_pr295_session_audit_tooling.py`, `test_pr314_queue_control_plane_audit_replay.py`, `test_pr254_finalize_ownership.py`, `test_pr266_session_recovery_boundary.py`, and `novaic-cortex/tests/test_operational_store.py`.
