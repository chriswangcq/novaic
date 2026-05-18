# Runtime finalize handler inventory

## Problem Definition

P337 needs a concrete inventory of runtime/finalize handlers before implementation. The inventory must identify which handlers mutate Cortex, session state, recovery state, message claims, or wake stack, and what identity fields guard those mutations.

## Proposed Solution

Run a read-only source audit over:

- `task_queue/handlers/*`
- `task_queue/contracts/*`
- `task_queue/sagas/*`
- `task_queue/utils/cortex_bridge.py`
- `queue_service/session_*`
- `queue_service/saga_repo.py`
- relevant tests.

Classify finalize/session-ended/skill-end/recovery paths as mutating, non-mutating, already guarded, or requiring P349-P352 work.

## Acceptance Criteria

- Result lists live finalize/session-ended/runtime handler files and functions.
- Result identifies mutation type and required identity fields.
- Result assigns implementation work to P349-P352.
- No code changes occur in this inventory.

## Verification Plan

- Use `rg`, `nl`, and targeted reads only.
- Cite evidence lines for each live path.

## Risks

- Search results may include unrelated attach/session code; keep the inventory scoped to finalize/session-ended/skill-end/recovery completion.

## Assumptions

- P348 is read-only inventory.
