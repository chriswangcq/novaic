# Phase 2.2: Projection scope stack and fold semantics

## Problem

Implement projection of skill scope lifecycle events into active stack and folded context messages. This belongs under Phase 2 because skill folding is the core behavior currently embedded in DFS `ContextEngine` logic.

## Success Criteria

- Projector handles `SkillScopeOpened` and `SkillScopeClosed` with LIFO validation.
- Non-empty closed skills render `[Skill '<name>' completed]\n<report>`.
- Blank structural closed scopes do not emit empty summaries.
- Nested skill scopes project deterministically.
- Newest open sibling remains active and stale open siblings are suppressed.
- Tests cover simple fold, blank structural close, nested fold, LIFO violation, and stale open sibling suppression.
