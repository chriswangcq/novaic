# Phase 2.2.2.2: Projection stale open sibling suppression

## Problem

Implement stale open sibling suppression so that when a newer open sibling appears under the same parent, older still-open sibling output is not projected as active context. This belongs under P019 because stale wake/skill residue was a root cause of earlier DFS context bugs.

## Success Criteria

- Opening a new sibling under the same parent suppresses older open sibling output.
- Older sibling is removed from active stack while the newer sibling remains active.
- Suppression does not break normal nested child scopes.
- Tests cover stale sibling stack and message suppression.
