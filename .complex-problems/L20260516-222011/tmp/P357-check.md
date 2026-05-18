# P357 success check

## Summary

Success. R334 solves P357's payload-only problem: terminal subagent status payload builders now carry current wake/session identity, reject missing/non-positive generation through the shared validator, preserve existing fields, and do not emit legacy last-scope payload fields.

## Evidence

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:43` and `:51` call `_subagent_terminal_status_identity(ctx)` for sleeping/completed payloads.
- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:71` delegates generation validation to `require_positive_session_generation(ctx, "wake_finalize")`.
- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py:75` emits `scope_id` and `session_generation` only for terminal status identity.
- `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py:16` and `:34` assert both payloads include `scope_id/session_generation` and exclude `last_scope_id/last_scope_archived_at`.
- `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py:53` asserts both builders reject missing and zero generation.
- Verification from R334: py_compile passed; focused pytest passed 18 tests; source guard found no last-scope or generation-defaulting residue in `wake_finalize.py`.

## Criteria Map

- Inspect status payload builders: met by R334 and source evidence in `wake_finalize.py`.
- Add explicit current finalize identity including `scope_id` and positive `session_generation`: met by `_subagent_terminal_status_identity(ctx)`.
- Preserve existing `agent_id/subagent_id` and completed `result` semantics: met by unchanged payload keys plus tests asserting exact payloads.
- Do not add/reintroduce `last_scope_id`: met by source guard and PR-43 test assertions.
- Add focused tests for identity and missing/non-positive generation: met by updated `test_pr43_last_scope_wiring.py`.

## Execution Map

- Code changed: `novaic-agent-runtime/task_queue/sagas/wake_finalize.py`.
- Tests changed: `novaic-agent-runtime/tests/test_pr43_last_scope_wiring.py`.
- Commands run:
  - `python3 -m py_compile task_queue/sagas/wake_finalize.py`
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py`
  - `rg -n 'last_scope_id|ctx\.get\("session_generation"\) or 0|session_generation.*or 0' task_queue/sagas/wake_finalize.py || true`

## Stress Test

- Plausible failure mode: a stale or malformed finalize context lacks generation or passes zero, producing a coarse terminal status payload anyway. The new builder test exercises both missing and zero generation for both sleeping and completed builders; the shared validator also rejects boolean and non-integer generation even though this focused test only asserts the core missing/zero cases.

## Residual Risk

- Handler-side pre-mutation rejection is not part of P357 and remains explicitly owned by P358.
- DAG ordering/session-ended gating is not part of P357 and remains explicitly owned by P359.
- Aggregate residue verification remains P360. These are non-blocking for the payload identity criterion.

## Result IDs

- R334
