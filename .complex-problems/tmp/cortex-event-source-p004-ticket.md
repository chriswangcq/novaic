# Cut write paths over to ContextEvents

## Problem Definition

Cortex still writes the current source-of-truth context files directly. Phase 3 must make ContextEvents the authoritative write target for wake/root initialization, context message append/batch, notification attachment, tool step recording, skill begin, and skill end. Legacy workspace files may only remain as derived projections or debug artifacts during the cutover.

## Proposed Solution

Split the write-path cutover into explicit implementation tickets:

- Map all current write endpoints and their existing persisted artifacts.
- Introduce an event writer adapter at the Cortex boundary with explicit clock/id dependencies.
- Cut root/wake initialization and notification attachment to append events.
- Cut context append/batch to append events.
- Cut tool step recording to append events.
- Cut skill begin/end to append events, including report/fold semantics.
- Make legacy direct writes projection-only or delete their active source-of-truth use.
- Add endpoint/workspace tests that verify emitted `context_events/events.jsonl`.

## Acceptance Criteria

- All listed write paths append ContextEvents as authoritative facts.
- Any remaining legacy files are explicitly marked projection/debug and not used as source-of-truth writes.
- Tests verify the event stream content for every write path.
- Explicit dependency boundaries are preserved: write-path code receives clock/id providers instead of generating them invisibly in pure modules.
- No compatibility branch keeps old direct-write source-of-truth behavior alive.

## Verification Plan

- Use `rg` to map direct writes to `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `summary.md`, and `meta.json`.
- Run focused Cortex tests for context stack/API/runtime.
- Add new tests around event log contents.
- Run full `novaic-cortex` suite.

## Risks

- This touches multiple write endpoints and should not be treated as one small patch.
- Existing tests may encode legacy file writes as behavior; those tests need to be updated only when the old behavior is truly no longer source-of-truth.

## Assumptions

- User explicitly allows deleting old data and doing a full cutover, so no legacy migration/compat reader is required.
