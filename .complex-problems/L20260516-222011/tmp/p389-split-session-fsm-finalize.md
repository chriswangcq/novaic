# Session FSM finalize generation validation

## Problem

`queue_service/session_fsm.py` still reduces finalize events with raw `int(event.payload.get("finalize_generation") or 0)` and `int(state.generation or 0)`. The pure FSM should not silently accept bool or malformed finalize generation when called directly.

## Success Criteria

- Session finalize decision path uses explicit positive/non-negative generation validation appropriate to input/state semantics.
- Focused session FSM tests reject bool/malformed finalize generation and preserve valid accept/reject behavior.
- Widened guard no longer reports unclassified live session FSM generation coercion.
