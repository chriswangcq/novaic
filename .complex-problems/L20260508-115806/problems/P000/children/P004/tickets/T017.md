# P004 Ticket - Docs Status Consistency Lint

## Problem Definition

Architecture docs and roadmap tickets can mislead future work if a closed architecture ledger says one thing while a roadmap ticket still says `Status: Doing` or `in progress`. The known stale case is `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md`, which still claims PR-338 is doing and P007 is in progress even though the architecture plan marks phase 13 closed.

## Proposed Solution

Fix the known PR-338 stale status and add CI tooling that catches this class of docs status drift.

The lint should:

- Check selected roadmap tickets against architecture-plan status markers.
- Fail if PR-338 returns to `Status: Doing` or `P007 in progress`.
- Verify the architecture plan still records phase 13 as closed.
- Be wired into the existing lint workflow.

## Acceptance Criteria

- PR-338 roadmap ticket status is corrected to closed/current wording.
- A docs status consistency lint exists and fails on the stale PR-338 wording.
- The lint is wired into `.github/workflows/lint.yml`.
- The lint passes locally.
- Existing roadmap archaeology/current docs residue lints still pass.

## Verification Plan

- Run the new docs status consistency lint.
- Run existing docs residue and roadmap archaeology lints.
- Inspect affected docs for stale `Doing` / `in progress` wording.

## Risks

- A too-generic docs linter could become noisy; keep this first version narrow and explicit.
- Future docs status expectations should be added deliberately as new entries.

## Assumptions

- `docs/architecture/generic-worker-substrate-plan.md` is the source of truth for PR-338 closure state.
