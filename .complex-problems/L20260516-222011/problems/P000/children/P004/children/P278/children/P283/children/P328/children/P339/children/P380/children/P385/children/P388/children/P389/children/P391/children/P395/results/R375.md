# Session ledger generation helper classification result

## Summary

Patched session ledger generation helpers so current-state generation is explicitly validated instead of defaulted through raw `int(current.get("generation") or 0)`.

## Done

- Added `_require_non_negative_generation` to `queue_service/session_ledger.py`.
- Updated `session_generation` and `next_generation` to validate current state generation with the helper.
- Added a focused malformed-state test using a monkeypatched `get_state` to exercise the adapter boundary directly.
- Updated a stale test assertion from synchronous `task_id` to durable attach `outbox_id`, matching the current outbox architecture.

## Verification

- `python3 -m py_compile queue_service/session_ledger.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr235_session_ledger.py tests/test_pr283_session_state_taxonomy.py tests/test_pr254_finalize_ownership.py` passed: 24 tests.
- Targeted source guard for the old session ledger generation defaults returned no matches.

## Known Gaps

- Audit/generic FSM generation classifications remain for P392.
- Round/stack-depth defaults remain for P393.

## Artifacts

- Patched files: `novaic-agent-runtime/queue_service/session_ledger.py`, `novaic-agent-runtime/tests/test_pr235_session_ledger.py`.
