# Verify attach worker-only cutover after patches

## Problem

After the logger and boundary test fixes, the attach worker-only cutover needs correct compile and focused test verification from the right working directory, followed by a broader session FSM/outbox focused suite if the first suite passes.

## Success Criteria

- `python3 -m py_compile queue_service/session_repo.py queue_service/session_outbox.py` passes from `novaic-agent-runtime`.
- Focused attach/boundary tests pass from `novaic-agent-runtime`.
- Broader session FSM/outbox focused tests pass from `novaic-agent-runtime` or any failure is recorded as a new explicit follow-up.
- Verification confirms no new eager attach publish path exists.
