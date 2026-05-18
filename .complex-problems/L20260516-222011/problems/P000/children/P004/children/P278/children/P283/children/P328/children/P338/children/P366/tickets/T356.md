# Ticket: Finalize Diagnostics Source Map

## Problem Definition

Before changing archive/session diagnostics behavior, map every live production path that constructs, forwards, persists, or archives `finalize_reason`, `remaining_stack`, `ended_at`, `finalize_generation`, and related generation/scope identity.

## Proposed Solution

Perform a read-only source map using `rg`, `nl`, and focused inspection. Classify each hit as mutating or non-mutating and identify whether it is guarded by explicit scope/generation identity.

## Acceptance Criteria

- Production files/functions are listed.
- Each mutating path has its identity fields named.
- Implementation targets for P367/P368 are clear.

## Verification Plan

- Search `task_queue`, `queue_service`, and relevant Cortex handler paths.
- Inspect representative code slices.
- Record findings without changing production code.
