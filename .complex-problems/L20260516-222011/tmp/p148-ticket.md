# Audit active write_step_projection call sites

## Problem Definition

Lower-level workspace step contracts are only useful if active API/runtime paths actually pass structured observations into `write_step_projection`. This audit must catch any call site that still writes legacy inline result strings, skips payload refs, or bypasses the workspace projection boundary.

## Proposed Solution

Map all active `write_step_projection` and direct `write_step` call sites outside tests, inspect their request/observation shapes, and run focused API tests that exercise the active projection path. Patch call sites or tests if any route can still persist legacy inline results or miss `step_ref`/`payload_ref`.

## Acceptance Criteria

- All active non-test call sites for `write_step_projection` and `write_step` are mapped.
- Active tool-step API path passes structured observation/percept data, not raw inline result strings.
- Active path propagates `step_ref`, `payload_ref`, and artifact metadata into workspace storage/index.
- A focused test proves one active projection path from request to stored step file and index row.

## Verification Plan

Use `rg` to find call sites, inspect API request models and tests, then run `test_context_event_api_steps_write.py` plus step-index tests. Add coverage if the active path lacks artifact/index assertion.

## Risks

- Tests may exercise workspace methods directly but not the actual API endpoint.
- Runtime bridge code outside Cortex may call the API with stale shapes; this ticket can map Cortex boundary but may spawn a child if runtime-side request generation needs changes.

## Assumptions

- Test-only direct `write_step` usage is acceptable when it exercises the workspace contract.
- The active Cortex API should reject unsafe step requests before writing durable projections.
