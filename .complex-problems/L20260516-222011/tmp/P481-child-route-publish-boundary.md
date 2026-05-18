# Generic task publish route boundary decision

## Problem

`queue_service/routes.py` exposes a generic `/tasks/publish` path that directly calls `queue.publish`. It may be a legitimate internal adapter boundary, but it is the most visible direct publish API and should be explicitly decided rather than hand-waved.

## Success Criteria

- The `/tasks/publish` route and any related direct route publish behavior are inspected.
- The decision is recorded: retain as adapter boundary, tighten with explicit contract/guard, or remove/replace.
- If retained, tests or guard evidence prove it does not bypass session-owned FSM/outbox rules.
- If changed, focused route/queue tests pass.
