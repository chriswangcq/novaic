# Wake-finalize payload positive generation check

## Summary

Success. The one-go change is narrow, tested, and directly removes the wake-finalize zero-generation fallback. The remaining handler/route/upstream defaults are not silently accepted as solved and are already assigned to sibling tickets.

## Evidence

- `novaic-agent-runtime/task_queue/sagas/wake_finalize.py::_session_generation(...)` now raises for missing/`None` `session_generation` and for `generation < 1`.
- `_build_session_ended_payload(...)` still uses `_session_generation(...)`, so the `session.ended` payload cannot be built with implicit zero generation from this path.
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` includes:
  - valid positive generation payload preservation.
  - missing generation rejection.
  - zero generation rejection.
- Verification: `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py` -> `7 passed in 0.12s`.
- Source guard in `task_queue/sagas/wake_finalize.py` found no remaining `session_generation") or 0` / `session_generation.*or 0` fallback.

## Criteria Map

- `wake_finalize.py` no longer silently emits `generation=0`: satisfied by strict `_session_generation`.
- Missing or non-positive session generation fails before `session.ended` payload publish: satisfied; payload construction raises before the saga step can return a payload.
- Existing valid wake-finalize payload test still passes: satisfied.
- New tests cover missing and zero generation: satisfied.

## Execution Map

- Production code changed only in `task_queue/sagas/wake_finalize.py`.
- Test code changed only in `tests/test_pr254_finalize_ownership.py`.
- Verification was limited and focused to the changed saga payload builder and finalize ownership tests.

## Stress Test

- Plausible failure mode: an upstream context omits `session_generation`, and wake-finalize previously emitted `generation=0`. New test proves this raises.
- Plausible compatibility residue: an upstream context explicitly passes `session_generation=0`. New test proves this raises.
- Valid positive path remains covered and still passes.

## Residual Risk

- Non-blocking for P341: handler/route still need their own positive generation enforcement in P342.
- Non-blocking for P341: upstream react contract defaults still need cleanup or explicit delegation in P343/P337/P339.

## Result IDs

- R323
