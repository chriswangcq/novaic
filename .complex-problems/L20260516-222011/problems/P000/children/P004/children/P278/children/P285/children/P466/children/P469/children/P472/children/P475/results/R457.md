# React saga decision config model result

## Summary

Added the explicit config model and default provider boundary for react saga decision limits. No saga behavior is wired to the new model yet; that belongs to P476.

## Done

- Added `novaic-agent-runtime/task_queue/contracts/react_saga_config.py` with `ReactSagaDecisionConfig`.
- Added `novaic-agent-runtime/task_queue/sagas/react_config.py` with `default_react_saga_decision_config()`.
- Kept `ServiceConfig` access in the saga adapter/provider layer, not in the pure contract module.

## Verification

- `python -m py_compile novaic-agent-runtime/task_queue/contracts/react_saga_config.py novaic-agent-runtime/task_queue/sagas/react_config.py` exited `0`.

## Known Gaps

- P476 still needs to wire this config into `react_think.py` and `react_actions.py`.
- P477 still needs tests proving callers can vary limits without monkeypatching global `ServiceConfig`.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p475/pycompile.log`
- `.complex-problems/L20260516-222011/tmp/p475/pycompile.exit`
