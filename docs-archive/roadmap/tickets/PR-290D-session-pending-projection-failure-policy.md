# PR-290D — Session Pending Projection Failure Policy

Status: Closed

## Goal

Decide and enforce whether pending projection failures are critical state
failures or non-critical diagnostics.

## Closure Notes

- Classified pending projection as derived observability, not authoritative
  inbox/state.
- Kept projection failures non-critical and documented that policy in
  `SessionRepository`.
- Authoritative input/event/state/outbox paths were hardened in PR-290A through
  PR-290C.
