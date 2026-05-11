# Audit Queue FSM Saga session cutover residue

## Problem Definition

The queue/session harness was migrated toward FSM, durable outbox, and generation-checked session coordination. We need audit whether any live runtime paths still bypass those substrates with old active-session authority, direct saga creation, direct finalize cleanup, or imperative dispatch branches.

## Proposed Solution

Search and inspect queue service/session repository, dispatch subscriber/client, saga repository/orchestrator, outbox workers, worker assemblies, and wake action engines. Classify residue as live gap, intentional cache/view, compatibility, or tests/docs-only.

## Acceptance Criteria

- Identify whether `tq_session_state` or `tq_active_sessions` is the real live authority.
- Identify direct `SagaOrchestrator.create()` paths, direct publish paths, and finalize ownership paths.
- Identify hidden dependency boundary issues in session/FSM decision code if still present.
- Record file/function evidence and priority.

## Verification Plan

- Use `rg` for `tq_active_sessions`, `tq_session_state`, `SagaOrchestrator`, `create(`, `wake_finalize`, `session_ended`, `generation`, `outbox`, `dispatch`, `os.environ`, `uuid`, and clocks.
- Inspect line slices around matches.
- Distinguish production code from docs/tests.

## Risks

- Some active-session tables may intentionally be compatibility views; verify by code ownership rather than table name alone.

## Assumptions

- The desired direction is session-state/FSM as authority, active session as view/cache, durable outbox for side effects, and finalize as an explicit event with reason/generation/remaining stack.
