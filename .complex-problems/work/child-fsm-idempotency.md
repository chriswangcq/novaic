# Make duplicate FSM transition events side-effect free

## Problem

The generic FSM transition runner currently treats an idempotent duplicate event as if it were a fresh transition, which can overwrite materialized state and attempt outbox effects. This can create a half-state such as a fresh active scope with no matching wake outbox.

## Success Criteria

- The generic store exposes whether an event insert was fresh or an idempotent replay.
- The generic transition runner skips state and outbox writes on duplicate event replay.
- Existing `append_event()` callers keep their original string return contract.
- A regression test proves duplicate transition replay does not mutate state or create outbox effects.

