# Phase 3.5 skill lifecycle event cutover result

## Summary

Completed the Phase 3.5 skill lifecycle event cutover. Successful skill begin/end now emit `SkillScopeOpened` and `SkillScopeClosed`, failure paths are event-silent, and the discovered legacy runtime bypass was physically removed.

## Done

- P038/R032: wired `context_skill_begin` to append `SkillScopeOpened`.
- P039/R033: wired `context_skill_end` to append `SkillScopeClosed` with exact report text after LIFO validation.
- P040/R034: audited lifecycle boundaries and found the legacy `/v1/skill/*` / `Cortex.skill_begin/end` bypass.
- P041/R035: removed the old JWT skill routes, removed runtime direct skill lifecycle methods/state, and added guard tests.
- P040/C038: rechecked the audit after P041 and closed successfully.

## Evidence

- Child success checks:
  - P038/C034
  - P039/C035
  - P041/C037
  - P040/C038
- Focused lifecycle tests passed.
- Legacy-bypass guard tests passed.
- Full Cortex suite passed after removal: `444 passed`.

## Residual Risk

- Legacy filesystem projections (`summary.md`, child scope index, scope meta phase) remain transitional and are deferred to later read-cutover/cleanup phases.
- Event append and projection write are still not a single transaction.
