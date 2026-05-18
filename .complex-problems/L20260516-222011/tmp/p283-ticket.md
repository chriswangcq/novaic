# Ticket: Audit session generation attach and finalize boundary

## Problem Definition

Inspect the Queue Service session generation model end to end: where generations are created/advanced, how attach requests carry and validate generation, and how finalize/session-ended paths ensure stale events cannot mutate or close the wrong wake/session.

## Proposed Solution

Split the audit into focused child problems instead of treating it as one pass: generation lifecycle/advancement inventory, attach expected-generation validation, finalize/session-ended generation ownership, and stale/missing-generation compatibility residue scan. Each child should map source paths and either prove correctness or create follow-up fixes.

## Acceptance Criteria

- Generation creation and advancement paths are mapped with file references.
- Attach request creation, outbox payload, worker dispatch, and handler-side expected-generation validation are mapped.
- Finalize/session-ended paths are mapped, including generation checks and remaining stack handling.
- Any missing-generation, stale-generation, or compatibility fallback that can mutate/close the wrong session is fixed or recorded as a follow-up.
- Verification includes targeted tests or source guards for stale attach/finalize behavior.

## Verification Plan

Use read-only source inventory first over `session_repo.py`, `session_decision.py`, `session_outbox.py`, `session_outbox_worker.py`, saga/finalize handlers, and related tests. Then run targeted tests for attach generation, finalize/session-ended behavior, recovery/restart behavior, and source guards for missing-generation compatibility.

## Risks

- Generation may be enforced at one boundary but lost in outbox or worker payload translation.
- Finalize paths can be deceptively safe if they close by saga id but clear session state without checking the current generation.
- Backward-compatible missing-generation branches can reintroduce stale-event acceptance.

## Assumptions

- `session_key + generation` is the intended concurrency boundary for active session mutation and attach delivery.
- `tq_session_state` is the authoritative active-session state source after P282.
