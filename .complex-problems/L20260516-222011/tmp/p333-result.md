# Attach stale and missing generation regression coverage audit result

## Summary

Completed aggregate attach generation regression coverage audit. The focused suite now covers repository stale-scope buffering, outbox missing expected generation rejection, outbox/task payload preservation, runtime missing expected scope/generation rejection, runtime stale scope/generation rejection, and happy-path append/claim.

## Done

- Built coverage matrix:
  - Repository stale active change: `tests/test_pr248_attach_outbox_cutover.py::test_attach_request_buffers_if_active_session_changes_before_record`.
  - Repository happy path and no eager direct publish: `tests/test_pr248_attach_outbox_cutover.py`, `tests/test_pr252_session_state_ssot.py`.
  - Outbox effect shape and missing generation rejection: `tests/test_pr267_session_outbox_effect_boundary.py`.
  - Outbox delivery task payload generation: `tests/test_pr248_attach_outbox_cutover.py`.
  - Runtime missing generation, missing expected wake scope, stale wake scope, stale generation: `tests/test_pr238_generation_checked_attach.py`.
  - Runtime happy path append/claim: `tests/test_pr233_active_inbox_dispatch.py`.
  - Legacy source contract: `tests/test_pr255_legacy_compat_cleanup.py`.
- Ran focused attach generation suite.
- Ran source guard for removed repository generation fallback helpers.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr238_generation_checked_attach.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr252_session_state_ssot.py tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr255_legacy_compat_cleanup.py`
  - Result: `31 passed in 0.23s`.
- Source guard:
  - `! rg -n "active_generation\\(|_active_session_generation_after_transaction|expected_session_generation\\s*=\\s*None" queue_service task_queue tests`
  - Result: no matches.

## Known Gaps

- None for aggregate attach generation coverage.

## Artifacts

- `novaic-agent-runtime/tests/test_pr238_generation_checked_attach.py`
- `novaic-agent-runtime/tests/test_pr248_attach_outbox_cutover.py`
- `novaic-agent-runtime/tests/test_pr252_session_state_ssot.py`
- `novaic-agent-runtime/tests/test_pr267_session_outbox_effect_boundary.py`
- `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py`
- `novaic-agent-runtime/tests/test_pr255_legacy_compat_cleanup.py`
