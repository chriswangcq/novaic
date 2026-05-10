# Remove or redirect legacy runtime skill lifecycle bypass

## Problem

Older JWT endpoints `/v1/skill/begin` and `/v1/skill/end` call `Cortex.skill_begin/end`, and those runtime methods directly create/close scope filesystem state without emitting `SkillScopeOpened` or `SkillScopeClosed`. This bypass means lifecycle events are not yet the single write path.

## Success Criteria

- `/v1/skill/begin` and `/v1/skill/end` can no longer create or close skill scopes without `SkillScopeOpened/Closed` events.
- Either the legacy endpoints are deleted/disabled with explicit tests, or they are redirected through the event-wired context lifecycle path.
- `Cortex.skill_begin/end` direct filesystem lifecycle code is removed or made unreachable for runtime lifecycle writes.
- Focused tests prove the old endpoints cannot bypass lifecycle events.
- Full Cortex suite passes.
