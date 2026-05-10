# Emit SkillScopeClosed on skill_end success

## Problem Definition

Successful `context_skill_end` validates LIFO and writes legacy child-scope closure state, but does not append the authoritative `SkillScopeClosed` event. Failure paths must remain event-silent so replay cannot record closes that never happened.

## Proposed Solution

- After resolving the active path and validating the requested id equals the stack top, append `SkillScopeClosed` with the exact report text.
- Keep missing id, empty stack, and scope mismatch returns before event append.
- Keep `complete_child_scope` as transitional filesystem projection after event append.
- Add focused tests for success plus failure no-op cases.

## Acceptance Criteria

- Successful skill end appends one `SkillScopeClosed`.
- Event payload contains the exact untruncated report text.
- Missing id, empty stack, and LIFO mismatch failures append no close event.
- Existing structured failure responses remain intact.
- Focused lifecycle event tests and full Cortex suite pass.

## Verification Plan

- Extend lifecycle API tests.
- Run lifecycle/projection/writer tests.
- Run full Cortex suite.

## Risks

- Event append before legacy `complete_child_scope` makes event stream authoritative if projection write fails; this is intended for cutover but still transitional.

## Assumptions

- Begin event was wired in P038.
