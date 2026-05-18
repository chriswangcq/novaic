# Map Cortex prepare_for_llm read-model authority

## Problem Definition

Cortex `/v1/context/prepare_for_llm` must use the ContextEvent read-model authority and must not read `context.jsonl` directly.

## Proposed Solution

Inspect endpoint implementation and context read-model functions, then run focused Cortex context read-model tests.

## Acceptance Criteria

- Endpoint and read-model helper source pointers are listed.
- No endpoint call to `read_context` exists.
- Focused context read-model tests pass.

## Verification Plan

Use `nl`/`rg` and run `test_context_event_read_model.py`, `test_context_event_projection.py`, and relevant API tests.

## Risks

- Endpoint may delegate to a helper with an ambiguous name; follow calls to the actual data source.

## Assumptions

- Runtime caller behavior is handled by sibling `P157`.
