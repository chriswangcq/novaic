# Phase 2.2.2.1: Projection closed-scope fold rendering

## Problem

Implement fold rendering for ordinary closed scopes and blank structural scopes. This belongs under P019 because fold rendering should be solved before stale sibling suppression adds extra stack behavior.

## Success Criteria

- Closing a skill with a non-empty report emits `[Skill '<name>' completed]\n<report>` into the parent message stream.
- Closing a skill with a blank report emits no empty summary.
- Blank structural parent close exposes child fold messages.
- Nested folds render deterministically.
- Tests cover non-empty fold, blank close, and nested structural fold.
