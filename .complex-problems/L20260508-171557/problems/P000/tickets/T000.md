# Ticket: Implement Full Pure DSL Runtime Closure

## Problem Definition

The audit backlog contains multiple independent implementation areas. Completing them in one unstructured pass would risk exactly the failure mode the user is avoiding: new code written without deleting or guarding old behavior. The work must be split into child problems with concrete implementation and verification boundaries.

## Proposed Solution

Split the implementation into focused child problems corresponding to DSL-001 through DSL-008, preserving dependency order:

1. Worker assembly specs.
2. Plan-first effect runner contract.
3. Task execution policy tables.
4. Saga launch and saga definition plan boundaries.
5. Scheduler and health action specs.
6. Handler registry metadata and guard.
7. CI bytecode/generated-artifact hygiene.
8. Architecture status documentation and final residue guard review.

Each child must implement, test, delete/guard displaced paths, record a result, and pass a success check before the root is closed.

## Acceptance Criteria

- Create child implementation problems for all backlog items.
- Each child problem has file-level success criteria and verification expectations.
- Child problems explicitly include deletion/guard requirements.
- Root result is recorded only after all children are done.

## Verification Plan

- Use the ledger split flow.
- Solve child problems one by one using `ledger.py next`.
- Run relevant targeted tests after each child and broader guards before root closure.

## Risks

- Some items may reveal deeper work while implementing; if a child cannot close cleanly, create follow-up child/follow-up problems rather than hiding the gap.
- The implementation must avoid introducing a second parallel runtime path.

## Assumptions

- The audit ledger `L20260508-165336` is accepted as source evidence.
- Runtime production behavior should remain compatible, but old internal implementation branches should be removed or guarded.
