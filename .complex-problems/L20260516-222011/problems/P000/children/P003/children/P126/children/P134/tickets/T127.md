# Audit workspace materialized projections and payload references

## Problem Definition

Workspace materialized files (`context.jsonl`, `steps/*.json`, `steps/_index.jsonl`, `payloads/*.json`) are important for observability and retrieval, but they must not be mistaken for the authoritative LLM context source now that ContextEvents drive read-model preparation. We need to verify their exact roles and payload reference behavior.

## Proposed Solution

Audit `novaic-cortex/novaic_cortex/workspace.py` and related API/tests across these slices:

- Payload write/read and blob externalization.
- Tool step normalization/write/index behavior.
- Context projection append/read helpers for `context.jsonl`.
- API call sites that append ContextEvents and materialize debug projections.

Classify each path as active source, materialized debug/read surface, compatibility, or stale. Fix narrow stale/misleading behavior if discovered; otherwise split into focused children.

## Acceptance Criteria

- Result maps payload write/read, step write/index, and context append/projection functions.
- Tool step write behavior is verified to reject inline raw `result` and require payload/payload_ref when writing raw payloads.
- `context.jsonl` append/read paths are classified relative to ContextEvent read-model authority.
- Tests for payload externalization, step indexes, and context writes are identified and run.
- Any stale or misleading materialized projection path is removed or split.

## Verification Plan

- Inspect:
  - `novaic-cortex/novaic_cortex/workspace.py`
  - `novaic-cortex/novaic_cortex/api.py`
  - relevant tests under `novaic-cortex/tests`
- Likely tests:
  - `novaic-cortex/tests/test_step_index_outcome.py`
  - `novaic-cortex/tests/test_workspace.py`
  - `novaic-cortex/tests/test_context_event_api_context_writes.py`
  - `novaic-cortex/tests/test_context_event_api_steps_write.py`
  - `novaic-cortex/tests/test_payload_inspection_api.py`

## Risks

- This ticket spans multiple workspace surfaces. If it grows beyond a clean audit/fix, split into payload, step, context-projection, and API-call-site children.
- `context.jsonl` may remain valid as an observability projection; deleting it would be wrong unless all consumers are mapped.

## Assumptions

- ContextEvent read-model is the authoritative LLM context source.
- Workspace materialized projections remain useful for inspection, replay, and payload retrieval unless proven stale.
