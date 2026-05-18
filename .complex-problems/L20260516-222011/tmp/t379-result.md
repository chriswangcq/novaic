# Cross-repo generation residue guard matrix result

## Summary

The narrow cross-repo generation coercion guard is now clean, but a wider skeptical guard found additional live or semi-live generation/defaulting residues outside the originally targeted three lines. The guard matrix is therefore useful but not clean enough to close the parent as fully solved.

## Done

- Reran the original narrow generation coercion guard across runtime Queue/task handlers and Cortex core directories; it returned no matches.
- Reran active-session/current-active guard and classified the remaining hits.
- Ran a wider `int(...generation...)` / `or 0` guard to catch naming variants such as `finalize_generation`, audit adapters, and stack-depth fallbacks.
- Inspected representative live candidates in `session_fsm.py`, `session_repo.py`, `wake_finalize.py`, and `session_recovery.py`.

## Verification

- Original narrow guard:
  - Command: `rg -n "int\\((generation|session_generation|current_generation|expected_generation)\\)|generation\\s*=\\s*None|session_generation\\s*=\\s*None|expected_session_generation\\s*=\\s*None" novaic-agent-runtime/queue_service novaic-agent-runtime/task_queue novaic-cortex/novaic_cortex`
  - Result: no matches.
- Active/current-active guard:
  - Runtime attach path now uses `_require_positive_generation(current_active.get("generation"), "active session attach")`.
  - Remaining hits are explicit current-generation comparison in `runtime_handlers.py`, active-session recording authority in `session_observed_events.py` / `session_rebuild.py` / `session_ledger.py`, and current-active lookup code in `session_repo.py`.
- Wider skeptical guard:
  - Found additional raw generation/default patterns in session FSM/repo/ledger/audit and generic task/saga/lease FSM infrastructure.

## Known Gaps

- `novaic-agent-runtime/queue_service/session_fsm.py` still reduces finalize input with `finalize_generation = int(event.payload.get("finalize_generation") or 0)` and `current_generation = int(state.generation or 0)`. Current callers validate before entry, but the pure FSM reducer itself can still silently coerce malformed direct inputs.
- `novaic-agent-runtime/queue_service/session_repo.py` still adapts session state with `int((active_session or {}).get("generation") or 0)` and `int(state.get("generation") or 0)` in dispatch/state reconstruction helpers. These appear adapter-like, but the guard cannot classify them as mathematically clean yet.
- `novaic-agent-runtime/queue_service/session_ledger.py`, `queue_audit.py`, `session_audit.py`, and broader task/saga/lease FSM modules still contain raw generation/default adapters. Some are likely projection/audit or generic FSM counters, but they need a separate explicit-boundary audit rather than being waved away.
- Stack depth / round number fallbacks (`stack_depth_at_finalize`, `round_num`) are not session generation, but they are still control-plane defaults and should be consciously classified.

## Artifacts

- Clean narrow guard result: no output, exit code 1.
- Residual examples: `session_fsm.py:280-281`, `session_repo.py:756`, `session_repo.py:781`, `session_ledger.py:453/462`, `queue_audit.py:96/121`, `session_audit.py:37`.
