# Session restart transaction flow audit

## Problem

Audit restart/recover-start paths to ensure they use the explicit FSM/session-state boundary and do not bypass generation or durable outbox ownership.

## Success Criteria

- Restart/recovery start path source is mapped.
- Generation and durable outbox boundaries are identified.
- Any legacy direct start or attach path is turned into a follow-up.
