# Repair Session Outbox Finalize Test Failures Ticket

## Problem Definition

The P517 focused pytest subset failed in three distinct tests. Each failure may have a different root cause and should be diagnosed independently before changing code or tests.

## Proposed Solution

Split repair into three child problems: recovery remaining-stack semantics, attach outbox published status, and session repository wrapper-boundary assertion. Each child must decide whether the failure is stale test expectation or production behavior drift, apply minimal correction, and rerun relevant tests.

## Acceptance Criteria

- Each failing test is diagnosed independently.
- Minimal correct code/test changes are applied.
- The three failing tests and the full P517 subset rerun green before P520 closes.

## Verification Plan

- Child checks cite source/test evidence and focused reruns.
- Parent result cites all child results and final P517 subset rerun.

## Risks

- Blindly updating tests could hide production regressions.
- Fixing one failure may affect the others.

## Assumptions

- Existing dirty worktree changes are intentional and must not be reverted.
