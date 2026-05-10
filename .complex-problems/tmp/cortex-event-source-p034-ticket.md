# Verify context append and batch cutover

## Problem Definition

After P032/P033, audit context append/batch event cutover and classify remaining `context.jsonl` writes.

## Proposed Solution

- Run focused context append/batch event tests.
- Run full Cortex tests.
- Static scan endpoint and workspace code for event writer and legacy `context.jsonl` writes.
- Record remaining legacy writes as transitional and owned by Phase 4/5 if appropriate.

## Acceptance Criteria

- Focused append/batch event tests pass.
- Full Cortex suite passes.
- Static scan confirms append/batch endpoints call event writer helper.
- Remaining `context.jsonl` writes are documented and not hidden as complete cleanup.

## Verification Plan

- Run `pytest` focused and full.
- Run `rg` scans for `append_context`, `context.jsonl`, and `_append_context_message_event`.

## Risks

- Static scan might reveal another context write path; if so, create a follow-up.

## Assumptions

- Read-path cutover and legacy deletion remain later phases.
