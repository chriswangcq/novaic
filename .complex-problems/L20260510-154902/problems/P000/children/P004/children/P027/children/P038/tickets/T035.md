# Emit SkillScopeOpened on skill_begin success

## Problem Definition

Successful `context_skill_begin` creates child scope filesystem state but does not append the authoritative `SkillScopeOpened` event. Event replay cannot reconstruct the active skill stack without this fact.

## Proposed Solution

- After `context_skill_begin` resolves the parent active scope and creates the child scope, append `SkillScopeOpened`.
- Use the resolved parent scope id, requested child scope id, requested skill name, and task/display name.
- Keep existing duplicate, invalid id, and depth-limit failure responses event-silent.
- Add focused API tests for success and duplicate failure no-op.

## Acceptance Criteria

- Successful skill begin appends one `SkillScopeOpened` event.
- Event payload includes child scope id, parent scope id, skill name, and name/task.
- Duplicate begin failure does not append another open event.
- Existing child scope filesystem projection still exists.

## Verification Plan

- Add focused lifecycle API tests.
- Run focused context event lifecycle/writer/projection tests.
- Run full Cortex suite.

## Risks

- Event append after filesystem child creation is transitional and not fully transactional; later outbox/cleanup can harden this.

## Assumptions

- Skill end event emission is handled by P039.
