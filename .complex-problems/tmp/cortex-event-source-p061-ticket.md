# Phase 5 final verification and diff review

## Problem Definition

Verify Phase 5 against the no-compat/full-cutover goal. This ticket must not rubber-stamp success if scans still show legacy code that should be physically deleted.

## Proposed Solution

- Run static scans for active DFS fallback, legacy DFS physical residue, materialized artifact reads, and double-read/double-write ambiguity.
- Run full Cortex tests.
- Review git diff for permanent ambiguity.
- If residual code violates the final desired shape, record a not-success check and create a concrete follow-up ticket instead of closing Phase 5.

## Acceptance Criteria

- Verification evidence is recorded.
- Any remaining legacy or ambiguity is either proven debug/projection-only or converted into a follow-up ticket.
- Full tests pass before any success claim.

## Verification Plan

- Static scans.
- Full Cortex test suite.
- `git diff --stat` and targeted diff review.

## Risks

- Physical DFS engine deletion may be required before Phase 5 can honestly close.

## Assumptions

- The correct outcome can be not-success if final verification finds a real gap.
