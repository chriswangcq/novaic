# Remove legacy runtime skill lifecycle bypass

## Problem Definition

The older JWT `/v1/skill/begin` and `/v1/skill/end` endpoints plus `Cortex.skill_begin/end` runtime methods can bypass the event-wired `/v1/context/skill_begin` and `/v1/context/skill_end` lifecycle path.

## Proposed Solution

- Delete the old JWT skill lifecycle endpoints and request models.
- Delete `Cortex.skill_begin/end`, runtime in-memory skill stack state, and the `SkillInstance` type/export.
- Replace old runtime skill lifecycle tests with guard tests proving the bypass routes/methods are gone.
- Run focused and full Cortex tests.

## Acceptance Criteria

- No `/v1/skill/begin` or `/v1/skill/end` route remains.
- No `Cortex.skill_begin/end` direct lifecycle method remains.
- No `SkillInstance` runtime lifecycle state remains.
- Focused guard tests pass.
- Full Cortex suite passes.

## Verification Plan

- Static scan old route/method/type names.
- Run guard lifecycle tests.
- Run full Cortex suite.

## Risks

- Any untracked external client still calling old JWT routes will now fail; this is intended for full cutover.

## Assumptions

- Agent-runtime uses the internal `/v1/context/skill_begin` and `/v1/context/skill_end` path.
