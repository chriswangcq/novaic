# Emit notification attachment events

## Problem Definition

`/v1/scope/append_input` registers input message ids in scope metadata but does not yet append `InputNotificationAttached` events. The event log must become the authoritative notification attachment fact.

## Proposed Solution

- Wire `ContextEventWriter.input_notification_attached` into `scope_append_input`.
- Resolve target root scope identity from the supplied or resolved `scope_path`.
- Append one event per requested message id using stable idempotency keys.
- Preserve existing metadata merge behavior for now as transitional debug/projection state.
- Add focused tests that verify event log contents and retry deduplication.

## Acceptance Criteria

- `scope_append_input` emits `InputNotificationAttached` events.
- Event payload includes notification id, source kind, and target scope id.
- Reposting the same message ids does not duplicate events.
- Existing PR-67 behavior remains green.
- Full Cortex tests pass.

## Verification Plan

- Add focused API notification event tests.
- Run focused lifecycle/PR-67 tests.
- Run full `novaic-cortex` suite.

## Risks

- Source kind is not currently part of `ScopeAppendInputRequest`; use `im_message` as the current explicit default unless a later caller provides richer source metadata.

## Assumptions

- Existing runtime callers use message ids for IM notifications.
