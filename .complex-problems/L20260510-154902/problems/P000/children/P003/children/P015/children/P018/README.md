# Phase 2.2.1: Projection scope stack and LIFO validation

## Problem

Implement scope lifecycle state in the pure projector: opening skill scopes, maintaining active stack, parent-child relation, and rejecting close events that violate LIFO. This belongs under P015 because fold rendering depends on correct active-scope state.

## Success Criteria

- `SkillScopeOpened` pushes a skill frame with scope id, parent scope id, skill name, and display name.
- `SkillScopeClosed` closes only the current stack top; non-top close raises projection error.
- Wake frames and skill frames coexist in the stack.
- Tests cover simple open stack, nested open stack, valid close, and LIFO violation.
