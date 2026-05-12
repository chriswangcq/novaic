# Fix production IM no-response after wake failure

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
