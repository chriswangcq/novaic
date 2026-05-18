# Session FSM event generation boundary

## Problem

`novaic-agent-runtime/queue_service/session_fsm.py` still has `event_generation=int(decision.payload.get("event_generation") or 0)` in the session FSM decision boundary. This is a generation-like control-plane default inside the session FSM, so it must be patched or explicitly classified with evidence rather than left as an ambiguous fallback.

## Success Criteria

- Inspect the `event_generation` path in `session_fsm.py` and identify whether it is live authority, event sequencing metadata, or a dead/unused value.
- Remove any silent `or 0` fallback for live or event-sequencing generation-like data.
- Add focused regression tests if behavior changes.
- Rerun a targeted guard that no unclassified `event_generation` raw default remains.
- Document the classification in the result.
