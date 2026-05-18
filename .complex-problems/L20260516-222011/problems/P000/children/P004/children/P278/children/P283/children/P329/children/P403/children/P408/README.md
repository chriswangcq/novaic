# Generic Queue infrastructure generation classification

## Problem

Generic Queue infrastructure files (`queue_db`, `saga_repo`, `task_fsm`, generic FSM state stores) contain `generation` and `or 0` patterns. These may be valid infrastructure counters, but they must be explicitly classified or patched if they influence live session authority.

## Success Criteria

- Inspect `queue_db.py`, `saga_repo.py`, `task_fsm.py`, and generic FSM generation hits from P402.
- Distinguish generic FSM generations from live session-generation authority.
- Patch dangerous live session-adjacent defaults, or document safe generic semantics with tests/evidence.
- Add focused tests if any generic infrastructure boundary is changed.
- Rerun generic Queue infrastructure guards.
