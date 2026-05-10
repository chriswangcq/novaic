# Phase 5 legacy cleanup, reset behavior, and full verification

## Problem Definition

The active read/write path is now event-backed, but the repo still contains legacy DFS renderer code, materialized projection artifact helpers, and old-data compatibility surfaces. The user explicitly allows deleting old data and wants a full cutover, so Phase 5 must remove ambiguity rather than preserve fallback behavior.

## Proposed Solution

Split Phase 5 into focused cleanup tickets:

- Inventory and decide physical deletion scope for legacy DFS engine/tests.
- Implement explicit old-data reset/no-compat behavior for missing event logs or legacy-only roots.
- Remove or rename lingering source-of-truth language around `context.jsonl`, `steps`, and `summary.md`.
- Verify there is no permanent double-read ambiguity and only projection/debug endpoints read materialized artifacts.
- Run comprehensive tests and diff review.

Do not attempt this as one giant one-go ticket; deletion scope and reset behavior can create follow-up issues and need narrower tickets.

## Acceptance Criteria

- Child tickets exist for deletion inventory, reset/no-compat behavior, residue cleanup, and final verification.
- Each child has explicit acceptance criteria and verification.
- Parent Phase 5 only closes after all child checks pass.

## Verification Plan

- Use ledger child tickets and close them one by one.
- Run static scans after cleanup.
- Run full Cortex tests and relevant broader tests if touched code crosses package boundaries.

## Risks

- Physical DFS deletion may require migrating/removing many legacy tests.
- Reset/no-compat behavior can break old local state; that is acceptable per user request but must be explicit.
- Materialized projection files may still be needed for debug/display endpoints; those must be named as projection artifacts, not sources of truth.

## Assumptions

- Old data compatibility is not required.
- Active behavior should prefer fail/reset over silent legacy fallback.
