# Generic FSM generation counter classification

## Problem

`task_fsm.py`, `saga_fsm.py`, `lease_fsm.py`, `queue_db.py`, and `saga_repo.py` contain generation counters for non-session FSMs. They must be classified separately from session generation authority.

## Success Criteria

- Generic FSM generation hits are classified as internal state-version counters or patched if externally malformed input can affect authority.
- Existing task/saga/lease focused tests pass.
- Final matrix avoids confusing generic FSM generation with Queue session generation.
