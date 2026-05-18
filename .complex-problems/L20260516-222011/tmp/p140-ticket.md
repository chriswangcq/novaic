# Audit ContextEvent read model and budget boundary

## Problem Definition

`ContextEventReadModel.prepare` is the boundary that turns authoritative ContextEvents into prepared LLM context. It must read the event stream, reject missing streams, project through the pure model, apply budget compaction, compute usage, and normalize the stack without falling back to legacy context assembly.

## Proposed Solution

Inspect `novaic-cortex/novaic_cortex/context_event_read_model.py` and `novaic-cortex/tests/test_context_event_read_model.py`. Record:

- Prepared context shape and status behavior.
- Empty root path behavior versus non-empty missing stream reset.
- Projection call and budget compaction boundary.
- Token counting and usage ratio calculation.
- Top-first stack normalization and wake `skill_name` normalization.
- Evidence that no legacy fallback is used in this layer.

Run the dedicated read-model tests. If a fallback or untested active behavior is found, fix if local or spawn a follow-up.

## Acceptance Criteria

- Result maps read model behavior with source pointers.
- Result identifies and runs read-model tests.
- Result explicitly classifies legacy fallback risk.
- Any active issue is fixed or split.

## Verification Plan

- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_read_model.py`

## Risks

- This ticket should not duplicate pure projection tests; projection internals are owned by P139.
- Budget compaction internals are not fully audited here unless read-model wiring reveals an issue.

## Assumptions

- Missing event stream for a non-empty root should raise reset-required, not silently use old context files.
