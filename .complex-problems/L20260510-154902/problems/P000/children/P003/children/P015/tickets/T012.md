# Implement projection scope stack and fold semantics

## Problem Definition

The projector currently handles root/wake/message/notification events, but not skill scope lifecycle. P015 must add stack and fold behavior so event replay can replace DFS skill-summary folding later.

## Proposed Solution

- Split into smaller child problems:
  - scope stack state and LIFO validation;
  - closed-scope fold rendering, blank structural behavior, nesting, and stale sibling suppression.
- Keep the projector pure and independent of Workspace/DFS.
- Preserve P014 behavior while adding scope-aware message routing.

## Acceptance Criteria

- Skill scope open/close events update projection stack deterministically.
- LIFO violations are rejected.
- Non-empty closed skills render folded summary messages.
- Blank structural closed scopes expose child folds without empty summaries.
- Nested scopes and stale open siblings are tested.

## Verification Plan

- Run focused projection tests after each child.
- Run event model/store tests to catch substrate regression.
- Static scan projector for hidden Workspace/DFS/IM/payload dependencies.

## Risks

- Scope fold logic can accidentally recreate DFS traversal assumptions.
- Stale sibling suppression is subtle; it should be tested separately from ordinary nested folds.

## Assumptions

- Tool call/result placement remains separate in P016.
