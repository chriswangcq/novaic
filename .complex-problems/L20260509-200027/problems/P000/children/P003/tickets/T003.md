# Recommend Staged RO/RW Mount Optimization Design

## Problem Definition

We need an implementable plan that improves shell mount speed without sacrificing the stable `/cortex/ro` and `/cortex/rw` contract or introducing hard-to-debug filesystem substrate risk.

## Proposed Solution

Design a staged target architecture: add metrics first, then explicit mount profiles, then manifest/delta sync, then a managed local cache, and only later consider deeper virtual filesystem work if needed.

## Acceptance Criteria

- Target architecture is concrete.
- Phases are ordered by safety and payoff.
- Invariants, tests, observability, and rollback are defined.
- Follow-up implementation tickets are listed.
- No implementation changes are performed in this research pass.

## Verification Plan

- Check design against P001 bottlenecks and P002 option comparison.
- Ensure all root success criteria are covered.

## Risks

- Over-optimization may accidentally change shell semantics.
- Cache invalidation bugs can be worse than slow sync.

## Assumptions

- Default user-facing shell behavior should remain compatible until metrics prove a faster default is safe.
