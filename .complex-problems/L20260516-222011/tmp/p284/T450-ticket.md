# Ticket: Audit session outbox side-effect ownership

## Problem Definition

Audit whether Queue/session side effects are owned by durable outbox rows and idempotent handlers instead of direct ad hoc calls. The scope includes wake saga creation, attach-input publishing, recovery/archive publishing, and observed wake-created updates.

## Proposed Solution

- Inventory session outbox effect types, constructors, persistence points, workers, and downstream handlers.
- Search for direct side effects that could bypass durable outbox ownership:
  - direct saga creation/publish paths
  - direct attach input publish paths
  - direct recovery/archive publish paths
  - direct wake-created active-state mutation paths
- Classify each direct call as:
  - safe implementation detail below an outbox-owned handler,
  - risky bypass requiring a child fix,
  - removable residue.
- Run focused tests/guards if the audit finds changed or risky paths.

## Acceptance Criteria

- File-referenced map of session outbox effect types and handlers.
- Every relevant direct side-effect hit is classified.
- Risky bypasses are fixed or split into follow-up child problems.
- The audit records whether side-effect ownership is complete.

## Verification Plan

- Use `rg` over `novaic-agent-runtime/queue_service`, `task_queue`, saga clients/workers, session outbox worker, recovery handlers, and tests.
- Save guard outputs under `.complex-problems/L20260516-222011/tmp/p284/`.
- Check representative tests if source behavior is non-trivial or changed.
