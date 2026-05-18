# Verify Cortex workspace persists tool step payload refs

## Problem Definition

Cortex workspace persistence must keep heavy tool outputs in durable payload records and keep step records pointer-based through `step_ref`/`payload_ref`.

## Proposed Solution

Inspect `novaic-cortex/novaic_cortex/workspace.py` around payload writing, payload reading, step writing, and step indexing. Run focused Cortex tests that exercise context-event step writes and step index outcomes.

## Acceptance Criteria

- Workspace functions for `write_payload`, `read_payload`, and `write_step` are mapped.
- Evidence shows step records contain pointer metadata and payload records are stored separately.
- Focused Cortex persistence tests pass.

## Verification Plan

Use `rg`/`nl`/`sed` on `workspace.py` and targeted pytest files for context event API step writes and step indexing.

## Risks

- Tests may cover API wrappers rather than direct workspace internals; include code pointer evidence.

## Assumptions

- Runtime handoff to these workspace functions is handled separately by `P236`.
