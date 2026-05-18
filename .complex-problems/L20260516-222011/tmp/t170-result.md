# Active stack source and projection audit result

## Summary

Mapped the active stack source/projection path. The active stack control-plane source of truth is `novaic-cortex`'s operational-store backed `active_stack_projection`, not workspace file walking. Cortex lifecycle APIs write/read/finalize this projection, while runtime only queries Cortex status or calls skill lifecycle endpoints through the bridge.

## Done

- Identified source-of-truth module: `novaic-cortex/novaic_cortex/active_stack_projection.py`.
- Mapped projection helpers:
  - `normalize_active_stack_frames`
  - `write_active_stack_projection`
  - `read_active_stack_projection`
  - `finalize_active_stack_projection`
- Mapped Cortex API call sites:
  - root/wake scope create initializes or writes stack projection,
  - `context_skill_begin` reads top scope from projection and writes pushed stack,
  - `context_skill_end` enforces LIFO from projection and writes popped stack,
  - `context_status` uses projection for cheap stack status,
  - archive/finalize records remaining stack and clears projection.
- Mapped runtime call sites:
  - `handle_cortex_skill_end` calls Cortex `context_skill_end`,
  - `handle_cortex_check_stack` calls Cortex `context_status`.
- Searched for file-walk active-stack collectors or duplicate stack builders in production code. No stale production stack collector was found.

## Verification

- Source search for stale patterns (`_collect_active_stack`, file walking, active stack prompt text) found no production bypass except the user-facing no-tool warning text.
- Focused Cortex tests passed:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_active_stack_projection.py \
  novaic-cortex/tests/test_context_event_api_skill_lifecycle.py \
  novaic-cortex/tests/test_context_event_read_source_guards.py \
  novaic-cortex/tests/test_operational_store.py
```

Result: `43 passed in 0.54s`.

## Known Gaps

- This ticket intentionally does not verify final LLM message ordering or current display media behavior; those are covered by sibling children P181 and P182.
- No active-stack source/projection production gap found.

## Artifacts

- `novaic-cortex/novaic_cortex/active_stack_projection.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/operational_store.py`
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- `novaic-cortex/tests/test_active_stack_projection.py`
- `novaic-cortex/tests/test_context_event_api_skill_lifecycle.py`
- `novaic-cortex/tests/test_context_event_read_source_guards.py`
