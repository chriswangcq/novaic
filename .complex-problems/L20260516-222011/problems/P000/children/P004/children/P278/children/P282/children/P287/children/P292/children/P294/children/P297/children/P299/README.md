# Problem: Dispatch start-wake helper implementation

## Problem

Implement the chosen helper extraction in `SessionRepository.dispatch()` and remove duplicated start-wake construction code.

## Success Criteria

- Production code compiles.
- Duplicate start-wake construction block is removed or reduced to one shared helper call.
- No unrelated behavior/refactor churn is introduced.
