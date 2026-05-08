# Health and Scheduler Engines Use Effect Adapters

## Problem Definition

`HealthRecoveryEngine` and `ScheduledWakeEngine` still own concrete side-effect collaborators. Health owns `httpx` client creation and Queue recover-all calls. Scheduler owns `business_client` and `assembler` and invokes due-agent scans and dispatch directly. These engines should match the task/saga architecture: compute action flow, while concrete side effects live in explicit adapters.

## Proposed Solution

Add health and scheduler effect adapters. Refactor engines to use `EffectExecutor` for external calls:

- health: `health.recover_all`
- scheduler: `scheduler.get_due_for_wake`, `scheduler.dispatch_wake`

Update assemblies and tests, then add boundary guards that reject direct client/assembler ownership in health/scheduler engines.

## Acceptance Criteria

- `HealthRecoveryEngine` no longer imports `httpx` or `internal_sync_client`, no longer owns `_client`, and no longer constructs HTTP clients.
- `ScheduledWakeEngine` no longer stores `business_client` or `assembler`.
- Worker assemblies wire health/scheduler effect adapters explicitly.
- Existing health and scheduler tests pass after migration.
- Boundary tests prevent direct collaborator ownership from returning.

## Verification Plan

- Run focused health dispatch/generic worker tests.
- Run focused scheduler dispatch/generic worker tests.
- Run new/updated boundary tests.
- Compile worker modules.

## Risks

- Health tests currently patch `_get_client`; they need to patch the adapter instead of engine internals.
- Scheduler dispatch error handling depends on `DispatchError` and must preserve metrics/logging behavior.

## Assumptions

- Handler classes remain lifecycle-free and keep delegating to action engines.
- Assembly may still create concrete clients/assemblers until the assembly DSL shrink ticket.
