# Demote/delete legacy source writes and verify write cutover

## Problem Definition

Phase 3 has event-wired root/wake/notification, context append/batch, tool steps, and skill lifecycle writes. The codebase still contains legacy filesystem writes for `context.jsonl`, `steps/*.json`, `steps/_index.jsonl`, `summary.md`, lifecycle `meta.json`, and older runtime structural helpers. These must be either physically removed from active source-of-truth paths or explicitly routed/labeled as transitional projections.

## Proposed Solution

Split the work because this phase mixes refactor, deletion, and audit:

- Rename/route remaining legacy context/step/lifecycle file writes as projection/debug writes where they are still needed before read cutover.
- Remove or fence runtime direct structural lifecycle helpers that bypass API event writers.
- Add tests proving every Phase 3 write path leaves a context event artifact as the authoritative record.
- Run static scans and full verification to classify remaining legacy files.

## Acceptance Criteria

- No active public/internal write endpoint can write context/step/skill lifecycle facts without a ContextEvent.
- Remaining `context.jsonl`, `steps/*.json`, `steps/_index.jsonl`, `summary.md`, and `meta.json` writes are named/classified as projections or support files.
- Legacy direct runtime helpers are deleted or proven unreachable from active paths.
- Static scans document all remaining legacy writes.
- Full Cortex tests pass.

## Verification Plan

- Split into focused child problems.
- Run event API tests and full Cortex suite for each child.
- Run `rg` scans for direct legacy write patterns.
- Treat any direct-only bypass as a follow-up, not a warning.

## Risks

- Removing runtime structural helpers may require updating old tests that were testing obsolete façade behavior.
- Some legacy projection writes are still needed until read cutover; do not delete required transitional readers in this phase unless tests prove read path has moved.

## Assumptions

- Event log is authoritative for write facts after Phase 3.
- Read cutover and projection deletion continue in later phases.
