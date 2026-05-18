# Remove observed wake outbox residue

## Problem

Production source still exposes `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA` even though observed wake-created is no longer a supported durable outbox effect.

## Success Criteria

- Remove `OBSERVE_CREATE_WAKE_SAGA` from production `SessionOutboxDispatcher`.
- Update negative guard tests to use the literal obsolete effect string or another test-local marker instead of importing a production constant.
- `rg "OBSERVE_CREATE_WAKE_SAGA|observe_create_wake_saga"` has no production source hits and only intentional test/documentation guard hits.
- Focused tests pass:
  - `tests/test_pr249_observed_wake_outbox_cleanup.py`
  - `tests/test_pr250_observed_wake_effect_rename.py`
  - `tests/test_pr251_wake_creation_outbox_cutover.py`

## Notes

This should be a small cleanup, but it must not weaken the tests that prove observed-wake outbox rows are no longer emitted or supported.
