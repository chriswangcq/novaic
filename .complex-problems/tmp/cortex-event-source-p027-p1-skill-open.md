# Phase 3.5.1: Emit SkillScopeOpened on skill_begin success

## Problem

Successful `/v1/context/skill_begin` currently creates a child scope directory and root scope id index, but does not append the authoritative `SkillScopeOpened` event.

## Success Criteria

- Successful `context_skill_begin` appends `SkillScopeOpened` after child scope creation.
- Event payload includes child scope id, parent scope id, skill name, and display name/task.
- Duplicate/invalid/depth-limit failure paths do not append open events.
- Focused API tests inspect the event stream.
