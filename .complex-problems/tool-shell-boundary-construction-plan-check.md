# Construction plan satisfies requested scope

## Summary

The construction plan result solves the requested planning problem. It converts the prior system design into dependency-ordered phases and concrete implementation tickets, with file targets, acceptance criteria, verification commands, deletion gates, and final cutover criteria. It does not implement runtime code changes.

## Evidence

- Result `R000` defines eight phases from baseline guardrails through deploy/smoke.
- Result `R000` maps current-state evidence to real files: Runtime tool dispatch, environment tools, device tools, Cortex projection, LLM preparation, multimodal handling, user attachment handling, and activity projection.
- Result `R000` lists concrete tickets per phase with files, work, acceptance, verification, and deletion gates.
- Result `R000` explicitly states the final LLM-visible tool set and forbidden direct tools.
- Result `R000` includes old-code cleanup checklist and cutover definition of done.
- Runtime code was not changed.

## Criteria Map

- Detailed phased construction plan -> covered by `R000` sections 3, 4, 8, and 9.
- Concrete tickets with file/module targets -> covered by each phase ticket in section 3.
- Cross-repo boundaries -> covered by Runtime, Cortex, Device, Business, Monitor/UI file targets.
- Explicit dependency boundaries and context-bloat guardrails -> covered by sections 5, 6, and 7.
- Strategy for moving IM/subagent/device/payload into shell -> covered by Phase 5.
- Final cutover criteria and physical deletion -> covered by Phase 7 and section 7.

## Execution Map

- Ticket `T000` was classified `one_go` because the requested output was one detailed construction plan, not implementation.
- Result `R000` records the plan.
- No child problems were needed for the design-only task.

## Stress Test

- Failure mode: plan adds new shell capabilities but leaves old direct tools active. Result `R000` includes Phase 7 shrink/delete gates and final forbidden-tool checks.
- Failure mode: plan is too abstract to execute. Result `R000` names concrete modules and pytest commands.
- Failure mode: display gets collapsed into shell. Result `R000` keeps display outside shell and treats it as explicit perception.
- Failure mode: context bloat remains. Result `R000` requires ToolOutputV1, manifest-only history, deletion of generic multimodal extraction, and large-output preview/ref policy.

## Residual Risk

- Non-blocking: exact CLI names and shell mounting mechanism remain implementation choices.
- Non-blocking: security/audit schemas need code-level tickets.
- Non-blocking: full test matrix was not run because this was design-only and no runtime code changed.

## Result IDs

- R000
