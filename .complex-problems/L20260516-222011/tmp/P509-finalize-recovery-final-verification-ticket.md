# Finalize Recovery Final Verification

## Problem Definition

P509 must verify after P507/P508 that finalize/watchdog/recovery ownership is coherent and covered by tests.

## Proposed Solution

Run focused finalize, suspected-dead, recovery, saga compensation, session-ended, and session outbox tests. Save final guard evidence and produce a final verification artifact mapping P280 criteria to evidence.

## Acceptance Criteria

- Focused finalize/recovery tests pass.
- Final guard artifacts show no unclassified ownership bypass.
- P280 criteria can be checked from saved evidence.
- Any remaining ambiguity is turned into a follow-up instead of waived.

## Verification Plan

Run the focused pytest set from `novaic-agent-runtime`, save the log, save final guard counts/classification, and record a result.

## Risks

- Tests may not cover all static paths; static guard classification must accompany test results.

## Assumptions

- P507/P508 already mapped and evaluated ownership paths.
