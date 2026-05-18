# Patch runtime attach generation validation

## Problem Definition

Runtime session attach still reads active session generation with a raw `int(... or 0)` coercion, which can hide malformed active state and violate explicit generation boundaries.

## Proposed Solution

Replace the raw coercion in `SessionRepository.dispatch` attach handling with `_require_positive_generation(current_active.get("generation"), "active session attach")`, preserving the existing stale-generation comparison semantics while rejecting malformed active state.

## Acceptance Criteria

- No raw `int(current_active.get("generation") or 0)` remains in `session_repo.py`.
- Focused runtime generation/attach tests pass.
- Compile check for `queue_service/session_repo.py` passes.

## Verification Plan

Run `python3 -m py_compile queue_service/session_repo.py` and focused runtime tests covering generation-checked attach and session repo/FSM boundaries.

## Risks

- If any historical active-state row lacks generation, this will now fail loudly instead of silently defaulting to `0`; this is intentional per no-backward-compatibility requirement.

## Assumptions

- Active session generation is semantically positive in runtime attach paths.
