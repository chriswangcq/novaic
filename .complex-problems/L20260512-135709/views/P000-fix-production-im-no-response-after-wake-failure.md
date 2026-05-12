# P000: Fix production IM no-response after wake failure

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Production agent messages can appear to be delivered while the runtime does not respond. The observed incident combined disk-full log growth, Redis persistence MISCONF, Cortex append/end failures, a subscriber delivery marker that prevented retry, and a session FSM idempotency replay bug that could materialize a fresh active scope without a matching outbox event.

The work must repair the immediate production state, remove code paths that can recreate the half-state, and reduce noisy poll logging so the same failure mode does not refill disk.

## Success Criteria
- Production queue session for the affected agent is recoverable and returns to `no_active` after the replayed message.
- The affected message is either answered or explicitly accounted for in `environment_im_messages` and `environment_notifications`.
- Generic FSM transition recording does not update materialized state or outbox effects when an event idempotency key is replayed.
- High-frequency internal polling logs no longer write INFO lines for successful task/saga claims or httpx/httpcore request noise.
- Tests cover both the FSM replay behavior and logging suppression.
- Deployed runtime/common code is verified on production with disk, Redis, session, and queue checks.

## Subproblems
- P001: Verify and recover production IM session state
- P002: Make duplicate FSM transition events side-effect free
- P003: Suppress high-frequency successful polling logs
- P004: Deploy and verify no-response repair

## Results
- R004

## Latest Check
C004

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R004: problems/P000/results/R004.md
- Check C004: problems/P000/checks/C004.md

## Follow-ups
- none
