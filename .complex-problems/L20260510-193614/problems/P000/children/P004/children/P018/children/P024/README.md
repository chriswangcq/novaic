# Phase 3B3 Finalize Remaining Stack Event

## Problem

Root finalize/scope archive currently writes a wake archived context event with `remaining_stack=[]`. Phase 3 needs explicit durable finalize semantics that records reason and actual remaining operational stack before clearing/updating projection.

## Success Criteria

- Finalize/root archive records explicit reason and remaining stack into operational SQLite event/projection state.
- Active-stack projection is cleared or updated deterministically after finalize.
- Idempotent finalize/retry behavior does not duplicate conflicting stack events.
- Tests cover root archive with empty and non-empty child stack cases.
