# LLM payload handoff regression coverage check

## Summary

`P170` is solved. The coverage audit maps concrete tests to the plausible regressions they catch, and the focused runtime slice passes. The one-go path is acceptable because builder/contract/handler work had already been split and this leaf only judged coverage.

## Evidence

- Builder authority guard: `test_runtime_explicit_contracts.py:34-67`.
- Contract preprocessing/tool guard: `test_runtime_explicit_contracts.py:100-142`.
- Handler no-context-read guard: `test_runtime_explicit_contracts.py:253-260`.
- Bridge prepare endpoint guard: `test_runtime_explicit_contracts.py:308-330`.
- Prepared snapshot versus legacy projection guard: `test_pr85_llm_context_smoke_guardrails.py:131-160`.
- Saga ordering guard: `test_saga_dag_refactor.py` asserts `prepare_context` before `call_llm` and `call_llm.depends_on == ["prepare_context"]`.
- Focused test result: `31 passed in 0.35s`.

## Criteria Map

- Existing tests listed with pointers: satisfied.
- Plausible regression per test stated: satisfied in `R153`.
- Missing direct guards added or split: satisfied; previous leaves added direct guards for stale local tools, payload tools, and bridge endpoint.
- Focused runtime tests run: satisfied.

## Execution Map

- `T158` one-go executed after source/handler leaves were closed.
- Coverage audit recorded as `R153`.

## Stress Test

The mapped guards catch these likely failures: stale local tools entering `llm.call`; payload tools being dropped before provider call; handler reading Cortex context directly; bridge posting prepare calls to the read endpoint; prepare handler using legacy context projection as provider authority; and saga calling LLM before prepare context completes.

## Residual Risk

- Coverage is focused on the runtime prepared-snapshot handoff path, not unrelated UI/log display behavior.

## Result IDs

- R153
