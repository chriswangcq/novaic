# Implement fold rendering and stale sibling suppression

## Problem Definition

The projector now tracks stack/LIFO, but it does not yet render closed skill summaries, expose structural child folds, or suppress stale open siblings. These are the core DFS-to-event projection semantics and need finer-grained closure.

## Proposed Solution

- Split into:
  - closed-scope fold rendering and structural blank close behavior;
  - stale open sibling suppression.
- Keep all behavior pure and event-driven.
- Add tests that operate only on ContextEvents.

## Acceptance Criteria

- Non-empty closed skill reports render folded summary messages.
- Blank structural closed scopes emit no empty summary and preserve child fold output.
- Nested folds render deterministically.
- Opening a new sibling suppresses older still-open sibling output and removes it from active stack.
- Focused projection tests pass.

## Verification Plan

- Run projection tests after each child.
- Run event substrate tests.
- Static scan projector for hidden Workspace/DFS dependencies.

## Risks

- Stale sibling suppression can conflict with strict LIFO if modeled poorly; isolate it from ordinary fold rendering.

## Assumptions

- P018 already handles ordinary stack/LIFO.
