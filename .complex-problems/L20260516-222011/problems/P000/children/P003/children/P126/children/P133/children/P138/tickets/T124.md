# Audit ContextEvent append-only store

## Problem Definition

`ContextEventStore` is the persisted append-only source for context events. We need a precise source-backed map and test evidence for its path, read behavior, append invariants, idempotency, and explicit dependencies.

## Proposed Solution

Inspect `novaic-cortex/novaic_cortex/context_event_store.py` and `novaic-cortex/tests/test_context_event_store.py`. Record a concise map of:

- Event log path ownership.
- Missing/invalid log read behavior.
- Append sequence assignment.
- Explicit clock/id provider dependency.
- Idempotency key duplicate/conflict behavior.
- Root initialization retry behavior.

Run the store tests. If the store has an active hidden input, fallback, or stale compatibility path, fix it if local; otherwise split a follow-up.

## Acceptance Criteria

- Result includes source pointers for each store invariant.
- Result includes test command and pass/fail evidence.
- Any issue found is either fixed or split into a specific follow-up.

## Verification Plan

- `PYTHONPATH=novaic-cortex pytest -q novaic-cortex/tests/test_context_event_store.py`
- If needed, run with adjacent package paths in `PYTHONPATH`.

## Risks

- This ticket should not modify projection or read model behavior.

## Assumptions

- Store-level append requires injected clock/id providers by design.
- Missing event logs read as empty; empty stream handling belongs to the read model.
