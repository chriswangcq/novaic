# Session state SSOT, outbox, and generation boundary audit

## Problem

Audit whether `tq_session_state`, outbox tables, generation checks, and active session cache/view behavior match the intended FSM model.

## Success Criteria

- Map session state and active session repository roles.
- Identify hidden inputs or state mutations outside explicit FSM/outbox boundaries.
- Classify any residual compatibility paths as safe, risky, or removable.
