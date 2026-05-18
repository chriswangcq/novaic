# Session FSM event generation cleanup ticket

## Problem Definition

`session_fsm.py` still computes `event_generation` with `int(decision.payload.get("event_generation") or 0)`. This hides missing/bool/malformed event generation-like data behind a default and leaves the widened guard unclosed.

## Proposed Solution

Inspect how `event_generation` is used in the session FSM result. If it is needed, replace the inline fallback with an explicit non-bool/non-negative validator or a typed optional boundary. If it is unnecessary or only diagnostic, remove it from the decision payload path. Add focused tests for malformed input if the behavior is live.

## Acceptance Criteria

- No raw `event_generation=int(... or 0)` fallback remains in `session_fsm.py`.
- The replacement behavior is deterministic and explicitly handles missing/bool/malformed values.
- Focused tests cover the changed boundary or removal.
- Targeted guard for `event_generation` passes.

## Verification Plan

- Inspect references to `event_generation`.
- Patch `session_fsm.py`.
- Add/update focused session FSM tests.
- Run targeted tests and `rg` guard for `event_generation`.

## Risks

- If `event_generation` is unused, keeping compatibility may preserve dead residue.
- If it is used by downstream audit, over-rejection could reveal missing test fixture fields.

## Assumptions

- There is no need to silently accept bool or malformed generation-like data at the FSM boundary.
