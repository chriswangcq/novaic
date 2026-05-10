# Phase 3.5: Cut skill begin/end lifecycle to events

## Problem

Skill begin/end currently create child scope directories, update scope meta, and write `summary.md` as direct source-of-truth facts. The authoritative lifecycle facts must become `SkillScopeOpened` and `SkillScopeClosed` events while preserving LIFO failure behavior.

## Success Criteria

- `skill_begin` appends `SkillScopeOpened`.
- `skill_end` appends `SkillScopeClosed` with exact report text.
- LIFO mismatch continues to return structured failure and does not append a close event.
- Event payloads are sufficient for fold rendering and active stack replay.
- Tests verify event stream content and failure no-op behavior.
