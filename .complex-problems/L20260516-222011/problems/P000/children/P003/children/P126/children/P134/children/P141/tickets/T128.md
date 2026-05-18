# Audit workspace payload store and blob externalization

## Problem Definition

Workspace payload storage is the explicit retrieval boundary for large tool outputs. We must verify local JSON payloads, external blob payloads, manifests, and failure status updates so normal context can remain pointer-oriented while full data remains recoverable by reference.

## Proposed Solution

Inspect `workspace.py` payload functions and tests:

- `write_payload`
- `read_payload`
- `_payload_read_error` / manifest status updates if relevant
- payload-related `write_step` tests
- payload inspection API tests for bounded explicit retrieval

Run focused payload/step tests. Fix any local active gap or split if the issue belongs to a different layer.

## Acceptance Criteria

- Source pointers map local JSON and external blob payload records.
- Source pointers map manifest fields and read failure status updates.
- Tests verify local payload readback, large payload externalization, missing/corrupt/mismatch/blob failures, missing blob client, and bounded payload APIs.
- Any active issue is fixed or split.

## Verification Plan

- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_step_index_outcome.py novaic-cortex/tests/test_payload_inspection_api.py`

## Risks

- `test_step_index_outcome.py` also covers step indexes; keep this ticket focused on payload sections and leave index-specific findings to P142.

## Assumptions

- Full payloads may be stored locally or in blob, but normal LLM context should carry only compact projection text plus references.
