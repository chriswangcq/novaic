# Session finalize transaction flow audit

## Problem

Audit the session finalize path to ensure it records explicit finalize/session-ended events with reason, generation, remaining stack, and durable state transition ownership instead of scattered direct state mutation.

## Success Criteria

- Finalize path source is mapped.
- Any direct active-session/session-state mutation outside the intended repository/FSM boundary is identified.
- Any durable outbox or event gap is identified as a follow-up.
