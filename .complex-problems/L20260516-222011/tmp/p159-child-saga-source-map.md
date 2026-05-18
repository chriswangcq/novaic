# ReAct saga prepare-context source ordering map

## Problem

The source-level saga step order must be mapped precisely enough to show whether `prepare_context` is the immediate data predecessor for `call_llm`.

## Success Criteria

- `react_think.py` step definitions are mapped with line pointers for `prepare_context`, `call_llm`, and relevant payload builders.
- The saga engine dependency assumption for `prev_result` is documented from source or tests.
- Any source branch that can bypass `prepare_context` before `call_llm` is classified.
- The result states whether source inspection found a blocking ordering defect.
