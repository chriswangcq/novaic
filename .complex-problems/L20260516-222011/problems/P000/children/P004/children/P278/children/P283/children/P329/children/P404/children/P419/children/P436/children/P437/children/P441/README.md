# Runtime bridge focused test fixture misses explicit session_generation

## Problem

The P437 focused runtime bridge test suite fails because `tests/test_pr85_llm_context_smoke_guardrails.py::test_tool_result_step_preserves_tool_call_id_and_step_ref` builds a React actions context without explicit `session_generation`. Production code correctly requires explicit positive session generation, so the test fixture is stale.

## Success Criteria

- The failing test fixture passes explicit positive `session_generation`.
- The focused runtime bridge test suite used by P437 passes.
- The change does not loosen the production explicit generation validator.
