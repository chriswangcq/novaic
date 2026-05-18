# Cross-repo stale compatibility residue guard result

## Summary

Completed a cross-repo source guard pass over runtime and Cortex state/generation paths and tightened several live boundaries, but the guard still found residual implicit generation coercions. This ticket result is therefore partial and should drive follow-up cleanup rather than be treated as solved.

## Done

- Re-ran the cross-repo generation coercion guard over `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and `novaic-cortex/novaic_cortex`.
- Confirmed `novaic-cortex/novaic_cortex/active_stack_projection.py` now uses explicit non-negative generation validation helpers instead of raw `int(generation)`.
- Confirmed runtime generation validation helpers are present in the session repo, runtime handler, session outbox, FSM sqlite store, and observed event handler paths.
- Confirmed prior focused runtime and Cortex regression suites passed before this final cross-repo guard pass.

## Verification

- `git status --short` showed the broad working tree remains intentionally dirty with the current optimization ledger and multi-repo changes.
- `rg -n "int\\((generation|session_generation|current_generation|expected_generation)\\)|generation\\s*=\\s*None|session_generation\\s*=\\s*None|expected_session_generation\\s*=\\s*None" novaic-agent-runtime/queue_service novaic-agent-runtime/task_queue novaic-cortex/novaic_cortex` still returned two live matches in `novaic-cortex/novaic_cortex/operational_store.py`.
- `rg -n "current_active|get\\(\"generation\"\\)|_require_(positive|non_negative)_generation|int\\(generation\\)" novaic-agent-runtime/queue_service/session_repo.py novaic-cortex/novaic_cortex/operational_store.py novaic-cortex/novaic_cortex/active_stack_projection.py` still returned one live raw active-session generation read in `novaic-agent-runtime/queue_service/session_repo.py`.

## Known Gaps

- `novaic-cortex/novaic_cortex/operational_store.py` still has raw `int(generation)` in `upsert_scope_projection`.
- `novaic-cortex/novaic_cortex/operational_store.py` still has raw `int(generation)` in `set_active_stack`.
- `novaic-agent-runtime/queue_service/session_repo.py` still has `session_generation = int(current_active.get("generation") or 0)` in the attach path.
- Follow-up work should patch these residual coercions, add focused validation tests, rerun focused suites, and rerun the guards until only classified-safe matches remain.

## Artifacts

- Source guard evidence: `novaic-cortex/novaic_cortex/operational_store.py:385`, `novaic-cortex/novaic_cortex/operational_store.py:451`, `novaic-agent-runtime/queue_service/session_repo.py:891`.
- Prior passing runtime focused suite: 81 tests passed across finalize, recovery, outbox, FSM store, observed events, and generation attach tests.
- Prior passing Cortex focused suite: 82 tests passed across context event lifecycle, skill lifecycle, write authority, projection, model, and scope summary contract tests.
