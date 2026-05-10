# Phase 3.3.1: Define context message event idempotency contract

## Problem

Context append/batch needs event idempotency without collapsing legitimately repeated identical messages. The request contract must be explicit before endpoint cutover.

## Success Criteria

- `ContextAppendRequest` and `ContextBatchRequest` support optional explicit event idempotency keys.
- Missing keys remain backward-compatible and append distinct events.
- Supplied keys are passed through to ContextEventStore.
- Tests prove same-content messages with different/no keys remain distinct, while retry with the same key dedupes.
