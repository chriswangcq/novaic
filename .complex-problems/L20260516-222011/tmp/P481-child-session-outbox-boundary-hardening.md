# Session outbox dispatcher boundary hardening

## Problem

`session_outbox.py` is intentionally the production boundary where durable session outbox effects become saga creation or queue publishes. Because it is a sanctioned direct side-effect location, it needs narrow guards proving that session-owned side effects do not appear elsewhere.

## Success Criteria

- Session outbox dispatcher direct effects are documented as the required boundary.
- Guards/tests verify `.saga_orchestrator.create(` and session-owned `queue.publish` effects remain limited to the intended dispatcher or explicit worker boundaries.
- Any discovered session-owned side-effect bypass outside the dispatcher is removed or split.
- Focused session outbox tests pass.
