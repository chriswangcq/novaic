# Add explicit context message idempotency contract

## Problem Definition

Context message events need optional idempotency keys supplied by callers. Without explicit keys, repeated identical messages must stay distinct; with keys, retries must dedupe.

## Proposed Solution

- Add optional `event_idempotency_key` to `ContextAppendRequest`.
- Add optional `event_idempotency_keys` to `ContextBatchRequest`.
- Validate batch key length when keys are supplied.
- Add tests around request model behavior and event writer/store semantics.

## Acceptance Criteria

- Append request accepts an optional key.
- Batch request accepts optional per-message keys.
- Batch rejects mismatched key count.
- Writer/store tests prove same content without keys creates distinct events.
- Writer/store tests prove same explicit key dedupes retry.

## Verification Plan

- Add focused tests.
- Run focused ContextEvent tests.
- Run full Cortex suite.

## Risks

- Pydantic model validation must remain backward-compatible for existing callers.

## Assumptions

- Endpoint wiring that uses the keys is owned by P033.
