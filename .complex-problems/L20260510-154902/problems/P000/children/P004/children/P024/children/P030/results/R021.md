# Notification attachment event emission completed

## Summary

Cut `/v1/scope/append_input` onto `InputNotificationAttached` events. The endpoint now appends one event per requested message id before preserving the transitional metadata merge, and retry/duplicate requests do not create duplicate notification events.

## Done

- Wired `ContextEventWriter.input_notification_attached` into `scope_append_input`.
- Resolved root stream identity from the target `scope_path`.
- Recorded target scope id in each notification event payload.
- Used stable idempotency keys through the writer for each notification id.
- Added focused tests for initial append and retry/dedup behavior.

## Verification

- Focused notification/lifecycle/projection tests:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_lifecycle.py tests/test_pr67_wake_child_api.py tests/test_context_event_projection.py -q`
  - Result: `37 passed in 0.32s`
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `433 passed in 0.60s`

## Residual Risk

- `source_kind` is currently fixed to `im_message` because `ScopeAppendInputRequest` does not yet carry richer source metadata.
- Legacy `meta.input_message_ids` remains as transitional projection/debug state until P028 cleanup.

## Artifacts

- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/tests/test_context_event_api_lifecycle.py`
