# Diagnose and repair message no-response path

## Problem Definition

Sending a chat message currently produces no visible assistant response. The failure may be in the app send path, Gateway action forwarding, Business message action, Entangled persistence/sync, queue dispatch, wake saga, Cortex/LLM execution, or reply projection back to the app. The diagnosis must follow the actual runtime evidence rather than assuming one layer.

## Proposed Solution

Trace the message from the app boundary through Gateway, Business, queue/saga runtime, Cortex, and Entangled sync using code inspection, prod/staging logs, and direct service checks. Once the stuck stage is known, implement the smallest correct code or deployment/config fix, add a focused regression test or guard, then deploy through Release Controller if backend behavior changes.

## Acceptance Criteria

- The failing stage is identified with log, database, API, or queue evidence.
- The fix targets the actual broken boundary and does not introduce fallback behavior.
- Regression coverage or a guard proves the message path will not silently stall in the same way.
- Relevant local tests pass.
- If backend runtime code changes, staging and prod are released through Release Controller.
- The final state is recorded in the ledger with residual risks clearly separated from solved criteria.

## Verification Plan

Inspect recent production logs and data for the user's latest sent message, reproduce with a direct API or local unit path when feasible, run targeted tests for the changed module, verify deployed health/queue behavior, and confirm that the message path either produces a response or exposes a concrete error.

## Risks

- Without the exact agent/message ID, production diagnosis must infer from recent activity.
- Some LLM/runtime failures may be external provider or credential failures rather than application code.
- A direct live chat test may create user-visible messages; prefer read-only evidence first.

## Assumptions

- The app is pointed at the current prod backend unless evidence shows a staging/local target.
- The user wants the problem fixed, not only explained.
- Release Controller remains the only backend deployment path.
