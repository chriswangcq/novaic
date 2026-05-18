# ReAct saga prepare-context ordering guard success check

## Summary

`P165` is successful. The result adds the missing direct guard: if `call_llm` no longer depends on `prepare_context`, or if `save_response` no longer depends on `call_llm`, the focused DAG integration test fails.

## Evidence

- `R144` updated `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`.
- The test now asserts:
  - `prepare_context` appears before `call_llm`.
  - `call_llm.depends_on == ["prepare_context"]`.
  - `save_response.depends_on == ["call_llm"]`.
  - Existing `trigger_actions.depends_on == ["decide_actions"]` still holds.
- Verification passed with `17 passed`.

## Criteria Map

- Existing tests/static guards around prepare-before-LLM are identified: satisfied; existing DAG test was broad and missing the direct assertion.
- If no direct guard exists, a small focused guard is added: satisfied by the patch to `test_react_think_dag_dependencies`.
- The guard is run with focused runtime tests: satisfied by the recorded pytest command.
- The result documents exactly which ordering regression the guard catches: satisfied by `R144` and this check.

## Execution Map

- `T149` was one-go because it was a single test guard patch.
- The patch was small, targeted, and verified immediately.

## Stress Test

- Regression mode caught: a future edit reorders the active ReAct think saga so `call_llm` no longer receives `prepare_context` as its first dependency.
- Regression mode caught: `save_response` no longer follows `call_llm`, which could make response persistence consume the wrong previous result.

## Residual Risk

- No blocking residual risk for this guard leaf. Handler response shape and continuity residue remain with sibling problems.

## Result IDs

- R144
