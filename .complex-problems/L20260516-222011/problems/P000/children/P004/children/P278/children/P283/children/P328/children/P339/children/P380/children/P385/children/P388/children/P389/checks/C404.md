# P389 check: not successful yet

## Summary

R381 closed several real default-boundary problems, and the focused tests are meaningful. However, P389's own criteria require a final widened-guard matrix with no unclassified generation residue. The result body itself records two suspicious live-adjacent generation hits plus broader round/counter hits. Under the requested skeptical review standard, P389 is not solved yet.

## Blocking Gaps

- Criterion "no unclassified session generation residue" is not satisfied: `novaic-agent-runtime/queue_service/session_fsm.py` still contains `event_generation=int(decision.payload.get("event_generation") or 0)`, which is a generation-like control-plane default in the session FSM decision boundary.
- Criterion "no unclassified session generation residue" is also not satisfied: `novaic-agent-runtime/task_queue/sagas/subagent_wake.py` still coerces `session_generation` with `int(ctx["session_generation"])`, and this looks closer to live session attach semantics than to a harmless metric counter.
- The widened guard still lists `round_num`/counter/default hits in session outbox, Cortex handlers/API, generic FSMs, and worker metrics. Some are probably acceptable, but the check cannot treat them as solved until the final matrix explicitly classifies or patches them.
- The verification is strong for the patched narrow session-generation surface, but insufficient for the broader P389 success criterion.

## Result IDs

- R381
