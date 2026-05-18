# Add ReAct saga prepare-context ordering guard

## Problem Definition

Existing tests cover broad DAG behavior and explicit payload builders, but they do not directly assert that the active `react_think` DAG makes `call_llm` depend on `prepare_context`. Without that direct guard, a future reorder could silently bypass the prepared ContextEvent snapshot.

## Proposed Solution

Add a focused assertion to the ReAct DAG integration test that checks the active `react_think` nodes contain `prepare_context`, `call_llm`, and `save_response` in the expected dependency chain: `call_llm.depends_on == ["prepare_context"]` and `save_response.depends_on == ["call_llm"]`. Run the focused DAG test and runtime explicit contract tests.

## Acceptance Criteria

- Existing guard coverage is identified as broad but missing direct `call_llm -> prepare_context` dependency assertion.
- A focused guard is added or an equivalent existing guard is cited.
- Focused runtime tests pass.
- The result states the exact regression caught by the guard.

## Verification Plan

- Patch `novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py`.
- Run `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/integration/test_saga_dag_refactor.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`.

## Risks

- The test should assert dependency semantics, not incidental list indexes beyond what is required.
- Do not use this guard to overclaim handler response shape; sibling problems own that.

## Assumptions

- The `react_think` DAG built by `get_saga_definition("react_think").to_dag()` is the active saga plan source for task dependencies.
