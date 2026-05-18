# Queue FSM Focused Verification Ticket

## Problem Definition

After the sibling cleanup/audit work, the queue/session/FSM/outbox/finalize surfaces need a final focused verification pass. The pass must prove the active behavior still works and that static residue scans do not expose an unclassified risky legacy path.

## Proposed Solution

Run a bounded verification workflow: identify the focused test set, execute queue-service/runtime tests that cover dispatch, session state, outbox, finalize, recovery, saga compensation, and FSM decisions, then run targeted static residue scans for legacy/imperative bypass terms and classify every remaining hit.

## Acceptance Criteria

- Focused queue/session/FSM/outbox/finalize tests pass, or any failure is turned into a follow-up problem.
- Static residue scan has no unclassified risky legacy path.
- Result records exact commands, counts, artifacts, and residual risk.

## Verification Plan

- Use `rg`/targeted source slices to build the final static residue scan.
- Run focused pytest files from `novaic-agent-runtime` that cover queue service, session dispatch/state, outbox, finalize, recovery, saga compensation, and FSM decisions.
- Save logs and classification artifacts under the ledger tmp directory.

## Risks

- Focused tests may miss a service boundary outside `novaic-agent-runtime`.
- Static scans may include legitimate live vocabulary and require careful classification rather than blind deletion.
- Existing dirty worktree state means verification must cite exact commands and not claim unrelated changes.

## Assumptions

- This ticket is verification-focused; broad new remediation should become a follow-up if a gap is found.
- The current repository dirty state contains prior intended work that must not be reverted.
