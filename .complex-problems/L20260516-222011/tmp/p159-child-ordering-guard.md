# ReAct saga prepare-context ordering guard

## Problem

Source mapping is not enough; a future edit could reorder or bypass `prepare_context`. A focused test/static guard should fail if `call_llm` stops depending on the prepare-context result.

## Success Criteria

- Existing tests/static guards around `prepare_context` before `call_llm` are identified.
- If no direct guard exists, a small focused guard is added.
- The guard is run with focused runtime tests.
- The result documents exactly which ordering regression the guard catches.
