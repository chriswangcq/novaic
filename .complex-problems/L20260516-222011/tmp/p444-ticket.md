# Ticket: Clarify runtime context task projection contract

## Problem Definition

Runtime `context.read` and `context.append` handlers maintain materialized context projections and notification hints. Their docs/tests still use broad “context” language that can be mistaken for LLM history assembly.

## Proposed Solution

- Update handler docstrings/comments to say materialized projection and notification hint maintenance.
- Ensure tests refer to projection/notification behavior rather than LLM history assembly.
- Keep functional behavior unchanged.

## Acceptance Criteria

- Runtime context handler docs/comments distinguish projection maintenance from LLM prepare.
- Notification hint idempotency tests still pass.
- Assistant/system projection append tests still pass.
- Focused context handler tests pass.

## Verification Plan

- Inspect handler source and tests.
- Patch wording where misleading.
- Run focused context read/order/by-id/activity tests and prepare-path guards.

## Risks

- Over-renaming task topics may be too broad; this ticket should avoid topic/API churn unless required.

## Assumptions

- P443 already narrowed bridge helper names.
