# Legacy imperative dispatch and compatibility residue cleanup ticket

## Problem Definition

P279 must find and close old imperative dispatch, finalize, and session compatibility branches that bypass or duplicate the FSM decision path. The risk is stale code remaining callable after the FSM/outbox migration, especially direct `SagaOrchestrator` creation, direct session mutation, finalize/session-ended compatibility branches, or fallback dispatch paths.

## Proposed Solution

Run a focused static inventory over queue/session/runtime dispatch paths for direct saga creation, direct session mutation, finalize compatibility language, fallback dispatch, legacy active-session APIs, and non-FSM side-effect publishing. Classify each hit as required boundary, test/docs guard, high-confidence removable residue, or ambiguous. Remove/tighten high-confidence stale residue directly; if any hit is ambiguous, split it into a smaller follow-up instead of speculative deletion. Finish with focused runtime/session tests and saved guard artifacts.

## Acceptance Criteria

- Static guard artifacts are saved with searched terms and matching files.
- Direct `SagaOrchestrator` creation is either limited to explicit outbox dispatcher boundaries or followed up.
- Direct session mutation/finalize compatibility branches are classified and high-confidence stale residue is removed.
- Ambiguous hits become smaller follow-up problems instead of broad speculative cleanup.
- Focused runtime/session tests pass after any source changes.

## Verification Plan

Run `rg` guards over `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and relevant tests for saga creation, finalize/session-ended branches, fallback/legacy/compat language, direct queue publishing, and session mutation APIs. If source changes occur, run focused session/runtime pytest suites that cover dispatch, finalize, outbox, and compatibility guards.

## Risks

- Some direct calls may be legitimate adapter/outbox boundaries and should not be deleted mechanically.
- Some legacy words may appear in tests that intentionally guard removed paths.
- Over-broad cleanup could break recovery/finalization flows if not split and verified.

## Assumptions

- P279 is source-code cleanup/audit scoped; deployment verification is outside this ticket unless a later ticket requests it.
- Existing P278 session state/outbox/generation audit results can be used as context, but this ticket must still record its own scan artifacts.
