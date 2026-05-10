# Ticket: Verify Cutover And Close Residue

## Problem Definition

The implementation must prove it is connected and not half-migrated. This ticket runs broader tests and residue audits, then fixes any immediate gaps found.

## Proposed Solution

Run focused and relevant broad test subsets in `novaic-cortex`, audit old terms, inspect schema/doc wording, and patch any stale current-path references that would confuse future agents.

## Acceptance Criteria

- Relevant pytest subset passes.
- `sandbox.py` compiles.
- Old command-gating symbols remain absent.
- Tool schema tests either pass or are updated to current wording.
- Final residue audit identifies only intentional historical-path rejection references.

## Verification Plan

- `pytest -q` for sandbox/incremental/stress/limits/schemas/capability/projection tests.
- `rg` residue audit.
- `git diff --stat` scoped review.

## Risks

- There may be unrelated pre-existing dirty tests or changes outside this scope; do not revert them.

## Assumptions

- Deployment is not requested in this turn; user asked to implement and verify the architecture state.
