# Phase 3.5.2: Emit SkillScopeClosed on skill_end success

## Problem

Successful `/v1/context/skill_end` writes `summary.md` and closes the child scope as filesystem truth, but does not append `SkillScopeClosed`. Failure paths must remain event-silent.

## Success Criteria

- Successful `context_skill_end` appends `SkillScopeClosed` with exact report text.
- LIFO mismatch, missing id, and empty stack failure responses append no close event.
- Existing structured failure payloads remain compatible.
- Focused API tests inspect event stream content and no-op failure behavior.
