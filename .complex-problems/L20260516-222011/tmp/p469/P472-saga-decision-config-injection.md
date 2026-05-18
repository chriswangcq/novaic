# Saga decision config injection

## Problem

`react_think.py` and `react_actions.py` currently read `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE` inside decision adapter functions, and `react_think.py` also reads `ServiceConfig.MAX_STACK_HOLD_RETRIES`. Move these values to an explicit configuration snapshot/provider at the saga or worker assembly boundary so decision construction is deterministic from explicit inputs.

## Success Criteria

- Decision adapter functions no longer directly read `ServiceConfig` for round/stack limits.
- Config values are supplied through an explicit object, provider, or saga context dependency.
- Tests can vary the limits without monkeypatching global `ServiceConfig`.
- Existing finalize/stack-hold behavior remains covered.
