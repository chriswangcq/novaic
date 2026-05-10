# Add consolidated write-path event authority test

## Problem Definition

Existing endpoint tests verify individual event rows, but there is no single authority test that exercises the Phase 3 write-path family end-to-end and proves `ContextEventStore` is the durable evidence for lifecycle, notifications, context messages, tool steps, and skill lifecycle.

## Proposed Solution

- Add a focused test file that creates one root/wake session and exercises:
  - root initialization,
  - wake start,
  - input notification attach,
  - context append,
  - context batch assistant/tool-call recording,
  - tool step recording,
  - skill begin,
  - skill end,
  - wake archive.
- Read `ContextEventStore.read_events(root_scope_path)` once at the end.
- Assert event type order and key payload fields.
- Avoid reading `context.jsonl`, `steps/*.json`, or `summary.md` as authority evidence in this test.
- Run the focused authority test and full Cortex suite.

## Acceptance Criteria

- A consolidated write-authority test exists.
- The test asserts expected event types and key payload fields from `context_events/events.jsonl` via `ContextEventStore`.
- The test does not use legacy materialized files as its evidence.
- Full Cortex suite passes.

## Verification Plan

- Run the new authority test.
- Run full Cortex suite.
- Static inspect the new test for no `read_context`, `read_step`, `summary.md`, or direct materialized file reads.

## Risks

- Event ordering must match real append sequence and should not become brittle around unrelated event fields.

## Assumptions

- Projection writes may still occur in endpoints, but this test’s evidence source must be the event store.
