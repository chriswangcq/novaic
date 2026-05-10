# Phase 2.2.2: Projection fold rendering and stale sibling suppression

## Problem

Implement rendering behavior for closed scopes and suppression of stale open siblings. This belongs under P015 because it is the event-sourced replacement for DFS folded summary rendering.

## Success Criteria

- Non-empty `SkillScopeClosed.report` renders `[Skill '<name>' completed]\n<report>` into the parent message stream.
- Blank structural closed scopes emit no empty summary and expose child fold messages.
- Nested folds render deterministically inside parents.
- When a new open sibling appears under the same parent, older still-open sibling output is suppressed and removed from active stack.
- Tests cover non-empty fold, blank structural close, nested fold, and stale open sibling suppression.
