# Session recovery missing identity handling result

## Summary

Implemented P363 recovery archive identity hardening. Suspected-dead recovery markers now carry positive session generation from the session event, recovery archive effects require that generation, and the session outbox publisher rejects malformed archive payloads before publishing a direct `cortex.scope_end` task.

## Done

- Updated `queue_service/session_recovery.py`:
  - Added positive generation normalization for recovery markers.
  - `recovery_marker_from_suspected_dead_event` preserves positive event generation as `session_generation`.
  - `build_recovery_archive_effect` returns no effect when `failed_scope_id` or positive `session_generation` is missing.
  - Recovery archive payload now includes `session_generation`.
- Updated `queue_service/session_outbox.py`:
  - `_publish_recovery_archive` now requires positive `session_generation`.
  - The published `TaskTopics.CORTEX_SCOPE_END` payload includes the validated generation.
- Updated tests:
  - `tests/test_pr266_session_recovery_boundary.py` verifies marker/effect generation preservation and missing/invalid generation rejection.
  - `tests/test_pr247_recovery_outbox_cutover.py` verifies published recovery archive tasks include generation and malformed archive payloads are rejected before queue publish.

## Verification

- Compilation:

```text
python3 -m py_compile queue_service/session_recovery.py queue_service/session_outbox.py \
  tests/test_pr266_session_recovery_boundary.py tests/test_pr247_recovery_outbox_cutover.py
```

- Focused recovery tests:

```text
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr266_session_recovery_boundary.py \
  tests/test_pr247_recovery_outbox_cutover.py \
  tests/test_pr245_suspected_dead_recovery.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr254_finalize_ownership.py
35 passed in 0.62s
```

- Broader recovery/compensation/finalize set:

```text
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr311_saga_compensation_outbox_cutover.py \
  tests/test_pr254_finalize_ownership.py \
  tests/test_pr266_session_recovery_boundary.py \
  tests/test_pr247_recovery_outbox_cutover.py \
  tests/test_pr245_suspected_dead_recovery.py \
  tests/test_pr233_active_inbox_dispatch.py
39 passed in 0.36s
```

- Source search confirms recovery archive code now references `session_generation` in marker creation, effect creation, publisher validation, and published `cortex.scope_end` payload.

## Known Gaps

- None for P363.
- P364 remains as aggregate verification after P361/P362/P363.

## Artifacts

- Modified production files:
  - `novaic-agent-runtime/queue_service/session_recovery.py`
  - `novaic-agent-runtime/queue_service/session_outbox.py`
- Modified test files:
  - `novaic-agent-runtime/tests/test_pr266_session_recovery_boundary.py`
  - `novaic-agent-runtime/tests/test_pr247_recovery_outbox_cutover.py`
