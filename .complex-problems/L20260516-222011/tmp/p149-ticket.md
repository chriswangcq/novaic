# Verify Cortex API step projection endpoint

## Problem Definition

The Cortex API endpoint that records tool steps must enforce the new step contract at the HTTP boundary: unsafe inline result requests rejected, valid structured observations normalized, and durable step/index projections written with refs.

## Proposed Solution

Inspect the API request model and handler, then run and extend `test_context_event_api_steps_write.py` if needed so the endpoint path, not only workspace helpers, proves the contract.

## Acceptance Criteria

- API model and handler source pointers are recorded.
- Inline result is rejected through the API path.
- Valid API request writes step file and `_index.jsonl` row through `write_step_projection`.
- The test verifies observation/payload/index fields on persisted data.

## Verification Plan

Use `rg`/`nl` for source mapping, then run `test_context_event_api_steps_write.py` and `test_step_index_outcome.py`. Patch tests or endpoint code if any criterion is unproven.

## Risks

- API tests may mock too much and miss real workspace storage.
- Double-normalization may work but be wasteful; only behavioral contract is in scope here.

## Assumptions

- Existing API rejects invalid step payloads by returning HTTP errors from `normalize_step`.
- Full runtime producer shape is handled by sibling `P150`.
