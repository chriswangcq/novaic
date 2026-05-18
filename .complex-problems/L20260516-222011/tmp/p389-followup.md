# Close remaining unclassified generation-like guard hits

## Problem

P389 still has widened-guard residue after R381. Two hits are too close to live control-plane semantics to leave as "probably safe": the session FSM `event_generation` default and the subagent wake saga `session_generation` coercion. Broader round/counter hits also need a final explicit matrix so the project does not keep ambiguous stale/default code.

## Success Criteria

- Inspect and either patch or explicitly classify `novaic-agent-runtime/queue_service/session_fsm.py` `event_generation=int(decision.payload.get("event_generation") or 0)`.
- Inspect and either patch or explicitly classify `novaic-agent-runtime/task_queue/sagas/subagent_wake.py` `session_generation` coercion.
- Produce a widened guard matrix that separates live session-generation authority, event-generation sequencing, round numbers, retry/health counters, and persistence/audit adapters.
- Patch any remaining live authority/default hit with explicit validators or typed inputs.
- Add focused regression tests for every patched live boundary.
- Rerun the narrow generation guard, the widened guard, and focused tests; no unclassified residue may remain.
