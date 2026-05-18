# Context projection regression test audit result

## Summary

Audited and ran focused context projection/read-model/leakage regression suites. Existing coverage, plus the new authority guards from `P157/P158`, adequately backs the current classification: `context.jsonl`/`read_context` projection helpers are materialized/debug and notification-hint support paths, not authoritative LLM prepare inputs.

## Done

- Identified Cortex projection/read-model tests:
  - `novaic-cortex/tests/test_context_event_api_context_writes.py`
  - `novaic-cortex/tests/test_context_event_read_model.py`
  - `novaic-cortex/tests/test_context_event_projection.py`
  - `novaic-cortex/tests/test_context_event_no_compat.py`
  - `novaic-cortex/tests/test_context_event_read_source_guards.py`
- Identified Runtime projection/leakage tests:
  - `novaic-agent-runtime/tests/test_context_read_by_ids.py`
  - `novaic-agent-runtime/tests/test_context_read_ordering.py`
  - `novaic-agent-runtime/tests/test_pr113_no_wake_im_replay.py`
  - `novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- Confirmed guard coverage now spans:
  - message append projections and corrupt projection handling,
  - ContextEvent read-model behavior,
  - no legacy prepare fallback,
  - notification-only `context.read`,
  - historical/raw tool payload and display image leakage boundaries.
- No new implementation gap was found in this ticket.

## Verification

- Cortex suite passed:
  - `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_api_context_writes.py novaic-cortex/tests/test_context_event_read_model.py novaic-cortex/tests/test_context_event_projection.py novaic-cortex/tests/test_context_event_no_compat.py novaic-cortex/tests/test_context_event_read_source_guards.py`
  - Result: `49 passed`.
- Runtime suite passed:
  - `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_context_read_by_ids.py novaic-agent-runtime/tests/test_context_read_ordering.py novaic-agent-runtime/tests/test_pr113_no_wake_im_replay.py novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - Result: `35 passed`.
- Search command reviewed:
  - `rg -n "read_context|append_context|context projection|ContextEventReadModel|context_event|payload|historical|tool image|display|step_ref" novaic-cortex/tests novaic-agent-runtime/tests -g '*.py'`

## Known Gaps

- No blocking test gap was found for this projection boundary.
- Some test discovery output included `__pycache__` files when using `find`; those are ignored/generated artifacts and not part of the committed coverage map.

## Artifacts

- Ledger result for `P155/T144`.
- Focused pytest evidence above.
