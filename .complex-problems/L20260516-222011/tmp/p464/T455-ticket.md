# Ticket: Remove observed wake outbox production residue

## Problem Definition

Production `SessionOutboxDispatcher` still defines the obsolete `OBSERVE_CREATE_WAKE_SAGA` effect constant, even though observed wake-created is no longer a supported durable outbox effect and is handled inside `create_wake_saga` delivery.

## Proposed Solution

- Remove `OBSERVE_CREATE_WAKE_SAGA` from `SessionOutboxDispatcher`.
- Update negative tests to use a test-local obsolete effect string instead of importing the production constant.
- Run focused tests for observed wake cleanup and wake creation outbox cutover.
- Save before/after guards and test logs.

## Acceptance Criteria

- No production source hit for `OBSERVE_CREATE_WAKE_SAGA` or `observe_create_wake_saga`.
- Test hits, if any, are clearly test-local negative guards.
- Focused tests pass.

## Verification Plan

- `rg "OBSERVE_CREATE_WAKE_SAGA|observe_create_wake_saga" novaic-agent-runtime/queue_service novaic-agent-runtime/tests`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr251_wake_creation_outbox_cutover.py`
