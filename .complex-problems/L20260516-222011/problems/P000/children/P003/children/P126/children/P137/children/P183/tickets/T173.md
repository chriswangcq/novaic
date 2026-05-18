# Audit stale active-stack injection and cleanup candidates

## Problem Definition

Active stack injection has been moved into explicit common assembly and operational-store projection. P183 must search for stale duplicate injection, old file-walk collectors, obsolete tests, and misleading compatibility code that could later reintroduce stack/message ordering bugs.

## Proposed Solution

Inventory active-stack-related strings, adapters, source guards, and tests across runtime, common, and Cortex. Classify each suspicious path as active, stale, or test-only. Remove stale code if found and safe; otherwise record why retained paths are active. Run focused tests after any changes or after confirming no stale cleanup is needed.

## Acceptance Criteria

- Production and tests are searched for active-stack injection/collector leftovers.
- Suspicious paths are classified as active, stale, or test-only.
- Stale code is removed if safe.
- Focused tests pass after the audit/change.

## Verification Plan

Run `rg` across `novaic-agent-runtime`, `novaic-common`, and `novaic-cortex` for active-stack literals, old helper names, stack adapters, and file-walk patterns. Run common/runtime/Cortex tests that guard local stack adapters and source reads.

## Risks

- Some test-only literals intentionally protect against regressions; deleting them would weaken guardrails.

## Assumptions

- P180-P182 already proved the current source, ordering, and display-media behavior. P183 is only stale-path cleanup.
