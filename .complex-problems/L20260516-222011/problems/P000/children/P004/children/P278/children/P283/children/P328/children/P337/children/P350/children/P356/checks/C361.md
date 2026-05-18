# P356 aggregate finalize mutation guard check

## Summary

Success. R340 provides enough aggregate evidence to close P356. The result reran focused tests, compiled the touched modules, searched for retired payload fields and generation fallback residue, and inspected the concrete finalize mutation paths. The remaining risks are outside P350/P356 scope and are explicitly not claimed solved here.

## Evidence

- Compilation passed for the finalize/session/subagent/FSM contract modules listed in R340.
- Focused aggregate pytest suite passed with `109 passed in 0.58s`.
- Production residue search for `last_scope_id|last_scope_archived_at` under `task_queue` returned no matches.
- Generation fallback search found no zero-default compatibility pattern in the finalize mutation paths.
- Direct inspection evidence:
  - `task_queue/sagas/wake_finalize.py` propagates `scope_id` and positive generation into Cortex scope-end, Session finalization, and terminal SubAgent status payloads.
  - `task_queue/handlers/cortex_handlers.py` requires positive `session_generation` before archive.
  - `task_queue/handlers/session_handlers.py` validates positive `generation` and converts `finalize_rejected` into a task-gating failure.
  - `task_queue/handlers/subagent_handlers.py` validates terminal identity before `entity_update`.
  - `task_queue/saga.py` / `tests/test_runtime_tool_path_contract.py` verify terminal status tasks depend on `session_ended`.

## Criteria Map

- Run focused tests covering Cortex scope-end, subagent status mutation, wake finalize payloads, and session finalize ownership: satisfied by the 109-test aggregate suite listed in R340.
- Run source/residue searches for unguarded finalize mutation payloads and missing generation compatibility fallbacks: satisfied by `rg` searches in R340, including no production `last_scope_*` matches and no finalize zero-generation fallback.
- Map every P350 success criterion to concrete evidence: satisfied by R340's map for Cortex scope-end identity, SubAgent terminal identity, wake payload propagation, session finalize ownership, and DAG composition.
- Record any remaining gap as a follow-up rather than marking P350 solved: no P356-owned gap was found; sibling recovery/compensation work is explicitly marked out of scope rather than hidden.

## Execution Map

- P353 evidence is exercised through Cortex scope-end tests and direct inspection of `handle_cortex_scope_end`.
- P354 evidence is exercised through SubAgent terminal status handler tests and direct inspection of the identity guard before Business mutation.
- P355 evidence is exercised through wake-finalize payload builder tests and the session-finalize ownership tests.
- P356 aggregate work recomposed those slices with DAG gating tests and production residue searches.

## Stress Test

The check specifically looked for the plausible failure modes that previously caused stale finalize hazards:

- A stale finalize payload tries to carry `last_scope_id` / `last_scope_archived_at`: production search shows no live propagation, and tests assert legacy noise is ignored before Business updates.
- A finalize path silently defaults missing generation to `0`: builder and handler tests reject missing/zero generation, and residue searches found no finalize default branch.
- Session Coordinator rejects finalization but status still flips: `session_ended` now raises `BusinessError` on `finalize_rejected`, and terminal status tasks depend on `session_ended`.

## Residual Risk

- Non-blocking: P356 only covers P350 finalize mutation ownership. Broader recovery/compensation hazards remain separate work and were not claimed solved.
- Non-blocking: `task_queue/sagas/subagent_wake.py` still has optional generation propagation, but that is wake-start propagation rather than finalize mutation and is outside this problem's success criteria.

## Result IDs

- R340
