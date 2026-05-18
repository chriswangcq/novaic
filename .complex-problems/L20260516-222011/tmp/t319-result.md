## Summary

T319 completed the attach expected-generation validation audit for P327. It closed the child audit tree P330-P333, fixed one real stale attach race, removed stale helper residue, and added missing-generation/stale-generation regression coverage across repository, outbox delivery, and runtime attach handling.

## Scope

Audited the attach expected-generation boundary under P327 by splitting it into four closed child problems:

- P330/R315/C336: repository payload generation audit.
- P331/R316/C337: session outbox delivery audit.
- P332/R317/C338: runtime attach handler generation enforcement audit.
- P333/R318/C339: aggregate stale/missing generation regression coverage audit.

## Changes made

- Fixed a real stale attach race in `novaic-agent-runtime/queue_service/session_repo.py`.
  - Attach outbox creation now re-reads the current active session inside the same global transaction that records the attach outbox.
  - If the active saga/scope changed between decision and effect recording, the request is buffered and projected as pending instead of publishing an attach effect for a stale wake.
- Removed stale generation helper residue:
  - Deleted `SessionLedgerRepository.active_generation(...)`.
  - Deleted `SessionRepository._active_session_generation_after_transaction(...)`.
- Added repository regression coverage:
  - `test_attach_request_buffers_if_active_session_changes_before_record`.
- Added outbox delivery regression coverage:
  - `test_attach_outbox_delivery_requires_expected_generation`.
- Added runtime handler regression coverage:
  - `test_session_attach_input_requires_expected_wake_scope`.

## Verification

Focused child checks passed:

```bash
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr248_attach_outbox_cutover.py \
  tests/test_pr252_session_state_ssot.py \
  tests/test_pr267_session_outbox_effect_boundary.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr255_legacy_compat_cleanup.py
# 26 passed

PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr238_generation_checked_attach.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr255_legacy_compat_cleanup.py
# 18 passed

PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr238_generation_checked_attach.py \
  tests/test_pr248_attach_outbox_cutover.py \
  tests/test_pr252_session_state_ssot.py \
  tests/test_pr267_session_outbox_effect_boundary.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr255_legacy_compat_cleanup.py
# 31 passed
```

Source guard passed:

```bash
! rg -n "active_generation\(|_active_session_generation_after_transaction|expected_session_generation\s*=\s*None" queue_service task_queue tests
# no matches
```

## Current conclusion

Within P327's attach expected-generation scope, stale attach and missing expected-generation paths are now guarded at the repository, outbox delivery, and runtime handler boundaries.

Remaining generation work is outside P327 and remains in sibling problems:

- P328: finalize/session-ended generation ownership audit.
- P329: missing or stale generation compatibility residue guard audit.
