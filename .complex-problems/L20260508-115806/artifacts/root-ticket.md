# Close All FSM Substrate And Business DSL Gaps

## Problem Definition

The previous audit found real progress but also non-negotiable gaps: action engines still perform imperative side effects, worker assembly is still thick, guardrails do not enforce the stricter effect-plan/DSL target, docs can drift, deploy smoke can be fooled by stale logs, and worker processes are shell-spawned rather than supervised. This ticket closes all of those gaps without discounting any category.

## Proposed Solution

Split the work into implementation phases:

1. Introduce an explicit action/effect-plan model and migrate task/saga/health/scheduler action engines to produce and execute approved effect plans.
2. Shrink worker assembly into declarative worker assembly specs and move reusable startup policies out of the large imperative composition root.
3. Add guardrails that enforce action-engine effect adapter boundaries and assembly structure.
4. Add docs consistency lint to catch stale roadmap/architecture status mismatches.
5. Add timestamp-aware deploy smoke tooling so stale append-only logs do not count as current failures/successes.
6. Add a minimal process supervisor layer or equivalent restart/watch mechanism for the runtime worker set.
7. Run final residue scans, targeted tests, and parent closure.

## Acceptance Criteria

- Task/saga/health/scheduler engines no longer freely grow direct side-effect branches; side effects are represented as explicit effect plans and executed by approved adapters.
- Worker assembly is declarative enough that business worker wiring is not a 600-line ad hoc composition file.
- Tests fail if business engines bypass effect adapters, if assembly regresses to thick imperative wiring, or if old worker paths return.
- Docs status consistency checks catch the PR-338-style stale ledger mismatch.
- Deploy smoke checks use fresh timestamps or structured process evidence rather than raw stale log tails.
- Runtime worker processes have a minimal supervision/restart mechanism or explicit process status guard that closes the shell-backgrounding gap.
- All new/changed code is covered by targeted tests and final residue scans.

## Verification Plan

- Use the ledger loop for each phase and split follow-ups whenever a phase is too large.
- Run targeted tests after each implementation phase.
- Run relevant lint/compile/residue scans.
- Run deploy smoke tooling locally; use remote read-only evidence where appropriate.
- Finish with ledger validate/render/status and a final summary of changed files, tests, residual risks, and whether deployment is needed.

## Risks

- The action-engine conversion can be invasive; preserve behavior while changing shape.
- Process supervision may need to stay minimal to avoid introducing a new deployment system in one pass, but it must close the concrete worker-death detection/restart gap.
- Guardrails can become brittle if they rely only on string matching; prefer structural tests where practical and targeted string guards for old residue.

## Assumptions

- Backward compatibility is not required for removed old paths.
- The current repository state is the implementation target.
- No production deployment is done unless a later user message explicitly asks or the final verification requires it.
