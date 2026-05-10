# P022 Success Check - Active Stack Helper Added

## Summary

P022 is solved. A small explicit active-stack projection helper exists, frame normalization is deterministic, malformed inputs fail loud, empty/nested stacks are covered, and idempotent event retry behavior is tested.

## Evidence

- R014 adds `novaic_cortex.active_stack_projection`.
- R014 adds tests covering empty stack, nested top-first stack, malformed frames, stable key filtering, explicit inputs, and idempotent event reuse.
- R014 verification reports 11 tests passing and bytecode compilation passing.

## Criteria Map

- Add helper with explicit inputs for root scope id/path, frames, generation, and reason: satisfied by `write_active_stack_projection`.
- Frames normalized top-first with stable keys for API and routing: satisfied by `normalize_active_stack_frames` and tests.
- Helper writes via `OperationalSqliteStore.set_active_stack` and can append durable event with idempotency key: satisfied by R014 implementation and tests.
- Unit tests cover empty, nested, and malformed frame inputs: satisfied by R014 test suite.

## Execution Map

- T017 was executed as a bounded helper/test implementation.
- Runtime API wiring was intentionally left for P023/P024.

## Stress Test

- The nested test includes `scope_path` fields needed by later active-path routing, not just display-only stack labels.
- The idempotent retry test verifies the scope event is not duplicated under a repeated idempotency key.

## Residual Risk

- Projection write and optional event append are separate store calls; P018/P025 should decide whether to add a compound transactional store operation before closing Phase 3B.
- No runtime path uses the helper yet.

## Result IDs

- R014
