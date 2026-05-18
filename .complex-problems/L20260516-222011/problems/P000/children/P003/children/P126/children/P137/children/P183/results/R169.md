# Active stack stale injection cleanup audit result

## Summary

Audited active-stack-related leftovers across runtime, common, and Cortex. No stale production duplicate injection path was found. The remaining matches are active implementation, prompt/tool contract text, context budget handling for transient stack snapshots, or tests that intentionally guard against old adapters and file-walk collectors.

## Done

- Searched for active-stack literals, local stack formatter names, old collector names, stack snapshot metadata, and file-walk-like patterns across:
  - `novaic-agent-runtime`
  - `novaic-common`
  - `novaic-cortex`
- Classified suspicious matches:
  - Active implementation: `novaic-common/common/contracts/llm_assembly.py`.
  - Active prompt contracts: `novaic-common/common/contracts/prompt_fragments.py`.
  - Active tool schema descriptions: `novaic-common/common/tools/llm_builtin.py`.
  - Active no-tool warning wording: `novaic-agent-runtime/task_queue/utils/no_tool_warning.py`.
  - Active context budgeting metadata handling: `novaic-cortex/novaic_cortex/context_stack/budget.py`.
  - Test-only guardrails: `test_pr85_llm_context_smoke_guardrails.py`, `test_llm_assembly_contract.py`, `test_context_event_read_source_guards.py`, `test_no_tool_warning.py`.
- Confirmed no runtime local `_format_skill_stack_system_message` implementation remains.
- Confirmed no Cortex `_collect_active_stack` production helper remains.

## Verification

- Common/runtime stack assembly guard tests passed:

```bash
PYTHONPATH=novaic-common:novaic-agent-runtime:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-common/tests/test_llm_assembly_contract.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py \
  novaic-agent-runtime/tests/test_no_tool_warning.py
```

Result: `24 passed in 0.10s`.

- Cortex source-guard test passed:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_context_event_read_source_guards.py
```

Result: `9 passed in 0.01s`.

- A combined common/runtime/Cortex pytest command was attempted first and hit the known Python `tests` package import collision; the same targets were then rerun in separated invocations and passed.

## Known Gaps

- No stale active-stack production path found.
- `novaic-cortex/novaic_cortex/context_stack/types.py` and budget compaction still exist as active context-budget infrastructure, not as duplicate active-stack injection. Any broader context-stack cleanup should be handled by a separate non-P183 problem.

## Artifacts

- `novaic-common/common/contracts/llm_assembly.py`
- `novaic-common/common/contracts/prompt_fragments.py`
- `novaic-common/common/tools/llm_builtin.py`
- `novaic-agent-runtime/task_queue/utils/no_tool_warning.py`
- `novaic-cortex/novaic_cortex/context_stack/budget.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-common/tests/test_llm_assembly_contract.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
