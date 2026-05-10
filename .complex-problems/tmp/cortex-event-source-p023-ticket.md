# Map write paths and add ContextEvent writer boundary

## Problem Definition

Phase 3 needs a concrete write-path map and a reusable event writer boundary before endpoint cutover. The boundary must inject clock/id dependencies explicitly and prevent endpoint code from hand-assembling append semantics.

## Proposed Solution

- Create a write-path map document under `docs/cortex/` naming every current source write and its event target.
- Add a small `ContextEventWriter` module around `ContextEventStore`.
- Require explicit clock/id providers for append operations.
- Add helper methods for currently known write facts:
  - root initialized;
  - wake started/archived;
  - context message appended;
  - input notification attached;
  - assistant tool call recorded;
  - tool step recorded;
  - skill scope opened/closed.
- Add focused unit tests using a fake workspace.

## Acceptance Criteria

- The write-path map exists and lists the legacy artifact, current code owner, target event type, and follow-up phase child for each path.
- `ContextEventWriter` exists and keeps time/id dependencies explicit.
- Writer tests verify event append payloads and idempotency keys for representative event types.
- No live endpoint behavior is cut over in this ticket.

## Verification Plan

- Run focused ContextEvent model/store/writer tests.
- Run full `novaic-cortex` tests.
- Static scan to confirm no endpoint imports the writer yet.

## Risks

- The writer could become a hidden dependency sink if it creates ids/time internally; tests must enforce explicit providers.

## Assumptions

- Later child tickets perform endpoint cutover; this ticket establishes substrate and map only.
