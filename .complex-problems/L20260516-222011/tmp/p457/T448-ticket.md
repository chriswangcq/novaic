# Ticket: Run Cortex focused compatibility behavior tests

## Problem Definition

The Cortex side of P454 must prove context event lifecycle, projection, payload inspection, shell blob contract, and legacy lifecycle removal behave as designed after the cleanup and contract narrowing.

## Proposed Solution

Run this focused Cortex test suite from `novaic-cortex`:

```bash
PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q \
  tests/test_context_event_api_lifecycle.py \
  tests/test_context_event_api_skill_lifecycle.py \
  tests/test_context_event_api_steps_write.py \
  tests/test_context_event_api_context_writes.py \
  tests/test_payload_inspection_api.py \
  tests/test_context_event_read_source_guards.py \
  tests/test_context_event_no_compat.py \
  tests/test_context_event_projection.py \
  tests/test_context_event_store.py \
  tests/test_pr74_scope_summary_contract.py \
  tests/test_pr57_list_archived_summaries.py \
  tests/test_shell_capabilities_blob_contract.py \
  tests/test_tool_output_projection.py \
  tests/test_step_result_projection.py \
  tests/test_legacy_skill_lifecycle_removed.py \
  tests/test_lock_and_compat_boundary_guards.py
```

Save stdout/stderr and exit status under `.complex-problems/L20260516-222011/tmp/p457/`.

## Acceptance Criteria

- Test command and log are saved.
- Exit status is 0.
- Log summary shows all selected tests pass.
- Any failure becomes a repair follow-up instead of being classified away.

## Verification Plan

- Inspect saved log tail and pytest summary.
- Record result only after the suite completes.
