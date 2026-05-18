# Audit and generic FSM generation classification

## Problem

Widened guard hits remain in audit/projector code and generic task/saga/lease FSM infrastructure. These may be safe counters/adapters, but they need explicit classification so session-generation cleanup does not leave misleading residue.

## Success Criteria

- Classify `session_audit.py`, `queue_audit.py`, `task_fsm.py`, `saga_fsm.py`, `lease_fsm.py`, `queue_db.py`, and `saga_repo.py` generation hits.
- Patch any live authority path that silently defaults generation in a way that can accept stale input.
- Leave only documented safe counter/projection hits.
- Run focused tests for any changed modules.
