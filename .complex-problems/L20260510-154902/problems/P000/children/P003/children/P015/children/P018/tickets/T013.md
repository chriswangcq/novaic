# Add projector scope stack and LIFO validation

## Problem Definition

The projector currently has wake stack support only. It needs to replay `SkillScopeOpened` and `SkillScopeClosed` into active stack state and reject non-LIFO closes before fold rendering can be trusted.

## Proposed Solution

- Extend `context_event_projection.py` with internal scope state for open skill frames.
- Handle `SkillScopeOpened` by pushing a skill frame with scope id, parent scope id, skill/name fields.
- Handle `SkillScopeClosed` by requiring that the closing scope is the stack top and then popping it.
- Preserve existing wake stack behavior.
- Add focused tests for simple open, nested open, valid close, and LIFO violation.

## Acceptance Criteria

- Skill open events appear in snapshot stack.
- Nested skill opens preserve order in stack.
- Valid closes pop stack.
- Non-top close raises `ContextEventProjectionError`.
- Existing P014 tests still pass.

## Verification Plan

- Run projection tests.
- Run event model/store tests.
- Static scan projector for hidden Workspace/DFS/IM dependencies.

## Risks

- This ticket should not render folded summaries yet; that belongs to P019.

## Assumptions

- `SkillScopeClosed.report` rendering is intentionally ignored or deferred until P019.
