# Effect-Plan Boundary Tests

## Problem Definition

The effect-plan migration must be guarded across all action engines, not just individual migrations. We need an aggregate verification ticket proving task, saga, health, and scheduler engines are all protected by source/AST boundary tests and behavior regressions.

## Proposed Solution

Use the PR-340 boundary suite as the cross-engine guardrail and run it together with focused task/saga/health/scheduler behavior suites. Confirm the tests cover all four migrated engines and assembly wiring.

## Acceptance Criteria

- Boundary test covers task, saga, health, and scheduler engines.
- Boundary test asserts adapter wiring for all four worker assemblies.
- Focused task/saga/health/scheduler tests pass together.
- Worker modules compile.

## Verification Plan

- Run PR-340 boundary tests.
- Run focused behavior tests touched by P009/P010.
- Compile worker modules.

## Risks

- If boundary tests cover only source residue but not behavior, a migration could be structurally clean but behaviorally broken; the aggregate suite must include both.

## Assumptions

- Detailed engine migrations are already handled by P009 and P010; this ticket is cross-engine verification and guardrail closure.
