# Recovery Remaining Stack Failure Ticket

## Problem Definition

`test_wake_finalize_failure_records_suspected_dead_event` expects recovery archive `remaining_stack.known == True`, but current behavior reports `False`.

## Proposed Solution

Inspect the failing test, recovery/finalize code, and recent ownership decisions to determine intended semantics. Apply the minimal correct production or test update, then rerun the specific failing test.

## Acceptance Criteria

- Root cause is recorded with source/test references.
- Minimal correct update is applied.
- The specific failing test passes.

## Verification Plan

- Run the single failing pytest test.
- Record files changed and command output.

## Risks

- Changing the assertion without understanding semantics could hide a real recovery archive bug.

## Assumptions

- The ownership audit established that unknown remaining-stack diagnostics can be intentional when saga failure lacks stack evidence.
