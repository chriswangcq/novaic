# Ticket: Runtime Finalize Enforcement Aggregate Verification

## Objective

Verify the full P337 runtime finalize enforcement set: stale or missing finalize identity must not mutate Cortex, queue session state, pending inbox, or recovery paths, while valid finalize still works.

## Implementation Scope

This is verification-first. Only change code if the aggregate check finds a concrete gap.

## Verification Plan

- Run focused tests across:
  - React finalize contract generation enforcement.
  - Wake finalize saga payload generation.
  - Cortex scope-end handler identity guards.
  - Session-ended delivery and repository finalize behavior.
  - Recovery/compensation identity handling.
  - Pending inbox restart/attach paths.
- Run residue searches for:
  - finalize/session-ended paths using `session_generation or 0`.
  - direct `CORTEX_SCOPE_END` publish paths without positive generation.
  - stale compatibility names or tests that still assert retired finalize behavior.
- Inspect suspicious hits and classify them as:
  - valid no-active sentinel read,
  - valid explicit rejection path,
  - or real finalize mutation gap.

## Acceptance Criteria

- Focused aggregate tests pass.
- No production finalize-producing path defaults missing generation into a valid identity.
- Any discovered gap is fixed or split into a follow-up before P337 is closed.
- Evidence is recorded with strict success/failure judgment.

## Risk

The risky part is false confidence: a passing test suite is not enough if source residue still allows stale finalize mutation. The check must be search-backed.
