# Scheduler Engine Effect Adapter Migration

## Problem Definition

`ScheduledWakeEngine` still stores `business_client` and `assembler`, then directly performs due-agent scans and wake dispatch. This violates the action-engine/effect-adapter boundary and keeps concrete side-effect collaborators in the business action engine.

## Proposed Solution

Add `ScheduledWakeEffectAdapter` to own `business_client` and dispatch assembler. Refactor `ScheduledWakeEngine` to accept `EffectExecutor`, use `scheduler.get_due_for_wake` to scan due agents, and use `scheduler.dispatch_wake` to perform wake dispatch.

## Acceptance Criteria

- `ScheduledWakeEngine` accepts `effect_executor` instead of `business_client` and `assembler`.
- `scheduled_wake.py` no longer stores `business_client` or `assembler`.
- Due-agent scan and dispatch are explicit named effects.
- `assemble_scheduler_worker` wires `ScheduledWakeEffectAdapter`.
- Existing scheduler tests pass with adapter-based setup.

## Verification Plan

- Run `tests/test_scheduler_dispatch.py` and `tests/test_pr329_scheduler_generic_worker.py`.
- Compile scheduler worker modules.
- Scan `scheduled_wake.py` for old collaborator ownership residue.

## Risks

- Dispatch result/error behavior must preserve existing metrics and log semantics.

## Assumptions

- The dispatch assembler is still constructed in assembly until the assembly DSL shrink ticket.
