# Phase Cortex State Authority Implementation

## Problem Definition

The remediation design is broad. Implementing all of it in one pass would create a high-risk half-cutover. We need a phased construction plan where each phase is independently checkable and either removes an old authority path or creates a clearly bounded substrate.

## Proposed Solution

Split implementation into child problems:

1. Phase 0: Construction plan and dependency boundary map.
2. Phase 1: Cortex operational SQLite store substrate.
3. Phase 2: Scope lifecycle/transition events move from local NDJSON to SQLite.
4. Phase 3: Active stack/status reads switch to SQLite projection.
5. Phase 4: Payload manifest contract for Blob raw bytes.
6. Phase 5: Cleanup old local state, stale docs, and fallback residues.

Do not include live LogicalFS rewrite in the first implementation chain; it is a separate larger service program and should only start after Cortex operational authority is stable.

## Acceptance Criteria

- Root ticket is split.
- Every child phase has a concrete implementation or clear blocker.
- Phase 1 must be implemented with tests before proceeding.
- Later phases may be split if implementation risk is too large.
- Final checks include targeted tests and diff review.

## Verification Plan

Use ledger checks per child phase, run relevant pytest targets, boundary grep, and diff review. If a phase cannot be completed, record a partial result and create follow-up through check_success.

## Risks

- One huge cutover could leave dual-authority paths.
- Introducing SQLite without connecting it would add dead code.
- Removing old paths before tests could break runtime.

## Assumptions

- Cortex can add a SQLite dependency through stdlib `sqlite3` without introducing a new package.
- SQLite state path can be required at service startup.
- Tests can use tmp SQLite files.

