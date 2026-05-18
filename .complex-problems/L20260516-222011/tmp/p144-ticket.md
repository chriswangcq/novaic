# Map Cortex API materialization call sites

## Problem Definition

Cortex API endpoints can both append authoritative ContextEvents and materialize workspace debug/retrieval files. Those dual paths must be mapped precisely so `context.jsonl`, `steps/*.json`, `_index.jsonl`, and payload retrieval remain intentional projections instead of divergent authority.

## Proposed Solution

Inspect `novaic-cortex/novaic_cortex/api.py` endpoint handlers and their `Workspace` calls for context writes, batch writes, tool step writes, step formatting/preview, and payload reads. Classify each call site as authoritative event append, materialized projection write, explicit payload retrieval, or legacy/stale path. Run focused API tests for context writes and step writes. If a duplicate active write path can diverge from ContextEvents, fix it or split a blocking child problem.

## Acceptance Criteria

- API call sites for context message writes, batch writes, tool step writes, and payload reads are listed with source pointers.
- Each call site is classified with authority/projection/retrieval status.
- Focused Cortex API context-write and step-write tests pass.
- Any duplicate active write path that can diverge from ContextEvents is fixed or explicitly split.

## Verification Plan

- Search `api.py` for context write/read, steps write/read/format/preview, and payload read endpoints.
- Follow each endpoint into `Workspace` calls and classify the boundary.
- Run `test_context_event_api_context_writes.py`, `test_context_event_api_steps_write.py`, and nearby contract/read tests.
- Add a focused guard only if endpoint mapping reveals an unguarded divergent write path.

## Risks

- Some endpoints intentionally materialize files after appending events; do not misclassify intentional projection writes as stale.
- Payload reads are retrieval surfaces and may not append ContextEvents; classify them separately from writes.
- If call-site mapping becomes broad, split into context API and step/payload API children instead of producing a vague result.

## Assumptions

- `Workspace` internals were already audited in sibling `P141/P142/P143`; this ticket focuses on API endpoints and their call-site intent.
