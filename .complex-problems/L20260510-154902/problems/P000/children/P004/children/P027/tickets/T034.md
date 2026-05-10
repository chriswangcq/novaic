# Cut skill begin/end lifecycle to events

## Problem Definition

`/v1/context/skill_begin` and `/v1/context/skill_end` still treat child scope directories, scope meta, and `summary.md` as the only authoritative lifecycle facts. Context event replay already understands `SkillScopeOpened` and `SkillScopeClosed`, so the write path must emit those events while preserving strict LIFO failure behavior and transitional filesystem projections.

## Proposed Solution

Split the phase because begin, close, and failure/audit semantics have different risk:

- Wire successful `context_skill_begin` to append `SkillScopeOpened` after child scope creation and before returning success.
- Wire successful `context_skill_end` to append `SkillScopeClosed` only after LIFO validation has proved the requested scope is the stack top.
- Add tests proving mismatch, missing id, and empty stack failures do not append close events.
- Audit remaining lifecycle direct writes (`summary.md`, child scope index, meta phase changes) and classify them as transitional projection or follow-up.

## Acceptance Criteria

- Successful skill begin appends `SkillScopeOpened` with scope id, parent scope id, skill name, and display name.
- Successful skill end appends `SkillScopeClosed` with exact report text.
- LIFO mismatch and other failure paths do not append close events.
- Existing structured failure responses remain intact.
- Focused lifecycle event tests and full Cortex suite pass.

## Verification Plan

- Add focused API tests for begin/end events and no-op failure behavior.
- Run context event lifecycle/projection/writer tests.
- Run full Cortex suite.
- Static scan remaining `complete_child_scope`, `summary.md`, and child scope index writes.

## Risks

- Event append ordering relative to legacy filesystem writes can create transitional divergence if one side fails.
- Idempotency for `SkillScopeClosed` must not hide a changed report conflict.
- Failure paths must stay event-silent.

## Assumptions

- Legacy scope directories and `summary.md` remain transitional projections until later cleanup phases.
