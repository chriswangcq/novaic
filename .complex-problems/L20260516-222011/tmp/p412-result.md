# React contract residue classification result

## Summary

Completed the React contract classification pass. No dangerous `session_generation` fallback remains in `react_think.py` or `react_actions.py`. The remaining numeric defaults are loop-control counters (`round_num`, retry counts, stack depth) rather than session-generation authority.

## Done

- Ran a targeted guard over `react_think.py` and `react_actions.py`.
- Classified `session_generation`:
  - both contracts import and use `require_positive_session_generation` / `require_positive_session_generation_value`;
  - `session_generation` is propagated from source context/action payloads, not defaulted to `0` or `1`.
- Classified `round_num`:
  - defaults to round `1` for agent loop sequencing and idempotency keys;
  - not used as session-generation authority.
- Classified retry counters:
  - `no_tool_retry_count`, `stack_hold_retry_count`, and `repeated_tool_error_count` are loop retry counters.
- Classified `stack_depth`:
  - stack-depth defaults to `0` for stack-empty/force-finalize decisions and archive metadata, not session identity.

## Verification

- Guard artifact: `.complex-problems/L20260516-222011/tmp/p412/react-contract-guard.txt`.
- Focused test run from `novaic-agent-runtime`:
  - `PYTHONPATH=.:../novaic-common pytest -q tests/test_runtime_explicit_contracts.py`
  - Result: `16 passed in 0.13s`.

## Known Gaps

- None for P412's React contract scope.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p412/react-contract-guard.txt`
