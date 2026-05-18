# Attach repository payload generation audit result

## Summary

Found and fixed a repository-side stale attach race. Previously, `SessionRepository` decided attach from one active state, then in a later transaction recomputed only the generation; if the active scope changed in between, it could enqueue an attach outbox payload with the old scope and the current generation. Runtime would likely reject it by scope, but the repository boundary still produced a misleading outbox row. The fix revalidates current active saga/scope in the same transaction that records the attach outbox; mismatch now buffers the input instead of publishing attach.

## Done

- Mapped attach request creation in `session_repo.py::dispatch(...)`.
- Mapped attach outbox generation in `_record_attach_request_after_transaction(...)`.
- Removed the stale-scope-prone `SessionLedgerRepository.active_generation(...)` helper and `SessionRepository._active_session_generation_after_transaction(...)`.
- Changed repository attach recording to:
  - re-read current session state under a global transaction,
  - require current active saga/scope to match the original attach request,
  - use the current active row generation only when saga/scope match,
  - buffer the input and record pending projection when the active session changed before attach recording.
- Added regression coverage in `tests/test_pr248_attach_outbox_cutover.py`.

## Verification

- `python3 -m py_compile queue_service/session_repo.py queue_service/session_ledger.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr248_attach_outbox_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr255_legacy_compat_cleanup.py`
- Result: `25 passed in 0.19s`.
- Source guard: `rg "active_generation\\(|_active_session_generation_after_transaction|active_session_changed_before_attach|expected_session_generation" queue_service/session_repo.py queue_service/session_ledger.py tests/test_pr248_attach_outbox_cutover.py`
  - No `active_generation(...)` or `_active_session_generation_after_transaction` remains in repository/ledger code.

## Known Gaps

- P331 still needs to verify session outbox worker delivery preserves/requires `expected_session_generation`.
- P332 still needs to verify runtime handler generation enforcement.
- P333 still needs to run the end-to-end stale/missing attach regression audit.

## Artifacts

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/tests/test_pr248_attach_outbox_cutover.py`
