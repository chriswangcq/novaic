# Ticket: Run session side-effect bypass final guard

## Problem Definition

After dispatcher classification and observed-wake cleanup, run a final guard across session/queue/task code for direct side-effect bypasses. Confirm no dangerous live path creates wake sagas, attaches input, or archives scopes outside durable session outbox ownership.

## Proposed Solution

- Save source guard outputs for:
  - direct `SagaOrchestrator.create` / `saga_orchestrator.create`
  - direct `queue.publish`
  - direct `TaskTopics.SESSION_ATTACH_INPUT`
  - direct `TaskTopics.CORTEX_SCOPE_END`
  - session outbox effect builders/dispatchers
  - observed-wake obsolete effect strings
- Classify retained hits.
- Run focused outbox tests after cleanup.

## Acceptance Criteria

- Guard artifacts are saved.
- Retained direct calls are classified.
- No production observed-wake source residue remains.
- Focused tests pass.

## Verification Plan

- `rg` source guard over `novaic-agent-runtime/queue_service` and `novaic-agent-runtime/task_queue`.
- Focused pytest for wake creation, attach outbox, recovery outbox, observed wake cleanup, and effect boundary.
