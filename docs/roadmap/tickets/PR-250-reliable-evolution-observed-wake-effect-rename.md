# PR-250 Reliable Evolution FSM-03C Observed Wake Effect Rename

Status: `[x]`

## Goal

Rename the observe-only wake saga account from `create_wake_saga` to
`observe_create_wake_saga`. PR-249 moved the row out of retryable `pending`
status, but the effect type name still reads like an executable side effect.
That residue is dangerous in an AI-maintained codebase: future work could
mistake the diagnostic row for an existing durable worker contract.

## Phase Ledger

```text
Phase: FSM-03C observed wake effect rename
Subject: observe-only wake saga creation account naming
Old source of truth: effect_type=create_wake_saga used for diagnostic rows
New source of truth: effect_type=observe_create_wake_saga for diagnostic rows
Input events: input_received(...)
Decision function: unchanged
State transition: unchanged
Outbox effects: observe_create_wake_saga observed-only; live retryable effects unchanged
Observation events: dispatch_saga_started, session_restarted
Generation/idempotency key: shadow:effect:observe_create_wake_saga:{saga_id}
Shadow drift metric: no new `create_wake_saga` rows while direct SagaOrchestrator.create remains live
Cutover switch: none
Rollback path: revert PR-250
Legacy deletion condition: future wake saga outbox cutover may introduce a real retryable `create_wake_saga`
Tests: new rows use observe effect; v13 migration renames old rows; guard scan catches new diagnostic rows using old name
Docs/guards to update: ticket index, architecture implementation record
```

## Scope

- Runtime schema migration v13 renames old diagnostic rows.
- `SessionRepository` writes `observe_create_wake_saga` for start/restart
  observe rows.
- Tests guard against new diagnostic rows using the old effect type.

## Out Of Scope

- Do not implement durable wake saga creation in this ticket.
- Do not add outbox dispatcher support for wake saga creation.
- Do not change active session authority.

## Small Tickets

- [x] **FSM-03C-A Effect constant**: define/use a clearly observe-only effect
  type for wake saga diagnostic rows.
- [x] **FSM-03C-B Migration**: migrate existing `create_wake_saga` diagnostic
  rows to `observe_create_wake_saga`.
- [x] **FSM-03C-C Tests/guards**: prove new rows and migrated rows use the new
  name.
- [x] **FSM-03C-D Docs**: update architecture and ticket ledger.

## Explicit Dependency Boundary Review

- The effect type is an explicit value passed into the ledger.
- Migration is deterministic and only depends on DB contents.
- No decision logic reads hidden process state.

## Verification

- `python -m py_compile queue_service/db/schema.py queue_service/session_repo.py tests/test_pr250_observed_wake_effect_rename.py`
- `pytest tests/test_pr250_observed_wake_effect_rename.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr237_session_outbox_observe.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Closed.

- `SessionOutboxDispatcher.OBSERVE_CREATE_WAKE_SAGA` now names the diagnostic
  wake account explicitly.
- `SessionRepository` writes `observe_create_wake_saga` for start/restart
  observe rows, including the matching `shadow:effect:observe_create_wake_saga`
  idempotency key.
- Schema v13 renames existing `create_wake_saga` rows and normalizes any old
  pending diagnostic wake rows to `observed`; matching historical idempotency
  keys are renamed too.
- No outbox dispatcher support was added for wake creation; this ticket does
  not pretend the durable wake cutover exists.

Verification passed:

- `python -m py_compile queue_service/db/schema.py queue_service/session_outbox.py queue_service/session_repo.py tests/test_pr250_observed_wake_effect_rename.py tests/test_pr249_observed_wake_outbox_cleanup.py`
- `pytest tests/test_pr250_observed_wake_effect_rename.py tests/test_pr249_observed_wake_outbox_cleanup.py tests/test_pr237_session_outbox_observe.py -q`
- `pytest -q`
- `git diff --check`

## Rollback

Revert PR-250. Diagnostic rows can be re-renamed if needed; no live retryable
side effect depends on this effect type.
