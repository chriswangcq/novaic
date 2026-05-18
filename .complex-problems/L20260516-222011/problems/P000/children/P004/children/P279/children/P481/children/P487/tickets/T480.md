# Direct side-effect bypass final verification ticket

## Problem Definition

P487 must verify the P481 direct side-effect bypass cleanup after classification and hardening. It should prove that remaining production side-effect call sites are classified required boundaries, while tests/docs fixtures are separated from production hits.

## Proposed Solution

Rerun targeted production guards for direct saga creation, direct queue/task publish, and session-owned outbox effect terms. Compare hits against the P484 classification and P485/P486 decisions. Save a final guard/classification artifact and rerun focused side-effect/session outbox tests.

## Acceptance Criteria

- Final guard artifact is saved.
- Remaining production direct side-effect call sites are classified required boundaries.
- No ambiguous production hit remains untracked.
- Test/docs fixture hits are separated from production hits.
- Focused side-effect/session outbox tests pass.

## Verification Plan

Run targeted `rg` guards from repo root and focused pytest from `novaic-agent-runtime`. Save logs under `.complex-problems/L20260516-222011/tmp/p487/`.

## Risks

- A pattern-based final guard can miss future spelling variants.
- Existing unrelated dirty worktree state should not be mistaken for P487 changes.

## Assumptions

- P484/P485/P486 decisions are the classification baseline.
