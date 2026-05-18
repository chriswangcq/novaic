# React contract positive session generation

## Problem Definition

`ReactThinkInput` and `ReactActionsInput` currently default `session_generation` to `0` and parse missing values as `0`. Their finalize-trigger builders forward that generation into `wake_finalize` contexts. Since wake-finalize now requires positive generation, these upstream contracts should fail early and explicitly instead of creating malformed finalize contexts.

## Proposed Solution

1. Add strict positive session-generation parsing to `task_queue/contracts/react_think.py` and `task_queue/contracts/react_actions.py`.
2. Remove dataclass default `session_generation: int = 0` where the input can feed finalize-trigger payloads.
3. Update tests in `tests/test_runtime_explicit_contracts.py`:
   - contexts that exercise prepare/LLM payloads must provide positive `session_generation`.
   - add missing/zero-generation rejection tests for both ReactThinkInput and ReactActionsInput.
   - verify finalize-trigger payloads preserve positive generation.
4. Run focused runtime contract tests and source guards.

## Acceptance Criteria

- Missing or non-positive session generation fails in both react input factories.
- React finalize-trigger payloads cannot be built from a zero-generation source.
- Existing valid runtime explicit contract tests still pass with explicit positive generation.
- Source guards show no `ctx.get("session_generation") or 0` in react contracts.

## Verification Plan

- `python3 -m py_compile task_queue/contracts/react_think.py task_queue/contracts/react_actions.py`
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_runtime_explicit_contracts.py tests/test_pr254_finalize_ownership.py`
- Source guard over react contracts for `session_generation.*or 0`.

## Risks

- Some tests may omit `session_generation` for non-finalize paths. Prefer making those tests explicit rather than restoring defaults.

## Assumptions

- Runtime contexts should always know the current positive session generation by the time react_think/react_actions run.
