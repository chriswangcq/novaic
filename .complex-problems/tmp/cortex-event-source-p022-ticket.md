# Implement projection replay watermark

## Problem Definition

The Phase 2 projector needs a stronger replay-integrity contract. It currently tracks `applied_seq`, but it should also validate a single stream identity and contiguous ordered event sequence, then expose the stream watermark in `ContextProjectionSnapshot`.

## Proposed Solution

- Extend `ContextProjectionSnapshot` with explicit `stream_id`, `first_seq`, and existing `applied_seq` watermark fields.
- Update `project_context_events` to reject:
  - mixed `stream_id`;
  - mixed `root_scope_id`;
  - duplicate sequence values;
  - gaps in sequence;
  - out-of-order events.
- Keep empty projection deterministic.
- Add focused tests for valid watermark and invalid replay order cases.
- Re-run focused ContextEvent tests.

## Acceptance Criteria

- Snapshot exposes `stream_id`, `root_scope_id`, `first_seq`, and `applied_seq`.
- Ordered contiguous replay succeeds.
- Empty replay still returns an empty deterministic snapshot.
- Mixed stream id, duplicate seq, seq gaps, and out-of-order seq fail with `ContextEventProjectionError`.
- Focused ContextEvent tests pass.

## Verification Plan

- Run focused projection/model/store tests with sibling dependency `PYTHONPATH`.
- Static-review the projector to ensure this stays pure.

## Risks

- Existing tests may assert the exact snapshot dict shape; update tests to include the new watermark fields deliberately.

## Assumptions

- Projection should validate events in the order provided, not sort them, because sorting would hide append-log corruption.
