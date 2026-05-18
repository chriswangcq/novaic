# Audit Task Saga Worker Focused Result Ticket

## Problem Definition

P525 produced a validated P518 target list and P526 ran it green, but P518 should only close if the target mapping and execution evidence together satisfy the original task/saga/worker focused verification criteria.

## Proposed Solution

Review P525 and P526 artifacts together, map them back to P518 coverage areas, and record whether the verification evidence is sufficient or whether a follow-up is needed.

## Acceptance Criteria

- The audit cites P525 target-list evidence and P526 pytest evidence.
- The audit maps evidence to P518 coverage areas.
- It explicitly handles the initial wrong-cwd pytest failure.
- It records residual risk and either supports closing P518 or creates a follow-up.

## Verification Plan

- Read P525 coverage/count artifacts.
- Read P526 corrected run/count artifacts.
- Confirm excluded broad candidates are delegated to P517/P519 rather than lost.

## Risks

- A green pytest run could still be misleading if the selected subset is incomplete.
- The initial root-cwd failure could be confused with a product failure if not documented.

## Assumptions

- P517 is already closed for session/outbox/finalize tests.
- P519 will cover unit/tool-output/task_queue boundary tests.
