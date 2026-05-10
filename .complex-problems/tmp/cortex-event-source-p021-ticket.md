# Implement projection stale open sibling suppression

## Problem Definition

The projector renders folds, but it does not yet suppress stale open siblings. If one open skill under a parent is abandoned and a newer sibling opens under the same parent, the older sibling should not remain active or leak buffered context.

## Proposed Solution

- Before pushing a `SkillScopeOpened` frame, remove older open skill frames under the same `parent_scope_id` from the active stack.
- Also remove descendants of those stale frames from the active stack.
- Keep stale scope buffers in internal state but do not emit them unless a valid later event explicitly closes them in a way the model accepts.
- Add tests proving:
  - newer sibling remains active;
  - older sibling is removed from stack;
  - older sibling buffered messages are not projected;
  - normal nested child scopes are not suppressed.

## Acceptance Criteria

- Opening a new sibling suppresses older open sibling stack frames.
- Buffered messages from stale open siblings do not appear in `snapshot.messages`.
- Nested child scopes under the current parent are unaffected.
- Focused projection tests pass.

## Verification Plan

- Run projection/substrate tests.
- Static scan projector for hidden dependencies.

## Risks

- Suppressing too broadly can break legitimate nested scopes; descendant detection must be parent-chain based.

## Assumptions

- Stale open siblings are recovery residue; keeping their buffered messages invisible is preferred to surfacing incomplete context.
