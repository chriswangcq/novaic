# Wake finalize remaining-stack strictness

## Problem

`wake_finalize.py` currently accepts absent `remaining_stack` and fabricates an empty one. That makes finalize look structurally valid while possibly losing stack state. This belongs under P489 because finalize ownership should require explicit reason, generation, and remaining stack semantics.

## Success Criteria

- `wake_finalize.py` requires `remaining_stack` to be a dict for scope-end and session-ended payloads.
- Legacy fallback synthesis from `stack_known_at_finalize` / `stack_depth_at_finalize` is removed or made unreachable by strict validation.
- Focused tests cover valid pass-through and missing/invalid stack rejection.
- Focused tests pass.
