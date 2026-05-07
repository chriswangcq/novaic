# PR-296 — Session Deployment Migration Plan

Status: Closed

## Goal

Make deployment and rollback explicit for the new FSM/outbox session harness so
runtime state can be recovered safely.

## Scope

- Document DB migrations, feature flags, worker startup, rollback behavior, and
  cleanup order.
- Define health checks for active, starting, pending outbox, and recovery
  states.
- Record deploy-time commands and post-deploy validation.

## Dependencies

- PR-286 durable outbox cutover.
- PR-293 return contract.
- PR-294 legacy cleanup.

## Risks

- Deploying code before worker wiring can strand queued wake creation.
- Rolling back after schema writes requires an explicit DB reset/export plan;
  the runtime no longer carries in-process schema compatibility.

## Acceptance Criteria

- Deployment plan names stateful rollout constraints and the no-backcompat
  rollback boundary.
- Health/audit checks are documented.
- The plan identifies when old code can be deleted.

## Verification

- Manual review against final diff.
- Post-migration test/deploy checklist.

## Closure Notes

- Added `docs/architecture/session-harness-deployment-migration-plan.md`.
- Documented staged migration, rollback, health checks, incident audit commands,
  and cleanup gate.
- PR-298 updated the plan to state that old schema versions fail fast instead
  of being migrated in-process.
- No code changes were needed for this ticket.
