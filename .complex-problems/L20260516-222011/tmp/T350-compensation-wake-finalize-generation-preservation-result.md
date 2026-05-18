# Compensation wake_finalize generation preservation result

## Summary

Implemented the P362 hardening. Saga compensation now emits `create_wake_finalize_saga` only when the failed wake/think/actions saga context carries a positive `session_generation`. Valid contexts preserve the generation into the compensation-created `wake_finalize`; malformed or missing generation produces no ambiguous mutating finalize effect.

## Done

- Added `_positive_session_generation_from_context` in `queue_service/saga_repo.py`.
- Updated `SagaOrchestrator._build_wake_finalize_compensation_effect` to:
  - require positive `session_generation`;
  - reject missing, zero, boolean, or malformed generation by returning no compensation finalize effect;
  - normalize and preserve valid generation in `finalize_context`;
  - stop copying `session_generation` opportunistically through the generic optional-key loop.
- Added focused tests in `tests/test_pr311_saga_compensation_outbox_cutover.py`:
  - valid compensation path still commits a durable `create_wake_finalize_saga` effect and preserves generation;
  - missing/invalid generation cases do not create the compensation finalize effect and drain no outbox work.

## Verification

- Compilation:

```text
python3 -m py_compile queue_service/saga_repo.py tests/test_pr311_saga_compensation_outbox_cutover.py
```

- Focused compensation test:

```text
PYTHONPATH=.:../novaic-common pytest -q tests/test_pr311_saga_compensation_outbox_cutover.py
9 passed in 0.15s
```

- Broader related test set:

```text
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr254_finalize_ownership.py \
  tests/test_pr311_saga_compensation_outbox_cutover.py \
  tests/test_pr245_suspected_dead_recovery.py
23 passed in 0.33s
```

- Residue/source inspection:
  - `queue_service/saga_repo.py` now centralizes compensation generation validation in `_positive_session_generation_from_context`.
  - `_build_wake_finalize_compensation_effect` no longer lets `session_generation` be omitted from emitted compensation finalize contexts.

## Known Gaps

- None for P362.
- P363 still owns the separate recovery archive path that publishes direct `cortex.scope_end`.

## Artifacts

- Modified production file: `novaic-agent-runtime/queue_service/saga_repo.py`
- Modified test file: `novaic-agent-runtime/tests/test_pr311_saga_compensation_outbox_cutover.py`
