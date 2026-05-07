# PR-300 — Session Outbox Canonical Payload Contract

Status: Closed

## Goal

Remove row/payload double-read compatibility from session outbox publishing and
observation. The outbox payload builder defines the canonical effect contract.

## Scope

- Make `create_wake_saga` publication read identity and generation from payload
  only.
- Make wake-created observation read identity and generation from payload only.
- Keep row fields as ledger indexes, not fallback business inputs.
- Add tests that missing canonical payload fields fail clearly.

## Dependencies

- PR-267 session outbox effect boundary.
- PR-286 durable wake outbox cutover.

## Risks

- Manually inserted malformed outbox rows will fail instead of being recovered
  from row columns. This is desired because the durable payload is the contract.

## Acceptance Criteria

- No wake-create publish or observe path uses `payload.get(...)` as a fallback
  to row fields or row fields as a fallback to payload fields.
- Missing payload identity/generation/scope fails with explicit errors.
- Runtime tests pass.

## Verification

- Targeted outbox/observed-event tests.
- Grep for double-read fallback patterns.
- Full runtime suite.

## Closure Notes

- `SessionOutboxDispatcher._publish_create_wake_saga()` now reads required
  identity, scope, saga type, and saga idempotency fields from canonical payload
  only.
- `SessionObservedEventHandler.apply_wake_created()` now reads identity and
  generation from payload only.
- Added malformed-payload tests proving row fields no longer rescue invalid
  payloads.
- Removed the duplicated `wake_finalize_saga_id` payload alias and recovery
  fallback.
- Verified by targeted outbox/observed-event tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 364 passed.
