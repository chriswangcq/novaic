# Patch session FSM finalize generation validation

## Problem Definition

The pure session FSM finalize reducer still coerces `finalize_generation` and current state generation with raw `int(... or 0)`, making direct FSM calls less deterministic and potentially accepting bool values as integer generation.

## Proposed Solution

Introduce local explicit generation normalization helpers in `session_fsm.py`: positive validation for finalize event generation and non-negative validation for existing state generation. Use them inside `_reduce_session_finalize`, and add focused unit tests covering bool/malformed generation rejection while preserving normal accept/reject behavior.

## Acceptance Criteria

- `_reduce_session_finalize` no longer uses raw `int(... or 0)` for finalize/current generation.
- Bool and malformed finalize generation are rejected or deterministically represented as finalize rejection rather than accepted.
- Existing valid finalize accept/mismatch tests continue to pass.
- Widened guard no longer reports unclassified session FSM finalize generation coercion.

## Verification Plan

Run compile check for `queue_service/session_fsm.py` and focused tests covering session FSM/finalize ownership.

## Risks

- `decide_transition` reducer APIs return decisions rather than raising for invalid business events; validation design must preserve this contract where appropriate.

## Assumptions

- Pure FSM direct calls should be deterministic and should not depend on external caller validation for bool/malformed generation values.
